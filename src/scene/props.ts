/**
 * Small screen-space pixel sprites for props that are awkward as boxes.
 * Keys map through PROP_PAL. '.' is transparent.
 */
import { C } from './colors';
import type { PixelBuffer } from './buffer';

export const PROP_PAL: Record<string, number> = {
  o: C.ink,
  g: C.leaf,
  G: C.leafHi,
  d: C.leafLo,
  p: C.pot,
  P: C.potLo,
  b: C.brass,
  B: C.brassHi,
  n: C.brassLo,
  w: C.white,
  c: C.cat,
  C: C.catLo,
  s: C.slate,
  S: C.slateHi,
  L: C.slateLo,
  t: C.waterTank,
  T: C.waterTankHi,
  k: C.waterTankLo,
  r: C.red,
  R: C.redHi,
  i: C.iron,
  I: C.ironHi,
  v: C.navy,
  e: C.steel,
  E: C.steelHi,
  q: C.steelLo,
  y: C.amber,
  a: C.water,
  A: C.waterHi,
  x: C.paper,
  f: rgba2('#e7a1b0'),
  F: rgba2('#f2d36b'),
  m: rgba2('#8a8f99'),
  M: rgba2('#b5b9c0'),
  h: C.wainscot,
  H: C.wainscotHi,
  j: C.woodDark,
};

function rgba2(hex: string) {
  const n = parseInt(hex.slice(1), 16);
  return ((255 << 24) | ((n & 255) << 16) | (((n >> 8) & 255) << 8) | ((n >> 16) & 255)) >>> 0;
}

export function stamp(buf: PixelBuffer, grid: string[], x: number, y: number, flip = false, pal = PROP_PAL) {
  const w = grid[0].length;
  for (let j = 0; j < grid.length; j++)
    for (let i = 0; i < w; i++) {
      const k = grid[j][i];
      if (k === '.') continue;
      const c = pal[k];
      if (c !== undefined) buf.set(x + (flip ? w - 1 - i : i), y + j, c);
    }
}

/** Anchor at bottom centre. */
export function stampAt(buf: PixelBuffer, grid: string[], sx: number, sy: number, flip = false) {
  stamp(buf, grid, Math.round(sx - grid[0].length / 2), Math.round(sy - grid.length), flip);
}

export const PALM = [
  '..g.G...d..',
  '.gGg.gG.dg.',
  'gG.dgGgd.Gg',
  'g..gdGgd..g',
  '..g.dgd.g..',
  '.d..gdg..d.',
  '....dgd....',
  '.....d.....',
  '.....d.....',
  '....d......',
  '...pppp....',
  '...pPPp....',
  '...pPPp....',
  '....pp.....',
];

export const FERN = [
  '.G.g.G.',
  'gGdgGdg',
  '.gdGdg.',
  'g.dgd.g',
  '.ppppp.',
  '.pPPPp.',
  '..ppp..',
];

export const SUCCULENT = ['.G.G.', 'GgdgG', '.gdg.', '.ppp.', '.pPp.'];

export const CAT_SIT = [
  'c...c..',
  'cc.cc..',
  'cocoC..',
  'ccccC..',
  '.cccC..',
  '.ccccC.',
  '.CcccC.',
];
export const CAT_TAIL = [
  ['.....cC', '.....C.', '......'],
  ['......C', '.....cC', '......'],
];

export const GLOBE = [
  '..aaa..',
  '.agaAa.',
  'aggaaAa',
  'aaggaga',
  'aagaaga',
  '.aaggn.',
  '..aan..',
  '...n...',
  '..nnn..',
];

export const SHRUB = ['..GgG..', '.GggdG.', 'GgdgGgd', 'gdgGgdg', '.dgdgd.'];

export const FLOWERS = ['f.F.f', 'g.g.g', '.g.g.'];

export const FLAG = [
  'nrRRRR',
  'nrrrRR',
  'nwwwww',
  'nvvvvv',
  'n.....',
];

export const PIGEON = ['.mm.', 'mMmo', '.mm.', '..q.'];

export const WATER_TOWER = [
  '....sSs....',
  '...sSSss...',
  '..sSSsssL..',
  '.sSSssssLL.',
  'sSSsssssLLL',
  'tTTtttttkkk',
  'tTttttttkkk',
  'kkkkkkkkkkk',
  'tTttttttkkk',
  'tTttttttkkk',
  'tTttttttkkk',
  'kkkkkkkkkkk',
  'tTttttttkkk',
  'tTttttttkkk',
  'tTttttttkkk',
  '.i.......i.',
  '.i..i.i..i.',
  '.ii.i.i.ii.',
  '.i.i...i.i.',
  '.i.......i.',
  '.i.......i.',
];

export const LAMP_HEAD = ['.iii.', 'iyyyi', 'iyByi', 'iyyyi', '.iii.', '..i..'];

export const CAMERA = ['..qq...', 'qqqqqqi', 'qMqqeqi', 'qqqqqqi', '...q...', '..q.q..', '.q...q.', 'q.....q'];

export const PORTRAIT = [
  'nnnnnnnnnnnn',
  'nhhhhhhhhhhn',
  'nhhMMMMMhhhn',
  'nhMMMMMMMhhn',
  'nhMwwwwwMhhn',
  'nhbobbobhhhn',
  'nhwwwwwwhhhn',
  'nhhwwmwwhhhn',
  'nhhhwwwhhhhn',
  'nhvvvbvvvhhn',
  'nvvvvbvvvvhn',
  'nvvvvbvvvvvn',
  'nnnnnnnnnnnn',
];
