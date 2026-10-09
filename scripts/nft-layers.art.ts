/**
 * Investors NFT trait layers. `npm run art -- nft-layers`
 *
 * Every layer is drawn by the same renderer as the site's traders
 * (src/art/figure.ts), one part at a time, then given the retro filter:
 * the bust is drawn at 80×80 hard pixels and scaled up 15× with
 * nearest-neighbour, so every layer is 1200×1200 and lines up exactly.
 *
 * Output: nft/layers/<NN-trait>/<option>.png, plus nft/preview.png.
 * Stack the folders in number order; see nft/README.md.
 */
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { it } from 'vitest';
import { PixelBuffer, rgba } from '../src/scene/buffer';
import { encodePng } from '../src/scene/png';
import { renderFigure, type FigureOpts, type SpriteImage } from '../src/art/figure';
import { HAIRS, HAIR_NAMES, HAIR_STYLE_NAMES, SKINS, shade } from '../src/art/palette';
import type { Look } from '../src/sim/types';

const G = 80;
const UP = 15;
const UNITS = 37;
const OUT = 'nft';

const BASE: Look = { skin: 1, hair: 0, hairStyle: 0, suit: 0, tie: 0, build: 1, height: 1, face: 0, outfit: 0, shirt: 0, neck: 0, eyes: 0, watch: false, cigar: false, fem: false };

/** One part of the bust, cropped to the shared frame, as hard pixels. */
function part(look: Partial<Look>, only: string[], extra: FigureOpts = {}): SpriteImage {
  const s = G / UNITS;
  const full = renderFigure({ ...BASE, ...look }, 'stand', 0, { ...extra, scale: s, ss: 1, only, noOutline: extra.noOutline });
  const x0 = Math.round(full.w / 2 - G / 2);
  const y0 = Math.round(full.h - 1 - 0.5 * s - (38.2 + 23.2) * s);
  const px = new Uint32Array(G * G);
  for (let y = 0; y < G; y++)
    for (let x = 0; x < G; x++) {
      const sx = x0 + x;
      const sy = y0 + y;
      if (sx < 0 || sy < 0 || sx >= full.w || sy >= full.h) continue;
      px[y * G + x] = full.px[sy * full.w + sx];
    }
  return { w: G, h: G, px };
}

const empty = (img: SpriteImage) => !img.px.some((c) => c >>> 24);

function save(dir: string, name: string, img: SpriteImage) {
  if (empty(img)) return false;
  mkdirSync(`${OUT}/layers/${dir}`, { recursive: true });
  const buf = new PixelBuffer(G, G);
  buf.data.set(img.px);
  writeFileSync(`${OUT}/layers/${dir}/${name}.png`, encodePng(buf, UP, 0));
  return true;
}

const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

// ---------------------------------------------------------------- traits

export const BACKGROUNDS: [string, string][] = [
  ['brass', '#e2c27c'],
  ['paper', '#ece5d3'],
  ['ledger-green', '#b6caae'],
  ['pink-paper', '#efcbb2'],
  ['brick', '#d39a86'],
  ['lilac', '#cbbfdc'],
  ['mint', '#c3e0cf'],
  ['after-hours', '#2b3245'],
];

const EXPRESSIONS: [string, FigureOpts['face']][] = [
  ['neutral', { mouth: 'line', brow: 'flat' }],
  ['smirk', { mouth: 'smirk', brow: 'cocky' }],
  ['grin', { mouth: 'grin', brow: 'flat' }],
  ['delighted', { mouth: 'grin', brow: 'up' }],
  ['frown', { mouth: 'frown', brow: 'down' }],
  ['talking', { mouth: 'talk', brow: 'flat' }],
  ['shouting', { mouth: 'shout', brow: 'down' }],
  ['surprised', { mouth: 'sip', brow: 'up' }],
];

/** Outfit presets: [name, outfit, suit, shirt, tie, neck]. Open collars are left out so no outfit needs skin. */
const OUTFITS: [string, number, number, number, number, number][] = [
  ['navy-suit', 0, 0, 0, 0, 0],
  ['charcoal-suit', 0, 1, 1, 1, 0],
  ['navy-pinstripe', 1, 0, 0, 3, 0],
  ['charcoal-pinstripe', 1, 1, 2, 5, 0],
  ['flannel-grey-suit', 0, 2, 3, 2, 0],
  ['tobacco-suit', 0, 3, 4, 1, 0],
  ['black-suit', 0, 4, 0, 5, 0],
  ['olive-suit', 0, 5, 0, 4, 0],
  ['navy-double-breasted', 6, 0, 1, 1, 0],
  ['black-double-breasted', 6, 4, 0, 0, 0],
  ['black-tie', 0, 4, 0, 5, 2],
  ['braces-pale-blue', 3, 0, 1, 0, 0],
  ['braces-pink', 3, 0, 2, 3, 0],
  ['grey-waistcoat', 4, 2, 0, 0, 0],
  ['turtleneck-and-blazer', 5, 1, 0, 0, 0],
  ['visitor-lanyard', 0, 2, 0, 3, 4],
];

const FACIAL = ['', 'stubble', 'beard', 'moustache', 'goatee'];
const EYEWEAR: [string, Partial<Look>, boolean][] = [
  ['sunglasses', { eyes: 1 }, false],
  ['glasses', { eyes: 2 }, false],
  ['gold-glasses', { eyes: 2 }, true],
  ['headset', { eyes: 3 }, false],
  ['earpiece', { eyes: 4 }, false],
];

/** A flat colour with a dithered shadow toward the bottom (4×4 Bayer). */
function backgroundLayer(hex: string): SpriteImage {
  const bayer = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
  const base = rgba(hex);
  const dark = rgba(shade(hex, -0.08));
  const px = new Uint32Array(G * G);
  for (let y = 0; y < G; y++)
    for (let x = 0; x < G; x++) {
      const t = Math.max(0, (y / G - 0.45) / 0.55);
      px[y * G + x] = t * 16 > bayer[(y % 4) * 4 + (x % 4)] + 0.5 ? dark : base;
    }
  return { w: G, h: G, px };
}

/**
 * Stubble is a tint over the skin, so on its own layer it would be empty.
 * Export the tinted area as hair colour at the same strength instead.
 */
function stubble(hc: number): SpriteImage {
  const look = { face: 1, hair: hc };
  const bare = part(look, ['head'], { noOutline: true });
  const tinted = part(look, ['head', 'facial'], { noOutline: true });
  const light = hc === 4 || hc === 5;
  const colour = rgba(shade(HAIRS[hc], light ? -0.18 : -0.24), Math.round(0.32 * 255));
  const px = new Uint32Array(G * G);
  for (let i = 0; i < px.length; i++) if (tinted.px[i] !== bare.px[i]) px[i] = colour;
  return { w: G, h: G, px };
}

// ---------------------------------------------------------------- building backgrounds

type Put = (x: number, y: number, w: number, h: number, hex: string) => void;

function scene(draw: (r: Put, px: Uint32Array) => void): SpriteImage {
  const px = new Uint32Array(G * G);
  const r: Put = (x, y, w, h, hex) => {
    const c = rgba(hex);
    for (let j = Math.max(0, y); j < Math.min(G, y + h); j++) for (let i = Math.max(0, x); i < Math.min(G, x + w); i++) px[j * G + i] = c;
  };
  draw(r, px);
  return { w: G, h: G, px };
}

/** Backgrounds taken from rooms in the building. Names start with the room. */
const SCENES: [string, (r: Put, px: Uint32Array) => void][] = [
  [
    'trading-floor',
    (r) => {
      r(0, 0, G, G, '#e9e2cf');
      r(0, 44, G, 2, '#c9bfa6');
      for (let x = 2; x < G; x += 19) {
        r(x, 18, 16, 12, '#22262c');
        r(x + 1, 19, 14, 10, '#17331f');
        for (let k = 0; k < 4; k++) r(x + 2 + k * 3, 26 - ((x + k * 5) % 6), 2, 1, k % 2 ? '#d0574a' : '#5fcf7a');
        r(x + 7, 30, 2, 3, '#22262c');
      }
      r(0, 33, G, 4, '#6b4a33');
      r(0, 37, G, 1, '#4e3424');
    },
  ],
  [
    'corner-office',
    (r) => {
      r(0, 0, G, G, '#3d2c22');
      r(8, 6, 64, 50, '#9cc3dc');
      const towers = [[10, 30, 8], [19, 22, 7], [27, 34, 9], [37, 18, 8], [46, 28, 10], [57, 24, 7], [64, 32, 8]];
      for (const [x, y, w] of towers) {
        r(x, y, w, 56 - y, '#5e7286');
        for (let j = y + 2; j < 54; j += 3) for (let i = x + 1; i < x + w - 1; i += 2) r(i, j, 1, 1, '#d9e6ee');
      }
      for (let y = 8; y < 56; y += 4) r(8, y, 64, 1, '#c7dbe8');
      r(8, 6, 64, 2, '#2a1e17');
      r(39, 6, 2, 50, '#2a1e17');
      r(0, 56, G, G - 56, '#6b4a33');
    },
  ],
  [
    'lobby',
    (r) => {
      r(0, 0, G, G, '#efe8d6');
      r(0, 8, G, 3, '#8b2f30');
      r(22, 13, 36, 9, '#2a2a2f');
      for (let i = 0; i < 8; i++) r(25 + i * 4, 16, 2, 3, '#d4a640');
      for (let y = 48; y < G; y += 4) for (let x = 0; x < G; x += 4) r(x, y, 4, 4, ((x + y) / 4) % 2 ? '#2f2f33' : '#e6e1d6');
      r(0, 46, G, 2, '#b88a38');
    },
  ],
  [
    'ticker-wall',
    (r) => {
      r(0, 0, G, G, '#16181c');
      for (let row = 0; row < 7; row++) {
        const y = 6 + row * 10;
        for (let x = (row * 7) % 5; x < G; x += 5) {
          const up = (x * 7 + row * 13) % 3 !== 0;
          r(x, y, 3, 1, up ? '#5fcf7a' : '#d0574a');
          r(x, y + 2, 2, 1, '#7b8590');
        }
      }
    },
  ],
  [
    'server-room',
    (r) => {
      r(0, 0, G, G, '#232a33');
      for (let x = 2; x < G; x += 15) {
        r(x, 4, 12, 60, '#3a4552');
        for (let y = 7; y < 62; y += 4) {
          r(x + 1, y, 10, 3, '#151a20');
          r(x + 2, y + 1, 1, 1, (x + y) % 3 ? '#5fcf7a' : '#e2a33c');
        }
      }
      r(0, 64, G, G - 64, '#1a1f26');
    },
  ],
  [
    'elevator',
    (r) => {
      r(0, 0, G, G, '#e2dac6');
      r(14, 4, 52, G, '#a77e3a');
      r(16, 6, 23, G, '#d4a640');
      r(41, 6, 23, G, '#d4a640');
      r(39, 6, 2, G, '#6e5224');
      for (const x of [20, 45]) r(x, 6, 2, G, '#e8c66e');
      r(34, 0, 12, 3, '#2a2a2f');
      r(38, 1, 4, 1, '#e2683a');
    },
  ],
];

/** Lips and mouth lines become see-through dark, so one expression suits every skin. */
function adaptMouth(img: SpriteImage, skinHex: string) {
  const lips = rgba(shade(skinHex, -0.22));
  const mouth = rgba(shade(skinHex, -0.4));
  for (let i = 0; i < img.px.length; i++) {
    if (img.px[i] === lips) img.px[i] = rgba('#4a2416', 140);
    else if (img.px[i] === mouth) img.px[i] = rgba('#3a1a12', 215);
  }
}

// ---------------------------------------------------------------- export

it('nft layers', () => {
  rmSync(`${OUT}/layers`, { recursive: true, force: true });
  const counts: Record<string, number> = {};
  const bank: Record<string, Record<string, SpriteImage>> = {};
  const add = (dir: string, name: string, img: SpriteImage) => {
    if (!save(dir, name, img)) return;
    counts[dir] = (counts[dir] ?? 0) + 1;
    (bank[dir] ??= {})[name] = img;
  };

  for (const [name, hex] of BACKGROUNDS) add('01-background', name, backgroundLayer(hex));
  for (const [name, draw] of SCENES) add('01-background', name, scene(draw));

  HAIRS.forEach((_, hc) =>
    HAIR_STYLE_NAMES.forEach((style, hs) => {
      const look = { hair: hc, hairStyle: hs };
      const n = `${slug(style)}-${slug(HAIR_NAMES[hc])}`;
      add('02-hair-back', n, part(look, ['hairBack']));
      add('08-hair', n, part(look, ['hair']));
    }),
  );

  SKINS.forEach((_, sk) => {
    const n = `skin-${sk + 1}`;
    add('03-neck', n, part({ skin: sk }, ['neck']));
    add('05-head', n, part({ skin: sk }, ['head']));
  });

  for (const [name, outfit, suit, shirt, tie, neck] of OUTFITS) {
    const look = { outfit, suit, shirt, tie, neck };
    const collar = part(look, ['collar'], { noOutline: true });
    if (!empty(collar)) throw new Error(`${name} shows skin at the collar; pick another neck`);
    add('04-outfit', name, part(look, ['body']));
  }

  HAIRS.forEach((_, hc) =>
    FACIAL.forEach((f, face) => {
      if (face === 1) add('06-facial-hair', `${f}-${slug(HAIR_NAMES[hc])}`, stubble(hc));
      else if (face) add('06-facial-hair', `${f}-${slug(HAIR_NAMES[hc])}`, part({ face, hair: hc }, ['facial']));
    }),
  );

  for (const [name, face] of EXPRESSIONS) {
    const img = part({ skin: 2 }, ['expression'], { face, noOutline: true });
    adaptMouth(img, SKINS[2]);
    add('07-expression', name, img);
  }

  for (const [name, look, gold] of EYEWEAR) add('09-eyewear', name, part(look, ['eyewear'], { glasses: gold, noOutline: name !== 'headset' }));
  add('10-accessory', 'cigar', part({ cigar: true }, ['cigar']));

  writeFileSync(`${OUT}/layers/counts.json`, JSON.stringify(counts, null, 2) + '\n');
  preview(bank);
  catalog(bank);
});

/** Alpha-blend `top` over `under`, in place. */
function over(under: Uint32Array, top: Uint32Array) {
  for (let i = 0; i < under.length; i++) {
    const c = top[i];
    const a = (c >>> 24) / 255;
    if (!a) continue;
    if (a >= 1) {
      under[i] = c;
      continue;
    }
    const u = under[i];
    const ch = (v: number, sh: number) => Math.round(((v >>> sh) & 255) * a + ((u >>> sh) & 255) * (1 - a));
    under[i] = ((255 << 24) | (ch(c, 16) << 16) | (ch(c, 8) << 8) | ch(c, 0)) >>> 0;
  }
}

/** Twelve random Investors stacked from the layers, the way a generator would. */
function preview(bank: Record<string, Record<string, SpriteImage>>) {
  let seed = 7;
  const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) / 2 ** 32);
  const pick = (dir: string) => {
    const keys = Object.keys(bank[dir]);
    return keys[Math.floor(rnd() * keys.length)];
  };
  const cell = 300;
  const cols = 6;
  const rows = 2;
  const W = cols * cell;
  const buf = new PixelBuffer(W, rows * cell);
  for (let n = 0; n < cols * rows; n++) {
    const hairName = pick('08-hair');
    const colour = HAIR_NAMES.map(slug).find((c) => hairName.endsWith(`-${c}`))!;
    const skin = pick('05-head');
    const stack: (SpriteImage | undefined)[] = [
      bank['01-background'][pick('01-background')],
      bank['02-hair-back']?.[hairName],
      bank['03-neck'][skin],
      bank['04-outfit'][pick('04-outfit')],
      bank['05-head'][skin],
      rnd() < 0.3 ? bank['06-facial-hair'][`${FACIAL[1 + Math.floor(rnd() * 4)]}-${colour}`] : undefined,
      bank['07-expression'][pick('07-expression')],
      bank['08-hair'][hairName],
      rnd() < 0.35 ? bank['09-eyewear'][pick('09-eyewear')] : undefined,
      rnd() < 0.08 ? bank['10-accessory'].cigar : undefined,
    ];
    const px = new Uint32Array(G * G);
    for (const l of stack) if (l) over(px, l.px);
    const x0 = (n % cols) * cell;
    const y0 = Math.floor(n / cols) * cell;
    for (let y = 0; y < cell; y++) for (let x = 0; x < cell; x++) buf.data[(y0 + y) * W + x0 + x] = px[Math.floor((y * G) / cell) * G + Math.floor((x * G) / cell)];
  }
  writeFileSync(`${OUT}/preview.png`, encodePng(buf, 1));
}

/** Every option once, on a plain base, for checking the art. */
function catalog(bank: Record<string, Record<string, SpriteImage>>) {
  const base = {
    '01-background': 'paper',
    '03-neck': 'skin-2',
    '04-outfit': 'navy-suit',
    '05-head': 'skin-2',
    '07-expression': 'neutral',
    '08-hair': 'side-part-dark-brown',
  } as Record<string, string>;
  const order = ['01-background', '02-hair-back', '03-neck', '04-outfit', '05-head', '06-facial-hair', '07-expression', '08-hair', '09-eyewear', '10-accessory'];
  const make = (o: Record<string, string>) => {
    const pick = { ...base, ...o };
    if (o['08-hair']) pick['02-hair-back'] = o['08-hair'];
    else pick['02-hair-back'] = base['08-hair'];
    const px = new Uint32Array(G * G);
    for (const d of order) {
      const img = pick[d] ? bank[d]?.[pick[d]] : undefined;
      if (img) over(px, img.px);
    }
    return px;
  };
  const rows: Uint32Array[][] = [
    HAIR_STYLE_NAMES.map((h) => make({ '08-hair': `${slug(h)}-dark-brown` })),
    HAIR_NAMES.map((c) => make({ '08-hair': `pompadour-${slug(c)}` })),
    Object.keys(bank['04-outfit']).map((o) => make({ '04-outfit': o })),
    [...Object.keys(bank['07-expression']).map((e) => make({ '07-expression': e })), ...Object.keys(bank['09-eyewear']).map((e) => make({ '09-eyewear': e })), make({ '10-accessory': 'cigar' })],
    [...Object.keys(bank['05-head']).map((k) => make({ '05-head': k, '03-neck': k, '01-background': 'brass' })), ...['stubble', 'beard', 'moustache', 'goatee'].map((f) => make({ '06-facial-hair': `${f}-dark-brown`, '08-hair': 'short-crop-dark-brown' })), ...Object.keys(bank['01-background']).map((b) => make({ '01-background': b }))],
  ];
  const cell = 160;
  const cols = Math.max(...rows.map((r) => r.length));
  const W = cols * cell;
  const buf = new PixelBuffer(W, rows.length * cell);
  buf.data.fill(rgba('#f6f4ee'));
  rows.forEach((r, j) =>
    r.forEach((px, i) => {
      for (let y = 0; y < cell; y++) for (let x = 0; x < cell; x++) buf.data[(j * cell + y) * W + i * cell + x] = px[Math.floor((y * G) / cell) * G + Math.floor((x * G) / cell)];
    }),
  );
  writeFileSync(`${OUT}/catalog.png`, encodePng(buf, 1));
}
