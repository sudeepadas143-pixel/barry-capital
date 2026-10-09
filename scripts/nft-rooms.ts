/**
 * Front-on rooms of the building, for Investors backgrounds. Drawn on the
 * 80×80 NFT grid with the same Painter, shading and outlines as the site's
 * figures and props, so they sit behind an Investor without looking pasted.
 *
 * The Investor covers roughly x 18–62 from y 14 down, so each room keeps its
 * best detail along the top and at the sides.
 */
import { Painter, capsule, ellipse, poly, renderBust, type SpriteImage } from '../src/art/figure';
import { PARTNER_LOOK } from '../src/art/partner';
import { blitAt, renderBull, renderGlobe, renderPlant } from '../src/art/props';
import { PixelBuffer, rgba } from '../src/scene/buffer';
import { drawText, textWidth } from '../src/scene/font';
import { shade } from '../src/art/palette';

const G = 80;
const INK = rgba('#1b1815');
const hx = (h: string, a = 0) => rgba(a ? shade(h, a) : h);

type Scene = { buf: PixelBuffer; rect: (x: number, y: number, w: number, h: number, c: number) => void; obj: (draw: (p: Painter) => void, outline?: boolean) => void; sprite: (img: SpriteImage, x: number, y: number) => void };

function scene(): Scene {
  const buf = new PixelBuffer(G, G);
  const rect = (x: number, y: number, w: number, h: number, c: number) => {
    for (let j = Math.max(0, y); j < Math.min(G, y + h); j++) for (let i = Math.max(0, x); i < Math.min(G, x + w); i++) buf.data[j * G + i] = c;
  };
  /** Draw an object on its own layer, outline it like the figures, then lay it down. */
  const obj = (draw: (p: Painter) => void, outline = true) => {
    const p = new Painter(G, G, 0, 0, 1);
    draw(p);
    if (outline) p.outline(INK);
    for (let i = 0; i < p.px.length; i++) if (p.px[i]) buf.data[i] = p.px[i];
  };
  const sprite = (img: SpriteImage, x: number, y: number) => blitAt(buf, img, x, y);
  return { buf, rect, obj, sprite };
}

/** 4×4 ordered dither between two colours, `t` from 0 to 1. */
const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
const dither = (x: number, y: number, t: number) => t * 16 > BAYER[(y & 3) * 4 + (x & 3)] + 0.5;

/** Sky and towers through a window from (x0, y0) to (x1, y1). */
function skyline(s: Scene, x0: number, y0: number, x1: number, y1: number, seed = 1, dusk = false) {
  const top = hx(dusk ? '#f0b07a' : '#bcd8ea');
  const low = hx(dusk ? '#e9d2a8' : '#e3eef4');
  for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) s.buf.data[y * G + x] = dither(x, y, (y - y0) / (y1 - y0)) ? low : top;
  let x = x0 - 2;
  let k = seed * 7;
  while (x < x1) {
    k = (k * 1103515245 + 12345) >>> 0;
    const w = 5 + (k % 5);
    const h = 6 + ((k >>> 8) % Math.max(4, y1 - y0 - 4));
    const body = hx(['#6f8396', '#5d7084', '#7c8fa0', '#53667a'][(k >>> 4) % 4]);
    const lit = hx(dusk ? '#f6d48a' : '#dbe8f0');
    for (let j = y1 - h; j < y1; j++)
      for (let i = Math.max(x0, x); i < Math.min(x1, x + w); i++) {
        const win = (j - (y1 - h)) % 2 === 1 && (i - x) % 2 === 1 && i < x + w - 1;
        s.buf.data[j * G + i] = win && ((i * 7 + j * 3 + k) % 3 !== 0) ? lit : body;
      }
    x += w + 1;
  }
}

/** A window band with mullions. */
function windowBand(s: Scene, x0: number, y0: number, x1: number, y1: number, every = 13, dusk = false) {
  skyline(s, x0, y0, x1, y1, x0 + y0, dusk);
  const frame = hx('#2a2a2f');
  s.rect(x0 - 1, y0 - 1, x1 - x0 + 2, 1, frame);
  s.rect(x0 - 1, y1, x1 - x0 + 2, 1, frame);
  for (let x = x0 - 1; x <= x1; x += every) s.rect(x, y0, 1, y1 - y0, frame);
}

function monitor(p: Painter, x: number, y: number, w: number, h: number, up: boolean) {
  p.part(poly([[x, y], [x + w, y], [x + w, y + h], [x, y + h]]), hx('#24272d'), { shade: hx('#17191d') });
  p.part(poly([[x + 1, y + 1], [x + w - 1, y + 1], [x + w - 1, y + h - 1], [x + 1, y + h - 1]]), hx('#13291b'));
  const pts: [number, number][] = [];
  for (let i = 0; i <= 4; i++) pts.push([x + 1.5 + ((w - 3) * i) / 4, y + h - 2 - (up ? i : 4 - i) * ((h - 4) / 4) + (i % 2 ? 0.8 : 0)]);
  for (let i = 0; i < 4; i++) p.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], hx(up ? '#5fcf7a' : '#e0645a'), 0.5);
  p.part(poly([[x + w / 2 - 1, y + h], [x + w / 2 + 1, y + h], [x + w / 2 + 1, y + h + 2], [x + w / 2 - 1, y + h + 2]]), hx('#24272d'));
}

function deskTop(p: Painter, x0: number, x1: number, y: number) {
  const wood = hx('#7a5538');
  p.part(poly([[x0, y], [x1, y], [x1, y + 3], [x0, y + 3]]), wood, { hi: hx('#9a7050'), bottom: hx('#563a26') });
  p.part(poly([[x0 + 1, y + 3], [x1 - 1, y + 3], [x1 - 1, G], [x0 + 1, G]]), hx('#5f4029'), { shade: hx('#48301e') });
}

// ---------------------------------------------------------------- rooms

export const ROOMS: [string, () => PixelBuffer][] = [
  [
    'trading-floor',
    () => {
      const s = scene();
      s.rect(0, 0, G, G, hx('#e9e2cf'));
      windowBand(s, 2, 3, 78, 30, 12);
      s.rect(0, 58, G, G - 58, hx('#3a3d44'));
      for (let x = 0; x < G; x += 8) s.rect(x, 58, 1, G - 58, hx('#34373d'));
      s.obj((p) => {
        deskTop(p, -2, 20, 52);
        deskTop(p, 60, 82, 52);
        monitor(p, 1, 38, 9, 7, true);
        monitor(p, 10, 39, 9, 7, false);
        monitor(p, 61, 39, 9, 7, true);
        monitor(p, 70, 38, 9, 7, true);
        p.part(poly([[3, 50], [8, 50], [8, 52], [3, 52]]), hx('#2a2a2f'));
        p.part(ellipse(74, 50.5, 2, 1.5), hx('#f3efe6'), { shade: hx('#c9bfae') });
      });
      s.sprite(renderPlant('fern', 0.9), 40, 58);
      return s.buf;
    },
  ],
  [
    'corner-office',
    () => {
      const s = scene();
      for (let x = 0; x < G; x++) s.rect(x, 0, 1, G, hx(x % 6 === 0 ? '#4a3123' : x % 6 < 3 ? '#5c3d2b' : '#573a29'));
      windowBand(s, 44, 4, 78, 40, 11, true);
      s.rect(0, 62, G, G - 62, hx('#3d2a1f'));
      s.rect(0, 62, G, 1, hx('#2a1d15'));
      // Steve's portrait in a gold frame.
      s.obj((p) => {
        p.part(poly([[3, 5], [21, 5], [21, 27], [3, 27]]), hx('#d4a640'), { shade: hx('#a5812c'), hi: hx('#f0d58a') });
        p.part(poly([[5, 7], [19, 7], [19, 25], [5, 25]]), hx('#34405a'));
      });
      const bust = renderBust(PARTNER_LOOK, 18, true, 1);
      for (let y = 0; y < 18; y++) for (let x = 1; x < 15; x++) { const c = bust.px[y * 18 + x + 1]; if (c >>> 24 > 128) s.buf.data[(7 + y) * G + 4 + x] = c; }
      s.obj((p) => {
        p.part(poly([[60, 50], [82, 50], [82, 53], [60, 53]]), hx('#7a5538'), { hi: hx('#9a7050'), bottom: hx('#563a26') });
        p.part(poly([[61, 53], [81, 53], [81, G], [61, G]]), hx('#5f4029'), { shade: hx('#48301e') });
        p.part(poly([[64, 47], [72, 47], [72, 50], [64, 50]]), hx('#f3efe6'), { shade: hx('#c9bfae') });
        p.part(capsule(74, 49, 78, 49.6, 0.6), hx('#6b4428'));
        p.dot(78.4, 49.6, hx('#ff8a3c'), 0.6);
      });
      s.sprite(renderGlobe(0.75), 9, 62);
      return s.buf;
    },
  ],
  [
    'lobby',
    () => {
      const s = scene();
      s.rect(0, 0, G, G, hx('#efe8d6'));
      for (let x = 0; x < G; x += 16) s.rect(x, 0, 1, 56, hx('#ddd3bd'));
      for (let y = 18; y < 56; y += 12) s.rect(0, y, G, 1, hx('#e2d9c3'));
      // The gold sign.
      s.obj((p) => p.part(poly([[3, 3], [77, 3], [77, 13], [3, 13]]), hx('#24252b'), { shade: hx('#18191d'), hi: hx('#3a3c44') }));
      const text = "STEVE'S INVESTORS".replace("'", '');
      const tx = Math.round((G - textWidth(text)) / 2);
      drawText(text, (x, y) => { s.buf.data[(6 + y) * G + tx + x] = hx('#e0b54a'); });
      s.rect(0, 15, G, 2, hx('#8b2f30'));
      // Checker floor and the red runner.
      for (let y = 56; y < G; y++) for (let x = 0; x < G; x++) s.buf.data[y * G + x] = hx(((x >> 2) + (y >> 2)) % 2 ? '#e6e1d6' : '#2f2f33');
      s.rect(0, 56, G, 1, hx('#b88a38'));
      s.rect(0, 66, G, 6, hx('#8b2f30'));
      s.rect(0, 66, G, 1, hx('#b88a38'));
      s.rect(0, 71, G, 1, hx('#b88a38'));
      s.obj((p) => p.part(poly([[-2, 50], [22, 50], [22, 58], [-2, 58]]), hx('#2c2d33'), { hi: hx('#4a4c55'), shade: hx('#1d1e22') }));
      s.sprite(renderBull(0.75), 10, 51);
      s.sprite(renderPlant('palm', 1), 71, 64);
      return s.buf;
    },
  ],
  [
    'server-room',
    () => {
      const s = scene();
      s.rect(0, 0, G, G, hx('#222932'));
      s.rect(0, 2, G, 3, hx('#3a4552'));
      for (let x = 2; x < G; x += 6) s.rect(x, 5, 1, 4, hx('#2d3640'));
      s.rect(0, 66, G, G - 66, hx('#1a1f26'));
      for (let x = 0; x < G; x += 6) s.rect(x, 66, 1, G - 66, hx('#232a33'));
      s.obj((p) => {
        for (const x of [1, 14, 54, 67]) {
          p.part(poly([[x, 10], [x + 12, 10], [x + 12, 68], [x, 68]]), hx('#3a4552'), { shade: hx('#2a323c'), hi: hx('#4c5968') });
          for (let y = 13; y < 66; y += 4) {
            p.part(poly([[x + 1.5, y], [x + 10.5, y], [x + 10.5, y + 3], [x + 1.5, y + 3]]), hx('#151a20'));
          }
        }
      });
      for (const x of [1, 14, 54, 67])
        for (let y = 13; y < 66; y += 4) {
          s.buf.data[(y + 1) * G + x + 3] = hx((x + y) % 3 ? '#5fcf7a' : '#e2a33c');
          if ((x * y) % 5 === 0) s.buf.data[(y + 1) * G + x + 5] = hx('#6fb6ff');
          s.rect(x + 7, y + 1, 3, 1, hx('#2b333d'));
        }
      return s.buf;
    },
  ],
  [
    'screen-wall',
    () => {
      const s = scene();
      s.rect(0, 0, G, G, hx('#1b1d22'));
      s.obj((p) => {
        for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) monitor(p, 1 + c * 20, 2 + r * 18, 18, 14, (r + c) % 3 !== 0);
      });
      const tick = 'SOL +4.2  STEVE +12  BONK -3';
      s.rect(0, 70, G, 10, hx('#0e0f12'));
      drawText(tick, (x, y) => { if (x + 2 < G) s.buf.data[(73 + y) * G + x + 2] = hx(x < 32 ? '#5fcf7a' : '#e0b54a'); });
      return s.buf;
    },
  ],
  [
    'putting-green',
    () => {
      const s = scene();
      s.rect(0, 0, G, G, hx('#e9e2cf'));
      windowBand(s, 2, 3, 78, 40, 15);
      s.rect(0, 52, G, G - 52, hx('#6b4a33'));
      for (let y = 54; y < G; y += 3) s.rect(0, y, G, 1, hx('#5f412c'));
      s.obj((p) => {
        p.part(poly([[-4, 60], [84, 60], [84, 74], [-4, 74]]), hx('#4e9a52'), { hi: hx('#6fbc6e'), bottom: hx('#3a7a3e') });
        p.part(ellipse(70, 66, 2.2, 1.1), hx('#1a2a1a'));
        p.part(capsule(70, 66, 70, 46, 0.6), hx('#8f8a80'));
        p.part(poly([[70, 46], [77, 48.5], [70, 51]]), hx('#d0574a'), { shade: hx('#a83f35') });
        p.dot(9, 67, hx('#ffffff'), 1.1);
      });
      return s.buf;
    },
  ],
  [
    'wall-street',
    () => {
      const s = scene();
      skyline(s, 0, 0, G, 30, 4);
      // A stone facade with columns.
      s.rect(0, 12, G, 50, hx('#d9d1bf'));
      s.rect(0, 12, G, 3, hx('#c5bca8'));
      s.obj((p) => {
        for (const x of [2, 16, 58, 72]) p.part(poly([[x, 16], [x + 6, 16], [x + 6, 60], [x, 60]]), hx('#e6dfcf'), { shade: hx('#c2b9a5'), hi: hx('#f4efe4') });
      }, false);
      s.rect(0, 60, G, 4, hx('#b9b09c'));
      s.rect(0, 64, G, 6, hx('#9b978f'));
      s.rect(0, 70, G, G - 70, hx('#3b3d42'));
      for (let x = 2; x < G; x += 10) s.rect(x, 75, 5, 1, hx('#e6d27a'));
      // The street sign.
      s.obj((p) => {
        p.part(capsule(72, 64, 72, 30, 0.6), hx('#3a3d44'));
        p.part(poly([[62, 26], [79, 26], [79, 40], [62, 40]]), hx('#2f6b45'), { shade: hx('#244f34') });
      });
      drawText('WALL', (x, y) => { s.buf.data[(28 + y) * G + 63 + x] = hx('#f4f1e8'); });
      drawText('ST', (x, y) => { s.buf.data[(34 + y) * G + 67 + x] = hx('#f4f1e8'); });
      // A yellow cab.
      s.obj((p) => {
        p.part(poly([[-6, 66], [18, 66], [20, 72], [-6, 72]]), hx('#f2c230'), { shade: hx('#c99a1a'), hi: hx('#ffe07a') });
        p.part(poly([[-2, 61], [11, 61], [14, 66], [-4, 66]]), hx('#f2c230'), { shade: hx('#c99a1a') });
        p.part(poly([[0, 62], [10, 62], [12, 66], [-2, 66]]), hx('#9fc3dc'));
        p.part(ellipse(14, 73, 2.6, 2.6), hx('#222226'));
        p.part(ellipse(0, 73, 2.6, 2.6), hx('#222226'));
        p.part(poly([[3, 59], [8, 59], [8, 61], [3, 61]]), hx('#f4f1e8'));
      });
      return s.buf;
    },
  ],
];
