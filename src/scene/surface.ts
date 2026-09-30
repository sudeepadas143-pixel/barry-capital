/**
 * Where scene art gets drawn. The building, the animation pass and the
 * renderer only talk to a Surface, so the same drawing code can produce:
 *
 *  - a CanvasSurface: vector paths on a 2D canvas at the screen's own
 *    resolution, anti-aliased, with real fonts (the site uses this), or
 *  - a PixelSurface: a plain pixel buffer, for Node scripts that write
 *    reference PNGs and for tests.
 *
 * Coordinates are always scene pixels (W × H); a CanvasSurface maps them to
 * device pixels with a uniform scale `k`.
 */
import { drawText, textWidth } from './font';
import { PixelBuffer } from './buffer';
import { over } from '../art/props';
import type { SpriteImage } from '../art/figure';

export type Pt = [number, number];

/** Maps text space (u right, v down) to scene pixels: (a·u + c·v + e, b·u + d·v + f). */
export interface Affine {
  a: number;
  b: number;
  c: number;
  d: number;
  e: number;
  f: number;
}

/** Something drawn from a procedural image, rendered at whatever resolution the surface needs. */
export interface SpriteSrc {
  id: string;
  /** Render with `k` image pixels per scene pixel. */
  render: (k: number) => SpriteImage;
}

export type FontKind = 'sans' | 'serif' | 'mono';

export interface TextOpts {
  font: FontKind;
  /** Font size in text-space units (world units on iso planes). */
  size: number;
  color: number;
  weight?: number;
  italic?: boolean;
  align?: 'left' | 'center' | 'right';
  /** Extra space between letters, in text units. */
  spacing?: number;
}

export interface StripItem {
  text: string;
  color: number;
}

export interface Surface {
  readonly w: number;
  readonly h: number;
  poly(pts: Pt[], c: number, alpha?: number): void;
  rect(x: number, y: number, w: number, h: number, c: number, alpha?: number): void;
  ellipse(cx: number, cy: number, rx: number, ry: number, c: number, alpha?: number): void;
  /** Draw a sprite with its bottom centre at (x, y). With `m`, the sprite's own pixel space (scene px, origin top-left) is mapped through m instead. */
  sprite(src: SpriteSrc, x: number, y: number, m?: Affine): void;
  /** Text with its baseline at v = 0. */
  text(s: string, m: Affine, o: TextOpts): void;
  /** Width of a string in text units. */
  measure(s: string, o: TextOpts): number;
  /** Run `draw` with output limited to a polygon. */
  clip(pts: Pt[], draw: () => void): void;
  /** Fade existing pixels inside `pts` along a line: gone at `from`, untouched at `to` (eased). */
  fade(pts: Pt[], from: Pt, to: Pt): void;
  /** Draw a full-size pixel buffer (custom art) stretched over the surface. */
  image(buf: PixelBuffer): void;
  /**
   * A looping line of text items on a plane, scrolled by `offset` text units and
   * clipped to `width`. Returns false if the surface can't do it cheaply.
   */
  ticker?(items: StripItem[], o: TextOpts, gap: number, m: Affine, offset: number, width: number): boolean;
}

const FAMILY: Record<FontKind, string> = {
  sans: "'Inter Tight', 'Helvetica Neue', Arial, sans-serif",
  serif: "'EB Garamond', Georgia, serif",
  mono: "'JetBrains Mono', ui-monospace, Menlo, monospace",
};

// ---------------------------------------------------------------- pixels

function inside(poly: Pt[], x: number, y: number): boolean {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}

export class PixelSurface implements Surface {
  private clipPoly: Pt[] | null = null;
  constructor(readonly buf: PixelBuffer) {}
  get w() {
    return this.buf.w;
  }
  get h() {
    return this.buf.h;
  }

  poly(pts: Pt[], c: number, alpha = 1) {
    if (!this.clipPoly) return this.buf.poly(pts, c, alpha);
    const cp = this.clipPoly;
    this.buf.polyEach(pts, (x, y) => {
      if (!inside(cp, x + 0.5, y + 0.5)) return;
      if (alpha >= 1) this.buf.data[y * this.buf.w + x] = c;
      else this.buf.tint(x, y, c, alpha);
    });
  }

  rect(x: number, y: number, w: number, h: number, c: number, alpha = 1) {
    this.poly([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], c, alpha);
  }

  ellipse(cx: number, cy: number, rx: number, ry: number, c: number, alpha = 1) {
    const pts: Pt[] = [];
    for (let i = 0; i < 20; i++) {
      const a = (i / 20) * Math.PI * 2;
      pts.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]);
    }
    this.poly(pts, c, alpha);
  }

  private static cache = new Map<string, SpriteImage>();
  sprite(src: SpriteSrc, x: number, y: number, m?: Affine) {
    let img = PixelSurface.cache.get(src.id);
    if (!img) {
      img = src.render(1);
      if (PixelSurface.cache.size > 1000) PixelSurface.cache.clear();
      PixelSurface.cache.set(src.id, img);
    }
    const d = this.buf.data;
    const W = this.buf.w;
    const H = this.buf.h;
    if (m) {
      for (let j = 0; j < img.h; j++)
        for (let i = 0; i < img.w; i++) {
          const c = img.px[j * img.w + i];
          if (!c) continue;
          const px = Math.round(m.a * i + m.c * j + m.e);
          const py = Math.round(m.b * i + m.d * j + m.f);
          if (px >= 0 && py >= 0 && px < W && py < H) d[py * W + px] = over(d[py * W + px], c);
        }
      return;
    }
    const x0 = Math.round(x - img.w / 2);
    const y0 = Math.round(y - img.h);
    for (let j = 0; j < img.h; j++) {
      const py = y0 + j;
      if (py < 0 || py >= H) continue;
      for (let i = 0; i < img.w; i++) {
        const c = img.px[j * img.w + i];
        const px = x0 + i;
        if (c && px >= 0 && px < W) d[py * W + px] = over(d[py * W + px], c);
      }
    }
  }

  /** Falls back to the 3×5 pixel font, scaled to the requested cap height. */
  text(s: string, m: Affine, o: TextOpts) {
    const cell = (o.size * 0.72) / 5;
    const width = this.measure(s, o);
    const u0 = o.align === 'center' ? -width / 2 : o.align === 'right' ? -width : 0;
    const map = (u: number, v: number): Pt => [m.a * u + m.c * v + m.e, m.b * u + m.d * v + m.f];
    drawText(s.toUpperCase(), (dx, dy) => {
      const u = u0 + dx * cell;
      const v = -5 * cell + dy * cell;
      this.poly([map(u, v), map(u + cell, v), map(u + cell, v + cell), map(u, v + cell)], o.color);
    });
  }

  measure(s: string, o: TextOpts): number {
    return textWidth(s) * ((o.size * 0.72) / 5);
  }

  clip(pts: Pt[], draw: () => void) {
    const prev = this.clipPoly;
    this.clipPoly = pts;
    draw();
    this.clipPoly = prev;
  }

  fade(pts: Pt[], from: Pt, to: Pt) {
    const dx = to[0] - from[0];
    const dy = to[1] - from[1];
    const len2 = dx * dx + dy * dy || 1;
    const d = this.buf.data;
    this.buf.polyEach(pts, (x, y) => {
      const i = y * this.buf.w + x;
      const col = d[i];
      if (!col) return;
      const t = Math.max(0, Math.min(1, ((x + 0.5 - from[0]) * dx + (y + 0.5 - from[1]) * dy) / len2));
      d[i] = ((Math.round(((col >>> 24) & 255) * t * t) << 24) | (col & 0xffffff)) >>> 0;
    });
  }

  image(buf: PixelBuffer) {
    if (buf.w === this.buf.w && buf.h === this.buf.h) this.buf.over(buf);
  }
}

// ---------------------------------------------------------------- canvas

const cssCache = new Map<number, string>();
export function css(c: number): string {
  let s = cssCache.get(c);
  if (!s) {
    s = `rgb(${c & 255},${(c >>> 8) & 255},${(c >>> 16) & 255})`;
    cssCache.set(c, s);
  }
  return s;
}

type Ctx = CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D;
type AnyCanvas = HTMLCanvasElement | OffscreenCanvas;

export function makeCanvas(w: number, h: number): AnyCanvas {
  if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(w, h);
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  return c;
}

/** Sprite images turned into canvases, by id and resolution. */
const spriteCanvases = new Map<string, { c: AnyCanvas; w: number; h: number }>();

export function spriteCanvas(src: SpriteSrc, k: number): { c: AnyCanvas; w: number; h: number } {
  const key = `${src.id}@${k.toFixed(3)}`;
  let hit = spriteCanvases.get(key);
  if (hit) return hit;
  const img = src.render(k);
  const c = makeCanvas(Math.max(1, img.w), Math.max(1, img.h));
  const ctx = c.getContext('2d') as Ctx;
  if (img.w && img.h) {
    const data = ctx.createImageData(img.w, img.h);
    new Uint32Array(data.data.buffer).set(img.px);
    ctx.putImageData(data, 0, 0);
  }
  hit = { c, w: img.w / k, h: img.h / k };
  if (spriteCanvases.size > 1500) spriteCanvases.clear();
  spriteCanvases.set(key, hit);
  return hit;
}

export class CanvasSurface implements Surface {
  readonly ctx: Ctx;
  /** Width of the anti-aliasing seam cover, in scene pixels. */
  private seam: number;
  constructor(
    readonly canvas: AnyCanvas,
    readonly w: number,
    readonly h: number,
    readonly k: number,
  ) {
    this.ctx = canvas.getContext('2d') as Ctx;
    this.seam = 0.8 / k;
    this.reset();
  }

  reset() {
    const { ctx, k } = this;
    ctx.setTransform(k, 0, 0, k, 0, 0);
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = 'source-over';
    ctx.lineJoin = 'bevel';
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
  }

  clear() {
    const { ctx } = this;
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.restore();
  }

  poly(pts: Pt[], c: number, alpha = 1) {
    if (pts.length < 3) return;
    const { ctx } = this;
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
    ctx.closePath();
    const col = css(c);
    if (alpha < 1) {
      ctx.globalAlpha = alpha;
      ctx.fillStyle = col;
      ctx.fill();
      ctx.globalAlpha = 1;
      return;
    }
    ctx.fillStyle = col;
    ctx.fill();
    // A hairline in the same colour hides the seams between neighbouring faces.
    ctx.strokeStyle = col;
    ctx.lineWidth = this.seam;
    ctx.stroke();
  }

  rect(x: number, y: number, w: number, h: number, c: number, alpha = 1) {
    const { ctx } = this;
    ctx.globalAlpha = alpha;
    ctx.fillStyle = css(c);
    ctx.fillRect(x, y, w, h);
    ctx.globalAlpha = 1;
  }

  ellipse(cx: number, cy: number, rx: number, ry: number, c: number, alpha = 1) {
    const { ctx } = this;
    ctx.globalAlpha = alpha;
    ctx.fillStyle = css(c);
    ctx.beginPath();
    ctx.ellipse(cx, cy, Math.max(0.01, rx), Math.max(0.01, ry), 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  }

  sprite(src: SpriteSrc, x: number, y: number, m?: Affine) {
    const { ctx } = this;
    if (m) {
      // Render at the resolution the transform needs.
      const scale = Math.hypot(m.a, m.b) * this.k;
      const s = spriteCanvas(src, scale);
      ctx.save();
      ctx.transform(m.a, m.b, m.c, m.d, m.e, m.f);
      ctx.drawImage(s.c, 0, 0, s.w, s.h);
      ctx.restore();
      return;
    }
    const s = spriteCanvas(src, this.k);
    ctx.drawImage(s.c, x - s.w / 2, y - s.h, s.w, s.h);
  }

  private font(o: TextOpts, px: number) {
    return `${o.italic ? 'italic ' : ''}${o.weight ?? 500} ${px}px ${FAMILY[o.font]}`;
  }

  text(s: string, m: Affine, o: TextOpts) {
    const { ctx } = this;
    // Draw at a large font size and scale down, so small text keeps its shapes.
    const unitPx = Math.hypot(m.a, m.b) * this.k;
    const px = Math.max(4, o.size * unitPx);
    const q = o.size / px;
    ctx.save();
    ctx.transform(m.a * q, m.b * q, m.c * q, m.d * q, m.e, m.f);
    ctx.font = this.font(o, px);
    ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = css(o.color);
    const spacing = (o.spacing ?? 0) / q;
    if (!spacing) {
      ctx.textAlign = o.align ?? 'left';
      ctx.fillText(s, 0, 0);
    } else {
      // Letter-spaced text, laid out by hand for browsers without letterSpacing.
      const widths = [...s].map((ch) => ctx.measureText(ch).width);
      const total = widths.reduce((a, b) => a + b, 0) + spacing * (widths.length - 1);
      let x = o.align === 'center' ? -total / 2 : o.align === 'right' ? -total : 0;
      ctx.textAlign = 'left';
      [...s].forEach((ch, i) => {
        ctx.fillText(ch, x, 0);
        x += widths[i] + spacing;
      });
    }
    ctx.restore();
  }

  private measured = new Map<string, number>();
  measure(s: string, o: TextOpts): number {
    const key = `${o.font}|${o.weight ?? 500}|${o.italic ? 1 : 0}|${o.spacing ?? 0}|${s}`;
    let per = this.measured.get(key);
    if (per === undefined) {
      const { ctx } = this;
      ctx.save();
      ctx.font = this.font(o, 100);
      per = ctx.measureText(s).width / 100 + ((o.spacing ?? 0) * Math.max(0, [...s].length - 1)) / o.size;
      ctx.restore();
      this.measured.set(key, per);
    }
    return per * o.size;
  }

  clip(pts: Pt[], draw: () => void) {
    const { ctx } = this;
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
    ctx.closePath();
    ctx.clip();
    draw();
    ctx.restore();
  }

  fade(pts: Pt[], from: Pt, to: Pt) {
    const { ctx } = this;
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
    ctx.closePath();
    ctx.clip();
    ctx.globalCompositeOperation = 'destination-out';
    const g = ctx.createLinearGradient(from[0], from[1], to[0], to[1]);
    // Remaining alpha is t², so erase 1 − t².
    for (let i = 0; i <= 10; i++) {
      const t = i / 10;
      g.addColorStop(t, `rgba(0,0,0,${(1 - t * t).toFixed(3)})`);
    }
    ctx.fillStyle = g;
    let x0 = Infinity;
    let y0 = Infinity;
    let x1 = -Infinity;
    let y1 = -Infinity;
    for (const [x, y] of pts) {
      x0 = Math.min(x0, x);
      y0 = Math.min(y0, y);
      x1 = Math.max(x1, x);
      y1 = Math.max(y1, y);
    }
    ctx.fillRect(x0 - 1, y0 - 1, x1 - x0 + 2, y1 - y0 + 2);
    ctx.restore();
  }

  private strips = new Map<string, { c: AnyCanvas; units: number; per: number }>();
  ticker(items: StripItem[], o: TextOpts, gap: number, m: Affine, offset: number, width: number): boolean {
    if (!items.length) return true;
    const unitPx = Math.hypot(m.a, m.b) * this.k;
    const key = `${o.size}|${unitPx.toFixed(3)}|${items.map((i) => i.text + i.color).join('|')}`;
    let strip = this.strips.get(key);
    if (!strip) {
      const widths = items.map((it) => this.measure(it.text, o) + gap);
      const units = widths.reduce((a, b) => a + b, 0);
      const per = unitPx;
      const hUnits = o.size * 1.3;
      const c = makeCanvas(Math.max(1, Math.ceil(units * per)), Math.max(1, Math.ceil(hUnits * per)));
      const ctx = c.getContext('2d') as Ctx;
      ctx.font = this.font(o, o.size * per);
      ctx.textBaseline = 'alphabetic';
      let x = 0;
      items.forEach((it, i) => {
        ctx.fillStyle = css(it.color);
        ctx.fillText(it.text, x * per, o.size * per);
        x += widths[i];
      });
      strip = { c, units, per };
      if (this.strips.size > 40) this.strips.clear();
      this.strips.set(key, strip);
    }
    const { ctx } = this;
    const q = 1 / strip.per;
    ctx.save();
    ctx.transform(m.a, m.b, m.c, m.d, m.e, m.f);
    // Now in text units; the strip's baseline sits at v = 0.
    let u = -((((offset % strip.units) + strip.units) % strip.units));
    for (let i = 0; i < 8 && u < width; i++) {
      ctx.drawImage(strip.c, u, -o.size, strip.units, strip.c.height * q);
      u += strip.units;
    }
    ctx.restore();
    return true;
  }

  image(buf: PixelBuffer) {
    const c = makeCanvas(buf.w, buf.h);
    const cx = c.getContext('2d') as Ctx;
    cx.putImageData(buf.toImageData(), 0, 0);
    this.ctx.drawImage(c, 0, 0, this.w, this.h);
  }

  /** Composite another canvas-backed surface of the same size. */
  draw(other: CanvasSurface) {
    const { ctx } = this;
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(other.canvas, 0, 0);
    ctx.restore();
  }
}
