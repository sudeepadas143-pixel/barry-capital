/**
 * A native-resolution pixel buffer. All scene art is written here as exact
 * colours (no anti-aliasing), then blitted to a canvas and upscaled with
 * nearest-neighbour sampling.
 */

/** '#rrggbb' → packed ABGR (little-endian RGBA in memory). */
export function rgba(hex: string, a = 255): number {
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return ((a << 24) | (b << 16) | (g << 8) | r) >>> 0;
}

export function mixColor(c: number, over: number, t: number): number {
  const lerp = (sh: number) => {
    const a = (c >>> sh) & 255;
    const b = (over >>> sh) & 255;
    return Math.round(a + (b - a) * t) & 255;
  };
  return ((255 << 24) | (lerp(16) << 16) | (lerp(8) << 8) | lerp(0)) >>> 0;
}

export class PixelBuffer {
  readonly data: Uint32Array;
  constructor(
    readonly w: number,
    readonly h: number,
  ) {
    this.data = new Uint32Array(w * h);
  }

  clear() {
    this.data.fill(0);
  }

  set(x: number, y: number, c: number) {
    x |= 0;
    y |= 0;
    if (x < 0 || y < 0 || x >= this.w || y >= this.h) return;
    this.data[y * this.w + x] = c;
  }

  get(x: number, y: number): number {
    if (x < 0 || y < 0 || x >= this.w || y >= this.h) return 0;
    return this.data[y * this.w + x];
  }

  /** Blend a colour over what's there, `t` in 0..1. */
  tint(x: number, y: number, c: number, t: number) {
    if (x < 0 || y < 0 || x >= this.w || y >= this.h) return;
    const i = y * this.w + x;
    const under = this.data[i];
    this.data[i] = under ? mixColor(under, c, t) : c;
  }

  span(y: number, x0: number, x1: number, c: number) {
    if (y < 0 || y >= this.h) return;
    const a = Math.max(0, x0);
    const b = Math.min(this.w, x1);
    if (b <= a) return;
    this.data.fill(c, y * this.w + a, y * this.w + b);
  }

  rect(x: number, y: number, w: number, h: number, c: number) {
    for (let j = 0; j < h; j++) this.span(y + j, x, x + w, c);
  }

  /** Fill a convex polygon, sampling pixel centres. Edges from integer iso coords never pass through a centre. */
  poly(pts: [number, number][], c: number, alpha = 1) {
    let minY = Infinity;
    let maxY = -Infinity;
    for (const [, y] of pts) {
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }
    const y0 = Math.max(0, Math.floor(minY));
    const y1 = Math.min(this.h - 1, Math.ceil(maxY));
    const n = pts.length;
    for (let py = y0; py <= y1; py++) {
      const yc = py + 0.5;
      let xl = Infinity;
      let xr = -Infinity;
      for (let i = 0; i < n; i++) {
        const [ax, ay] = pts[i];
        const [bx, by] = pts[(i + 1) % n];
        if (ay === by) continue;
        if ((yc < ay && yc < by) || (yc > ay && yc > by)) continue;
        const x = ax + ((yc - ay) * (bx - ax)) / (by - ay);
        if (x < xl) xl = x;
        if (x > xr) xr = x;
      }
      if (xl === Infinity) continue;
      const a = Math.ceil(xl - 0.5);
      const b = Math.ceil(xr - 0.5);
      if (alpha >= 1) this.span(py, a, b, c);
      else for (let x = a; x < b; x++) this.tint(x, py, c, alpha);
    }
  }

  /** Visit the pixels a convex polygon covers (same sampling as `poly`). */
  polyEach(pts: [number, number][], fn: (x: number, y: number) => void) {
    let minY = Infinity;
    let maxY = -Infinity;
    for (const [, y] of pts) {
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }
    const n = pts.length;
    for (let py = Math.max(0, Math.floor(minY)); py <= Math.min(this.h - 1, Math.ceil(maxY)); py++) {
      const yc = py + 0.5;
      let xl = Infinity;
      let xr = -Infinity;
      for (let i = 0; i < n; i++) {
        const [ax, ay] = pts[i];
        const [bx, by] = pts[(i + 1) % n];
        if (ay === by) continue;
        if ((yc < ay && yc < by) || (yc > ay && yc > by)) continue;
        const x = ax + ((yc - ay) * (bx - ax)) / (by - ay);
        if (x < xl) xl = x;
        if (x > xr) xr = x;
      }
      if (xl === Infinity) continue;
      for (let x = Math.max(0, Math.ceil(xl - 0.5)); x < Math.min(this.w, Math.ceil(xr - 0.5)); x++) fn(x, py);
    }
  }

  /** Copy every non-transparent pixel of `src` over this buffer. */
  over(src: PixelBuffer) {
    const s = src.data;
    const d = this.data;
    for (let i = 0; i < s.length; i++) if (s[i]) d[i] = s[i];
  }

  toImageData(): ImageData {
    return new ImageData(new Uint8ClampedArray(this.data.buffer as ArrayBuffer, this.data.byteOffset, this.data.byteLength), this.w, this.h);
  }
}

/** A sparse copy of a layer's opaque pixels, for fast per-frame compositing. */
export class Sparse {
  readonly idx: Int32Array;
  readonly col: Uint32Array;
  constructor(src: PixelBuffer) {
    let n = 0;
    for (let i = 0; i < src.data.length; i++) if (src.data[i]) n++;
    this.idx = new Int32Array(n);
    this.col = new Uint32Array(n);
    let k = 0;
    for (let i = 0; i < src.data.length; i++)
      if (src.data[i]) {
        this.idx[k] = i;
        this.col[k++] = src.data[i];
      }
  }
  draw(dst: PixelBuffer) {
    const d = dst.data;
    for (let k = 0; k < this.idx.length; k++) d[this.idx[k]] = this.col[k];
  }
}
