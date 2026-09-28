/**
 * Plants and the office cat, drawn with the same shaded-shape renderer as the
 * traders so the whole scene shares one finish. Design units, feet at y = 0.
 */
import { Painter, capsule, ellipse, poly, rgba, type Box, type SpriteImage, type Test } from './figure';

const LEAF = rgba('#5b8f55');
const LEAF_S = rgba('#3f6b41');
const LEAF_H = rgba('#86b872');
const POT = rgba('#b8704e');
const POT_S = rgba('#8c4f37');
const POT_H = rgba('#d08a66');
const SOIL = rgba('#4a3326');
const INK = rgba('#1d1a17');

/** An ellipse rotated by `a` radians. */
function leaf(cx: number, cy: number, rx: number, ry: number, a: number): [Test, Box] {
  const c = Math.cos(a);
  const s = Math.sin(a);
  const r = Math.max(rx, ry);
  return [
    (x, y) => {
      const dx = x - cx;
      const dy = y - cy;
      const u = (dx * c + dy * s) / rx;
      const v = (-dx * s + dy * c) / ry;
      return u * u + v * v <= 1;
    },
    [cx - r, cy - r, cx + r, cy + r],
  ];
}

function canvas(wu: number, hu: number, scale: number) {
  const w = Math.ceil(wu * scale) + 2;
  const h = Math.ceil(hu * scale) + 2;
  return new Painter(w, h, w / 2, h - 1, scale);
}

function pot(p: Painter, w: number, h: number) {
  p.part(poly([[-w / 2, -h], [w / 2, -h], [w * 0.36, 0], [-w * 0.36, 0]]), POT, { shade: POT_S, hi: POT_H });
  p.part(ellipse(0, -h, w / 2 + 0.6, 1.1), POT_H, { shade: POT });
  p.part(ellipse(0, -h - 0.1, w / 2 - 0.4, 0.6), SOIL);
}

function done(p: Painter): SpriteImage {
  p.outline(INK);
  return { w: p.w, h: p.h, px: p.px };
}

export type PlantKind = 'palm' | 'fern' | 'succulent' | 'shrub' | 'flowers';

export function renderPlant(kind: PlantKind, scale = 2): SpriteImage {
  if (kind === 'palm') {
    const p = canvas(22, 30, scale);
    pot(p, 7, 6);
    p.part(capsule(0, -6, 0.4, -16, 0.7), rgba('#6d5238'));
    const fronds: [number, number][] = [[-2.4, -0.5], [-1.7, -0.9], [-0.9, -1.2], [-0.2, -1.1], [0.6, -1.1], [1.3, -0.8], [2.2, -0.4], [2.9, -0.2], [-3.1, -0.1]];
    for (const [a] of fronds) {
      const ang = a;
      const cx = 0.4 + Math.cos(ang - Math.PI / 2) * 0;
      const len = 6.2;
      const dx = Math.sin(ang) * len;
      const dy = -Math.cos(ang) * len * 0.8;
      p.part(leaf(cx + dx * 0.6, -16 + dy * 0.6, len * 0.62, 1.25, Math.atan2(dy, dx)), LEAF, { shade: LEAF_S, hi: LEAF_H });
    }
    return done(p);
  }
  if (kind === 'fern') {
    const p = canvas(14, 14, scale);
    pot(p, 6, 4.5);
    for (let i = 0; i < 9; i++) {
      const a = -Math.PI / 2 + (i - 4) * 0.36;
      const len = 4.2 + (i % 2) * 1.1;
      p.part(leaf(Math.cos(a) * len * 0.55, -5 + Math.sin(a) * len * 0.55, len * 0.55, 1, a), i % 2 ? LEAF : LEAF_H, { shade: LEAF_S });
    }
    return done(p);
  }
  if (kind === 'succulent') {
    const p = canvas(7, 6, scale);
    pot(p, 3.6, 2.4);
    for (let i = 0; i < 6; i++) {
      const a = -Math.PI / 2 + (i - 2.5) * 0.55;
      p.part(leaf(Math.cos(a) * 1.3, -2.8 + Math.sin(a) * 1.2, 1.4, 0.7, a), i % 2 ? LEAF_H : LEAF, { shade: LEAF_S });
    }
    return done(p);
  }
  if (kind === 'shrub') {
    const p = canvas(12, 8, scale);
    for (const [x, y, r] of [[-3.2, -2.6, 2.6], [3, -2.8, 2.7], [0, -4.4, 3.2], [-1.2, -2.2, 2.4], [1.8, -2, 2.3]] as const)
      p.part(ellipse(x, y, r, r * 0.85), LEAF, { shade: LEAF_S, hi: LEAF_H });
    return done(p);
  }
  const p = canvas(8, 5, scale);
  const petals = [rgba('#e8a0b0'), rgba('#f2d36b'), rgba('#e8a0b0')];
  [-2.6, 0, 2.6].forEach((x, i) => {
    p.part(capsule(x, 0, x, -2.6, 0.35), LEAF_S);
    p.part(ellipse(x, -3, 1, 0.9), petals[i], { shade: rgba('#c7788a') });
  });
  return done(p);
}

const CAT = rgba('#e3a04f');
const CAT_S = rgba('#b87832');
const CAT_H = rgba('#f2c27e');

/** The cat on the HR filing cabinet. `tail` 0/1 flicks, `blink` closes the eyes. */
export function renderCat(tail: number, blink: boolean, scale = 2): SpriteImage {
  const p = canvas(11, 9, scale);
  p.part(capsule(3.4, -0.8, 5 + (tail ? 0.6 : 0), -3.6 - (tail ? 1.4 : 0), 0.7), CAT, { shade: CAT_S });
  p.part(ellipse(0.4, -2.6, 3.4, 2.6), CAT, { shade: CAT_S, hi: CAT_H });
  p.part(ellipse(-1.6, -5.4, 2.4, 2.1), CAT, { shade: CAT_S, hi: CAT_H });
  p.part(poly([[-3.6, -6.2], [-3.3, -8.4], [-2.2, -6.9]]), CAT, { shade: CAT_S });
  p.part(poly([[-1.1, -6.9], [0.2, -8.3], [0.3, -6.2]]), CAT_S);
  if (blink) {
    p.line(-2.7, -5.4, -2.1, -5.4, INK, 0.3);
    p.line(-1.2, -5.4, -0.6, -5.4, INK, 0.3);
  } else {
    p.dot(-2.4, -5.5, INK, 0.35);
    p.dot(-0.9, -5.5, INK, 0.35);
  }
  // Stripes.
  p.line(1.2, -4.6, 1.6, -3.4, CAT_S, 0.3);
  p.line(2.4, -4.2, 2.8, -3.1, CAT_S, 0.3);
  return done(p);
}

/** Blit a sprite image with its bottom centre at (sx, sy). */
export function blitAt(buf: { w: number; h: number; data: Uint32Array }, img: SpriteImage, sx: number, sy: number) {
  const x0 = Math.round(sx - img.w / 2);
  const y0 = Math.round(sy - img.h);
  for (let y = 0; y < img.h; y++) {
    const dy = y0 + y;
    if (dy < 0 || dy >= buf.h) continue;
    for (let x = 0; x < img.w; x++) {
      const c = img.px[y * img.w + x];
      const dx = x0 + x;
      if (c && dx >= 0 && dx < buf.w) buf.data[dy * buf.w + dx] = c;
    }
  }
}
