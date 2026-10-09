/**
 * Procedural character renderer. Traders are built from shaded shapes at any
 * scale, then given a thin selective outline. Every trader shares one rig but
 * differs in build, height, haircut, facial hair, outfit, shirt, neckwear and
 * accessories (see traits.ts), and in how they carry themselves.
 *
 * Design units: a standing figure of average height is 50 units tall, feet at
 * y = 0, up is negative. Scale 1 means one unit per pixel.
 */
import type { Look } from '../sim/types';
import { HAIRS, SHIRTS, SKINS, SUITS, TIES, VESTS, shade } from './palette';

export type Pose =
  | 'stand'
  | 'walk'
  | 'back'
  | 'sit'
  | 'celebrate'
  | 'slump'
  | 'box'
  | 'backbox'
  | 'leanback'
  | 'phone'
  | 'point'
  | 'coffee'
  | 'stretch'
  | 'rub'
  | 'mobile'
  | 'eat'
  | 'hips'
  | 'arms'
  | 'tie'
  | 'chat'
  | 'watch'
  | 'drink'
  | 'putt'
  | 'call';

export const POSE_FRAMES: Record<Pose, number> = {
  stand: 2,
  walk: 8,
  back: 8,
  sit: 3,
  celebrate: 2,
  slump: 2,
  box: 8,
  backbox: 8,
  leanback: 2,
  phone: 4,
  point: 2,
  coffee: 3,
  stretch: 2,
  rub: 2,
  mobile: 2,
  eat: 3,
  hips: 2,
  arms: 2,
  tie: 2,
  chat: 2,
  watch: 2,
  drink: 2,
  putt: 4,
  call: 4,
};

/** Poses drawn sitting down (the lower body is hidden by a desk). */
export const SEATED_POSES: Pose[] = ['sit', 'leanback', 'phone', 'coffee', 'slump', 'stretch', 'rub', 'mobile', 'eat', 'tie', 'chat'];

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

const hx = (c: string, a = 0) => rgba(a ? shade(c, a) : c);

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
  stripe: number;
  trou: number;
  trouS: number;
  shirt: number;
  shirtS: number;
  shirtStripe: number;
  tie: number;
  tieS: number;
  tieH: number;
  vest: number;
  vestS: number;
  vestH: number;
  shoe: number;
  shoeH: number;
  eye: number;
  iris: number;
  white: number;
  mouth: number;
  lips: number;
  teeth: number;
  blush: number;
  box: number;
  boxS: number;
  boxH: number;
  tape: number;
  gold: number;
  goldS: number;
  frame: number;
  lens: number;
  lensH: number;
  brace: number;
  phone: number;
  cup: number;
  cupS: number;
  cigar: number;
  ember: number;
  ink: number;
}

function palette(look: Look): Pal {
  const skin = SKINS[look.skin % SKINS.length];
  const hair = HAIRS[look.hair % HAIRS.length];
  const suit = SUITS[look.suit % SUITS.length];
  const tie = TIES[look.tie % TIES.length];
  const shirt = SHIRTS[(look.shirt ?? 0) % SHIRTS.length];
  const turtle = look.outfit === 5;
  const vest = turtle ? VESTS[(look.suit + 2) % VESTS.length] : VESTS[(look.suit + look.tie) % VESTS.length];
  const light = hair === HAIRS[5] || hair === HAIRS[4];
  const dark = look.skin >= 3;
  return {
    skin: hx(skin),
    skinS: hx(skin, -0.14),
    skinH: hx(skin, 0.08),
    hair: hx(hair),
    hairS: hx(hair, light ? -0.18 : -0.24),
    hairH: hx(hair, light ? 0.08 : 0.38),
    suit: hx(suit),
    suitS: hx(suit, -0.28),
    suitH: hx(suit, 0.22),
    stripe: hx(suit, 0.45),
    trou: hx(suit, -0.16),
    trouS: hx(suit, -0.4),
    shirt: hx(shirt),
    shirtS: hx(shirt, -0.13),
    shirtStripe: hx('#8fb0d8'),
    tie: hx(tie),
    tieS: hx(tie, -0.3),
    tieH: hx(tie, 0.25),
    vest: hx(vest),
    vestS: hx(vest, -0.25),
    vestH: hx(vest, 0.2),
    shoe: hx('#221d1a'),
    shoeH: hx('#56493f'),
    eye: hx('#1f1a17'),
    iris: hx(['#4a3524', '#3f5a6e', '#4b5d3a', '#2e2219'][look.hair % 4]),
    white: hx('#fbf8f2'),
    mouth: hx(skin, -0.4),
    lips: look.fem ? hx('#b3504f', dark ? -0.2 : 0) : hx(skin, -0.22),
    teeth: hx('#fbf6ec'),
    blush: hx('#e8907f'),
    box: hx('#c79a62'),
    boxS: hx('#a67c48'),
    boxH: hx('#dcb47d'),
    tape: hx('#e9d9a6'),
    gold: hx('#e0b54a'),
    goldS: hx('#a5812c'),
    frame: hx('#3b2f25'),
    lens: hx('#18181c'),
    lensH: hx('#6f8fb0'),
    brace: hx(['#7a2a2a', '#222226', '#2f4a73', '#6e5a2a'][look.tie % 4]),
    phone: hx('#1c1d22'),
    cup: hx('#f3efe6'),
    cupS: hx('#c9bfae'),
    cigar: hx('#6b4428'),
    ember: hx('#ff8a3c'),
    ink: hx('#1b1815'),
  };
}

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

/** A capsule that tapers from ra to rb. */
export const taper = (ax: number, ay: number, bx: number, by: number, ra: number, rb: number): [Test, Box] => {
  const dx = bx - ax;
  const dy = by - ay;
  const len2 = dx * dx + dy * dy || 1e-6;
  const r = Math.max(ra, rb);
  return [
    (x, y) => {
      let t = ((x - ax) * dx + (y - ay) * dy) / len2;
      t = t < 0 ? 0 : t > 1 ? 1 : t;
      const px = ax + t * dx - x;
      const py = ay + t * dy - y;
      const rr = ra + (rb - ra) * t;
      return px * px + py * py <= rr * rr;
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
const minus = (a: [Test, Box], b: [Test, Box]): [Test, Box] => [(x, y) => a[0](x, y) && !b[0](x, y), a[1]];

// ---------------------------------------------------------------- painter

/** Which parts a painter draws; see `FigureOpts.only`. */
export interface Gate {
  tag: string;
  allow: Set<string> | null;
}

export class Painter {
  readonly px: Uint32Array;
  /**
   * `ss` is the supersampling factor: the painter works at `ss`× the final
   * resolution, and minimum line widths, rims and the outline are measured in
   * final pixels so the downsampled result keeps the same weight.
   */
  constructor(
    readonly w: number,
    readonly h: number,
    readonly ox: number,
    readonly oy: number,
    readonly s: number,
    px?: Uint32Array,
    readonly ss = 1,
    /** Shared by every view of this painter: with `allow` set, only parts whose current tag is allowed are drawn. */
    readonly gate: Gate = { tag: '', allow: null },
  ) {
    this.px = px ?? new Uint32Array(w * h);
  }

  /** Draw what `fn` draws under `tag`, then go back to the previous tag. */
  tagged(tag: string, fn: () => void) {
    const prev = this.gate.tag;
    this.gate.tag = tag;
    fn();
    this.gate.tag = prev;
  }

  private get skip() {
    return this.gate.allow !== null && !this.gate.allow.has(this.gate.tag);
  }

  /** Pixels per design unit in the final (downsampled) image. */
  get fs() {
    return this.s / this.ss;
  }

  /** A view that draws `k` times larger around the design point (ax, ay), on the same pixels. */
  /** The same painter, with everything drawn moved by (dx, dy) units. */
  moved(dx: number, dy: number): Painter {
    return new Painter(this.w, this.h, this.ox + dx * this.s, this.oy + dy * this.s, this.s, this.px, this.ss, this.gate);
  }

  scaled(k: number, ax: number, ay: number): Painter {
    const s2 = this.s * k;
    return new Painter(this.w, this.h, this.ox + ax * this.s - ax * s2, this.oy + ay * this.s - ay * s2, s2, this.px, this.ss, this.gate);
  }

  /**
   * Fill a shape with a base colour, a shaded rim on the right (away from the
   * light), an optional darker bottom rim and a highlight on the upper left.
   */
  part([test, box]: [Test, Box], base: number, opts: { shade?: number; sd?: number; hi?: number; hd?: number; bottom?: number; bd?: number; only?: number[] } = {}) {
    if (this.skip) return;
    const { s, ox, oy } = this;
    const x0 = Math.max(0, Math.floor(box[0] * s + ox) - 1);
    const x1 = Math.min(this.w - 1, Math.ceil(box[2] * s + ox) + 1);
    const y0 = Math.max(0, Math.floor(box[1] * s + oy) - 1);
    const y1 = Math.min(this.h - 1, Math.ceil(box[3] * s + oy) + 1);
    const fs = s / this.ss;
    const unit = Math.max(1 / fs, Math.min(1, 1.7 / fs));
    const sd = (opts.sd ?? 1.2) * unit;
    const hd = (opts.hd ?? 0.9) * unit;
    const bd = (opts.bd ?? 1) * unit;
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
    const m = Math.max(r, 0.5 / this.fs);
    this.part(ellipse(x, y, m, m), c);
  }

  /** A thin line in design units, at least one pixel wide. */
  line(ax: number, ay: number, bx: number, by: number, c: number, r = 0.4) {
    this.part(capsule(ax, ay, bx, by, Math.max(r, 0.5 / this.fs)), c);
  }

  tint([test, box]: [Test, Box], c: number, t: number) {
    if (this.skip) return;
    const { s, ox, oy } = this;
    for (let py = Math.max(0, Math.floor(box[1] * s + oy)); py <= Math.min(this.h - 1, Math.ceil(box[3] * s + oy)); py++)
      for (let pxl = Math.max(0, Math.floor(box[0] * s + ox)); pxl <= Math.min(this.w - 1, Math.ceil(box[2] * s + ox)); pxl++) {
        const i = py * this.w + pxl;
        if (this.px[i] && test((pxl + 0.5 - ox) / s, (py + 0.5 - oy) / s)) this.px[i] = mix(this.px[i], c, t);
      }
  }

  /**
   * Selective outline: empty pixels within `ss` pixels of the figure take a
   * dark version of their nearest neighbour (one final pixel wide).
   */
  outline(ink: number) {
    const { w, h, px, ss } = this;
    const r = Math.max(1, Math.round(ss));
    // Separable square dilation that carries the source colour along.
    const horiz = new Uint32Array(w * h);
    for (let y = 0; y < h; y++) {
      const row = y * w;
      for (let x = 0; x < w; x++) {
        const i = row + x;
        if (px[i]) {
          horiz[i] = px[i];
          continue;
        }
        for (let d = 1; d <= r; d++) {
          if (x - d >= 0 && px[i - d]) {
            horiz[i] = px[i - d];
            break;
          }
          if (x + d < w && px[i + d]) {
            horiz[i] = px[i + d];
            break;
          }
        }
      }
    }
    for (let y = 0; y < h; y++)
      for (let x = 0; x < w; x++) {
        const i = y * w + x;
        if (px[i]) continue;
        let n = horiz[i];
        for (let d = 1; !n && d <= r; d++) {
          if (y - d >= 0 && horiz[i - d * w]) n = horiz[i - d * w];
          else if (y + d < h && horiz[i + d * w]) n = horiz[i + d * w];
        }
        if (n) px[i] = mix(n, ink, 0.74);
      }
  }

  /** The finished image, box-filtered down by `ss`. */
  image(): SpriteImage {
    return downsample({ w: this.w, h: this.h, px: this.px }, this.ss);
  }
}

/** Average `k`×`k` blocks, weighting colour by alpha. */
export function downsample(img: SpriteImage, k: number): SpriteImage {
  if (k <= 1) return img;
  const w = Math.floor(img.w / k);
  const h = Math.floor(img.h / k);
  const px = new Uint32Array(w * h);
  const n = k * k;
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      let r = 0;
      let g = 0;
      let b = 0;
      let a = 0;
      for (let j = 0; j < k; j++) {
        const row = (y * k + j) * img.w + x * k;
        for (let i = 0; i < k; i++) {
          const c = img.px[row + i];
          if (!c) continue;
          const ca = c >>> 24;
          a += ca;
          r += (c & 255) * ca;
          g += ((c >>> 8) & 255) * ca;
          b += ((c >>> 16) & 255) * ca;
        }
      }
      if (!a) continue;
      const oa = Math.round(a / n);
      if (!oa) continue;
      px[y * w + x] = ((oa << 24) | (Math.round(b / a) << 16) | (Math.round(g / a) << 8) | Math.round(r / a)) >>> 0;
    }
  return { w, h, px };
}

// ---------------------------------------------------------------- rig

type P2 = [number, number];

interface Arm {
  sh: P2;
  el: P2;
  hd: P2;
  /** Hand hidden (in a pocket, behind the head). */
  hide?: boolean;
  fist?: boolean;
  /** Drawn after the head (hands at the face). */
  over?: boolean;
  finger?: P2;
}

type Mouth = 'smirk' | 'grin' | 'shout' | 'talk' | 'frown' | 'line' | 'sip';

interface Rig {
  facing: 'front' | 'back';
  /** How far the upper body is lowered (sitting). */
  up: number;
  bob: number;
  legs: 'stand' | 'sit';
  footL: number;
  footR: number;
  armL: Arm;
  armR: Arm;
  mouth: Mouth;
  brow: 'cocky' | 'flat' | 'up' | 'down';
  head: 'up' | 'down';
  headDx: number;
  box: boolean;
  phone?: boolean;
  cup?: P2;
  /** A phone held low in both hands. */
  mobile?: P2;
  /** A sandwich on its way to the mouth. */
  food?: P2;
  /** A whisky tumbler. */
  glass?: P2;
  /** Putter: grip point and club-head x offset. */
  putter?: { grip: P2; head: number };
}

function sideArms(up: number): [Arm, Arm] {
  return [
    { sh: [-7, -33.6 + up], el: [-7.9, -27.2 + up], hd: [-7.6, -21.2 + up] },
    { sh: [7, -33.6 + up], el: [7.9, -27.2 + up], hd: [7.6, -21.2 + up] },
  ];
}

function rigFor(pose: Pose, frame: number): Rig {
  const f = frame % POSE_FRAMES[pose];
  const ph = (f / 8) * Math.PI * 2;
  const walking = pose === 'walk' || pose === 'back' || pose === 'box' || pose === 'backbox';
  const lift = (p: number) => Math.max(0, Math.sin(p)) * 2.3;
  const bob = walking ? -Math.abs(Math.sin(ph)) * 0.9 : 0;
  const [L0, R0] = sideArms(bob);
  const r: Rig = {
    facing: pose === 'back' || pose === 'backbox' ? 'back' : 'front',
    up: 0,
    bob,
    legs: 'stand',
    footL: walking ? lift(ph) : 0,
    footR: walking ? lift(ph + Math.PI) : 0,
    armL: L0,
    armR: R0,
    mouth: 'smirk',
    brow: 'cocky',
    head: 'up',
    headDx: 0,
    box: pose === 'box' || pose === 'backbox',
  };
  const seated = () => {
    r.up = 11;
    r.legs = 'sit';
  };
  switch (pose) {
    case 'stand': {
      // Hands in pockets, chest out, the occasional smug look.
      r.armL = { sh: [-7, -33.6], el: [-9.2, -27.6], hd: [-5.6, -22.4], hide: true };
      r.armR = { sh: [7, -33.6], el: [9.2, -27.6], hd: [5.6, -22.4], hide: true };
      r.headDx = f ? 0.4 : 0;
      break;
    }
    case 'walk':
    case 'back': {
      const sw = Math.sin(ph) * 1.4;
      r.armL = { ...L0, el: [L0.el[0], L0.el[1] - sw * 0.4], hd: [L0.hd[0] - Math.abs(sw) * 0.3, L0.hd[1] - sw] };
      r.armR = { ...R0, el: [R0.el[0], R0.el[1] + sw * 0.4], hd: [R0.hd[0] + Math.abs(sw) * 0.3, R0.hd[1] + sw] };
      r.mouth = 'smirk';
      break;
    }
    case 'box':
    case 'backbox':
      r.armL = { sh: [-7, -33.6 + bob], el: [-8.8, -28.4 + bob], hd: [-8, -25.4 + bob] };
      r.armR = { sh: [7, -33.6 + bob], el: [8.8, -28.4 + bob], hd: [8, -25.4 + bob] };
      r.mouth = 'frown';
      r.brow = 'up';
      break;
    case 'sit': {
      seated();
      const tL = f === 0 ? -0.9 : 0;
      const tR = f === 1 ? -0.9 : 0;
      r.armL = { sh: [-7, -22.6], el: [-8.4, -16.8], hd: [-4, -13.2 + tL] };
      r.armR = { sh: [7, -22.6], el: [8.4, -16.8], hd: [4, -13.2 + tR] };
      r.mouth = 'line';
      r.brow = 'down';
      break;
    }
    case 'leanback': {
      // Hands behind the head, elbows wide, very pleased with the position.
      seated();
      r.up = 12 + (f ? 0.3 : 0);
      r.armL = { sh: [-7, -22.8], el: [-12.2, -30.5], hd: [-3.8, -35.8], hide: true };
      r.armR = { sh: [7, -22.8], el: [12.2, -30.5], hd: [3.8, -35.8], hide: true };
      r.mouth = f ? 'grin' : 'smirk';
      r.brow = 'cocky';
      break;
    }
    case 'phone': {
      seated();
      r.armR = { sh: [7, -22.6], el: [9.8, -21.4], hd: [6.4, -32.4], over: true };
      r.phone = true;
      const g = [0, 1, 2, 1][f];
      r.armL =
        g === 2
          ? { sh: [-7, -22.6], el: [-11, -25.2], hd: [-10.6, -31.8], fist: true }
          : { sh: [-7, -22.6], el: [-9.6, -18.2], hd: [-7.4 + g, -16.4 - g * 2] };
      r.mouth = f % 2 ? 'shout' : 'talk';
      r.brow = f === 2 ? 'down' : 'up';
      break;
    }
    case 'point': {
      // Standing behind the desk, jabbing at the screen.
      r.armR = { sh: [7, -33.6], el: [12.2, -37.6], hd: [16 + f * 0.5, -40.6 - f * 0.4], fist: true, finger: [18.4 + f * 0.5, -42 - f * 0.4] };
      r.armL = { sh: [-7, -33.6], el: [-10.2, -28.2], hd: [-6.8, -24.4], hide: true };
      r.mouth = 'shout';
      r.brow = 'down';
      r.headDx = 0.5;
      break;
    }
    case 'coffee': {
      seated();
      const up = f < 2;
      r.armR = up ? { sh: [7, -22.6], el: [9.6, -19.4], hd: [3.4, -28.2], over: true } : { sh: [7, -22.6], el: [8.8, -17.2], hd: [6.2, -14.4] };
      r.cup = up ? [3.4, -29.6] : [6.4, -15.8];
      r.armL = { sh: [-7, -22.6], el: [-8.4, -16.8], hd: [-4, -13.4] };
      r.mouth = up && f === 0 ? 'sip' : 'smirk';
      break;
    }
    case 'celebrate': {
      const hgt = f ? -1.4 : 0;
      r.bob = f ? -0.9 : 0;
      r.armL = { sh: [-7, -33.6 + r.bob], el: [-11, -39.6 + hgt], hd: [-9.6, -48.4 + hgt], fist: true };
      r.armR = { sh: [7, -33.6 + r.bob], el: [11, -39.6 + hgt], hd: [9.6, -48.4 + hgt], fist: true };
      r.mouth = 'shout';
      r.brow = 'up';
      break;
    }
    case 'stretch': {
      // Arms straight up, a long seated stretch.
      seated();
      r.up = 10.4 - (f ? 0.4 : 0);
      const hgt = f ? -1.2 : 0;
      r.armL = { sh: [-7, -22.8], el: [-10.4, -35 + hgt], hd: [-7.6, -47.6 + hgt], fist: true };
      r.armR = { sh: [7, -22.8], el: [10.4, -35 + hgt], hd: [7.6, -47.6 + hgt], fist: true };
      r.mouth = f ? 'shout' : 'line';
      r.brow = 'flat';
      break;
    }
    case 'rub': {
      // Rubbing tired eyes, elbows on the desk.
      seated();
      r.up = 12;
      r.head = 'down';
      r.armL = { sh: [-7, -21.8], el: [-8.6, -15.8], hd: [-2.2 - (f ? 0.3 : 0), -28.4], over: true };
      r.armR = { sh: [7, -21.8], el: [8.6, -15.8], hd: [2.2 + (f ? 0.3 : 0), -28.6], over: true };
      r.mouth = 'line';
      r.brow = 'down';
      break;
    }
    case 'mobile': {
      // Head down, thumbing through a phone under the desk line.
      seated();
      r.head = 'down';
      r.armL = { sh: [-7, -22.6], el: [-8.2, -16.4], hd: [-2, -19.2] };
      r.armR = { sh: [7, -22.6], el: [8.2, -16.4], hd: [2, -19.4 + (f ? 0.4 : 0)] };
      r.mobile = [0, -20.2];
      r.mouth = 'line';
      r.brow = 'flat';
      break;
    }
    case 'eat': {
      // Lunch at the desk, eyes on the screen.
      seated();
      const up = f !== 2;
      r.armR = up ? { sh: [7, -22.6], el: [9.4, -19.6], hd: [3.2, -27.6 - (f ? 0.6 : 0)], over: true } : { sh: [7, -22.6], el: [8.8, -17.2], hd: [6, -14.6] };
      r.food = up ? [2.6, -28.8 - (f ? 0.6 : 0)] : [6.4, -15.6];
      r.armL = { sh: [-7, -22.6], el: [-8.4, -16.8], hd: [-4, -13.4] };
      r.mouth = f === 1 ? 'sip' : 'line';
      r.brow = 'flat';
      break;
    }
    case 'tie': {
      // Loosening the tie with one finger.
      seated();
      r.armR = { sh: [7, -22.6], el: [9.2, -24.6], hd: [1.4, -32.8 + (f ? 0.6 : 0)], over: true, fist: true };
      r.armL = { sh: [-7, -22.6], el: [-8.4, -16.8], hd: [-4, -13.4] };
      r.mouth = 'line';
      r.brow = f ? 'up' : 'flat';
      r.headDx = -0.5;
      break;
    }
    case 'chat': {
      // Turned to the next desk, one hand making the point.
      seated();
      r.headDx = 1.1;
      r.armR = { sh: [7, -22.6], el: [11, -21], hd: [13 + (f ? 0.6 : 0), -26 - (f ? 1 : 0)] };
      r.armL = { sh: [-7, -22.6], el: [-8.4, -16.8], hd: [-4, -13.4] };
      r.mouth = f ? 'talk' : 'grin';
      r.brow = 'cocky';
      break;
    }
    case 'hips': {
      // Standing at the desk, hands on hips, reading the screen.
      r.armL = { sh: [-7, -33.6], el: [-11.4, -27.6], hd: [-7.2, -22.6], fist: true };
      r.armR = { sh: [7, -33.6], el: [11.4, -27.6], hd: [7.2, -22.6], fist: true };
      r.mouth = 'line';
      r.brow = 'down';
      r.headDx = f ? 0.4 : -0.2;
      break;
    }
    case 'arms': {
      // Arms folded.
      r.armL = { sh: [-7, -33.6], el: [-8.6, -26.8], hd: [4.8, -28.4] };
      r.armR = { sh: [7, -33.6], el: [8.6, -27.4], hd: [-4.8, -28.8] };
      r.mouth = f ? 'smirk' : 'line';
      r.brow = 'cocky';
      break;
    }
    case 'watch': {
      // Checking the time, wrist up.
      r.armL = { sh: [-7, -33.6], el: [-9.4, -29.6], hd: [-1.2, -33.8 - (f ? 0.4 : 0)], over: true };
      r.armR = { sh: [7, -33.6], el: [9.2, -27.6], hd: [5.6, -22.4], hide: true };
      r.head = 'down';
      r.mouth = 'line';
      r.brow = 'down';
      break;
    }
    case 'drink': {
      const up = f === 0;
      r.armR = up ? { sh: [7, -33.6], el: [9.6, -30.4], hd: [3.4, -39.2], over: true } : { sh: [7, -33.6], el: [9.4, -28.6], hd: [8.4, -25.6] };
      r.glass = up ? [3.4, -40.4] : [8.8, -27];
      r.armL = { sh: [-7, -33.6], el: [-9.2, -27.6], hd: [-5.6, -22.4], hide: true };
      r.mouth = up ? 'sip' : 'smirk';
      break;
    }
    case 'putt': {
      // Lining up a putt: hands together low, head down, the club swinging.
      const sw = [0, -1.6, 0, 1.4][f];
      r.head = 'down';
      r.armL = { sh: [-7, -33.6], el: [-5.6, -27.4], hd: [-0.8 + sw * 0.2, -22.6] };
      r.armR = { sh: [7, -33.6], el: [5.6, -27.4], hd: [0.8 + sw * 0.2, -22.4] };
      r.putter = { grip: [sw * 0.2, -22.4], head: sw * 2.2 };
      r.mouth = 'line';
      r.brow = 'down';
      break;
    }
    case 'call': {
      // On the phone, standing.
      r.armR = { sh: [7, -33.6], el: [10.4, -32.8], hd: [6.4, -43.4], over: true };
      r.phone = true;
      const g = [0, 1, 2, 1][f];
      r.armL = g === 2 ? { sh: [-7, -33.6], el: [-11, -35.8], hd: [-10.4, -42], fist: true } : { sh: [-7, -33.6], el: [-9.4, -28], hd: [-6, -22.4], hide: true };
      r.mouth = f % 2 ? 'talk' : 'smirk';
      r.brow = f === 2 ? 'down' : 'cocky';
      break;
    }
    case 'slump': {
      // Head in hand, staring at a red screen.
      seated();
      r.up = 13 + (f ? 0.5 : 0);
      r.head = 'down';
      r.armL = { sh: [-7, -21.6], el: [-7.6, -15.6], hd: [5, -15.4] };
      r.armR = { sh: [7, -21.6], el: [9.2, -18.4], hd: [3.4 + (f ? 0.4 : 0), -29.2], over: true };
      r.mouth = 'frown';
      r.brow = 'up';
      break;
    }
  }
  return r;
}

// ---------------------------------------------------------------- figure

interface Body {
  /** Width multiplier for the torso, shoulders and arms. */
  bw: number;
  /** Height multiplier for the body below the head. */
  hf: number;
  look: Look;
  c: Pal;
  partner: boolean;
}

const X = (b: Body, x: number) => x * b.bw;
const Yb = (b: Body, y: number) => y * b.hf;

function armPoints(b: Body, a: Arm): Arm {
  const f = (p: P2): P2 => [X(b, p[0]), Yb(b, p[1])];
  return { ...a, sh: f(a.sh), el: f(a.el), hd: f(a.hd), finger: a.finger ? f(a.finger) : undefined };
}

function drawArm(p: Painter, b: Body, arm: Arm, front: boolean) {
  const a = armPoints(b, arm);
  const { c, look } = b;
  const jacket = look.outfit === 0 || look.outfit === 1 || look.outfit === 5 || look.outfit === 6;
  const rolled = look.outfit === 3;
  const sleeve = jacket ? c.suit : c.shirt;
  const sleeveS = jacket ? c.suitS : c.shirtS;
  const sleeveH = jacket ? c.suitH : mix(c.shirt, 0xffffffff, 0.3);
  const r = 2.05 * Math.min(1.12, b.bw);
  p.part(capsule(a.sh[0], a.sh[1], a.el[0], a.el[1], r), sleeve, { shade: sleeveS, hi: sleeveH });
  if (rolled && front) {
    // Sleeves rolled to the elbow.
    p.part(capsule(a.el[0], a.el[1], a.hd[0], a.hd[1], r * 0.8), c.skin, { shade: c.skinS, hi: c.skinH });
    p.part(ellipse(a.el[0], a.el[1], r * 1.02, r * 0.75), c.shirtS, { hi: c.shirt });
  } else p.part(capsule(a.el[0], a.el[1], a.hd[0], a.hd[1] - 0.6, r * 0.94), sleeve, { shade: sleeveS, hi: sleeveH });
  if (!front || a.hide) return;
  const dx = a.hd[0] - a.el[0];
  const dy = a.hd[1] - a.el[1];
  const len = Math.hypot(dx, dy) || 1;
  const ux = dx / len;
  const uy = dy / len;
  if (!rolled) p.part(capsule(a.hd[0] - ux * 1.3, a.hd[1] - uy * 1.3, a.hd[0] - ux * 0.6, a.hd[1] - uy * 0.6, 1.5), c.shirt, { shade: c.shirtS });
  if (look.watch && arm.sh[0] < 0) {
    // A thin band across the wrist, with a face.
    const wx = a.hd[0] - ux * 1.5;
    const wy = a.hd[1] - uy * 1.5;
    p.part(capsule(wx - uy * 1.25, wy + ux * 1.25, wx + uy * 1.25, wy - ux * 1.25, 0.42), c.gold, { shade: c.goldS });
    p.part(ellipse(wx, wy, 0.62, 0.62), c.goldS);
  }
  const hr = a.fist ? 1.75 : 1.6;
  p.part(ellipse(a.hd[0] + ux * 0.5, a.hd[1] + uy * 0.5, hr, hr * 1.08), c.skin, { shade: c.skinS, hi: c.skinH });
  if (a.fist) p.line(a.hd[0] - 0.8, a.hd[1] + 0.2, a.hd[0] + 0.8, a.hd[1] + 0.2, c.skinS, 0.25);
  if (a.finger) p.part(taper(a.hd[0] + ux * 1.2, a.hd[1] + uy * 1.2, a.finger[0], a.finger[1], 0.75, 0.55), c.skin, { shade: c.skinS });
}

function drawLegs(p: Painter, b: Body, r: Rig) {
  const { c } = b;
  if (r.legs === 'sit') {
    p.part(poly([[X(b, -6.4), -12], [X(b, -0.4), -12], [X(b, -0.8), -4], [X(b, -6), -4]]), c.trou, { shade: c.trouS });
    p.part(poly([[X(b, 0.4), -12], [X(b, 6.4), -12], [X(b, 6), -4], [X(b, 0.8), -4]]), c.trou, { shade: c.trouS });
    return;
  }
  for (const [side, lift] of [
    [-1, r.footL],
    [1, r.footR],
  ] as const) {
    const x = X(b, side * 3.1);
    const hip = Yb(b, -21) + r.bob;
    const w = b.look.fem ? 2.3 : 2.6 * Math.min(1.1, b.bw);
    p.part(taper(x, hip, x + side * 0.2, -3.2 - lift, w, w * 0.88), c.trou, { shade: c.trouS, hi: mix(c.trou, 0xffffffff, 0.08) });
    // Crease.
    p.line(x - side * 0.2, hip + 3, x, -4.5 - lift, c.trouS, 0.18);
    p.part(ellipse(x + side * 0.5, -1.5 - lift, b.look.fem ? 2.6 : 3.2, 1.75), c.shoe, { hi: c.shoeH });
  }
}

function torsoShape(b: Body, y: (v: number) => number, jacket: boolean): [Test, Box] {
  const sw = b.look.fem ? 7.1 : 7.7;
  const ww = b.look.fem ? 5.6 : 6.3;
  return union(
    poly([
      [X(b, -sw), y(-35.2)],
      [X(b, sw), y(-35.2)],
      [X(b, ww), y(-24)],
      [X(b, jacket ? 6.8 : 6.2), y(-19.3)],
      [X(b, jacket ? -6.8 : -6.2), y(-19.3)],
      [X(b, -ww), y(-24)],
    ]),
    ellipse(X(b, -(sw - 2)), y(-33.9), 2.7 * b.bw, 1.9),
    ellipse(X(b, sw - 2), y(-33.9), 2.7 * b.bw, 1.9),
  );
}

function drawNeckwear(p: Painter, b: Body, y: (v: number) => number, V: Test) {
  const { c, look } = b;
  const neck = look.fem && look.neck === 0 ? 3 : look.neck ?? 0;
  if (neck === 2) {
    // Bow tie.
    p.part(poly([[-2.3, y(-35.9)], [0, y(-35.1)], [-2.3, y(-34.1)]]), c.tie, { shade: c.tieS });
    p.part(poly([[2.3, y(-35.9)], [0, y(-35.1)], [2.3, y(-34.1)]]), c.tieS);
    p.part(ellipse(0, y(-35.05), 0.7, 0.7), c.tieH);
    return;
  }
  if (neck === 3) {
    // Open collar.
    p.tagged('collar', () => p.part(poly([[-1.5, y(-35.8)], [1.5, y(-35.8)], [0, y(-32.2)]]), c.skin, { shade: c.skinS }));
    return;
  }
  const low = neck === 1 ? 2.4 : 0;
  if (low) p.tagged('collar', () => p.part(poly([[-1.6, y(-35.8)], [1.6, y(-35.8)], [0, y(-32.4)]]), c.skin, { shade: c.skinS }));
  const tie = clip(poly([[-1.1, y(-34.2 + low)], [1.1, y(-34.2 + low)], [1.6, y(-28.3 + low * 0.3)], [0, y(-26.2)], [-1.6, y(-28.3 + low * 0.3)]]), V);
  p.part(tie, c.tie, { shade: c.tieS, hi: c.tieH });
  p.part(ellipse(0, y(-34.6 + low), 1.25, 0.95), c.tie, { shade: c.tieS });
  if (neck === 4) {
    // Lanyard and a visitor-style badge.
    p.line(-2.2, y(-35.4), -0.8, y(-27.6), c.tieS, 0.25);
    p.line(2.2, y(-35.4), 0.8, y(-27.6), c.tieS, 0.25);
    p.part(poly([[-1.6, y(-27.8)], [1.6, y(-27.8)], [1.6, y(-24.6)], [-1.6, y(-24.6)]]), c.white, { shade: c.cupS });
    p.part(poly([[-1.6, y(-27.8)], [1.6, y(-27.8)], [1.6, y(-26.9)], [-1.6, y(-26.9)]]), c.tie);
  }
}

function drawTorso(p: Painter, b: Body, r: Rig) {
  const { c, look } = b;
  const y = (v: number) => Yb(b, v) + r.up + r.bob;
  const outfit = look.outfit ?? 0;
  const jacket = outfit === 0 || outfit === 1 || outfit === 5 || outfit === 6;
  const turtle = outfit === 5;
  // Neck.
  const nw = look.fem ? 1.45 : 1.8;
  p.tagged('neck', () => p.part(poly([[-nw, y(-38.6) - (1 - b.hf) * 2], [nw, y(-38.6) - (1 - b.hf) * 2], [nw + 0.1, y(-34.6)], [-nw - 0.1, y(-34.6)]]), c.skin, { shade: c.skinS }));
  const body = torsoShape(b, y, jacket);

  if (r.facing === 'back') {
    const col = jacket ? c.suit : outfit === 2 ? c.vest : c.shirt;
    const colS = jacket ? c.suitS : outfit === 2 ? c.vestS : c.shirtS;
    p.part(body, col, { shade: colS, hi: jacket ? c.suitH : undefined, bottom: colS });
    if (jacket) p.line(0, y(-34), 0, y(-20), c.suitS, 0.3);
    if (outfit === 3) {
      p.line(X(b, -3.2), y(-35), X(b, -0.4), y(-24), c.brace, 0.5);
      p.line(X(b, 3.2), y(-35), X(b, 0.4), y(-24), c.brace, 0.5);
    }
    if (outfit === 4) p.part(poly([[X(b, -6), y(-33)], [X(b, 6), y(-33)], [X(b, 6.2), y(-19.6)], [X(b, -6.2), y(-19.6)]]), c.suit, { shade: c.suitS });
    p.part(poly([[-2.6, y(-36)], [2.6, y(-36)], [2.2, y(-34.6)], [-2.2, y(-34.6)]]), turtle ? c.vest : jacket ? c.suitS : c.shirtS);
    return;
  }

  // The shirt underneath everything.
  const V = poly([
    [-2.7, y(-35.8)],
    [2.7, y(-35.8)],
    [0, y(-26.2)],
  ]);
  if (!jacket) {
    p.part(body, c.shirt, { shade: c.shirtS, hi: mix(c.shirt, 0xffffffff, 0.35), bottom: c.shirtS });
    if (look.shirt === 4) for (let x = -6; x <= 6; x += 1.4) p.part(clip(capsule(X(b, x), y(-35), X(b, x), y(-19.5), 0.18), body[0]), c.shirtStripe);
    // Placket and buttons.
    p.line(0, y(-33), 0, y(-19.6), c.shirtS, 0.2);
    for (const v of [-30, -26.5, -23]) p.dot(0.4, y(v), c.shirtS, 0.3);
    // Belt.
    p.part(poly([[X(b, -6.2), y(-20.6)], [X(b, 6.2), y(-20.6)], [X(b, 6.2), y(-19.3)], [X(b, -6.2), y(-19.3)]]), c.shoe);
    p.part(poly([[-0.8, y(-20.5)], [0.8, y(-20.5)], [0.8, y(-19.4)], [-0.8, y(-19.4)]]), c.gold);
  }

  if (outfit === 2) {
    // Fleece vest over the shirt: the uniform of the trend.
    const vestShape = union(
      poly([
        [X(b, -5.6), y(-35.4)],
        [X(b, -2.6), y(-35.6)],
        [0, y(-31.6)],
        [X(b, 2.6), y(-35.6)],
        [X(b, 5.6), y(-35.4)],
        [X(b, 6.1), y(-24)],
        [X(b, 6.6), y(-19.2)],
        [X(b, -6.6), y(-19.2)],
        [X(b, -6.1), y(-24)],
      ]),
    );
    p.part(vestShape, c.vest, { shade: c.vestS, hi: c.vestH, bottom: c.vestS });
    p.line(0, y(-31.4), 0, y(-19.4), c.vestS, 0.25);
    p.part(poly([[X(b, 2.2), y(-30.4)], [X(b, 4.4), y(-30.4)], [X(b, 4.4), y(-29.2)], [X(b, 2.2), y(-29.2)]]), mix(c.vest, 0xffffffff, 0.55));
    p.part(poly([[-2.8, y(-36)], [2.8, y(-36)], [2.4, y(-34.6)], [-2.4, y(-34.6)]]), c.vestS);
  }
  if (outfit === 3) {
    // Braces.
    p.part(capsule(X(b, -3.4), y(-35.2), X(b, -2.6), y(-20.6), 0.55), c.brace, { shade: mix(c.brace, 0xff000000, 0.3) });
    p.part(capsule(X(b, 3.4), y(-35.2), X(b, 2.6), y(-20.6), 0.55), c.brace, { shade: mix(c.brace, 0xff000000, 0.3) });
    for (const x of [-2.6, 2.6]) p.dot(X(b, x), y(-21.2), c.gold, 0.35);
  }
  if (outfit === 4) {
    // Waistcoat.
    const w = poly([
      [X(b, -5.8), y(-33.4)],
      [X(b, -2.2), y(-33.4)],
      [0, y(-27.8)],
      [X(b, 2.2), y(-33.4)],
      [X(b, 5.8), y(-33.4)],
      [X(b, 6.2), y(-20.4)],
      [0.8, y(-18.8)],
      [-0.8, y(-18.8)],
      [X(b, -6.2), y(-20.4)],
    ]);
    p.part(w, c.suit, { shade: c.suitS, hi: c.suitH });
    for (const v of [-26.2, -24, -21.8]) p.dot(0, y(v), c.gold, 0.32);
    p.line(X(b, 1.6), y(-23.4), X(b, 4.6), y(-22.4), c.gold, 0.18);
  }

  if (jacket) {
    if (turtle) p.part(body, c.vest, { shade: c.vestS });
    const coat = outfit === 5 ? minus(body, poly([[-3.6, y(-36)], [3.6, y(-36)], [2.2, y(-19)], [-2.2, y(-19)]])) : body;
    p.part(coat, c.suit, { shade: c.suitS, hi: c.suitH, bottom: c.suitS });
    if (outfit === 1) for (let x = -6.6; x <= 6.6; x += 1.5) p.part(clip(capsule(X(b, x), y(-34.8), X(b, x * 0.95), y(-19.4), 0.14), coat[0]), c.stripe);
    if (turtle) {
      p.part(poly([[-2.6, y(-37.2)], [2.6, y(-37.2)], [2.8, y(-34.4)], [-2.8, y(-34.4)]]), c.vest, { shade: c.vestS, hi: c.vestH });
      for (const v of [-36.6, -35.6]) p.line(-2.4, y(v), 2.4, y(v), c.vestS, 0.14);
    } else {
      p.part(V, c.shirt, { shade: c.shirtS });
      if (look.shirt === 4) for (let x = -2.4; x <= 2.4; x += 1.2) p.part(clip(capsule(x, y(-36), x, y(-26), 0.16), V[0]), c.shirtStripe);
      p.part(poly([[-2.7, y(-35.9)], [-0.3, y(-35.2)], [-1.4, y(-33)]]), c.shirt, { shade: c.shirtS });
      p.part(poly([[2.7, y(-35.9)], [0.3, y(-35.2)], [1.4, y(-33)]]), c.shirtS);
      drawNeckwear(p, b, y, V[0]);
    }
    // Lapels.
    const dbl = outfit === 6;
    p.part(poly([[-2.7, y(-35.6)], [-4.5, y(-35.4)], [dbl ? -2.4 : -1.2, y(-27.4)], [-0.2, y(-26.6)]]), c.suitH);
    p.part(poly([[2.7, y(-35.6)], [4.5, y(-35.4)], [dbl ? 2.4 : 1.2, y(-27.4)], [0.2, y(-26.6)]]), c.suitS);
    if (dbl) {
      for (const v of [-25, -22.6]) {
        p.dot(-1.8, y(v), c.suitS, 0.4);
        p.dot(1.8, y(v), c.suitS, 0.4);
      }
    } else for (const v of [-24.6, -22.2]) p.dot(0, y(v), c.suitS, 0.42);
    // Pocket square, or a plain breast pocket.
    if (b.partner || outfit === 6 || outfit === 1) p.part(poly([[X(b, 3.2), y(-30.8)], [X(b, 5.4), y(-30.8)], [X(b, 4.9), y(-29.4)], [X(b, 3.7), y(-29.8)]]), b.partner ? c.gold : c.white);
    else p.line(X(b, 3.3), y(-30.2), X(b, 5.3), y(-30.2), c.suitS, 0.28);
  } else if (outfit !== 2) {
    // Collar and neckwear on a shirt with no jacket.
    p.part(poly([[-2.7, y(-35.9)], [-0.3, y(-35.2)], [-1.6, y(-33)]]), c.shirt, { shade: c.shirtS });
    p.part(poly([[2.7, y(-35.9)], [0.3, y(-35.2)], [1.6, y(-33)]]), c.shirtS);
    drawNeckwear(p, b, y, () => true);
  } else {
    // Open collar under the vest.
    p.tagged('collar', () => p.part(poly([[-1.5, y(-35.4)], [1.5, y(-35.4)], [0, y(-32.4)]]), c.skin, { shade: c.skinS }));
  }
}

// ---------------------------------------------------------------- head

interface HairSet {
  back?: [Test, Box];
  cap?: [Test, Box];
  /** Extra shape drawn on top: bun, quiff. */
  top?: [Test, Box];
  /** Long hair falling behind the shoulders. */
  long?: [Test, Box];
  part?: [number, number, number, number];
  bald?: boolean;
  shaved?: boolean;
}

function bumps(cx: number, cy: number, rx: number, ry: number, n: number, r: number): [Test, Box] {
  const s: [Test, Box][] = [];
  for (let i = 0; i < n; i++) {
    const a = Math.PI + (i / (n - 1)) * Math.PI;
    s.push(ellipse(cx + Math.cos(a) * rx, cy + Math.sin(a) * ry, r, r));
  }
  return union(ellipse(cx, cy, rx, ry), ...s);
}

function hairFor(style: number, cy: number): HairSet {
  const back = ellipse(0, cy - 1.1, 6.95, 6.9);
  switch (style) {
    case 0:
      return { back, cap: clip(ellipse(0, cy - 3.2, 6.85, 5.3), (x, y) => y < cy - 3.3 + 0.24 * (x + 3.5) - (x < -2 ? 0.6 : 0)), part: [-2.3, cy - 7.9, -2.1, cy - 4.8] };
    case 1:
      return { back: ellipse(0, cy - 0.9, 6.6, 6.6), cap: clip(ellipse(0, cy - 2.6, 6.55, 5.1), (_x, y) => y < cy - 3.8) };
    case 2:
      return { back, cap: clip(ellipse(0, cy - 2.4, 6.7, 5.4), (x, y) => (Math.abs(x) > 3.9 && y < cy - 1.4) || y < cy - 6.6) };
    case 3:
      // Slicked straight back, with shine.
      return { back: ellipse(0, cy - 1.6, 7.05, 7.1), cap: clip(ellipse(0, cy - 3.6, 7, 5.6), (x, y) => y < cy - 4.4 - 0.05 * Math.abs(x)) };
    case 4:
      return { back: ellipse(0, cy - 0.6, 6.4, 6.6), cap: clip(ellipse(0, cy - 2.2, 6.35, 5), (_x, y) => y < cy - 3.9), shaved: true };
    case 5:
      return { bald: true, back: clip(ellipse(0, cy, 6.6, 6.8), (x, y) => Math.abs(x) > 5 && y > cy - 2.4 && y < cy + 1.4) };
    case 6:
      return { back: bumps(0, cy - 2.4, 6.4, 5.6, 7, 1.7), cap: clip(bumps(0, cy - 3.2, 6.2, 4.8, 8, 1.6), (_x, y) => y < cy - 3.2) };
    case 7:
      // Pompadour.
      return {
        back: ellipse(0, cy - 1.2, 6.8, 6.8),
        cap: clip(ellipse(0, cy - 3.4, 6.8, 5.4), (_x, y) => y < cy - 4.2),
        top: taper(-2.6, cy - 7.6, 2.6, cy - 9.4, 3.2, 2.2),
      };
    case 8:
      return {
        back: ellipse(0, cy - 1, 6.9, 6.9),
        cap: clip(ellipse(0, cy - 3.2, 6.9, 5.4), (_x, y) => y < cy - 4.2),
        top: ellipse(0.6, cy - 9.8, 2.6, 2.2),
      };
    case 9:
      // Long, past the shoulders.
      return {
        back: ellipse(0, cy - 0.6, 7.3, 7.4),
        cap: clip(ellipse(0, cy - 2.8, 7.1, 5.6), (x, y) => y < cy - 3.6 + 0.22 * Math.abs(x + 1)),
        long: union(poly([[-7.2, cy - 1], [7.2, cy - 1], [8, cy + 13], [-8, cy + 13]]), ellipse(0, cy + 13, 8, 2.4)),
      };
    case 10:
      // Bob with a fringe.
      return {
        back: union(ellipse(0, cy - 0.4, 7.4, 7.3), poly([[-7.4, cy], [7.4, cy], [7.2, cy + 5.6], [-7.2, cy + 5.6]])),
        cap: clip(ellipse(0, cy - 2.4, 7.2, 5.9), (_x, y) => y < cy - 2.6),
      };
    case 11:
      // Pulled back into a high ponytail.
      return {
        back: ellipse(0, cy - 1, 6.8, 6.8),
        cap: clip(ellipse(0, cy - 3, 6.8, 5.4), (_x, y) => y < cy - 4),
        top: union(ellipse(3.8, cy - 7.4, 1.6, 1.4), taper(4.6, cy - 7, 7.2, cy + 2.4, 1.6, 0.9)),
      };
    case 12:
      return {
        back: ellipse(0, cy - 1, 6.9, 6.8),
        cap: clip(ellipse(0, cy - 3, 6.9, 5.4), (_x, y) => y < cy - 4),
        top: ellipse(0, cy - 8.8, 3.2, 2.6),
      };
    default:
      // Afro.
      return { back: ellipse(0, cy - 2.2, 8.8, 8.4), cap: clip(ellipse(0, cy - 3, 8.4, 7), (_x, y) => y < cy - 3.2) };
  }
}

function drawHead(pn: Painter, b: Body, r: Rig, t: number) {
  const { c, look } = b;
  const down = r.head === 'down';
  const cy = -44.6 + r.up + r.bob + (down ? 2.2 : 0);
  const cx = r.headDx;
  const style = look.hairStyle % 14;
  const hs = hairFor(style, cy);
  const shift = (s?: [Test, Box]): [Test, Box] | undefined => (s ? [(x, y) => s[0](x - cx, y), [s[1][0] + cx, s[1][1], s[1][2] + cx, s[1][3]]] : undefined);
  const H = { back: shift(hs.back), cap: shift(hs.cap), top: shift(hs.top) };
  const hairOpts = { shade: c.hairS, hi: c.hairH };
  const shaved = hs.shaved ? mix(c.hair, c.skin, 0.45) : c.hair;
  const detailed = pn.fs >= 1.4;

  if (r.facing === 'back') {
    pn.part(ellipse(cx - 6.1, cy + 0.6, 1.2, 1.8), c.skin, { shade: c.skinS });
    pn.part(ellipse(cx + 6.1, cy + 0.6, 1.2, 1.8), c.skinS);
    pn.part(ellipse(cx, cy, 6.2, 7), c.skin, { shade: c.skinS, hi: c.skinH });
    if (!hs.bald) {
      const cover = clip(union(...([H.back, ellipse(cx, cy, 6.4, 7.1), H.cap].filter(Boolean) as [Test, Box][])), (_x, y) => y < cy + (style === 10 ? 6 : 4.4));
      pn.part(cover, shaved, hairOpts);
      if (H.top) pn.part(H.top, c.hair, hairOpts);
      if (style === 11) pn.part(taper(cx, cy - 6, cx + 0.8, cy + 8, 2, 1), c.hair, hairOpts);
      if (style === 9) pn.part(poly([[cx - 7, cy], [cx + 7, cy], [cx + 7.6, cy + 13], [cx - 7.6, cy + 13]]), c.hair, hairOpts);
    } else pn.part(H.back!, c.hair, hairOpts);
    return;
  }

  // Hair behind the head, ears, the head itself.
  pn.gate.tag = 'hairBack';
  if (!hs.bald && H.back) pn.part(clip(H.back, (_x, y) => y < cy + (style === 10 ? 6 : 1.6)), shaved, { shade: c.hairS });
  pn.gate.tag = 'head';
  pn.part(ellipse(cx - 6.1, cy + 0.4, 1.25, 1.85), c.skin, { hi: c.skinH });
  pn.part(ellipse(cx + 6.1, cy + 0.4, 1.25, 1.85), c.skinS);
  const jaw = look.fem ? 4.5 : b.bw > 1.05 ? 5.4 : 4.9;
  pn.part(union(ellipse(cx, cy, 6.15, 7), ellipse(cx, cy + 2.6, jaw, 4.6)), c.skin, { shade: c.skinS, hi: c.skinH });
  if (look.fem) {
    pn.dot(cx - 6.1, cy + 2.1, c.gold, 0.45);
  }

  // Eyes, brows.
  pn.gate.tag = 'expression';
  const ey = cy + 0.4 + (down ? 0.8 : 0);
  const squint = r.brow === 'cocky';
  for (const sx of [-1, 1]) {
    const ex = cx + sx * 2.35;
    if (down) {
      pn.line(ex - 0.9, ey, ex + 0.9, ey, c.eye, 0.28);
      continue;
    }
    if (detailed) {
      pn.part(ellipse(ex, ey, 1.1, squint && sx > 0 ? 0.62 : 0.85), c.white);
      pn.part(ellipse(ex + 0.2, ey + 0.05, 0.6, squint && sx > 0 ? 0.5 : 0.72), c.iris);
      pn.part(ellipse(ex + 0.2, ey + 0.05, 0.3, 0.38), c.eye);
      pn.dot(ex - 0.05, ey - 0.3, c.white, 0.16);
      pn.line(ex - 1.1, ey - 0.75, ex + 1.1, ey - 0.75, look.fem ? c.eye : c.skinS, look.fem ? 0.26 : 0.18);
    } else pn.part(ellipse(ex, ey, 0.5, 0.95), c.eye);
  }
  const brow = (sx: number) => {
    const bx = cx + sx * 2.4;
    const by = ey - 2.1;
    const col = hs.bald ? c.skinS : c.hairS;
    const w = look.fem ? 0.26 : 0.38;
    if (r.brow === 'cocky') pn.line(bx - 1.2, by + (sx > 0 ? -0.2 : 0.3), bx + 1.2, by + (sx > 0 ? -0.9 : 0), col, w);
    else if (r.brow === 'down') pn.line(bx - 1.2 * sx, by - 0.4, bx + 1.2 * sx, by + 0.5, col, w);
    else if (r.brow === 'up') pn.line(bx - 1.2, by - 0.4, bx + 1.2, by - 0.7, col, w);
    else pn.line(bx - 1.2, by, bx + 1.2, by, col, w);
  };
  if (!down) {
    brow(-1);
    brow(1);
  }
  // Nose, cheeks.
  pn.gate.tag = 'head';
  pn.part(ellipse(cx + 0.6, cy + 2.5, 0.6, 1), c.skinS);
  pn.dot(cx - 0.2, cy + 2.2, c.skinH, 0.28);
  pn.tint(ellipse(cx - 3.6, cy + 3, 1.3, 0.75), c.blush, look.fem ? 0.26 : 0.12);
  pn.tint(ellipse(cx + 3.6, cy + 3, 1.3, 0.75), c.blush, look.fem ? 0.2 : 0.09);

  // Facial hair.
  pn.gate.tag = 'facial';
  const face = look.face ?? 0;
  const fh = c.hairS;
  const my = cy + 4.8;
  if (face === 1) pn.tint(clip(union(ellipse(cx, cy + 2.8, 5.2, 4.6)), (_x, y) => y > cy + 3.2), fh, 0.32);
  if (face === 2) {
    pn.part(minus(clip(union(ellipse(cx, cy + 2.9, 5.5, 5)), (_x, y) => y > cy + 2.4), ellipse(cx, my + 0.1, 1.9, 0.9)), c.hair, hairOpts);
  }
  if (face === 3 || face === 4) pn.part(union(ellipse(cx - 1, my - 0.8, 1.5, 0.6), ellipse(cx + 1, my - 0.8, 1.5, 0.6)), c.hair, { shade: c.hairS });
  if (face === 4) pn.part(ellipse(cx, my + 1.9, 1.4, 1.2), c.hair, { shade: c.hairS });

  // Mouth.
  pn.gate.tag = 'expression';
  const m = r.mouth;
  if (m === 'shout') {
    pn.part(ellipse(cx, my + 0.2, 1.8, 1.35), c.mouth);
    pn.part(ellipse(cx, my - 0.55, 1.4, 0.4), c.teeth);
  } else if (m === 'talk') pn.part(ellipse(cx, my, 1.3, 0.75), c.mouth);
  else if (m === 'grin') {
    pn.part(clip(ellipse(cx, my - 0.3, 2.2, 1.2), (_x, y) => y > my - 0.5), c.mouth);
    pn.part(clip(ellipse(cx, my - 0.3, 2, 1), (_x, y) => y > my - 0.5 && y < my + 0.1), c.teeth);
  } else if (m === 'frown') {
    pn.line(cx - 1.4, my + 0.4, cx + 1.4, my + 0.4, c.lips, 0.28);
    pn.line(cx - 1.4, my + 0.4, cx - 1.9, my + 1, c.lips, 0.25);
    pn.line(cx + 1.4, my + 0.4, cx + 1.9, my + 1, c.lips, 0.25);
  }
  else if (m === 'sip') pn.part(ellipse(cx, my, 0.7, 0.6), c.mouth);
  else if (m === 'smirk') {
    pn.line(cx - 1.3, my + 0.1, cx + 0.6, my + 0.1, c.lips, 0.3);
    pn.line(cx + 0.6, my + 0.1, cx + 1.8, my - 0.6, c.lips, 0.3);
  } else pn.line(cx - 1.3, my, cx + 1.3, my, c.lips, 0.32);

  // Hair on top.
  pn.gate.tag = 'hair';
  if (hs.bald) {
    if (H.back) pn.part(H.back, c.hair, hairOpts);
    pn.tagged('shine', () => pn.part(ellipse(cx - 2.2, cy - 5, 1.6, 0.8), mix(c.skin, 0xffffffff, 0.35)));
  } else {
    if (H.cap) pn.part(H.cap, shaved, hairOpts);
    if (H.top) pn.part(H.top, c.hair, hairOpts);
    if (hs.part) pn.line(cx + hs.part[0], hs.part[1], cx + hs.part[2], hs.part[3], c.hairS, 0.3);
    if (style === 3) {
      for (const [a, b2] of [
        [-3.5, -1.2],
        [0.4, 2.8],
      ])
        pn.line(cx + a, cy - 8.3, cx + b2, cy - 7.2, c.hairH, 0.26);
    }
  }

  // Accessories on the face.
  pn.gate.tag = 'eyewear';
  const eyes = look.eyes ?? 0;
  if (eyes === 1 && !down) {
    // Sunglasses. Indoors.
    for (const sx of [-1, 1]) pn.part(union(ellipse(cx + sx * 2.45, ey + 0.1, 1.9, 1.3)), c.lens);
    pn.line(cx - 0.8, ey - 0.3, cx + 0.8, ey - 0.3, c.lens, 0.3);
    pn.line(cx - 4.2, ey - 0.3, cx - 6.2, ey - 0.6, c.lens, 0.3);
    pn.line(cx + 4.2, ey - 0.3, cx + 6.2, ey - 0.6, c.lens, 0.3);
    pn.line(cx - 3.3, ey - 0.4, cx - 2.3, ey + 0.4, c.lensH, 0.22);
    pn.line(cx + 1.7, ey - 0.4, cx + 2.7, ey + 0.4, c.lensH, 0.22);
  }
  if (eyes === 2 && !down) {
    for (const sx of [-1, 1]) {
      const [t1] = ellipse(cx + sx * 2.35, ey, 1.75, 1.35);
      const [t2] = ellipse(cx + sx * 2.35, ey, 1.28, 0.9);
      pn.part([(x, y) => t1(x, y) && !t2(x, y), [cx + sx * 2.35 - 2, ey - 1.5, cx + sx * 2.35 + 2, ey + 1.5]], b.partner ? c.gold : c.frame);
    }
    pn.line(cx - 0.7, ey - 0.3, cx + 0.7, ey - 0.3, b.partner ? c.gold : c.frame, 0.28);
  }
  if (eyes === 3) {
    // Headset: band over the top, a cup on one ear, a boom to the mouth.
    const [o] = ellipse(cx, cy - 1, 7.6, 8.2);
    const [i] = ellipse(cx, cy - 1, 6.9, 7.5);
    pn.part([(x, y) => o(x, y) && !i(x, y) && y < cy - 0.5, [cx - 8, cy - 10, cx + 8, cy]], c.phone);
    pn.part(ellipse(cx - 6.6, cy + 0.2, 1.4, 2), c.phone, { hi: mix(c.phone, 0xffffffff, 0.3) });
    pn.line(cx - 6.2, cy + 1.6, cx - 1.8, my + 0.4, c.phone, 0.28);
    pn.dot(cx - 1.6, my + 0.4, c.phone, 0.55);
  }
  if (eyes === 4) {
    pn.dot(cx + 6.2, cy + 0.6, c.phone, 0.55);
    pn.line(cx + 6.2, cy + 1.2, cx + 5.4, cy + 7.2, c.cupS, 0.18);
  }
  pn.gate.tag = 'cigar';
  if (look.cigar && r.mouth !== 'shout') {
    pn.part(capsule(cx + 1.4, my + 0.2, cx + 5.6, my + 1.2, 0.55), c.cigar, { hi: mix(c.cigar, 0xffffffff, 0.2) });
    pn.dot(cx + 5.9, my + 1.25, c.ember, 0.5);
    const puff = t % 3;
    pn.tint(ellipse(cx + 6.4 + puff * 0.4, my - 1.6 - puff * 1.6, 0.9 + puff * 0.3, 0.8 + puff * 0.3), 0xffe8e8e8, 0.55);
  }
}

function drawBox(pn: Painter, c: Pal, r: Rig, behind: boolean) {
  const b = r.bob;
  if (behind) {
    pn.part(poly([[-8.6, -31 + b], [8.6, -31 + b], [8.6, -20.5 + b], [-8.6, -20.5 + b]]), c.boxS);
    return;
  }
  pn.part(poly([[-7.8, -31.5 + b], [7.8, -31.5 + b], [7.8, -19.8 + b], [-7.8, -19.8 + b]]), c.box, { shade: c.boxS, hi: c.boxH });
  pn.part(poly([[-7.8, -31.5 + b], [7.8, -31.5 + b], [6.8, -29.8 + b], [-6.8, -29.8 + b]]), c.boxH);
  pn.part(poly([[-0.9, -31.5 + b], [0.9, -31.5 + b], [0.9, -26 + b], [-0.9, -26 + b]]), c.tape);
  pn.part(ellipse(-4.2, -32.6 + b, 1.9, 1.5), LEAF, { shade: LEAF_S });
  pn.part(poly([[2.2, -34 + b], [5.6, -33.2 + b], [5.2, -31.5 + b], [2, -31.5 + b]]), c.white, { shade: c.cupS });
  // A framed photo of a sports car.
  pn.part(poly([[-1.6, -34.4 + b], [1.2, -34.8 + b], [1.4, -31.5 + b], [-1.4, -31.5 + b]]), c.gold);
  pn.part(poly([[-1.1, -33.8 + b], [0.8, -34.1 + b], [0.9, -32.1 + b], [-0.9, -32.1 + b]]), c.tieH);
}

const LEAF = rgba('#5a8a55');
const LEAF_S = rgba('#3f6a42');

// ---------------------------------------------------------------- entry points

export interface FigureOpts {
  scale?: number;
  glasses?: boolean;
  /** Supersampling factor for smooth edges (1 = hard pixels). */
  ss?: number;
  /**
   * Draw only these parts (for NFT trait layers): hairBack, neck, body,
   * collar, head, expression, facial, hair, eyewear, cigar.
   */
  only?: string[];
  /** Skip the ink outline. */
  noOutline?: boolean;
  /** Override the pose's expression. */
  face?: { mouth?: Mouth; brow?: Rig['brow'] };
}

const HEAD_SCALE = 1.15;
const W_UNITS = 40;
const H_UNITS = 64;

/** Every field that changes how a figure looks, for cache keys. */
export const lookKey = (l: Look) =>
  [l.skin, l.hair, l.hairStyle, l.suit, l.tie, l.build, l.height, l.face, l.outfit, l.shirt, l.neck, l.eyes, l.watch ? 1 : 0, l.cigar ? 1 : 0, l.fem ? 1 : 0].join('.');

export function renderFigure(look: Look, pose: Pose, frame: number, opts: FigureOpts = {}): SpriteImage {
  const s = opts.scale ?? 1;
  const ss = Math.max(1, Math.round(opts.ss ?? 1));
  const w = Math.ceil(W_UNITS * s) + 2;
  const h = Math.ceil(H_UNITS * s) + 2;
  const pn = new Painter(w * ss, h * ss, (w / 2) * ss, (h - 1 - 0.5 * s) * ss, s * ss, undefined, ss, { tag: 'body', allow: opts.only ? new Set(opts.only) : null });
  const partner = !!opts.glasses;
  const lk: Look = partner ? { ...look, eyes: look.eyes ?? 2 } : look;
  const b: Body = {
    bw: [0.9, 1, 1.14][lk.build ?? 1] * (lk.fem ? 0.94 : 1),
    hf: [0.93, 1, 1.07][lk.height ?? 1] * (lk.fem ? 0.97 : 1),
    look: lk,
    c: palette(lk),
    partner,
  };
  const r = { ...rigFor(pose, frame), ...opts.face };
  const front = r.facing === 'front';
  const c = b.c;

  // Long hair falls behind everything.
  const style = lk.hairStyle % 14;
  if (front && style === 9) {
    pn.gate.tag = 'hairBack';
    const cy = -44.6 + r.up + r.bob + Yb(b, -38.2) + 38.2;
    pn.part(union(poly([[-7.2, cy - 1], [7.2, cy - 1], [7.8, cy + 12.6], [-7.8, cy + 12.6]]), ellipse(0, cy + 12.6, 7.8, 2.2)), c.hair, { shade: c.hairS, hi: c.hairH });
  }
  pn.gate.tag = 'body';
  if (r.box && !front) drawBox(pn, c, r, true);
  drawLegs(pn, b, r);
  if (!front) {
    drawArm(pn, b, r.armL, false);
    drawArm(pn, b, r.armR, false);
  }
  // Arms raised behind the head go before the torso and head.
  const behind = (a: Arm) => a.hide && a.hd[1] < -30;
  if (front) for (const a of [r.armL, r.armR]) if (behind(a)) drawArm(pn, b, a, true);
  drawTorso(pn, b, r);
  if (front && !r.box) for (const a of [r.armL, r.armR]) if (!a.over && !behind(a)) drawArm(pn, b, a, true);
  if (r.box && front) {
    drawBox(pn, c, r, false);
    pn.part(ellipse(-8, -25.4 + r.bob, 1.5, 1.7), c.skin, { shade: c.skinS });
    pn.part(ellipse(8, -25.4 + r.bob, 1.5, 1.7), c.skin, { shade: c.skinS });
  }
  // The head is drawn at the standard height, scaled about its own chin,
  // then lifted or dropped onto this body's neck so it always sits on the collar.
  const lift = r.up + r.bob + (r.head === 'down' ? 2.2 : 0);
  drawHead(pn.moved(0, Yb(b, -38.2) + 38.2).scaled(HEAD_SCALE, 0, -38.2 + lift), b, r, frame);
  pn.gate.tag = 'body';
  if (front) for (const a of [r.armL, r.armR]) if (a.over) drawArm(pn, b, a, true);
  if (r.phone) {
    const hd = armPoints(b, r.armR).hd;
    pn.part(poly([[hd[0] - 0.9, hd[1] - 3.2], [hd[0] + 0.9, hd[1] - 3.4], [hd[0] + 1.1, hd[1] + 0.8], [hd[0] - 0.7, hd[1] + 1]]), c.phone, { hi: mix(c.phone, 0xffffffff, 0.3) });
  }
  if (r.cup) {
    const [x, y] = [X(b, r.cup[0]), Yb(b, r.cup[1])];
    pn.part(poly([[x - 1.3, y - 1.8], [x + 1.3, y - 1.8], [x + 1, y + 1.8], [x - 1, y + 1.8]]), c.cup, { shade: c.cupS });
    pn.part(poly([[x - 1.45, y - 2.4], [x + 1.45, y - 2.4], [x + 1.4, y - 1.7], [x - 1.4, y - 1.7]]), c.tie);
    pn.part(poly([[x - 1.2, y - 0.4], [x + 1.2, y - 0.4], [x + 1.1, y + 0.6], [x - 1.1, y + 0.6]]), c.cupS);
  }
  if (r.mobile) {
    const [x, y] = [X(b, r.mobile[0]), Yb(b, r.mobile[1])];
    pn.part(poly([[x - 1.6, y - 1.2], [x + 1.6, y - 1.2], [x + 1.4, y + 1.6], [x - 1.4, y + 1.6]]), c.phone, { hi: mix(c.phone, 0xffffffff, 0.3) });
    pn.part(poly([[x - 1.2, y - 0.9], [x + 1.2, y - 0.9], [x + 1.05, y + 1.2], [x - 1.05, y + 1.2]]), rgba('#8fc8f0'));
    // Thumbs over the screen.
    pn.part(ellipse(x - 1.3, y + 0.6, 0.8, 0.7), c.skin, { shade: c.skinS });
    pn.part(ellipse(x + 1.3, y + 0.4, 0.8, 0.7), c.skin, { shade: c.skinS });
  }
  if (r.food) {
    const [x, y] = [X(b, r.food[0]), Yb(b, r.food[1])];
    pn.part(poly([[x - 2, y - 0.8], [x + 2, y - 1.2], [x + 2, y + 0.2], [x - 2, y + 0.6]]), rgba('#e2b877'), { shade: rgba('#b88a4c') });
    pn.part(poly([[x - 2, y - 0.1], [x + 2, y - 0.5], [x + 2, y - 0.1], [x - 2, y + 0.3]]), rgba('#6ea865'));
    pn.part(poly([[x - 2, y + 0.3], [x + 2, y - 0.1], [x + 2, y + 1], [x - 2, y + 1.4]]), rgba('#e2b877'), { shade: rgba('#b88a4c') });
  }
  if (r.glass) {
    const [x, y] = [X(b, r.glass[0]), Yb(b, r.glass[1])];
    pn.part(poly([[x - 1.2, y - 1.4], [x + 1.2, y - 1.4], [x + 1.1, y + 1.4], [x - 1.1, y + 1.4]]), rgba('#dcebf2'), { shade: rgba('#a9c0cc') });
    pn.part(poly([[x - 1.1, y], [x + 1.1, y], [x + 1.05, y + 1.3], [x - 1.05, y + 1.3]]), rgba('#c07a2c'), { shade: rgba('#8a5418') });
  }
  if (r.putter) {
    const [gx, gy] = [X(b, r.putter.grip[0]), Yb(b, r.putter.grip[1])];
    const hx2 = r.putter.head + 1.4;
    pn.line(gx, gy, hx2, -0.9, rgba('#9aa2ab'), 0.3);
    pn.part(poly([[hx2 - 0.4, -1.8], [hx2 + 2.2, -1.8], [hx2 + 2.2, -0.2], [hx2 - 0.4, -0.2]]), rgba('#3a3d44'), { hi: rgba('#b7bcc3') });
    pn.part(ellipse(r.putter.head + 6.5, -0.5, 0.7, 0.6), rgba('#ffffff'), { shade: rgba('#cfcfcf') });
  }
  if (r.box && !front) {
    pn.part(capsule(-7, -33.6 + r.bob, -8.6, -26 + r.bob, 2), c.suit, { shade: c.suitS });
    pn.part(capsule(7, -33.6 + r.bob, 8.6, -26 + r.bob, 2), c.suit, { shade: c.suitS });
  }
  if (!opts.noOutline) pn.outline(c.ink);
  return pn.image();
}

/** Head and shoulders, square, for headshots. */
export function renderBust(look: Look, size: number, glasses = false, ss = 1, extra: FigureOpts = {}): SpriteImage {
  const s = size / 30;
  const full = renderFigure(look, 'stand', 0, { ...extra, scale: s, glasses, ss });
  const cx = full.w / 2;
  const hf = [0.93, 1, 1.07][look.height ?? 1];
  const top = full.h - 1 - 0.5 * s - (38.2 * hf + 17.5) * s;
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
