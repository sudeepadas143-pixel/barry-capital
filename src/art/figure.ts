/**
 * Procedural character renderer. Each trader is built from shaded shapes
 * (head, hair, jacket, shirt, tie, arms, legs) at any scale, then given a thin
 * selective outline. One body, palette-swapped per trader.
 *
 * Design units: a standing figure is 50 units tall, feet at y = 0, up is negative.
 * At scale 1 a unit is one pixel, which is the scene's resolution.
 */
import type { Look } from '../sim/types';
import { HAIRS, SKINS, SUITS, TIES, shade } from './palette';

export type Pose = 'stand' | 'walk' | 'back' | 'sit' | 'celebrate' | 'slump' | 'box' | 'backbox';

export const POSE_FRAMES: Record<Pose, number> = {
  stand: 1,
  walk: 8,
  back: 8,
  sit: 3,
  celebrate: 2,
  slump: 2,
  box: 8,
  backbox: 8,
};

export interface SpriteImage {
  w: number;
  h: number;
  px: Uint32Array;
}

export type Test = (x: number, y: number) => boolean;
export type Box = [number, number, number, number];

// ---------------------------------------------------------------- colour

export function rgba(hex: string): number {
  const n = parseInt(hex.slice(1), 16);
  return ((255 << 24) | ((n & 255) << 16) | (((n >> 8) & 255) << 8) | ((n >> 16) & 255)) >>> 0;
}

export function mix(a: number, b: number, t: number): number {
  const ch = (c: number, s: number) => (c >>> s) & 255;
  const m = (s: number) => Math.round(ch(a, s) + (ch(b, s) - ch(a, s)) * t) & 255;
  return ((255 << 24) | (m(16) << 16) | (m(8) << 8) | m(0)) >>> 0;
}

interface Pal {
  skin: number;
  skinS: number;
  skinH: number;
  hair: number;
  hairS: number;
  hairH: number;
  suit: number;
  suitS: number;
  suitH: number;
  trou: number;
  trouS: number;
  shirt: number;
  shirtS: number;
  tie: number;
  tieS: number;
  shoe: number;
  shoeH: number;
  eye: number;
  white: number;
  mouth: number;
  blush: number;
  box: number;
  boxS: number;
  boxH: number;
  tape: number;
  frame: number;
  ink: number;
}

function palette(look: Look): Pal {
  const skin = SKINS[look.skin % SKINS.length];
  const hair = HAIRS[look.hair % HAIRS.length];
  const suit = SUITS[look.suit % SUITS.length];
  const tie = TIES[look.tie % TIES.length];
  const light = hair === HAIRS[5] || hair === HAIRS[4];
  return {
    skin: rgba(skin),
    skinS: rgba(shade(skin, -0.14)),
    skinH: rgba(shade(skin, 0.07)),
    hair: rgba(hair),
    hairS: rgba(shade(hair, light ? -0.18 : -0.22)),
    hairH: rgba(shade(hair, light ? 0.08 : 0.35)),
    suit: rgba(suit),
    suitS: rgba(shade(suit, -0.26)),
    suitH: rgba(shade(suit, 0.2)),
    trou: rgba(shade(suit, -0.18)),
    trouS: rgba(shade(suit, -0.4)),
    shirt: rgba('#f6f3ec'),
    shirtS: rgba('#d9d3c6'),
    tie: rgba(tie),
    tieS: rgba(shade(tie, -0.28)),
    shoe: rgba('#211d1a'),
    shoeH: rgba('#4a433c'),
    eye: rgba('#231e1b'),
    white: rgba('#fbf8f2'),
    mouth: rgba(shade(skin, -0.38)),
    blush: rgba('#e8907f'),
    box: rgba('#c79a62'),
    boxS: rgba('#a67c48'),
    boxH: rgba('#dcb47d'),
    tape: rgba('#e9d9a6'),
    frame: rgba('#5a4520'),
    ink: rgba('#1d1a17'),
  };
}

const LEAF = rgba('#5a8a55');
const LEAF_S = rgba('#3f6a42');

// ---------------------------------------------------------------- shapes

export const ellipse = (cx: number, cy: number, rx: number, ry: number): [Test, Box] => [
  (x, y) => {
    const a = (x - cx) / rx;
    const b = (y - cy) / ry;
    return a * a + b * b <= 1;
  },
  [cx - rx, cy - ry, cx + rx, cy + ry],
];

export const capsule = (ax: number, ay: number, bx: number, by: number, r: number): [Test, Box] => {
  const dx = bx - ax;
  const dy = by - ay;
  const len2 = dx * dx + dy * dy || 1e-6;
  return [
    (x, y) => {
      let t = ((x - ax) * dx + (y - ay) * dy) / len2;
      t = t < 0 ? 0 : t > 1 ? 1 : t;
      const px = ax + t * dx - x;
      const py = ay + t * dy - y;
      return px * px + py * py <= r * r;
    },
    [Math.min(ax, bx) - r, Math.min(ay, by) - r, Math.max(ax, bx) + r, Math.max(ay, by) + r],
  ];
};

export const poly = (pts: [number, number][]): [Test, Box] => {
  const xs = pts.map((p) => p[0]);
  const ys = pts.map((p) => p[1]);
  return [
    (x, y) => {
      let c = false;
      for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
        const [xi, yi] = pts[i];
        const [xj, yj] = pts[j];
        if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
      }
      return c;
    },
    [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)],
  ];
};

export const union = (...s: [Test, Box][]): [Test, Box] => [
  (x, y) => s.some(([t]) => t(x, y)),
  [Math.min(...s.map((q) => q[1][0])), Math.min(...s.map((q) => q[1][1])), Math.max(...s.map((q) => q[1][2])), Math.max(...s.map((q) => q[1][3]))],
];

export const clip = (a: [Test, Box], b: Test): [Test, Box] => [(x, y) => a[0](x, y) && b(x, y), a[1]];

// ---------------------------------------------------------------- painter

export class Painter {
  readonly px: Uint32Array;
  constructor(
    readonly w: number,
    readonly h: number,
    readonly ox: number,
    readonly oy: number,
    readonly s: number,
    px?: Uint32Array,
  ) {
    this.px = px ?? new Uint32Array(w * h);
  }

  /** A view that draws `k` times larger around the design point (ax, ay), on the same pixels. */
  scaled(k: number, ax: number, ay: number): Painter {
    const s2 = this.s * k;
    return new Painter(this.w, this.h, this.ox + ax * this.s - ax * s2, this.oy + ay * this.s - ay * s2, s2, this.px);
  }

  /**
   * Fill a shape with a base colour, a shaded rim on the right (away from the light)
   * and an optional highlight rim on the upper left.
   */
  part([test, box]: [Test, Box], base: number, opts: { shade?: number; sd?: number; hi?: number; hd?: number; bottom?: number; bd?: number; only?: number[] } = {}) {
    const { s, ox, oy } = this;
    const x0 = Math.max(0, Math.floor(box[0] * s + ox) - 1);
    const x1 = Math.min(this.w - 1, Math.ceil(box[2] * s + ox) + 1);
    const y0 = Math.max(0, Math.floor(box[1] * s + oy) - 1);
    const y1 = Math.min(this.h - 1, Math.ceil(box[3] * s + oy) + 1);
    // Rim widths are in pixels at scales above 1, so detail stays fine as figures grow.
    const px = 1 / s;
    const sd = (opts.sd ?? 1.2) * Math.max(px, Math.min(1, 1.6 / s) );
    const hd = (opts.hd ?? 0.9) * Math.max(px, Math.min(1, 1.6 / s));
    const bd = (opts.bd ?? 1) * Math.max(px, Math.min(1, 1.6 / s));
    for (let py = y0; py <= y1; py++) {
      const y = (py + 0.5 - oy) / s;
      for (let pxl = x0; pxl <= x1; pxl++) {
        const x = (pxl + 0.5 - ox) / s;
        if (!test(x, y)) continue;
        const i = py * this.w + pxl;
        if (opts.only && !opts.only.includes(this.px[i])) continue;
        let c = base;
        if (opts.shade !== undefined && !test(x + sd * 1.6, y)) c = opts.shade;
        else if (opts.bottom !== undefined && !test(x, y + bd * 1.4)) c = opts.bottom;
        else if (opts.hi !== undefined && (!test(x - hd * 1.4, y) || !test(x, y - hd * 1.4))) c = opts.hi;
        this.px[i] = c;
      }
    }
  }

  dot(x: number, y: number, c: number, r = 0.5) {
    const cx = x * this.s + this.ox;
    const cy = y * this.s + this.oy;
    const rr = Math.max(0.5, r * this.s);
    for (let py = Math.floor(cy - rr); py <= Math.ceil(cy + rr); py++)
      for (let pxl = Math.floor(cx - rr); pxl <= Math.ceil(cx + rr); pxl++) {
        if (pxl < 0 || py < 0 || pxl >= this.w || py >= this.h) continue;
        const dx = pxl + 0.5 - cx;
        const dy = py + 0.5 - cy;
        if (dx * dx + dy * dy <= rr * rr) this.px[py * this.w + pxl] = c;
      }
  }

  /** A 1px (at scale 1) line in design units. */
  line(ax: number, ay: number, bx: number, by: number, c: number, r = 0.45) {
    this.part(capsule(ax, ay, bx, by, Math.max(r, 0.5 / this.s)), c);
  }

  tint([test, box]: [Test, Box], c: number, t: number) {
    const { s, ox, oy } = this;
    for (let py = Math.max(0, Math.floor(box[1] * s + oy)); py <= Math.min(this.h - 1, Math.ceil(box[3] * s + oy)); py++)
      for (let pxl = Math.max(0, Math.floor(box[0] * s + ox)); pxl <= Math.min(this.w - 1, Math.ceil(box[2] * s + ox)); pxl++) {
        const i = py * this.w + pxl;
        if (this.px[i] && test((pxl + 0.5 - ox) / s, (py + 0.5 - oy) / s)) this.px[i] = mix(this.px[i], c, t);
      }
  }

  /** Selective outline: every empty pixel touching the figure takes a dark version of its neighbour. */
  outline(ink: number) {
    const { w, h, px } = this;
    const out = px.slice();
    for (let y = 0; y < h; y++)
      for (let x = 0; x < w; x++) {
        const i = y * w + x;
        if (px[i]) continue;
        let n = 0;
        if (x > 0 && px[i - 1]) n = px[i - 1];
        else if (x < w - 1 && px[i + 1]) n = px[i + 1];
        else if (y > 0 && px[i - w]) n = px[i - w];
        else if (y < h - 1 && px[i + w]) n = px[i + w];
        if (n) out[i] = mix(n, ink, 0.72);
      }
    px.set(out);
  }
}

// ---------------------------------------------------------------- body

interface Arm {
  sh: [number, number];
  el: [number, number];
  hd: [number, number];
}

interface Rig {
  facing: 'front' | 'back';
  /** Vertical offset of the whole upper body (sitting lowers it). */
  up: number;
  bob: number;
  legs: 'stand' | 'sit' | 'none';
  footL: number;
  footR: number;
  armL: Arm;
  armR: Arm;
  mouth: 'line' | 'smile' | 'open';
  head: 'up' | 'down';
  box: boolean;
}

function standArms(swing: number, up: number): [Arm, Arm] {
  const L: Arm = { sh: [-6.9, -33.6 + up], el: [-7.9 - swing * 0.3, -27.2 + up], hd: [-7.6 - swing, -21.2 + up + Math.abs(swing) * 0.3] };
  const R: Arm = { sh: [6.9, -33.6 + up], el: [7.9 + swing * 0.3, -27.2 + up], hd: [7.6 + swing, -21.2 + up + Math.abs(swing) * 0.3] };
  return [L, R];
}

function rigFor(pose: Pose, frame: number): Rig {
  const f = frame % POSE_FRAMES[pose];
  const walkPhase = (f / 8) * Math.PI * 2;
  const walking = pose === 'walk' || pose === 'back' || pose === 'box' || pose === 'backbox';
  const lift = (p: number) => Math.max(0, Math.sin(p)) * 2.2;
  const bob = walking ? -Math.abs(Math.sin(walkPhase)) * 0.8 : 0;
  const base: Rig = {
    facing: pose === 'back' || pose === 'backbox' ? 'back' : 'front',
    up: 0,
    bob,
    legs: 'stand',
    footL: walking ? lift(walkPhase) : 0,
    footR: walking ? lift(walkPhase + Math.PI) : 0,
    armL: standArms(0, 0)[0],
    armR: standArms(0, 0)[1],
    mouth: 'line',
    head: 'up',
    box: pose === 'box' || pose === 'backbox',
  };
  if (walking && !base.box) {
    // Arms swing opposite the legs; seen from the front that reads as the hands rising and falling.
    const sw = Math.sin(walkPhase) * 1.3;
    const [L, R] = standArms(0, bob);
    L.hd = [L.hd[0] - Math.abs(sw) * 0.3, L.hd[1] - sw];
    L.el = [L.el[0], L.el[1] - sw * 0.4];
    R.hd = [R.hd[0] + Math.abs(sw) * 0.3, R.hd[1] + sw];
    R.el = [R.el[0], R.el[1] + sw * 0.4];
    base.armL = L;
    base.armR = R;
  }
  if (base.box) {
    base.armL = { sh: [-6.9, -33.6 + bob], el: [-8.6, -28.4 + bob], hd: [-7.9, -25.4 + bob] };
    base.armR = { sh: [6.9, -33.6 + bob], el: [8.6, -28.4 + bob], hd: [7.9, -25.4 + bob] };
  }
  if (pose === 'sit' || pose === 'slump') {
    base.up = 11;
    base.legs = 'sit';
    const tL = f === 0 ? -0.9 : 0;
    const tR = f === 1 ? -0.9 : 0;
    base.armL = { sh: [-6.9, -22.6], el: [-8.2, -16.8], hd: [-3.9, -13.2 + tL] };
    base.armR = { sh: [6.9, -22.6], el: [8.2, -16.8], hd: [3.9, -13.2 + tR] };
  }
  if (pose === 'slump') {
    base.head = 'down';
    base.up = 14 + (f === 1 ? 0.6 : 0);
    base.armL = { sh: [-6.9, -19.6], el: [-7.6, -15.6], hd: [5.2, -15.4] };
    base.armR = { sh: [6.9, -19.6], el: [7.6, -16.2], hd: [-5.2, -16.4] };
  }
  if (pose === 'celebrate') {
    const h = f === 1 ? -1.2 : 0;
    base.bob = f === 1 ? -0.8 : 0;
    base.armL = { sh: [-6.9, -33.6 + base.bob], el: [-10.6, -39.4 + h], hd: [-9.4, -47.8 + h] };
    base.armR = { sh: [6.9, -33.6 + base.bob], el: [10.6, -39.4 + h], hd: [9.4, -47.8 + h] };
    base.mouth = 'open';
  }
  return base;
}

function drawArm(p: Painter, a: Arm, c: Pal, front: boolean) {
  const r = 2.05;
  p.part(capsule(a.sh[0], a.sh[1], a.el[0], a.el[1], r), c.suit, { shade: c.suitS, hi: c.suitH });
  p.part(capsule(a.el[0], a.el[1], a.hd[0], a.hd[1] - 0.9, r * 0.95), c.suit, { shade: c.suitS, hi: c.suitH });
  if (!front) return;
  // Cuff and hand.
  const dx = a.hd[0] - a.el[0];
  const dy = a.hd[1] - a.el[1];
  const len = Math.hypot(dx, dy) || 1;
  const ux = dx / len;
  const uy = dy / len;
  p.part(capsule(a.hd[0] - ux * 1.4, a.hd[1] - uy * 1.4, a.hd[0] - ux * 0.7, a.hd[1] - uy * 0.7, 1.55), c.shirt, { shade: c.shirtS });
  p.part(ellipse(a.hd[0] + ux * 0.4, a.hd[1] + uy * 0.4, 1.55, 1.75), c.skin, { shade: c.skinS, hi: c.skinH });
}

function drawLegs(p: Painter, rig: Rig, c: Pal) {
  if (rig.legs === 'none') return;
  if (rig.legs === 'sit') {
    // Thighs toward the viewer, mostly behind the desk.
    p.part(poly([[-6.4, -12], [-0.4, -12], [-0.8, -4], [-6, -4]]), c.trou, { shade: c.trouS });
    p.part(poly([[0.4, -12], [6.4, -12], [6, -4], [0.8, -4]]), c.trou, { shade: c.trouS });
    return;
  }
  for (const [side, lift] of [
    [-1, rig.footL],
    [1, rig.footR],
  ] as const) {
    const x = side * 3.1;
    p.part(capsule(x, -21 + rig.bob, x + side * 0.2, -3.2 - lift, 2.55), c.trou, { shade: c.trouS, hi: rig.facing === 'front' ? undefined : undefined });
    p.part(ellipse(x + side * 0.4, -1.5 - lift, 3.1, 1.75), c.shoe, { hi: c.shoeH });
  }
}

function drawTorso(p: Pal, pn: Painter, rig: Rig, partner: boolean) {
  const y = (v: number) => v + rig.up + rig.bob;
  const jacket = union(
    poly([
      [-7.7, y(-35.2)],
      [7.7, y(-35.2)],
      [6.3, y(-24)],
      [6.8, y(-19.3)],
      [-6.8, y(-19.3)],
      [-6.3, y(-24)],
    ]),
    ellipse(-5.7, y(-33.9), 2.7, 1.9),
    ellipse(5.7, y(-33.9), 2.7, 1.9),
  );
  pn.part(jacket, p.suit, { shade: p.suitS, hi: p.suitH, bottom: p.suitS });
  // Neck.
  pn.part(poly([[-1.7, y(-38.6)], [1.7, y(-38.6)], [1.8, y(-34.6)], [-1.8, y(-34.6)]]), p.skin, { shade: p.skinS });
  if (rig.facing === 'back') {
    pn.line(0, y(-34), 0, y(-19.8), p.suitS, 0.35);
    pn.part(poly([[-2.6, y(-36)], [2.6, y(-36)], [2.2, y(-34.6)], [-2.2, y(-34.6)]]), p.suitS);
    return;
  }
  // Shirt V, collar, tie.
  const V = poly([
    [-2.7, y(-35.8)],
    [2.7, y(-35.8)],
    [0, y(-26.2)],
  ]);
  pn.part(V, p.shirt, { shade: p.shirtS });
  pn.part(poly([[-2.7, y(-35.9)], [-0.3, y(-35.2)], [-1.4, y(-33)]]), p.shirt, { shade: p.shirtS });
  pn.part(poly([[2.7, y(-35.9)], [0.3, y(-35.2)], [1.4, y(-33)]]), p.shirtS);
  const tie = clip(poly([[-1.1, y(-34.2)], [1.1, y(-34.2)], [1.6, y(-28.5)], [0, y(-26.4)], [-1.6, y(-28.5)]]), V[0]);
  pn.part(tie, p.tie, { shade: p.tieS });
  pn.part(ellipse(0, y(-34.6), 1.25, 0.95), p.tie, { shade: p.tieS });
  // Lapels.
  pn.part(poly([[-2.7, y(-35.6)], [-4.3, y(-35.4)], [-1.2, y(-27.4)], [-0.2, y(-26.6)]]), p.suitH);
  pn.part(poly([[2.7, y(-35.6)], [4.3, y(-35.4)], [1.2, y(-27.4)], [0.2, y(-26.6)]]), p.suitS);
  // Buttons.
  pn.dot(0, y(-24.6), p.suitS, 0.45);
  pn.dot(0, y(-22.2), p.suitS, 0.45);
  // Breast pocket (a pocket square for the partner).
  if (partner) pn.part(poly([[3.2, y(-30.6)], [5.4, y(-30.6)], [4.8, y(-29.4)], [3.6, y(-29.8)]]), p.shirt);
  else pn.line(3.3, y(-30.2), 5.3, y(-30.2), p.suitS, 0.3);
}

function hairShapes(style: number, cy: number): { back: [Test, Box]; cap: [Test, Box]; part?: [number, number, number, number] } {
  const back = ellipse(0, cy - 1.1, 6.95, 6.9);
  switch (style % 4) {
    case 0: {
      // Side part with a swept fringe.
      const cap = clip(ellipse(0, cy - 3.2, 6.85, 5.3), (x, y) => y < cy - 3.3 + 0.24 * (x + 3.5) - (x < -2 ? 0.6 : 0));
      return { back, cap, part: [-2.3, cy - 7.9, -2.1, cy - 4.8] };
    }
    case 1: {
      const cap = clip(ellipse(0, cy - 2.6, 6.55, 5.1), (_x, y) => y < cy - 3.8);
      return { back: ellipse(0, cy - 0.9, 6.6, 6.6), cap };
    }
    case 2: {
      // Receding: sides and a thin band at the crown.
      const cap = clip(ellipse(0, cy - 2.4, 6.7, 5.4), (x, y) => (Math.abs(x) > 3.9 && y < cy - 1.4) || y < cy - 6.6);
      return { back, cap };
    }
    default: {
      // Swept back, with volume.
      const cap = clip(ellipse(0, cy - 3.9, 7.1, 5.8), (x, y) => y < cy - 3.9 - 0.08 * Math.abs(x));
      return { back: ellipse(0, cy - 1.6, 7.1, 7.2), cap };
    }
  }
}

function drawHead(pn: Painter, c: Pal, rig: Rig, style: number, glasses: boolean) {
  const down = rig.head === 'down';
  const cy = -44.6 + rig.up + rig.bob + (down ? 2.6 : 0);
  const hs = hairShapes(style, cy);
  const detailed = pn.s >= 2;
  if (rig.facing === 'back' || down) {
    pn.part(ellipse(-6.1, cy + 0.6, 1.2, 1.8), c.skin, { shade: c.skinS });
    pn.part(ellipse(6.1, cy + 0.6, 1.2, 1.8), c.skinS);
    pn.part(ellipse(0, cy, 6.2, 7), c.skin, { shade: c.skinS });
    // Hair over nearly all of the head.
    const cover = down ? clip(union(hs.back, hs.cap, ellipse(0, cy, 6.4, 7.1)), (_x, y) => y < cy + 3.4) : clip(union(hs.back, ellipse(0, cy, 6.4, 7.1)), (_x, y) => y < cy + 4.6);
    if (style % 4 === 2 && !down) {
      pn.part(clip(ellipse(0, cy, 6.4, 7.1), (x, y) => y < cy + 4.6 && (Math.abs(x) > 2.6 || y > cy - 1)), c.hair, { shade: c.hairS, hi: c.hairH });
    } else pn.part(cover, c.hair, { shade: c.hairS, hi: c.hairH });
    return;
  }
  // Hair behind the head, ears, the head.
  pn.part(clip(hs.back, (_x, y) => y < cy + 1.5), c.hair, { shade: c.hairS });
  pn.part(ellipse(-6.1, cy + 0.4, 1.25, 1.85), c.skin, { hi: c.skinH });
  pn.part(ellipse(6.1, cy + 0.4, 1.25, 1.85), c.skinS);
  pn.part(union(ellipse(0, cy, 6.15, 7), ellipse(0, cy + 2.6, 4.9, 4.6)), c.skin, { shade: c.skinS, hi: c.skinH });
  // Face.
  const ey = cy + 0.4;
  if (rig.mouth === 'open' && !detailed) {
    // Happy eyes.
    for (const sx of [-1, 1]) {
      pn.line(sx * 2.3 - 0.8, ey + 0.2, sx * 2.3, ey - 0.5, c.eye, 0.35);
      pn.line(sx * 2.3, ey - 0.5, sx * 2.3 + 0.8, ey + 0.2, c.eye, 0.35);
    }
  } else if (detailed) {
    for (const sx of [-1, 1]) {
      pn.part(ellipse(sx * 2.35, ey, 1.05, 0.85), c.white);
      pn.part(ellipse(sx * 2.35 + 0.15, ey + 0.05, 0.55, 0.7), c.eye);
      pn.dot(sx * 2.35 - 0.05, ey - 0.25, c.white, 0.18);
    }
  } else {
    for (const sx of [-1, 1]) pn.part(ellipse(sx * 2.3, ey, 0.5, 0.95), c.eye);
  }
  // Brows.
  for (const sx of [-1, 1]) pn.line(sx * 1.6, ey - 2.1 - (rig.mouth === 'open' ? 0.4 : 0), sx * 3.2, ey - 2.2 + (sx > 0 ? 0 : 0), c.hairS, 0.38);
  // Nose, cheeks, mouth.
  pn.part(ellipse(0.55, cy + 2.5, 0.55, 0.9), c.skinS);
  pn.tint(ellipse(-3.6, cy + 3, 1.3, 0.75), c.blush, 0.28);
  pn.tint(ellipse(3.6, cy + 3, 1.3, 0.75), c.blush, 0.22);
  const my = cy + 4.7;
  if (rig.mouth === 'open') {
    pn.part(ellipse(0, my, 1.7, 1.1), c.mouth);
    if (detailed) pn.part(ellipse(0, my - 0.45, 1.35, 0.4), c.white);
  } else pn.line(-1.3, my, 1.3, my, c.mouth, 0.36);
  // Hair on top.
  pn.part(hs.cap, c.hair, { shade: c.hairS, hi: c.hairH });
  if (hs.part) pn.line(hs.part[0], hs.part[1], hs.part[2], hs.part[3], c.hairS, 0.3);
  if (style % 4 === 3) {
    pn.line(-3.5, cy - 7.8, -1.2, cy - 6.6, c.hairH, 0.28);
    pn.line(0.6, cy - 8.2, 2.9, cy - 7, c.hairH, 0.28);
  }
  if (glasses) {
    for (const sx of [-1, 1]) {
      const [t] = ellipse(sx * 2.35, ey, 1.75, 1.35);
      const [t2] = ellipse(sx * 2.35, ey, 1.25, 0.88);
      pn.part([(x, y) => t(x, y) && !t2(x, y), [sx * 2.35 - 2, ey - 1.5, sx * 2.35 + 2, ey + 1.5]], c.frame);
    }
    pn.line(-0.7, ey - 0.3, 0.7, ey - 0.3, c.frame, 0.3);
  }
}

function drawBox(pn: Painter, c: Pal, rig: Rig, behind: boolean) {
  const b = rig.bob;
  if (behind) {
    pn.part(poly([[-8.6, -31 + b], [8.6, -31 + b], [8.6, -20.5 + b], [-8.6, -20.5 + b]]), c.boxS);
    return;
  }
  pn.part(poly([[-7.8, -31.5 + b], [7.8, -31.5 + b], [7.8, -19.8 + b], [-7.8, -19.8 + b]]), c.box, { shade: c.boxS, hi: c.boxH });
  pn.part(poly([[-7.8, -31.5 + b], [7.8, -31.5 + b], [6.8, -29.8 + b], [-6.8, -29.8 + b]]), c.boxH);
  pn.part(poly([[-0.9, -31.5 + b], [0.9, -31.5 + b], [0.9, -26 + b], [-0.9, -26 + b]]), c.tape);
  // A plant and some papers poking out of the top.
  pn.part(ellipse(-4.2, -32.6 + b, 1.9, 1.5), LEAF, { shade: LEAF_S });
  pn.part(poly([[2.2, -34 + b], [5.6, -33.2 + b], [5.2, -31.5 + b], [2, -31.5 + b]]), c.shirt, { shade: c.shirtS });
}

// ---------------------------------------------------------------- entry points

export interface FigureOpts {
  scale?: number;
  glasses?: boolean;
}

const HEAD_SCALE = 1.15;
const W_UNITS = 30;
const H_UNITS = 58;

export function renderFigure(look: Look, pose: Pose, frame: number, opts: FigureOpts = {}): SpriteImage {
  const s = opts.scale ?? 1;
  const w = Math.ceil(W_UNITS * s) + 2;
  const h = Math.ceil(H_UNITS * s) + 2;
  const pn = new Painter(w, h, w / 2, h - 1 - 0.5 * s, s);
  const c = palette(look);
  const rig = rigFor(pose, frame);
  const front = rig.facing === 'front';

  if (rig.box && !front) drawBox(pn, c, rig, true);
  drawLegs(pn, rig, c);
  if (!front) {
    drawArm(pn, rig.armL, c, false);
    drawArm(pn, rig.armR, c, false);
  }
  drawTorso(c, pn, rig, !!opts.glasses);
  if (front && !rig.box) {
    drawArm(pn, rig.armL, c, true);
    drawArm(pn, rig.armR, c, true);
  }
  if (rig.box && front) {
    drawBox(pn, c, rig, false);
    // Hands on the sides of the box.
    pn.part(ellipse(-7.9, -25.4 + rig.bob, 1.5, 1.7), c.skin, { shade: c.skinS });
    pn.part(ellipse(7.9, -25.4 + rig.bob, 1.5, 1.7), c.skin, { shade: c.skinS });
  }
  if (rig.head === 'down') {
    drawArm(pn, rig.armL, c, true);
    drawArm(pn, rig.armR, c, true);
  }
  // Heads are drawn a little larger than life, scaled up from the chin.
  const chin = -38.2 + rig.up + rig.bob + (rig.head === 'down' ? 2.6 : 0);
  drawHead(pn.scaled(HEAD_SCALE, 0, chin), c, rig, look.hairStyle, !!opts.glasses);
  if (rig.box && !front) {
    // Arms reach round to the box.
    pn.part(capsule(-6.9, -33.6 + rig.bob, -8.4, -26 + rig.bob, 2), c.suit, { shade: c.suitS });
    pn.part(capsule(6.9, -33.6 + rig.bob, 8.4, -26 + rig.bob, 2), c.suit, { shade: c.suitS });
  }
  pn.outline(c.ink);
  return { w, h, px: pn.px };
}

/** Head and shoulders, square, for headshots. */
export function renderBust(look: Look, size: number, glasses = false): SpriteImage {
  // The bust spans roughly 28 design units; pick a scale that fills `size`.
  const s = size / 28;
  const full = renderFigure(look, 'stand', 0, { scale: s, glasses });
  const cx = full.w / 2;
  const top = full.h - 1 - 0.5 * s - 54 * s;
  const x0 = Math.round(cx - size / 2);
  const y0 = Math.round(top);
  const px = new Uint32Array(size * size);
  for (let y = 0; y < size; y++)
    for (let x = 0; x < size; x++) {
      const sx = x0 + x;
      const sy = y0 + y;
      if (sx < 0 || sy < 0 || sx >= full.w || sy >= full.h) continue;
      px[y * size + x] = full.px[sy * full.w + sx];
    }
  return { w: size, h: size, px };
}
