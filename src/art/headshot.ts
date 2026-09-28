/**
 * 16x16 headshot, used in the header, lists and employee files.
 * Base grid plus a hair overlay per style. In an overlay, '.' keeps the base.
 */

export const HEAD_W = 16;
export const HEAD_H = 16;

const BASE = [
  '................',
  '................',
  '................',
  '.....oooooo.....',
  '....osssssso....',
  '...osssssssso...',
  '...ossessesso...',
  '..oSssssssssSo..',
  '...osssmmssso...',
  '....oSSSSSSo....',
  '.....oSSSSo.....',
  '..ouuuwttwuuuo..',
  '.ouuuuwttwuuuuo.',
  'ouUuuuwttwuuuUuo',
  'ouUuuuuttuuuuUuo',
  'ouUuuuuTTuuuuUuo',
];

const HAIR: string[][] = [
  // side part
  [
    '................',
    '................',
    '.....oooooo.....',
    '....ohhhhhhoo...',
    '...ohhhhHhhhho..',
    '...ohHs..shhho..',
    '...oh........o..',
  ],
  // short crop
  [
    '................',
    '................',
    '................',
    '.....oooooo.....',
    '....ohhhhhho....',
    '...ohhhhhhhho...',
    '...oh......ho...',
  ],
  // receding
  [
    '................',
    '................',
    '................',
    '.....oooooo.....',
    '....os....so....',
    '...oh......ho...',
    '...oh......ho...',
  ],
  // swept back
  [
    '................',
    '................',
    '.....ooooooo....',
    '....ohhhhhhhho..',
    '...ohHhhhhhhhho.',
    '...oHhs....shho.',
    '...oh.......hoo.',
  ],
];

export function headshotGrid(hairStyle: number, glasses = false): string[] {
  const hair = HAIR[hairStyle % HAIR.length];
  const rows = BASE.map((row, y) => {
    const over = hair[y];
    if (!over) return row;
    let out = '';
    for (let x = 0; x < HEAD_W; x++) out += over[x] !== '.' ? over[x] : row[x];
    return out;
  });
  if (glasses) {
    rows[6] = rows[6].slice(0, 4) + 'gegggeg' + rows[6].slice(11);
  }
  return rows;
}
