/**
 * Flat pixel portraits: a 32×32 grid, one flat colour per region and a
 * one-cell ink outline around each part. Used for every headshot on the site,
 * Steve's profile picture and the Investors NFT collection.
 *
 * Each part draws into its own transparent layer, so the same code renders
 * the site portraits (all layers stacked) and the NFT trait PNGs (one layer
 * per file). The layers line up because every head shares the same skull
 * top, eye line and mouth line.
 *
 * Browser-safe: no Node imports.
 */
import { rgba } from '../scene/buffer';
import { HAIRS, SKINS, SUITS, TIES, shade } from './palette';
import type { Look } from '../sim/types';

export const GRID = 32;
export type Layer = Uint32Array;

const CX = 16;
const CY = 14.5;
const R = 9.2;
const INK = rgba('#1d1c19');
const WHITE = rgba('#f7f4ec');
const GOLD = rgba('#d4a640');
const GOLD_HI = rgba('#f0d58a');

const blank = (): Layer => new Uint32Array(GRID * GRID);
const at = (x: number, y: number) => y * GRID + x;
const inGrid = (x: number, y: number) => x >= 0 && y >= 0 && x < GRID && y < GRID;

function put(l: Layer, x: number, y: number, c: number) {
  if (inGrid(x, y)) l[at(x, y)] = c;
}

/** Fill every cell whose centre passes the test. */
function fill(l: Layer, test: (px: number, py: number, x: number, y: number) => boolean, c: number | ((x: number, y: number) => number)) {
  for (let y = 0; y < GRID; y++)
    for (let x = 0; x < GRID; x++) if (test(x + 0.5, y + 0.5, x, y)) l[at(x, y)] = typeof c === 'number' ? c : c(x, y);
}

/** Ink every empty cell that touches a filled one (4-neighbour). `rows` limits where. */
function outline(l: Layer, rows: [number, number] = [0, GRID - 1], c = INK) {
  const add: number[] = [];
  for (let y = rows[0]; y <= rows[1]; y++)
    for (let x = 0; x < GRID; x++) {
      if (l[at(x, y)]) continue;
      const n = [
        [x - 1, y],
        [x + 1, y],
        [x, y - 1],
        [x, y + 1],
      ].some(([a, b]) => inGrid(a, b) && l[at(a, b)] && l[at(a, b)] !== c);
      if (n) add.push(at(x, y));
    }
  for (const i of add) l[i] = c;
}

const dx = (px: number) => px - CX;
const dy = (py: number) => py - CY;
const skull = (px: number, py: number, r = R) => dx(px) ** 2 + dy(py) ** 2 <= r * r;

// ---------------------------------------------------------------- options

export const BACKGROUNDS = [
  { id: 'paper', name: 'Paper', hex: '#ece5d3' },
  { id: 'ledger', name: 'Ledger green', hex: '#b6caae' },
  { id: 'salmon', name: 'Pink paper', hex: '#efcbb2' },
  { id: 'brass', name: 'Brass', hex: '#e2c27c' },
  { id: 'brick', name: 'Brick', hex: '#d39a86' },
  { id: 'lilac', name: 'Lilac', hex: '#cbbfdc' },
  { id: 'mint', name: 'Mint', hex: '#c3e0cf' },
  { id: 'night', name: 'After hours', hex: '#2b3245' },
] as const;

export const HEADS = [
  { id: 'round', name: 'Round' },
  { id: 'long', name: 'Long' },
  { id: 'square', name: 'Square jaw' },
  { id: 'wide', name: 'Jowly' },
] as const;
export type HeadId = (typeof HEADS)[number]['id'];

export const SKIN_NAMES = ['Porcelain', 'Fair', 'Olive', 'Tan', 'Brown', 'Deep'];

export const EXPRESSIONS = [
  { id: 'content', name: 'Content' },
  { id: 'smug', name: 'Smug' },
  { id: 'grin', name: 'Toothy grin' },
  { id: 'deadpan', name: 'Deadpan' },
  { id: 'wide', name: 'Wide-eyed' },
  { id: 'worried', name: 'Worried' },
  { id: 'wink', name: 'Wink' },
  { id: 'side', name: 'Side-eye' },
  { id: 'cocky', name: 'Cocky' },
] as const;
export type ExpressionId = (typeof EXPRESSIONS)[number]['id'];

export const HAIR_STYLES = [
  { id: 'crop', name: 'Short crop' },
  { id: 'part', name: 'Side part' },
  { id: 'slick', name: 'Slicked back' },
  { id: 'messy', name: 'Messy' },
  { id: 'buzz', name: 'Buzz cut' },
  { id: 'bald', name: 'Bald' },
  { id: 'curly', name: 'Curly' },
  { id: 'pomp', name: 'Pompadour' },
  { id: 'receding', name: 'Receding' },
  { id: 'long', name: 'Long' },
  { id: 'bob', name: 'Bob' },
  { id: 'bun', name: 'Top bun' },
  { id: 'afro', name: 'Afro' },
  { id: 'visor', name: 'Green visor' },
  { id: 'bowler', name: 'Bowler hat' },
  { id: 'beanie', name: 'Beanie' },
] as const;
export type HairId = (typeof HAIR_STYLES)[number]['id'];

export const HAIR_COLORS = [
  { id: 'black', name: 'Black', hex: HAIRS[0] },
  { id: 'brown', name: 'Dark brown', hex: HAIRS[1] },
  { id: 'chestnut', name: 'Chestnut', hex: HAIRS[2] },
  { id: 'sandy', name: 'Sandy', hex: HAIRS[3] },
  { id: 'grey', name: 'Silver', hex: HAIRS[4] },
  { id: 'white', name: 'White', hex: HAIRS[5] },
  { id: 'auburn', name: 'Auburn', hex: HAIRS[6] },
  { id: 'teal', name: 'Dyed teal', hex: '#3d8c86' },
] as const;

export const FACIAL_HAIR = [
  { id: 'none', name: 'Clean-shaven' },
  { id: 'stubble', name: 'Stubble' },
  { id: 'moustache', name: 'Moustache' },
  { id: 'goatee', name: 'Goatee' },
  { id: 'beard', name: 'Full beard' },
] as const;
export type FacialId = (typeof FACIAL_HAIR)[number]['id'];

export const OUTFITS = [
  { id: 'navy', name: 'Navy suit', kind: 'suit', body: SUITS[0], tie: TIES[0], shirt: '#f4f1e8' },
  { id: 'charcoal', name: 'Charcoal suit', kind: 'suit', body: SUITS[1], tie: TIES[1], shirt: '#cfe0f2' },
  { id: 'pinstripe', name: 'Pinstripe', kind: 'pinstripe', body: '#2b3550', tie: TIES[5], shirt: '#f4f1e8' },
  { id: 'tweed', name: 'Tobacco tweed', kind: 'tweed', body: SUITS[3], tie: TIES[2], shirt: '#f4f1e8' },
  { id: 'double', name: 'Double-breasted', kind: 'double', body: '#30303a', tie: TIES[0], shirt: '#f4f1e8' },
  { id: 'jacket', name: 'Floor jacket', kind: 'jacket', body: '#d9a238', tie: TIES[3], shirt: '#f4f1e8' },
  { id: 'braces', name: 'Shirt and braces', kind: 'braces', body: '#f4f1e8', tie: TIES[3], shirt: '#f4f1e8', trim: '#9b2f33' },
  { id: 'vest', name: 'Fleece vest', kind: 'vest', body: '#5e6672', tie: '', shirt: '#bcd3ec' },
  { id: 'turtleneck', name: 'Black turtleneck', kind: 'turtleneck', body: '#232327', tie: '', shirt: '' },
  { id: 'hoodie', name: 'Grey hoodie', kind: 'hoodie', body: '#8a8d93', tie: '', shirt: '' },
] as const;
export type OutfitKind = 'suit' | 'pinstripe' | 'tweed' | 'double' | 'jacket' | 'braces' | 'vest' | 'turtleneck' | 'hoodie';
export interface OutfitSpec {
  kind: OutfitKind;
  body: string;
  tie: string;
  shirt: string;
  trim?: string;
  bow?: boolean;
}

export const ACCESSORIES = [
  { id: 'none', name: 'None' },
  { id: 'glasses', name: 'Glasses' },
  { id: 'shades', name: 'Sunglasses' },
  { id: 'cigar', name: 'Cigar' },
  { id: 'pin', name: 'Gold lapel pin' },
  { id: 'pen', name: 'Pen behind the ear' },
  { id: 'earpiece', name: 'Earpiece' },
  { id: 'chain', name: 'Gold chain' },
  { id: 'headset', name: 'Headset' },
  { id: 'monocle', name: 'Monocle' },
] as const;
export type AccessoryId = (typeof ACCESSORIES)[number]['id'];

// ---------------------------------------------------------------- layers

export function background(hex: string): Layer {
  return new Uint32Array(GRID * GRID).fill(rgba(hex));
}

function headTest(shape: HeadId) {
  return (px: number, py: number) => {
    const x = dx(px);
    const y = dy(py);
    if (y < 0) return x * x + y * y <= R * R;
    switch (shape) {
      case 'long':
        return (x / R) ** 2 + (y / (R + 1.5)) ** 2 <= 1;
      case 'square':
        return (x / R) ** 4 + (y / (R - 0.2)) ** 4 <= 1;
      case 'wide':
        return (x / (R + 0.9)) ** 2 + (y / (R - 0.5)) ** 2 <= 1;
      default:
        return x * x + y * y <= R * R;
    }
  };
}

/** The neck sits under the outfit, so a turtleneck can cover it. */
export function neckLayer(skinHex: string): Layer {
  const l = blank();
  const c = rgba(shade(skinHex, -0.14));
  fill(l, (px, py) => Math.abs(dx(px)) <= 2.2 && py > CY + 6 && py < 27, c);
  outline(l, [CY + 6, 26]);
  return l;
}

export function headLayer(shape: HeadId, skinHex: string): Layer {
  const l = blank();
  const skin = rgba(skinHex);
  const test = headTest(shape);
  const earX = R - 0.3;
  const ear = (px: number, py: number) => [-1, 1].some((s) => ((px - (CX + s * earX)) / 1.3) ** 2 + ((py - (CY + 1.4)) / 1.7) ** 2 <= 1);
  fill(l, (px, py) => test(px, py) || ear(px, py), skin);
  outline(l);
  // Inner ear, nose.
  const sh = rgba(shade(skinHex, -0.18));
  put(l, Math.floor(CX - earX), Math.floor(CY + 1.2), sh);
  put(l, Math.floor(CX + earX), Math.floor(CY + 1.2), sh);
  put(l, 16, 17, sh);
  return l;
}

const EYE_L = 12;
const EYE_R = 19;
const EYE_Y = 14;
const MOUTH_Y = 19;

export function expressionLayer(e: ExpressionId): Layer {
  const l = blank();
  const p = (x: number, y: number, c = INK) => put(l, x, y, c);
  const dot = (x: number) => {
    p(x, EYE_Y);
    p(x, EYE_Y + 1);
  };
  const smile = () => {
    for (let x = 14; x <= 17; x++) p(x, MOUTH_Y);
    p(13, MOUTH_Y - 1);
    p(18, MOUTH_Y - 1);
  };
  switch (e) {
    case 'content':
      dot(EYE_L);
      dot(EYE_R);
      smile();
      break;
    case 'smug':
      dot(EYE_L);
      p(EYE_R, EYE_Y + 1);
      for (const x of [11, 12, 13]) p(x, EYE_Y - 2);
      for (const x of [18, 19, 20]) p(x, EYE_Y);
      for (let x = 14; x <= 17; x++) p(x, MOUTH_Y);
      p(18, MOUTH_Y - 1);
      break;
    case 'grin':
      dot(EYE_L);
      dot(EYE_R);
      p(13, MOUTH_Y - 1);
      p(18, MOUTH_Y - 1);
      p(13, MOUTH_Y);
      p(18, MOUTH_Y);
      for (let x = 14; x <= 17; x++) {
        p(x, MOUTH_Y, WHITE);
        p(x, MOUTH_Y + 1);
      }
      break;
    case 'deadpan':
      for (const x of [11, 12, 19, 20]) p(x, EYE_Y + 1);
      for (let x = 14; x <= 17; x++) p(x, MOUTH_Y);
      break;
    case 'wide':
      for (const x0 of [11, 19]) {
        for (const [x, y] of [
          [x0, EYE_Y],
          [x0 + 1, EYE_Y],
          [x0, EYE_Y + 1],
          [x0 + 1, EYE_Y + 1],
        ])
          p(x, y, WHITE);
        p(x0, EYE_Y - 1);
        p(x0 + 1, EYE_Y - 1);
      }
      p(12, EYE_Y + 1);
      p(19, EYE_Y + 1);
      for (const [x, y] of [
        [15, MOUTH_Y],
        [16, MOUTH_Y],
        [15, MOUTH_Y + 1],
        [16, MOUTH_Y + 1],
      ])
        p(x, y);
      break;
    case 'worried':
      dot(EYE_L);
      dot(EYE_R);
      p(11, EYE_Y - 1);
      p(12, EYE_Y - 2);
      p(19, EYE_Y - 2);
      p(20, EYE_Y - 1);
      for (let x = 14; x <= 17; x++) p(x, MOUTH_Y);
      p(13, MOUTH_Y + 1);
      p(18, MOUTH_Y + 1);
      break;
    case 'wink':
      dot(EYE_L);
      p(18, EYE_Y + 1);
      p(19, EYE_Y);
      p(20, EYE_Y + 1);
      smile();
      break;
    case 'side':
      for (const x0 of [11, 18]) {
        p(x0, EYE_Y, WHITE);
        p(x0, EYE_Y + 1, WHITE);
        p(x0 + 1, EYE_Y);
        p(x0 + 1, EYE_Y + 1);
      }
      for (const x of [11, 12, 18, 19]) p(x, EYE_Y - 1);
      for (let x = 15; x <= 17; x++) p(x, MOUTH_Y);
      break;
    case 'cocky':
      dot(EYE_L);
      dot(EYE_R);
      p(11, EYE_Y - 2);
      p(12, EYE_Y - 1);
      p(19, EYE_Y - 1);
      p(20, EYE_Y - 2);
      for (let x = 14; x <= 16; x++) p(x, MOUTH_Y);
      p(17, MOUTH_Y - 1);
      p(18, MOUTH_Y - 1);
      break;
  }
  return l;
}

export function facialHairLayer(f: FacialId, hairHex: string, shape: HeadId = 'round'): Layer {
  const l = blank();
  if (f === 'none') return l;
  const c = rgba(hairHex);
  const face = headTest(shape);
  if (f === 'stubble') {
    const s = rgba(shade(hairHex, 0.15));
    fill(l, (px, py, x, y) => face(px, py) && py > 17.5 && (x + y) % 4 === 0 && y % 2 === 0 && Math.abs(dx(px)) < R - 1.2, s);
    return l;
  }
  const tash = () => {
    for (let x = 13; x <= 18; x++) put(l, x, MOUTH_Y - 1, c);
  };
  if (f === 'moustache') tash();
  if (f === 'goatee') {
    tash();
    fill(l, (px, py) => Math.abs(dx(px)) <= 2 && py > MOUTH_Y + 1 && face(px, py), c);
  }
  if (f === 'beard') {
    fill(l, (px, py) => face(px, py) && py > 17 && (Math.abs(dx(px)) > 5.5 || py > MOUTH_Y - 0.5), c);
    tash();
  }
  outline(l, [MOUTH_Y + 1, GRID - 1]);
  return l;
}

/** Rough 1-D hash, for jagged edges that are the same every time. */
const jag = (x: number) => ((x * 2654435761) >>> 0) % 3;

export function hairLayer(style: HairId, hairHex: string): Layer {
  const l = blank();
  const h = rgba(hairHex);
  const hi = rgba(shade(hairHex, hairHex === HAIRS[5] ? -0.12 : 0.3));
  const lo = rgba(shade(hairHex, -0.25));
  const cap = (rOut: number, hairline: (px: number) => number) => fill(l, (px, py) => skull(px, py, rOut) && py < hairline(px), h);
  const sideburns = (to: number) => fill(l, (px, py) => skull(px, py, R + 0.4) && Math.abs(dx(px)) > R - 1.1 && py < to - 1.5, h);

  switch (style) {
    case 'crop':
      cap(R + 0.8, () => CY - 4);
      sideburns(CY);
      break;
    case 'part':
      cap(R + 1.1, (px) => CY - 4.6 + Math.max(0, CX - 1 - px) * 0.32);
      sideburns(CY);
      put(l, 12, 6, lo);
      put(l, 12, 7, lo);
      break;
    case 'slick':
      cap(R + 0.6, () => CY - 4.9);
      sideburns(CY - 0.5);
      for (const [x0, y] of [[10, 8], [14, 7], [18, 7]]) for (let x = x0; x < x0 + 3; x++) if (l[at(x, y)]) l[at(x, y)] = hi;
      break;
    case 'messy':
      fill(l, (px, py, x) => skull(px, py, R + 1 + jag(x) * 0.6) && py < CY - 3.6 + (x % 2), h);
      sideburns(CY);
      for (const [x, y] of [
        [13, 4],
        [13, 3],
        [12, 2],
        [19, 4],
        [19, 3],
        [20, 2],
      ])
        put(l, x, y, h);
      break;
    case 'buzz': {
      const b = rgba(shade(hairHex, 0.35));
      fill(l, (px, py) => skull(px, py, R + 0.25) && py < CY - 4.6, b);
      break;
    }
    case 'bald':
      break;
    case 'curly':
      fill(l, (px, py, x, y) => skull(px, py, R + 1.4 + ((x + y) % 3 === 0 ? 0.8 : 0)) && py < CY - 3.2 + (x % 3 === 0 ? 1 : 0), h);
      sideburns(CY);
      for (let y = 3; y < 12; y++) for (let x = 6; x < 26; x++) if (l[at(x, y)] && (x + 2 * y) % 5 === 0) l[at(x, y)] = hi;
      break;
    case 'pomp':
      cap(R + 0.7, () => CY - 4.4);
      sideburns(CY);
      fill(l, (px, py) => ((px - 16.5) / 7.5) ** 2 + ((py - 6) / 2.6) ** 2 <= 1 && py > 3, h);
      for (const [x, y] of [
        [12, 5],
        [13, 4],
        [14, 4],
        [15, 4],
        [16, 4],
      ])
        put(l, x, y, hi);
      break;
    case 'receding':
      fill(l, (px, py) => skull(px, py, R + 0.7) && ((Math.abs(dx(px)) > 4.5 && py < CY - 1.5) || py < 6.4), h);
      sideburns(CY - 0.5);
      break;
    case 'long':
      cap(R + 1.2, () => CY - 4.3);
      fill(l, (px, py) => Math.abs(dx(px)) <= R + 2 && py >= CY - 4.3 && py < CY + 9 && !headTest('round')(px, py) && !(py > CY + 7 && Math.abs(dx(px)) < R), h);
      break;
    case 'bob':
      cap(R + 1.5, () => CY - 3.1);
      fill(l, (px, py) => Math.abs(dx(px)) <= R + 1.8 && py >= CY - 3.1 && py < CY + 5 && (Math.abs(dx(px)) > R - 1.2 || !headTest('round')(px, py)), h);
      break;
    case 'bun':
      cap(R + 0.6, () => CY - 4.7);
      sideburns(CY - 1);
      outline(l);
      fill(l, (px, py) => ((px - 16) / 2.8) ** 2 + ((py - 2.6) / 2) ** 2 <= 1, h);
      put(l, 15, 2, hi);
      break;
    case 'afro':
      fill(l, (px, py) => (px - 16) ** 2 + (py - 12.4) ** 2 <= 12.2 ** 2 && py < CY + 3.5 && !(skull(px, py) && py >= CY - 3.4), h);
      for (let y = 1; y < 18; y++) for (let x = 3; x < 29; x++) if (l[at(x, y)] && (x * 3 + y * 5) % 7 === 0) l[at(x, y)] = hi;
      break;
    case 'visor': {
      cap(R + 0.7, () => CY - 4.2);
      sideburns(CY);
      outline(l);
      const g = rgba('#3f8f5a');
      const gh = rgba('#7cc08f');
      fill(l, (px, py) => skull(px, py, R + 0.8) && py > 8 && py < 10, g);
      fill(l, (px, py) => Math.abs(dx(px)) < 10.5 - (py - 10) * 1.2 && py > 10 && py < 12, gh);
      outline(l, [7, 13]);
      return l;
    }
    case 'bowler': {
      const k = rgba('#2a2a2f');
      const kb = rgba('#7a2b2e');
      sideburns(CY);
      fill(l, (px, py) => ((px - 16) / 7) ** 2 + ((py - 7.6) / 4.8) ** 2 <= 1 && py < 10, k);
      fill(l, (px, py) => py > 8 && py < 9 && Math.abs(dx(px)) < 7.2, kb);
      fill(l, (px, py) => py > 10 && py < 11 && Math.abs(dx(px)) < 11, k);
      fill(l, (px, py) => py > 9 && py < 10 && Math.abs(dx(px)) < 7.2, k);
      break;
    }
    case 'beanie': {
      const b = rgba('#c8643b');
      const bf = rgba('#a64e2c');
      sideburns(CY);
      fill(l, (px, py) => skull(px, py, R + 1.1) && py < 10, b);
      fill(l, (px, py) => skull(px, py, R + 1.4) && py > 8 && py < 11, bf);
      for (let x = 9; x <= 22; x += 2) for (let y = 4; y < 8; y++) if (l[at(x, y)]) l[at(x, y)] = bf;
      break;
    }
  }
  outline(l);
  return l;
}

export function outfitLayer(o: OutfitSpec): Layer {
  const l = blank();
  const body = rgba(o.body);
  const dark = rgba(shade(o.body, -0.22));
  const light = rgba(shade(o.body, 0.28));
  const torso = (px: number, py: number) => py >= 24.6 && (dx(px) / 12) ** 2 + ((py - 33.5) / 9) ** 2 <= 1;
  fill(l, torso, body);

  const vee = (px: number, py: number) => py > 24.6 && Math.abs(dx(px)) <= 3 - (py - 25) * 0.7;
  const shirt = o.shirt ? rgba(o.shirt) : 0;
  const tie = o.tie ? rgba(o.tie) : 0;
  const tieDark = o.tie ? rgba(shade(o.tie, -0.25)) : 0;

  const tieDown = (to: number) => {
    if (!tie) return;
    if (o.bow) {
      for (const x of [14, 15, 16, 17]) put(l, x, 25, x === 15 || x === 16 ? tieDark : tie);
      return;
    }
    put(l, 15, 25, tieDark);
    put(l, 16, 25, tieDark);
    for (let y = 26; y <= to; y++) {
      put(l, 15, y, tie);
      put(l, 16, y, tie);
    }
  };

  switch (o.kind) {
    case 'suit':
    case 'pinstripe':
    case 'tweed':
    case 'double':
    case 'jacket': {
      if (o.kind === 'pinstripe') fill(l, (px, py, x) => torso(px, py) && x % 3 === 1, light);
      if (o.kind === 'tweed') fill(l, (px, py, x, y) => torso(px, py) && (x + y) % 4 === 0, dark);
      fill(l, vee, shirt);
      // Lapels: a darker edge along the opening.
      fill(l, (px, py) => torso(px, py) && !vee(px, py) && py < 30 && Math.abs(dx(px)) <= 4 - (py - 25) * 0.7, dark);
      tieDown(28);
      if (o.kind === 'double') for (const [x, y] of [[13, 29], [18, 29], [13, 31], [18, 31]]) put(l, x, y, GOLD);
      else if (o.kind !== 'jacket') put(l, 16, 30, dark);
      if (o.kind === 'jacket') {
        // Exchange badge on the chest.
        for (const [x, y] of [[21, 28], [22, 28], [21, 29], [22, 29]]) put(l, x, y, WHITE);
        put(l, 22, 29, INK);
      }
      break;
    }
    case 'braces': {
      const trim = rgba(o.trim ?? '#9b2f33');
      fill(l, (px, py, x) => torso(px, py) && (x === 11 || x === 20), trim);
      tieDown(31);
      put(l, 14, 25, rgba(shade(o.body, -0.12)));
      put(l, 17, 25, rgba(shade(o.body, -0.12)));
      break;
    }
    case 'vest': {
      const sleeve = shirt;
      fill(l, (px, py) => torso(px, py) && Math.abs(dx(px)) > 7.5, sleeve);
      fill(l, (px, py) => py > 24.6 && Math.abs(dx(px)) <= 2.2 - (py - 25) * 0.6, sleeve);
      fill(l, (px, py) => torso(px, py) && Math.abs(dx(px)) <= 7.5 && Math.abs(dx(px)) > 7.5 - 1 && py > 26, dark);
      break;
    }
    case 'turtleneck':
      fill(l, (px, py) => Math.abs(dx(px)) <= 3.2 && py > 22.6 && py < 26, dark);
      fill(l, (px, py) => Math.abs(dx(px)) <= 3.2 && py > 23.6 && py < 24.4, body);
      break;
    case 'hoodie': {
      fill(l, (px, py) => py > 23.6 && py < 27 && Math.abs(dx(px)) <= 5.2 && !(Math.abs(dx(px)) <= 2.2 && py < 26), dark);
      for (const x of [14, 17]) for (let y = 26; y <= 28; y++) put(l, x, y, WHITE);
      break;
    }
  }
  outline(l, [22, GRID - 1]);
  return l;
}

export function accessoryLayer(a: AccessoryId, metal: 'ink' | 'gold' = 'ink'): Layer {
  const l = blank();
  const p = (x: number, y: number, c: number) => put(l, x, y, c);
  const frame = metal === 'gold' ? GOLD : INK;
  switch (a) {
    case 'glasses':
      for (const x0 of [10, 18]) {
        for (let x = x0; x <= x0 + 3; x++) {
          p(x, EYE_Y - 1, frame);
          p(x, EYE_Y + 2, frame);
        }
        for (let y = EYE_Y - 1; y <= EYE_Y + 2; y++) {
          p(x0, y, frame);
          p(x0 + 3, y, frame);
        }
      }
      for (const x of [14, 15, 16, 17, 7, 8, 9, 22, 23, 24]) p(x, EYE_Y, frame);
      break;
    case 'shades':
      for (const x0 of [10, 18]) for (let x = x0; x <= x0 + 3; x++) for (let y = EYE_Y - 1; y <= EYE_Y + 1; y++) p(x, y, INK);
      for (const x of [14, 15, 16, 17, 7, 8, 9, 22, 23, 24]) p(x, EYE_Y - 1, INK);
      p(11, EYE_Y - 1, rgba('#6b7a8f'));
      p(19, EYE_Y - 1, rgba('#6b7a8f'));
      break;
    case 'cigar': {
      const c = rgba('#6b4426');
      for (let x = 18; x <= 23; x++) {
        p(x, MOUTH_Y, c);
        p(x, MOUTH_Y - 1, INK);
        p(x, MOUTH_Y + 1, INK);
      }
      p(24, MOUTH_Y, rgba('#e2683a'));
      p(24, MOUTH_Y - 1, INK);
      p(24, MOUTH_Y + 1, INK);
      p(25, MOUTH_Y, INK);
      const smoke = rgba('#d9d6cf');
      p(26, MOUTH_Y - 2, smoke);
      p(27, MOUTH_Y - 3, smoke);
      p(27, MOUTH_Y - 5, smoke);
      p(28, MOUTH_Y - 6, smoke);
      break;
    }
    case 'pin':
      p(20, 27, GOLD);
      p(21, 27, GOLD_HI);
      p(20, 28, GOLD);
      break;
    case 'pen': {
      const b = rgba('#2f55a4');
      for (const [x, y] of [[23, 11], [24, 12], [25, 13], [26, 14]]) p(x, y, b);
      p(22, 10, INK);
      p(27, 15, rgba('#c9c3b5'));
      break;
    }
    case 'earpiece':
      p(25, 15, INK);
      p(25, 16, INK);
      for (const [x, y] of [[25, 18], [24, 19], [25, 20], [24, 21], [25, 22]]) p(x, y, rgba('#cfcfcf'));
      break;
    case 'chain':
      for (const [x, y] of [[12, 25], [13, 26], [14, 27], [15, 27], [16, 27], [17, 27], [18, 26], [19, 25]]) p(x, y, (x + y) % 2 ? GOLD : GOLD_HI);
      break;
    case 'headset':
      for (let x = 9; x <= 22; x++) p(x, x === 9 || x === 22 ? 6 : 5, INK);
      for (let y = 7; y <= 13; y++) {
        p(7, y, INK);
        p(24, y, INK);
      }
      for (const [x, y] of [[6, 14], [7, 14], [6, 15], [7, 15], [6, 16], [7, 16]]) p(x, y, INK);
      for (const [x, y] of [[8, 17], [9, 18], [10, 19], [11, 19], [12, 19]]) p(x, y, rgba('#3a3a3e'));
      break;
    case 'monocle':
      for (let x = 18; x <= 21; x++) {
        p(x, EYE_Y - 2, GOLD);
        p(x, EYE_Y + 2, GOLD);
      }
      for (let y = EYE_Y - 1; y <= EYE_Y + 1; y++) {
        p(17, y, GOLD);
        p(22, y, GOLD);
      }
      for (const [x, y] of [[22, 17], [23, 18], [23, 19], [22, 20], [23, 21], [23, 22]]) p(x, y, GOLD_HI);
      break;
  }
  return l;
}

/** Later layers cover earlier ones. */
export function compose(layers: Layer[]): Layer {
  const out = blank();
  for (const l of layers) for (let i = 0; i < out.length; i++) if (l[i]) out[i] = l[i];
  return out;
}

// ---------------------------------------------------------------- portraits

export interface Portrait {
  background: string;
  head: HeadId;
  skin: string;
  expression: ExpressionId;
  hair: HairId;
  hairColor: string;
  facial: FacialId;
  outfit: OutfitSpec;
  accessories: { id: AccessoryId; metal?: 'ink' | 'gold' }[];
}

export function portraitLayers(p: Portrait): Layer[] {
  return [
    background(p.background),
    neckLayer(p.skin),
    outfitLayer(p.outfit),
    headLayer(p.head, p.skin),
    facialHairLayer(p.facial, p.hairColor, p.head),
    expressionLayer(p.expression),
    hairLayer(p.hair, p.hairColor),
    ...p.accessories.map((a) => accessoryLayer(a.id, a.metal)),
  ];
}

export const renderPortrait = (p: Portrait): Layer => compose(portraitLayers(p));

// ---------------------------------------------------------------- traders

const STYLE_FROM_LOOK: HairId[] = ['part', 'crop', 'receding', 'slick', 'buzz', 'bald', 'curly', 'pomp', 'bun', 'long', 'bob', 'slick', 'bun', 'afro'];
const FACE_FROM_LOOK: FacialId[] = ['none', 'stubble', 'beard', 'moustache', 'goatee'];
const KIND_FROM_OUTFIT: OutfitKind[] = ['suit', 'pinstripe', 'vest', 'braces', 'suit', 'turtleneck', 'double'];
const MOODS: ExpressionId[] = ['content', 'smug', 'deadpan', 'cocky', 'side', 'grin', 'content', 'worried'];
const TRADER_BGS = BACKGROUNDS.filter((b) => b.id !== 'night');

function hashLook(look: Look): number {
  const s = [look.skin, look.hair, look.hairStyle, look.suit, look.tie, look.build, look.face, look.outfit, look.shirt, look.neck, look.eyes, look.fem ? 1 : 0].join('.');
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
}

/** A floor trader's portrait, from the same look that draws them in the building. */
export function portraitFromLook(look: Look, partner = false): Portrait {
  const h = hashLook(look);
  const kind = KIND_FROM_OUTFIT[(look.outfit ?? 0) % KIND_FROM_OUTFIT.length];
  const neck = look.neck ?? 0;
  const shirts = ['#f6f3ec', '#cfe0f2', '#f2cfd6', '#ddd3ee', '#d8e6f5'];
  const acc: Portrait['accessories'] = [];
  const eyes = partner ? 2 : look.eyes ?? 0;
  if (eyes === 1) acc.push({ id: 'shades' });
  if (eyes === 2) acc.push({ id: 'glasses', metal: partner ? 'gold' : 'ink' });
  if (eyes === 3) acc.push({ id: 'headset' });
  if (eyes === 4) acc.push({ id: 'earpiece' });
  if (look.cigar) acc.push({ id: 'cigar' });
  return {
    background: partner ? '#e2c27c' : TRADER_BGS[h % TRADER_BGS.length].hex,
    head: partner ? 'square' : (['long', 'round', 'wide'] as HeadId[])[look.build ?? 1],
    skin: SKINS[look.skin % SKINS.length],
    expression: partner ? 'smug' : MOODS[(h >>> 8) % MOODS.length],
    hair: STYLE_FROM_LOOK[look.hairStyle % STYLE_FROM_LOOK.length],
    hairColor: HAIRS[look.hair % HAIRS.length],
    facial: look.fem ? 'none' : FACE_FROM_LOOK[look.face ?? 0],
    outfit: {
      kind: kind === 'vest' ? 'vest' : kind,
      body: kind === 'braces' ? shirts[(look.shirt ?? 0) % shirts.length] : kind === 'vest' ? '#5e6672' : kind === 'turtleneck' ? '#232327' : SUITS[look.suit % SUITS.length],
      tie: kind === 'vest' || kind === 'turtleneck' || neck === 3 ? '' : TIES[look.tie % TIES.length],
      shirt: shirts[(look.shirt ?? 0) % shirts.length],
      trim: TIES[look.tie % TIES.length],
      bow: neck === 2,
    },
    accessories: acc,
  };
}
