/**
 * Investors NFT trait layers. `npm run art -- nft-layers`
 *
 * Every layer is drawn by the same renderer as the site's traders
 * (src/art/figure.ts), one part at a time, then given the retro filter:
 * the bust is drawn at 80×80 hard pixels and scaled to 1024×1024 with
 * nearest-neighbour, so every layer lines up exactly.
 *
 * Output: nft/layers/<NN-trait>/<option>.png, plus nft/preview.png.
 * Stack the folders in number order; see nft/README.md.
 */
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { it } from 'vitest';
import { PixelBuffer, rgba } from '../src/scene/buffer';
import { ROOMS } from './nft-rooms';
import { drawText } from '../src/scene/font';
import { CHARTS, FINISHES, FRAMES, shadow } from './nft-flair';
import { encodePng } from '../src/scene/png';
import { renderFigure, type FigureOpts, type SpriteImage } from '../src/art/figure';
import { HAIRS, HAIR_NAMES, HAIR_STYLE_NAMES, SKINS, shade } from '../src/art/palette';
import type { Look } from '../src/sim/types';

const G = 80;
/** Output size. Generators offer 1024; every layer uses the same pixel mapping, so they still stack exactly. */
const SIZE = 1024;
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

/** Nearest-neighbour from the 80×80 grid to SIZE×SIZE (each cell 12 or 13 px). */
function upscale(img: SpriteImage): PixelBuffer {
  const buf = new PixelBuffer(SIZE, SIZE);
  for (let y = 0; y < SIZE; y++) {
    const sy = Math.floor((y * G) / SIZE);
    for (let x = 0; x < SIZE; x++) buf.data[y * SIZE + x] = img.px[sy * G + Math.floor((x * G) / SIZE)];
  }
  return buf;
}

const empty = (img: SpriteImage) => !img.px.some((c) => c >>> 24);

function save(dir: string, name: string, img: SpriteImage) {
  if (empty(img)) return false;
  mkdirSync(`${OUT}/layers/${dir}`, { recursive: true });
  writeFileSync(`${OUT}/layers/${dir}/${name}.png`, encodePng(upscale(img), 1, 0));
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

const FACIAL = ['', 'stubble', 'short-beard', 'moustache', 'goatee'];
/** Hair styles left out of the NFTs (the afro read as a helmet at this size). */
const SKIP_STYLES = new Set(['afro']);
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
  for (const [name, draw] of ROOMS) add('01-background', name, { w: G, h: G, px: draw().data });
  for (const [name, draw] of CHARTS) add('02-chart', name, draw());
  add('03-shadow', 'shadow', shadow(part({ hairStyle: 1 }, ['neck', 'body', 'head', 'hair'])));
  for (const [name, draw] of FRAMES) add('13-frame', name, draw());
  for (const [name, draw] of FINISHES) add('14-finish', name, draw());

  HAIRS.forEach((_, hc) =>
    HAIR_STYLE_NAMES.forEach((style, hs) => {
      if (SKIP_STYLES.has(style)) return;
      const look = { hair: hc, hairStyle: hs };
      const n = `${slug(style)}-${slug(HAIR_NAMES[hc])}`;
      add('04-hair-back', n, part(look, ['hairBack']));
      add('10-hair', n, part(look, ['hair']));
    }),
  );

  SKINS.forEach((_, sk) => {
    const n = `skin-${sk + 1}`;
    add('05-neck', n, part({ skin: sk }, ['neck']));
    add('07-head', n, part({ skin: sk }, ['head']));
  });

  for (const [name, outfit, suit, shirt, tie, neck] of OUTFITS) {
    const look = { outfit, suit, shirt, tie, neck };
    const collar = part(look, ['collar'], { noOutline: true });
    if (!empty(collar)) throw new Error(`${name} shows skin at the collar; pick another neck`);
    add('06-outfit', name, part(look, ['body']));
  }

  HAIRS.forEach((_, hc) =>
    FACIAL.forEach((f, face) => {
      if (face === 1) add('08-facial-hair', `${f}-${slug(HAIR_NAMES[hc])}`, stubble(hc));
      else if (face) add('08-facial-hair', `${f}-${slug(HAIR_NAMES[hc])}`, part({ face, hair: hc }, ['facial']));
    }),
  );

  for (const [name, face] of EXPRESSIONS) {
    const img = part({ skin: 2 }, ['expression'], { face, noOutline: true });
    adaptMouth(img, SKINS[2]);
    add('09-expression', name, img);
  }

  for (const [name, look, gold] of EYEWEAR) add('11-eyewear', name, part(look, ['eyewear'], { glasses: gold, noOutline: name !== 'headset' }));
  add('12-accessory', 'cigar', part({ cigar: true }, ['cigar']));

  writeFileSync(`${OUT}/layers/counts.json`, JSON.stringify(counts, null, 2) + '\n');
  preview(bank);
  catalog(bank);
  generated(bank);
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
    const hairName = pick('10-hair');
    const colour = HAIR_NAMES.map(slug).find((c) => hairName.endsWith(`-${c}`))!;
    const skin = pick('07-head');
    const bg = pick('01-background');
    const plain = BACKGROUNDS.some(([b]) => b === bg);
    const stack: (SpriteImage | undefined)[] = [
      bank['01-background'][bg],
      plain && rnd() < 0.8 ? bank['02-chart'][pick('02-chart')] : undefined,
      bank['03-shadow'].shadow,
      bank['04-hair-back']?.[hairName],
      bank['05-neck'][skin],
      bank['06-outfit'][pick('06-outfit')],
      bank['07-head'][skin],
      rnd() < 0.3 ? bank['08-facial-hair'][`${FACIAL[1 + Math.floor(rnd() * 4)]}-${colour}`] : undefined,
      bank['09-expression'][pick('09-expression')],
      bank['10-hair'][hairName],
      rnd() < 0.35 ? bank['11-eyewear'][pick('11-eyewear')] : undefined,
      rnd() < 0.08 ? bank['12-accessory'].cigar : undefined,
      rnd() < 0.45 ? bank['13-frame'][pick('13-frame')] : undefined,
      rnd() < 0.6 ? bank['14-finish'][pick('14-finish')] : undefined,
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
    '03-shadow': 'shadow',
    '05-neck': 'skin-2',
    '06-outfit': 'navy-suit',
    '07-head': 'skin-2',
    '09-expression': 'neutral',
    '10-hair': 'side-part-dark-brown',
  } as Record<string, string>;
  const order = ['01-background', '02-chart', '03-shadow', '04-hair-back', '05-neck', '06-outfit', '07-head', '08-facial-hair', '09-expression', '10-hair', '11-eyewear', '12-accessory', '13-frame', '14-finish'];
  const make = (o: Record<string, string>) => {
    const pick = { ...base, ...o };
    if (o['10-hair']) pick['04-hair-back'] = o['10-hair'];
    else pick['04-hair-back'] = base['10-hair'];
    const px = new Uint32Array(G * G);
    for (const d of order) {
      const img = pick[d] ? bank[d]?.[pick[d]] : undefined;
      if (img) over(px, img.px);
    }
    return px;
  };
  const rows: Uint32Array[][] = [
    HAIR_STYLE_NAMES.filter((h) => !SKIP_STYLES.has(h)).map((h) => make({ '10-hair': `${slug(h)}-dark-brown` })),
    HAIR_NAMES.map((c) => make({ '10-hair': `pompadour-${slug(c)}` })),
    Object.keys(bank['06-outfit']).map((o) => make({ '06-outfit': o })),
    [...Object.keys(bank['09-expression']).map((e) => make({ '09-expression': e })), ...Object.keys(bank['11-eyewear']).map((e) => make({ '11-eyewear': e })), make({ '12-accessory': 'cigar' })],
    [...Object.keys(bank['07-head']).map((k) => make({ '07-head': k, '05-neck': k, '01-background': 'brass' })), ...['stubble', 'short-beard', 'moustache', 'goatee'].map((f) => make({ '08-facial-hair': `${f}-dark-brown`, '10-hair': 'short-crop-dark-brown' })), ...Object.keys(bank['01-background']).map((b) => make({ '01-background': b }))],
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

  // The newest options, large.
  const fresh = [
    ...[['black', 'skin-1'], ['dark-brown', 'skin-3'], ['sandy', 'skin-2'], ['auburn', 'skin-5']].map(([c, sk]) => make({ '10-hair': `curtains-${c}`, '07-head': sk, '05-neck': sk })),
    ...[['black', 'skin-6'], ['dark-brown', 'skin-2'], ['grey', 'skin-4'], ['auburn', 'skin-1']].map(([c, sk]) => make({ '08-facial-hair': `short-beard-${c}`, '10-hair': `short-crop-${c}`, '07-head': sk, '05-neck': sk })),
  ];
  const fb = 300;
  const fbuf = new PixelBuffer(4 * fb, 2 * fb);
  fresh.forEach((px, i) => {
    for (let y = 0; y < fb; y++) for (let x = 0; x < fb; x++) fbuf.data[(Math.floor(i / 4) * fb + y) * 4 * fb + (i % 4) * fb + x] = px[Math.floor((y * G) / fb) * G + Math.floor((x * G) / fb)];
  });
  writeFileSync(`${OUT}/new-options.png`, encodePng(fbuf, 1));

  // The flair layers, large: charts, frames and finishes.
  const flair = [
    ...Object.keys(bank['02-chart']).map((c, i) => make({ '02-chart': c, '01-background': BACKGROUNDS[i % 7][0], '09-expression': 'smirk' })),
    ...Object.keys(bank['13-frame']).map((f, i) => make({ '13-frame': f, '02-chart': ['moon', 'rug-pull', 'candles', 'steady-climb', 'v-recovery'][i], '01-background': ['ledger-green', 'brick', 'paper', 'lilac', 'brass'][i], '14-finish': 'vignette' })),
    ...Object.keys(bank['14-finish']).map((f) => make({ '14-finish': f, '02-chart': 'chop', '01-background': 'mint' })),
  ];
  const fl = 300;
  const fc = 5;
  const flb = new PixelBuffer(fc * fl, Math.ceil(flair.length / fc) * fl);
  flb.data.fill(rgba('#f6f4ee'));
  flair.forEach((px, i) => {
    for (let y = 0; y < fl; y++) for (let x = 0; x < fl; x++) flb.data[(Math.floor(i / fc) * fl + y) * fc * fl + (i % fc) * fl + x] = px[Math.floor((y * G) / fl) * G + Math.floor((x * G) / fl)];
  });
  writeFileSync(`${OUT}/flair.png`, encodePng(flb, 1));

  // A showcase: every kind of trait, rare ones included, each with a caption.
  type Pick = [string, Record<string, string>];
  const sk = (n: number) => ({ '05-neck': `skin-${n}`, '07-head': `skin-${n}` });
  const show: Pick[] = [
    ['RARE: GOLD CERT + CIGAR', { '01-background': 'after-hours', '10-hair': 'slicked-back-grey', '09-expression': 'smirk', '06-outfit': 'navy-double-breasted', '11-eyewear': 'gold-glasses', '12-accessory': 'cigar', '13-frame': 'gold-certificate', ...sk(2) }],
    ['RARE: MOON CHART', { '01-background': 'ledger-green', '02-chart': 'moon', '10-hair': 'pompadour-sandy', '09-expression': 'grin', '06-outfit': 'charcoal-suit', '13-frame': 'ticker-green', ...sk(1) }],
    ['RUG PULL', { '01-background': 'brick', '02-chart': 'rug-pull', '10-hair': 'receding-grey', '09-expression': 'frown', '06-outfit': 'black-suit', '11-eyewear': 'sunglasses', '13-frame': 'ticker-red', ...sk(3) }],
    ['BREAKING', { '01-background': 'lobby', '10-hair': 'bun-auburn', '09-expression': 'delighted', '06-outfit': 'braces-pink', '13-frame': 'breaking', ...sk(5) }],
    ['CORNER OFFICE', { '01-background': 'corner-office', '10-hair': 'side-part-black', '08-facial-hair': 'goatee-black', '09-expression': 'smirk', '06-outfit': 'black-tie', '11-eyewear': 'glasses', '14-finish': 'vignette', ...sk(4) }],
    ['TRADING FLOOR', { '01-background': 'trading-floor', '10-hair': 'short-crop-black', '09-expression': 'talking', '06-outfit': 'navy-pinstripe', '11-eyewear': 'headset', ...sk(6) }],
    ['SERVER ROOM', { '01-background': 'server-room', '10-hair': 'buzz-cut-dark-brown', '09-expression': 'neutral', '06-outfit': 'turtleneck-and-blazer', '11-eyewear': 'earpiece', '14-finish': 'scanlines', ...sk(2) }],
    ['SCREEN WALL', { '01-background': 'screen-wall', '10-hair': 'curly-top-chestnut', '09-expression': 'shouting', '06-outfit': 'charcoal-pinstripe', '14-finish': 'film-grain', ...sk(5) }],
    ['WALL STREET', { '01-background': 'wall-street', '10-hair': 'curtains-dark-brown', '09-expression': 'smirk', '06-outfit': 'tobacco-suit', ...sk(1) }],
    ['PUTTING GREEN', { '01-background': 'putting-green', '10-hair': 'slicked-back-white', '08-facial-hair': 'moustache-white', '09-expression': 'grin', '06-outfit': 'grey-waistcoat', '12-accessory': 'cigar', ...sk(2) }],
    ['CANDLES + INK BORDER', { '01-background': 'paper', '02-chart': 'candles', '10-hair': 'long-black', '09-expression': 'surprised', '06-outfit': 'olive-suit', '13-frame': 'ink-border', ...sk(3) }],
    ['DEAD CAT BOUNCE', { '01-background': 'pink-paper', '02-chart': 'dead-cat-bounce', '10-hair': 'bob-chestnut', '09-expression': 'frown', '06-outfit': 'flannel-grey-suit', '14-finish': 'vignette', ...sk(4) }],
    ['V RECOVERY', { '01-background': 'lilac', '02-chart': 'v-recovery', '10-hair': 'man-bun-dark-brown', '08-facial-hair': 'short-beard-dark-brown', '09-expression': 'delighted', '06-outfit': 'visitor-lanyard', ...sk(5) }],
    ['CHOP', { '01-background': 'mint', '02-chart': 'chop', '10-hair': 'ponytail-sandy', '09-expression': 'neutral', '06-outfit': 'braces-pale-blue', '14-finish': 'scanlines', ...sk(1) }],
    ['STEADY CLIMB', { '01-background': 'brass', '02-chart': 'steady-climb', '10-hair': 'side-part-chestnut', '08-facial-hair': 'stubble-chestnut', '09-expression': 'smirk', '06-outfit': 'navy-suit', ...sk(3) }],
    ['RARE: AFTER HOURS', { '01-background': 'after-hours', '10-hair': 'bald-black', '08-facial-hair': 'short-beard-black', '09-expression': 'grin', '06-outfit': 'black-double-breasted', '11-eyewear': 'gold-glasses', '14-finish': 'vignette', ...sk(6) }],
  ];
  for (const [label, o] of show) for (const [d, n] of Object.entries(o)) if (!bank[d]?.[n]) throw new Error(`showcase "${label}": no ${d}/${n}`);
  const sc = 300;
  const cap = 30;
  const scols = 4;
  const sbuf = new PixelBuffer(scols * sc, Math.ceil(show.length / scols) * (sc + cap));
  sbuf.data.fill(rgba('#111317'));
  show.forEach(([label, o], i) => {
    const px = make(o);
    const x0 = (i % scols) * sc;
    const y0 = Math.floor(i / scols) * (sc + cap);
    for (let y = 0; y < sc; y++) for (let x = 0; x < sc; x++) sbuf.data[(y0 + y) * scols * sc + x0 + x] = px[Math.floor((y * G) / sc) * G + Math.floor((x * G) / sc)];
    const gold = label.startsWith('RARE');
    drawText(label, (gx, gy) => {
      for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) {
        const xx = x0 + 10 + gx * 3 + a;
        const yy = y0 + sc + 8 + gy * 3 + b;
        if (xx < x0 + sc) sbuf.data[yy * scols * sc + xx] = rgba(gold ? '#e0b54a' : '#f4f1e8');
      }
    });
  });
  writeFileSync(`${OUT}/showcase.png`, encodePng(sbuf, 1));

  // The building rooms, large.
  const rooms = ROOMS.map(([n]) => make({ '01-background': n, '09-expression': 'smirk', '10-hair': 'slicked-back-grey' }));
  const big = 360;
  const rb = new PixelBuffer(4 * big, 2 * big);
  rb.data.fill(rgba('#f6f4ee'));
  rooms.forEach((px, i) => {
    for (let y = 0; y < big; y++) for (let x = 0; x < big; x++) rb.data[(Math.floor(i / 4) * big + y) * 4 * big + (i % 4) * big + x] = px[Math.floor((y * G) / big) * G + Math.floor((x * G) / big)];
  });
  writeFileSync(`${OUT}/rooms.png`, encodePng(rb, 1));
}

/**
 * What a generator makes: traits rolled by the weights in RARITY.md, with the
 * README's rules applied, stacked from the exported layers. No picking, no labels.
 */
function generated(bank: Record<string, Record<string, SpriteImage>>) {
  const tables: Record<string, [string, number][]> = {};
  let section = '';
  for (const line of readFileSync(`${OUT}/RARITY.md`, 'utf8').split('\n')) {
    const h = line.match(/^## (.+)/);
    if (h) section = h[1].split(' (')[0].trim();
    const row = line.match(/^\| ([a-z0-9-]+) \| (\d+)/);
    if (row && section) (tables[section] ??= []).push([row[1], Number(row[2])]);
  }
  // mulberry32: a small, well-mixed generator (plain LCGs repeat patterns across rolls).
  let seed = 20261009;
  const rnd = () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const roll = (t: string) => {
    const rows = tables[t];
    if (!rows) throw new Error(`RARITY.md has no table for ${t}`);
    let r = rnd() * rows.reduce((n, [, w]) => n + w, 0);
    for (const [name, w] of rows) if ((r -= w) < 0) return name;
    return rows[rows.length - 1][0];
  };
  const plainBgs = new Set(BACKGROUNDS.map(([b]) => b));
  const order = ['01-background', '02-chart', '03-shadow', '04-hair-back', '05-neck', '06-outfit', '07-head', '08-facial-hair', '09-expression', '10-hair', '11-eyewear', '12-accessory', '13-frame', '14-finish'];
  const tally: Record<string, number> = {};
  const N = 24;
  const cols = 6;
  const cell = 256;
  const buf = new PixelBuffer(cols * cell, (N / cols) * cell);
  for (let i = 0; i < N; i++) {
    const bg = roll('Background');
    tally[bg] = (tally[bg] ?? 0) + 1;
    const hair = `${roll('Hair style')}-${roll('Hair colour')}`;
    const colour = HAIR_NAMES.map(slug).find((c) => hair.endsWith(`-${c}`))!;
    const skin = `skin-${1 + Math.floor(rnd() * 6)}`;
    const expression = roll('Expression');
    const eyewear = roll('Eyewear');
    let accessory = roll('Accessory');
    if (expression === 'shouting' || eyewear === 'headset') accessory = 'none';
    const facial = roll('Facial hair');
    const chart = plainBgs.has(bg) ? roll('Chart') : 'none';
    const pick: Record<string, string> = {
      '01-background': bg,
      '02-chart': chart,
      '03-shadow': 'shadow',
      '04-hair-back': hair,
      '05-neck': skin,
      '06-outfit': roll('Outfit'),
      '07-head': skin,
      '08-facial-hair': facial === 'none' ? 'none' : `${facial}-${colour}`,
      '09-expression': expression,
      '10-hair': hair,
      '11-eyewear': eyewear,
      '12-accessory': accessory,
      '13-frame': roll('Frame'),
      '14-finish': roll('Finish'),
    };
    const px = new Uint32Array(G * G);
    for (const d of order) {
      const name = pick[d];
      if (name === 'none') continue;
      const layer = bank[d]?.[name];
      if (!layer && d !== '04-hair-back') throw new Error(`no layer ${d}/${name}`);
      if (layer) over(px, layer.px);
    }
    const x0 = (i % cols) * cell;
    const y0 = Math.floor(i / cols) * cell;
    for (let y = 0; y < cell; y++) for (let x = 0; x < cell; x++) buf.data[(y0 + y) * cols * cell + x0 + x] = px[Math.floor((y * G) / cell) * G + Math.floor((x * G) / cell)];
  }
  writeFileSync(`${OUT}/generated-sample.png`, encodePng(buf, 1));
  // Sanity check on the roller: 10,000 background rolls should land near RARITY.md's weights.
  const big: Record<string, number> = {};
  for (let k = 0; k < 10000; k++) {
    const b = roll('Background');
    big[b] = (big[b] ?? 0) + 1;
  }
  console.log('background mix per 10,000 rolls', big, 'in this sample', tally);
}
