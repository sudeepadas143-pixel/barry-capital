/**
 * Plants and the office cat, drawn with the same shaded-shape renderer as the
 * traders so the whole scene shares one finish. Design units, feet at y = 0.
 */
import { Painter, capsule, clip, ellipse, poly, rgba, taper, type Box, type SpriteImage, type Test } from './figure';

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

function canvas(wu: number, hu: number, scale: number, ss = 1) {
  const w = Math.ceil(wu * scale) + 2;
  const h = Math.ceil(hu * scale) + 2;
  const k = Math.max(1, Math.round(ss));
  return new Painter(w * k, h * k, (w / 2) * k, (h - 1) * k, scale * k, undefined, k);
}

function pot(p: Painter, w: number, h: number) {
  p.part(poly([[-w / 2, -h], [w / 2, -h], [w * 0.36, 0], [-w * 0.36, 0]]), POT, { shade: POT_S, hi: POT_H });
  p.part(ellipse(0, -h, w / 2 + 0.6, 1.1), POT_H, { shade: POT });
  p.part(ellipse(0, -h - 0.1, w / 2 - 0.4, 0.6), SOIL);
}

function done(p: Painter): SpriteImage {
  p.outline(INK);
  return p.image();
}

export type PlantKind = 'palm' | 'fern' | 'succulent' | 'shrub' | 'flowers';

export function renderPlant(kind: PlantKind, scale = 2, ss = 1): SpriteImage {
  if (kind === 'palm') {
    const p = canvas(22, 30, scale, ss);
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
    const p = canvas(14, 14, scale, ss);
    pot(p, 6, 4.5);
    for (let i = 0; i < 9; i++) {
      const a = -Math.PI / 2 + (i - 4) * 0.36;
      const len = 4.2 + (i % 2) * 1.1;
      p.part(leaf(Math.cos(a) * len * 0.55, -5 + Math.sin(a) * len * 0.55, len * 0.55, 1, a), i % 2 ? LEAF : LEAF_H, { shade: LEAF_S });
    }
    return done(p);
  }
  if (kind === 'succulent') {
    const p = canvas(7, 6, scale, ss);
    pot(p, 3.6, 2.4);
    for (let i = 0; i < 6; i++) {
      const a = -Math.PI / 2 + (i - 2.5) * 0.55;
      p.part(leaf(Math.cos(a) * 1.3, -2.8 + Math.sin(a) * 1.2, 1.4, 0.7, a), i % 2 ? LEAF_H : LEAF, { shade: LEAF_S });
    }
    return done(p);
  }
  if (kind === 'shrub') {
    const p = canvas(12, 8, scale, ss);
    for (const [x, y, r] of [[-3.2, -2.6, 2.6], [3, -2.8, 2.7], [0, -4.4, 3.2], [-1.2, -2.2, 2.4], [1.8, -2, 2.3]] as const)
      p.part(ellipse(x, y, r, r * 0.85), LEAF, { shade: LEAF_S, hi: LEAF_H });
    return done(p);
  }
  const p = canvas(8, 5, scale, ss);
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
export function renderCat(tail: number, blink: boolean, scale = 2, ss = 1): SpriteImage {
  const p = canvas(11, 9, scale, ss);
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

/** Blit a sprite image with its bottom centre at (sx, sy), blending partial alpha. */
export function blitAt(buf: { w: number; h: number; data: Uint32Array }, img: SpriteImage, sx: number, sy: number) {
  const x0 = Math.round(sx - img.w / 2);
  const y0 = Math.round(sy - img.h);
  for (let y = 0; y < img.h; y++) {
    const dy = y0 + y;
    if (dy < 0 || dy >= buf.h) continue;
    for (let x = 0; x < img.w; x++) {
      const c = img.px[y * img.w + x];
      const dx = x0 + x;
      if (!c || dx < 0 || dx >= buf.w) continue;
      const i = dy * buf.w + dx;
      buf.data[i] = over(buf.data[i], c);
    }
  }
}

/** Source-over for two packed ABGR colours. */
export function over(dst: number, src: number): number {
  const sa = src >>> 24;
  if (sa >= 255 || !dst) return sa ? src : dst;
  if (!sa) return dst;
  const da = dst >>> 24;
  const t = sa / 255;
  const oa = sa + da * (1 - t);
  const ch = (sh: number) => {
    const s = (src >>> sh) & 255;
    const d = (dst >>> sh) & 255;
    return Math.round((s * sa + d * da * (1 - t)) / oa) & 255;
  };
  return ((Math.round(oa) << 24) | (ch(16) << 16) | (ch(8) << 8) | ch(0)) >>> 0;
}

const BRONZE = rgba('#8a5a2e');
const BRONZE_S = rgba('#5a381b');
const BRONZE_H = rgba('#c99255');

/** A charging bronze bull, facing left, for the lobby. Design units ≈ world units. */
export function renderBull(scale = 3, ss = 1): SpriteImage {
  const p = canvas(34, 20, scale, ss);
  const o = { shade: BRONZE_S, hi: BRONZE_H };
  // Legs, braced.
  p.part(taper(-9, -6, -12, 0, 1.4, 1), BRONZE, o);
  p.part(taper(-5, -6, -4, 0, 1.4, 1), BRONZE_S);
  p.part(taper(6, -6, 9, 0, 1.5, 1), BRONZE, o);
  p.part(taper(9, -6, 12.5, -0.4, 1.4, 1), BRONZE_S);
  // Body: a big shoulder hump sloping to the haunches.
  p.part(ellipse(0, -9, 11, 5.2), BRONZE, o);
  p.part(ellipse(-6, -11, 6.4, 5.6), BRONZE, o);
  p.part(ellipse(8.5, -9.6, 4.6, 4.4), BRONZE, o);
  // Head down, horns forward.
  p.part(ellipse(-13, -8.2, 3.6, 3), BRONZE, o);
  p.part(ellipse(-15.6, -6.8, 1.9, 1.6), BRONZE_S);
  p.part(taper(-12.2, -10.6, -16.2, -14.8, 0.9, 0.35), BRONZE_H);
  p.part(taper(-11, -10.8, -9.4, -15.4, 0.9, 0.35), BRONZE_H);
  // Tail up.
  p.part(taper(12.4, -11, 15.6, -16.4, 0.6, 0.4), BRONZE, o);
  p.dot(15.8, -16.8, BRONZE_S, 0.8);
  // Polished nose and highlights where everyone touches it.
  p.dot(-15.9, -6.8, BRONZE_H, 0.6);
  p.part(ellipse(-5, -14, 3, 1), BRONZE_H);
  return done(p);
}

/** A small corporate helicopter, side view facing left. `f` spins the rotor. */
export function renderHeli(f: number, scale = 3, ss = 1): SpriteImage {
  const p = canvas(40, 18, scale, ss);
  const navy = rgba('#1f2c45');
  const navyS = rgba('#141c2e');
  const navyH = rgba('#3a4d70');
  const glass = rgba('#9fc3dc');
  p.part(ellipse(-3, -8, 9, 4.6), navy, { shade: navyS, hi: navyH });
  p.part(taper(4, -8.6, 17, -9.6, 2.2, 0.8), navy, { shade: navyS });
  p.part(poly([[15.4, -9.6], [18.4, -14], [19.4, -13.6], [17.6, -9]]), navy);
  p.part(clip(ellipse(-6.4, -9, 5.2, 3), (x, y) => y < -8 && x < -3), glass, { hi: rgba('#e3f0f8') });
  p.part(poly([[-4, -8.8], [2.4, -8.8], [2.4, -6.6], [-4, -6.6]]), rgba('#d8ae4a'));
  // Skids.
  p.line(-9, -1.6, 4, -1.6, rgba('#2a2c31'), 0.45);
  p.line(-6, -1.6, -5, -3.6, rgba('#2a2c31'), 0.4);
  p.line(1.6, -1.6, 1, -3.6, rgba('#2a2c31'), 0.4);
  p.line(-1.6, -12.6, -1.6, -14.4, rgba('#2a2c31'), 0.4);
  // Rotor: a blur that sweeps.
  const span = [18, 11, 4, 11][f % 4];
  p.part(ellipse(-1.6, -14.8, span, 0.45), rgba('#3a3d44'));
  p.dot(18, -9.8 + (f % 2 ? -2 : 2), rgba('#3a3d44'), 0.6);
  return done(p);
}

/** A floor-standing globe bar on a walnut stand. */
export function renderGlobe(scale = 3, ss = 1): SpriteImage {
  const p = canvas(10, 14, scale, ss);
  const wood = rgba('#6a4630');
  const woodS = rgba('#452c1d');
  const woodH = rgba('#8c6244');
  p.part(poly([[-3.4, 0], [3.4, 0], [1.2, -1.2], [-1.2, -1.2]]), wood, { shade: woodS, hi: woodH });
  p.part(capsule(0, -1, 0, -5.6, 0.55), wood, { shade: woodS });
  p.part(ellipse(0, -9.2, 4.2, 4.2), rgba('#3f6f8f'), { shade: rgba('#2a4d66'), hi: rgba('#6f9bb8') });
  // Continents, roughly.
  p.part(ellipse(-1.2, -10.4, 1.6, 1.1), rgba('#8f9b5c'), { shade: rgba('#6c7744') });
  p.part(ellipse(1.4, -8.2, 1.2, 1.7), rgba('#8f9b5c'), { shade: rgba('#6c7744') });
  p.part(ellipse(-1.8, -7.6, 0.8, 0.6), rgba('#8f9b5c'));
  // Brass meridian.
  p.part(clip(ellipse(0, -9.2, 5, 5), (x, y) => (x * x + (y + 9.2) * (y + 9.2)) >= 20.2), rgba('#c9a24a'), { shade: rgba('#8f6f2a') });
  return done(p);
}

/** A studio camera on a tripod, for HR headshots. */
export function renderCamera(scale = 3, ss = 1): SpriteImage {
  const p = canvas(12, 18, scale, ss);
  const leg = rgba('#2a2c31');
  p.line(0, -10, -4.6, 0, leg, 0.35);
  p.line(0, -10, 4.2, 0, leg, 0.35);
  p.line(0, -10, 0.6, -0.4, leg, 0.35);
  p.part(poly([[-3.6, -14.6], [2.6, -14.6], [2.6, -10.4], [-3.6, -10.4]]), rgba('#1f2227'), { shade: rgba('#121417'), hi: rgba('#3a3d44') });
  p.part(ellipse(-4.6, -12.5, 1.6, 1.8), rgba('#15171b'), { hi: rgba('#4a5f78') });
  p.dot(1.6, -13.8, rgba('#ef5d4f'), 0.35);
  // A softbox beside it.
  p.part(poly([[3.8, -16.8], [5.8, -17.4], [5.8, -11.4], [3.8, -12]]), rgba('#f4f1ea'), { shade: rgba('#cfc9bd') });
  p.line(4.8, -12, 4.8, 0, leg, 0.3);
  return done(p);
}

/** The brass bell on the terminal floor. */
export function renderBell(scale = 3, ss = 1): SpriteImage {
  const p = canvas(10, 9, scale, ss);
  const gold = rgba('#d8ae4a');
  p.part(poly([[-2, -8], [2, -8], [3.2, -2.4], [4.4, -1.2], [-4.4, -1.2], [-3.2, -2.4]]), gold, { shade: rgba('#9c7a2a'), hi: rgba('#f2d68a') });
  p.part(ellipse(0, -8.1, 2, 0.7), rgba('#f2d68a'), { shade: gold });
  p.part(ellipse(0, -1.1, 4.4, 0.8), rgba('#9c7a2a'));
  p.dot(0, -0.4, rgba('#6b521c'), 0.7);
  return done(p);
}
