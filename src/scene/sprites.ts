/**
 * Character sprites as palette-indexed grids. One base body, palette-swapped
 * per trader (skin, hair, suit, tie). Keys:
 *   o outline  s skin  S skin shade  h hair  H hair light  k eyes  m mouth
 *   u suit  U suit shade  v lapel  p trousers  w shirt  W shirt shade  t tie  T tie shade
 *   b shoes  g glasses  x box  X box shade  n tape
 */
import type { Look } from '../sim/types';
import { HAIRS, SKINS, SUITS, TIES, shade } from '../art/palette';
import { rgba } from './buffer';
import { lookKey, renderFigure } from '../art/figure';
import { S } from './layout';

export interface SpriteImage {
  w: number;
  h: number;
  px: Uint32Array;
}

const cache = new Map<string, SpriteImage>();

export const SPR_W = 15;
export const SPR_H = 25;

const pad = (rows: string[]) => rows.map((r) => `.${r}.`);

const HEAD_FRONT = [
  '...ooooooo...',
  '..ohhhhhhho..',
  '..ohhhHHhho..',
  '..ohsssssho..',
  '..osksssksо..',
  '.oSsssssssSo.',
  '..osssmsssо..',
  '...oSSSSSo...',
];
const HEAD_BACK = [
  '...ooooooo...',
  '..ohhhhhhho..',
  '..ohhhHHhho..',
  '..ohhhhhhho..',
  '..ohhhhhhho..',
  '.oShhhhhhhSo.',
  '..ohhhhhhho..',
  '...oSSSSSo...',
];

const HAIR_STYLES: string[][] = [
  // side part
  ['...ooooooo...', '..ohhhhhhho..', '..ohHhhhhho..', '..ohhsssssо..'],
  // short crop
  ['...ooooooo...', '..ohhhhhhho..', '..ohhhhhhho..', '..osssssssо..'],
  // receding
  ['...ooooooo...', '..ohsssssho..', '..ohsssssho..', '..ohsssssho..'],
  // swept back
  ['..oooooooo...', '.ohhhhhhhhо..', '.ohHHhhhhho..', '..ohsssssho..'],
];

const TORSO_FRONT = [
  '....owWwo....',
  '.ouuuwtwuuuo.',
  'ouuuuwtwuuuuo',
  'ouUuuvtvuuUuo',
  'ouUuuuTuuuUuo',
  'ouUuuuTuuuUuo',
  'ouUuuuuuuuUuo',
  'osUuuuuuuuUso',
  '.opppppppppo.',
];
const TORSO_BACK = [
  '....oSSSo....',
  '.ouuuuuuuuuo.',
  'ouuuuuuuuuuuo',
  'ouUuuuuuuuUuo',
  'ouUuuuUuuuUuo',
  'ouUuuuUuuuUuo',
  'ouUuuuUuuuUuo',
  'osUuuuUuuuUso',
  '.opppppppppo.',
];

const LEGS_STAND = ['..opppoppp o..', '..opppopppo..', '..opppopppo..', '..opppopppo..', '..opppopppo..', '..obbbobbbo..', '..obbbobbbo..', '..ooooooooo..'];
const LEGS_STEP = ['..opppopppo..', '..opppopppo..', '..opppopppo..', '..opppopppo..', '..obbbopppo..', '..ooooopppo..', '......obbbo..', '......ooooo..'];

const fix = (rows: string[]) => rows.map((r) => r.replace(/[о]/g, 'o').replace(/ /g, ''));

function withHair(head: string[], style: number): string[] {
  const hair = fix(HAIR_STYLES[style % HAIR_STYLES.length]);
  return fix(head).map((row, i) => (hair[i] ? hair[i] : row));
}

function mirror(rows: string[]): string[] {
  return rows.map((r) => r.split('').reverse().join(''));
}

export type { Pose } from '../art/figure';
import type { Pose } from '../art/figure';

let overrides: Map<Pose, string[][]> | null = null;

/** Replace procedural grids with frames loaded from custom sprite sheets. */
export function setSpriteOverrides(m: Map<Pose, string[][]>) {
  overrides = m;
  cache.clear();
}

/** Build the grid for a pose and frame. All grids are SPR_W wide; heights vary (seated poses are shorter). */
export function poseGrid(pose: Pose, frame: number, hairStyle: number, glasses: boolean): string[] {
  const o = overrides?.get(pose);
  if (o && o.length) return o[frame % o.length];
  const headF = withHair(HEAD_FRONT, hairStyle);
  if (glasses) headF[4] = '..ogkgggkgo..';
  const headB = fix(HEAD_BACK);
  const torsoF = fix(TORSO_FRONT);
  const torsoB = fix(TORSO_BACK);
  const stand = fix(LEGS_STAND);
  const step = fix(LEGS_STEP);
  const legsFor = (f: number) => (f % 2 === 0 ? stand : f === 1 ? step : mirror(step));

  switch (pose) {
    case 'stand':
      return pad([...headF, ...torsoF, ...stand]);
    case 'walk':
      return pad([...headF, ...torsoF, ...legsFor(frame % 4)]);
    case 'back':
      return pad([...headB, ...torsoB, ...legsFor(frame % 4)]);
    case 'box':
    case 'backbox': {
      const g = pad([...(pose === 'box' ? headF : headB), ...(pose === 'box' ? torsoF : torsoB), ...legsFor(frame % 4)]).map((r) => r.split(''));
      // A cardboard box held in front, rows 13–18.
      for (let y = 13; y <= 18; y++)
        for (let x = 2; x <= 12; x++) g[y][x] = y === 13 ? 'X' : x === 2 || x === 12 ? 'o' : y === 18 ? 'o' : x === 7 && y < 16 ? 'n' : x > 9 ? 'X' : 'x';
      g[14][1] = 's';
      g[14][13] = 's';
      if (pose === 'backbox') for (let y = 13; y <= 18; y++) for (let x = 3; x <= 11; x++) if (g[y][x] === 'x' || g[y][x] === 'n') g[y][x] = 'u';
      return g.map((r) => r.join(''));
    }
    case 'sit': {
      // Typing: hands move on the keyboard. Frame 2 is a pause.
      const t = torsoF.slice(0, 7).map((r) => r.split(''));
      const hands = frame % 3;
      t[6] = 'ouUuuuuuuuUuo'.split('');
      if (hands === 0) {
        t[6][3] = 's';
        t[5][9] = 's';
      } else if (hands === 1) {
        t[5][3] = 's';
        t[6][9] = 's';
      } else {
        t[6][3] = 's';
        t[6][9] = 's';
      }
      const lap = ['.opppppppppo.', '.opppppppppo.', '.opppppppppo.', '..ooooooooo..'];
      return pad([...headF, ...t.map((r) => r.join('')), ...lap]);
    }
    case 'celebrate': {
      const g = pad([...headF, ...torsoF, ...stand]).map((r) => r.split(''));
      const lift = frame % 2;
      // Remove the arms at the sides and raise them.
      for (let y = 10; y <= 15; y++) {
        g[y][2] = y === 15 ? 'o' : 'o';
        g[y][12] = 'o';
        g[y][1] = '.';
        g[y][13] = '.';
      }
      g[10][2] = 'u';
      g[10][12] = 'u';
      for (let y = 3 - lift; y <= 9; y++) {
        g[y][1] = 'u';
        g[y][13] = 'u';
        g[y][0] = 'o';
        g[y][14] = 'o';
      }
      g[2 - lift][1] = 's';
      g[2 - lift][13] = 's';
      g[1 - lift][1] = 'o';
      g[1 - lift][13] = 'o';
      // A grin.
      g[6][6] = 'm';
      g[6][8] = 'm';
      return g.map((r) => r.join(''));
    }
    case 'slump': {
      const rows = [
        '.............',
        '.............',
        '.............',
        '.............',
        '.............',
        '.............',
        '.............',
        '...ooooooo...',
        '..ohhhhhhho..',
        '..ohhhHHhho..',
        '.oohhhhhhhoo.',
        'ouuohhhhhouuo',
        'ouuuusssuuuuo',
        'oUUUUUUUUUUUo',
        '.ouUuuuuuUuo.',
        '.opppppppppo.',
        '.opppppppppo.',
        '..ooooooooo..',
      ];
      if (frame % 2) rows.unshift('.............'), rows.pop();
      return pad(fix(rows));
    }
    default:
      return pad([...headF, ...torsoF, ...stand]);
  }
}


function paletteFor(look: Look): Record<string, number> {
  const skin = SKINS[look.skin % SKINS.length];
  const hair = HAIRS[look.hair % HAIRS.length];
  const suit = SUITS[look.suit % SUITS.length];
  const tie = TIES[look.tie % TIES.length];
  return {
    o: rgba('#22201c'),
    s: rgba(skin),
    S: rgba(shade(skin, -0.16)),
    h: rgba(hair),
    H: rgba(shade(hair, hair === HAIRS[5] ? -0.12 : 0.3)),
    k: rgba('#1d1c19'),
    m: rgba(shade(skin, -0.34)),
    u: rgba(suit),
    U: rgba(shade(suit, -0.25)),
    v: rgba(shade(suit, 0.25)),
    p: rgba(shade(suit, -0.38)),
    w: rgba('#f4f1e8'),
    W: rgba('#d6d1c3'),
    t: rgba(tie),
    T: rgba(shade(tie, -0.25)),
    b: rgba('#1f1c1a'),
    g: rgba('#c9a24a'),
    x: rgba('#c79a62'),
    X: rgba('#a67c48'),
    n: rgba('#e9d9a6'),
  };
}


export function sprite(look: Look, pose: Pose, frame: number, glasses = false): SpriteImage {
  const key = `${lookKey(look)}|${pose}|${frame}|${glasses ? 1 : 0}`;
  const hit = cache.get(key);
  if (hit) return hit;
  let img: SpriteImage;
  if (overrides?.get(pose)?.length) {
    // Hand-drawn sheets, palette-swapped from their key colours.
    const grid = poseGrid(pose, frame, look.hairStyle, glasses);
    const pal = paletteFor(look);
    const w = grid[0].length;
    const h = grid.length;
    const px = new Uint32Array(w * h);
    for (let y = 0; y < h; y++)
      for (let x = 0; x < w; x++) {
        const c = pal[grid[y][x]];
        if (c) px[y * w + x] = c;
      }
    img = { w, h, px };
  } else img = renderFigure(look, pose, frame, { glasses, scale: S / 2 });
  if (cache.size > 800) cache.clear();
  cache.set(key, img);
  return img;
}
