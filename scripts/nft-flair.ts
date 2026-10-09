/**
 * The layers that make an Investor look like it came from this firm: a
 * price chart behind them, a cast shadow, a frame (a finance-TV news strip,
 * a breaking banner, an ink border or a gold stock-certificate edge) and a
 * finish over everything (dithered vignette, CRT scanlines or film grain).
 *
 * All drawn on the same 80×80 grid as the figures, in the site's palette.
 */
import type { SpriteImage } from '../src/art/figure';
import { rgba } from '../src/scene/buffer';
import { drawText, textWidth } from '../src/scene/font';
import { shade } from '../src/art/palette';

const G = 80;
const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
const bayer = (x: number, y: number) => (BAYER[(y & 3) * 4 + (x & 3)] + 0.5) / 16;
const img = (): SpriteImage => ({ w: G, h: G, px: new Uint32Array(G * G) });
const put = (im: SpriteImage, x: number, y: number, c: number) => {
  if (x >= 0 && y >= 0 && x < G && y < G) im.px[y * G + x] = c;
};
const rect = (im: SpriteImage, x: number, y: number, w: number, h: number, c: number) => {
  for (let j = y; j < y + h; j++) for (let i = x; i < x + w; i++) put(im, i, j, c);
};
const text = (im: SpriteImage, s: string, x: number, y: number, c: number) => drawText(s, (dx, dy) => put(im, x + dx, y + dy, c));
/** A small deterministic wobble, so lines look traded rather than plotted. */
const wob = (x: number, seed: number) => {
  const k = Math.floor(x / 4);
  const h = (((k * 7919 + seed * 104729) >>> 0) % 5) - 2;
  return h * 0.6;
};

const UP = '#4fc271';
const DOWN = '#e0574a';
const FLAT = '#d9a83a';

// ---------------------------------------------------------------- charts

function line(path: (x: number) => number, hex: string, seed: number): SpriteImage {
  const im = img();
  const c = rgba(hex);
  const dark = rgba(shade(hex, -0.32));
  const fill = rgba(hex, 46);
  const grid = rgba('#1b1815', 26);
  // Faint chart paper.
  for (let y = 8; y < G; y += 12) for (let x = 0; x < G; x += 2) put(im, x, y, grid);
  let prev = Math.round(path(0) + wob(0, seed));
  for (let x = 0; x < G; x++) {
    const y = Math.round(path(x) + wob(x, seed));
    // Soft area under the line, fading as it goes down.
    for (let j = Math.max(y, prev) + 2; j < G; j++) if ((j - y) / 30 < 1 - bayer(x, j) * 0.9) put(im, x, j, fill);
    // The line, two pixels thick, joined vertically so steep moves stay solid.
    for (let j = Math.min(prev, y); j <= Math.max(prev, y) + 1; j++) put(im, x, j, j === Math.max(prev, y) + 1 ? dark : c);
    prev = y;
  }
  // The last price, pulsing at the right edge.
  const ly = Math.round(path(G - 6) + wob(G - 6, seed));
  rect(im, G - 8, ly - 1, 4, 4, rgba('#ffffff'));
  rect(im, G - 7, ly, 2, 2, c);
  return im;
}

function candles(seed: number): SpriteImage {
  const im = img();
  const grid = rgba('#1b1815', 26);
  for (let y = 8; y < G; y += 12) for (let x = 0; x < G; x += 2) put(im, x, y, grid);
  let price = 60;
  for (let x = 1, i = 0; x < G - 3; x += 7, i++) {
    const r = ((i * 2654435761 + seed * 40503) >>> 0) % 100;
    const move = r < 64 ? -(4 + (r % 6)) : 3 + (r % 5);
    const open = price;
    const close = Math.max(10, Math.min(68, price + move));
    const up = close < open;
    const c = rgba(up ? UP : DOWN);
    const edge = rgba(shade(up ? UP : DOWN, -0.32));
    const top = Math.min(open, close);
    const bot = Math.max(open, close);
    for (let y = top - 4; y <= bot + 3; y++) put(im, x + 2, y, edge);
    rect(im, x, top, 5, Math.max(3, bot - top), c);
    for (let y = top; y < top + Math.max(3, bot - top); y++) put(im, x + 4, y, edge);
    price = close;
  }
  return im;
}

export const CHARTS: [string, () => SpriteImage][] = [
  ['moon', () => line((x) => 66 - 56 * (x / 79) ** 3, UP, 1)],
  ['steady-climb', () => line((x) => 60 - 36 * (x / 79), UP, 2)],
  ['chop', () => line((x) => 36 + ((Math.floor(x / 7) * 5) % 3 - 1) * 5, FLAT, 3)],
  ['rug-pull', () => line((x) => (x < 56 ? 58 - 44 * (x / 56) : 74), DOWN, 4)],
  ['dead-cat-bounce', () => line((x) => (x < 40 ? 14 + x : x < 50 ? 54 - (x - 40) * 1.2 : 42 + (x - 50) * 1.1), DOWN, 5)],
  ['v-recovery', () => line((x) => (x < 40 ? 18 + x * 1.15 : 64 - (x - 40) * 1.2), UP, 6)],
  ['candles', () => candles(7)],
];

// ---------------------------------------------------------------- shadow

/** The figure's silhouette, pushed back and to the right, as a soft dithered shadow. */
export function shadow(silhouette: SpriteImage): SpriteImage {
  const im = img();
  const c = rgba('#1b1815', 52);
  for (let y = 0; y < G; y++)
    for (let x = 0; x < G; x++) {
      const sx = x - 4;
      const sy = y - 2;
      if (sx < 0 || sy < 0 || sx >= G || sy >= G) continue;
      if (silhouette.px[sy * G + sx] >>> 24 > 128) put(im, x, y, c);
    }
  return im;
}

// ---------------------------------------------------------------- frames

function chyron(tag: string, tagHex: string, message: string, msgHex: string): SpriteImage {
  const im = img();
  const bar = rgba('#111317', 238);
  rect(im, 0, 68, G, 12, bar);
  rect(im, 0, 67, G, 1, rgba(tagHex));
  const tw = textWidth(tag) + 5;
  rect(im, 0, 68, tw, 12, rgba(tagHex));
  text(im, tag, 3, 71, rgba('#ffffff'));
  text(im, message, tw + 3, 71, rgba(msgHex));
  return im;
}

function inkBorder(): SpriteImage {
  const im = img();
  const ink = rgba('#1b1815');
  const paper = rgba('#f6f4ee');
  rect(im, 0, 0, G, 3, ink);
  rect(im, 0, G - 3, G, 3, ink);
  rect(im, 0, 0, 3, G, ink);
  rect(im, G - 3, 0, 3, G, ink);
  for (let i = 3; i < G - 3; i++) {
    put(im, i, 3, paper);
    put(im, i, G - 4, paper);
    put(im, 3, i, paper);
    put(im, G - 4, i, paper);
  }
  return im;
}

function certificate(): SpriteImage {
  const im = img();
  const gold = rgba('#d4a640');
  const hi = rgba('#f0d58a');
  const lo = rgba('#8a6a22');
  for (let i = 0; i < G; i++)
    for (const [x, y] of [
      [i, 0],
      [i, G - 1],
      [0, i],
      [G - 1, i],
    ])
      put(im, x, y, lo);
  for (let i = 1; i < G - 1; i++)
    for (const [x, y] of [
      [i, 1],
      [i, G - 2],
      [1, i],
      [G - 2, i],
    ])
      put(im, x, y, (i >> 1) % 2 ? gold : hi);
  for (let i = 3; i < G - 3; i++)
    for (const [x, y] of [
      [i, 3],
      [i, G - 4],
      [3, i],
      [G - 4, i],
    ])
      put(im, x, y, gold);
  // Engraved corner rosettes.
  for (const [cx, cy] of [
    [6, 6],
    [G - 7, 6],
    [6, G - 7],
    [G - 7, G - 7],
  ]) {
    rect(im, cx - 2, cy - 2, 5, 5, gold);
    put(im, cx, cy, lo);
    for (const [dx, dy] of [
      [0, -3],
      [0, 3],
      [-3, 0],
      [3, 0],
    ])
      put(im, cx + dx, cy + dy, hi);
  }
  return im;
}

export const FRAMES: [string, () => SpriteImage][] = [
  ['ticker-green', () => chyron('SI', '#2f9e5a', '$STEVE +4.20%', UP)],
  ['ticker-red', () => chyron('SI', '#a83f35', '$STEVE -6.90%', DOWN)],
  ['breaking', () => chyron('LIVE', '#c8352b', 'INVESTOR HIRED', '#f4f1e8')],
  ['ink-border', inkBorder],
  ['gold-certificate', certificate],
];

// ---------------------------------------------------------------- finishes

function vignette(): SpriteImage {
  const im = img();
  const c = rgba('#120f0c', 70);
  for (let y = 0; y < G; y++)
    for (let x = 0; x < G; x++) {
      const dx = (x + 0.5) / G - 0.5;
      const dy = (y + 0.5) / G - 0.45;
      const t = (Math.sqrt(dx * dx + dy * dy) - 0.5) / 0.3;
      if (t > bayer(x, y)) put(im, x, y, c);
    }
  return im;
}

function scanlines(): SpriteImage {
  const im = img();
  const c = rgba('#0c0f0d', 24);
  for (let y = 1; y < G; y += 3) rect(im, 0, y, G, 1, c);
  return im;
}

function grain(): SpriteImage {
  const im = img();
  const lite = rgba('#ffffff', 34);
  const dark = rgba('#000000', 40);
  let st = 0x9e3779b9;
  for (let i = 0; i < G * G; i++) {
    st ^= st << 13;
    st ^= st >>> 17;
    st ^= st << 5;
    const r = (st >>> 0) % 97;
    if (r < 5) im.px[i] = lite;
    else if (r < 10) im.px[i] = dark;
  }
  return im;
}

export const FINISHES: [string, () => SpriteImage][] = [
  ['vignette', vignette],
  ['scanlines', scanlines],
  ['film-grain', grain],
];
