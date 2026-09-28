/**
 * Per-frame paint over the static background. Screens, tickers and server
 * LEDs are drawn only onto their key colours, so anything standing in front
 * of them keeps covering them.
 */
import type { PixelBuffer } from './buffer';
import { mixColor } from './buffer';
import type { Built, ScreenSpec } from './building';
import { C } from './colors';
import { drawText, textWidth } from './font';
import type { Iso } from './iso';
import { BAY_X, S, W, X, Y, deskSpot, floorZ } from './layout';
import { blitAt, renderCat, renderHeli } from '../art/props';

const CATS = [renderCat(0, false, S), renderCat(0, true, S), renderCat(1, false, S), renderCat(1, true, S)];
const HELI = [0, 1, 2, 3].map((f) => renderHeli(f, S));

export interface TickerItem {
  text: string;
  color: number;
}

export interface SceneData {
  /** Price history to show on each desk's wall screen. */
  deskSeries: Map<number, number[]>;
  /** A second coin per desk, for the side monitors. */
  sideSeries?: Map<number, number[]>;
  terminalSeries: number[][];
  ticker: TickerItem[];
  stale: boolean;
  hotDesk: number | null;
  doorSpin: boolean;
}

function hash(a: number, b: number) {
  let h = (a * 374761393 + b * 668265263) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

/** Fill a rectangle on a y-plane (world units), only over the key colour. */
function maskY(buf: PixelBuffer, iso: Iso, y: number, x0: number, x1: number, z0: number, z1: number, key: number, c: number) {
  buf.polyEach([iso.p(x0, y, z1), iso.p(x1, y, z1), iso.p(x1, y, z0), iso.p(x0, y, z0)], (px, py) => {
    const i = py * buf.w + px;
    if (buf.data[i] === key) buf.data[i] = c;
  });
}

/** The same on an x-plane; u runs along y. */
function maskX(buf: PixelBuffer, iso: Iso, x: number, y0: number, y1: number, z0: number, z1: number, key: number, c: number) {
  buf.polyEach([iso.p(x, y0, z1), iso.p(x, y1, z1), iso.p(x, y1, z0), iso.p(x, y0, z0)], (px, py) => {
    const i = py * buf.w + px;
    if (buf.data[i] === key) buf.data[i] = c;
  });
}

type Rect = (u0: number, u1: number, z0: number, z1: number, c: number) => void;

/** A painter in screen-left-to-right order for either plane. */
function surface(buf: PixelBuffer, iso: Iso, s: ScreenSpec): { rect: Rect; u0: number; u1: number } {
  if (s.plane === 'x') {
    // On an x-plane, screen-left-to-right runs toward smaller y.
    const x = s.x!;
    const hi = s.x1;
    return { rect: (a, b, z0, z1, c) => maskX(buf, iso, x, hi - b + s.x0, hi - a + s.x0, z0, z1, C.screen, c), u0: s.x0, u1: s.x1 };
  }
  return { rect: (a, b, z0, z1, c) => maskY(buf, iso, s.y, a, b, z0, z1, C.screen, c), u0: s.x0, u1: s.x1 };
}

function candles(buf: PixelBuffer, iso: Iso, s: ScreenSpec, series: number[] | undefined) {
  const { rect, u0, u1 } = surface(buf, iso, s);
  const { z0, z1 } = s;
  const h = z1 - z0;
  // Grid.
  for (const f of [0.25, 0.5, 0.75]) rect(u0, u1, z0 + h * f, z0 + h * f + 0.34, C.screenGrid);
  if (!series || series.length < 4) {
    rect(u0 + 0.6, u1 - 0.6, z0 + h / 2, z0 + h / 2 + 0.4, C.amberDim);
    return;
  }
  const step = 1.05;
  const n = Math.max(1, Math.floor((u1 - u0 - 0.6) / step));
  const per = series.length / n;
  const bars: { o: number; h: number; l: number; c: number }[] = [];
  for (let i = 0; i < n; i++) {
    const a = Math.floor(i * per);
    const b = Math.max(a + 1, Math.floor((i + 1) * per));
    const chunk = series.slice(a, b + 1);
    bars.push({ o: chunk[0], c: chunk[chunk.length - 1], h: Math.max(...chunk), l: Math.min(...chunk) });
  }
  const lo = Math.min(...bars.map((b) => b.l));
  const hi = Math.max(...bars.map((b) => b.h));
  const span = hi - lo || 1;
  const zr = (v: number) => z0 + 0.4 + ((v - lo) / span) * (h - 0.8);
  bars.forEach((b, i) => {
    const x = u0 + 0.4 + i * step;
    const col = b.c >= b.o ? C.candleUp : C.candleDown;
    rect(x + 0.28, x + 0.44, zr(b.l), zr(b.h), mixColor(col, C.screen, 0.3));
    const top = Math.max(zr(b.o), zr(b.c));
    const bot = Math.min(zr(b.o), zr(b.c));
    rect(x, x + 0.72, bot, Math.max(top, bot + 0.36), col);
  });
  // Last price line.
  const last = zr(series[series.length - 1]);
  rect(u0, u1, last, last + 0.2, mixColor(C.amber, C.screen, 0.35));
}

function lineChart(buf: PixelBuffer, iso: Iso, s: ScreenSpec, series: number[] | undefined) {
  const { rect, u0, u1 } = surface(buf, iso, s);
  const { z0, z1 } = s;
  if (!series || series.length < 2) return;
  const lo = Math.min(...series);
  const hi = Math.max(...series);
  const span = hi - lo || 1;
  const col = series[series.length - 1] >= series[0] ? C.candleUp : C.candleDown;
  const w = u1 - u0;
  const steps = Math.floor(w / 0.34);
  let prev = -1;
  for (let i = 0; i < steps; i++) {
    const v = series[Math.floor((i / (steps - 1)) * (series.length - 1))];
    const z = z0 + 0.5 + ((v - lo) / span) * (z1 - z0 - 1);
    const a = prev < 0 ? z : Math.min(prev, z);
    const b = prev < 0 ? z : Math.max(prev, z);
    rect(u0 + i * 0.34, u0 + i * 0.34 + 0.36, a, b + 0.34, col);
    rect(u0 + i * 0.34, u0 + i * 0.34 + 0.36, z0, a, mixColor(col, C.screen, 0.82));
    prev = z;
  }
}

function crt(buf: PixelBuffer, iso: Iso, s: ScreenSpec, t: number, stale: boolean) {
  const { y, x0, x1, z0, z1 } = s;
  if (stale) {
    for (let k = 0; k < 40; k++) {
      const x = x0 + hash(k, Math.floor(t * 8)) * (x1 - x0 - 0.4);
      const z = z0 + hash(k + 99, Math.floor(t * 8)) * (z1 - z0 - 0.4);
      maskY(buf, iso, y, x, x + 0.4, z, z + 0.4, C.screen, mixColor(C.screen, C.steelHi, 0.5));
    }
    if (Math.floor(t * 2) % 2 === 0) maskY(buf, iso, y, x0 + 1, x1 - 1, z0 + 2.4, z0 + 3.2, C.screen, C.ledRed);
    return;
  }
  const scroll = Math.floor(t * 3);
  for (let r = 0; r < 6; r++) {
    const len = 1 + hash(r + scroll, 3) * (x1 - x0 - 2.5);
    maskY(buf, iso, y, x0 + 0.8, x0 + 0.8 + len, z1 - 1 - r * 0.9, z1 - 0.6 - r * 0.9, C.screen, C.candleUp);
  }
}

/** Scrolling text in the 3×5 font across a key-coloured strip on a y-plane. */
function scrollText(buf: PixelBuffer, iso: Iso, y: number, x0: number, x1: number, zTop: number, items: TickerItem[], offset: number, key: number, cell = 1) {
  if (!items.length) return;
  const gap = 6;
  const widths = items.map((it) => (textWidth(it.text) + gap) * cell);
  const total = widths.reduce((a, c) => a + c, 0);
  const width = x1 - x0;
  let cursor = -(((offset % total) + total) % total);
  for (let rep = 0; rep < 4 && cursor < width; rep++)
    for (let i = 0; i < items.length && cursor < width; i++) {
      const start = cursor;
      if (start + widths[i] > 0)
        drawText(items[i].text, (dx, dy) => {
          const x = start + dx * cell;
          if (x >= 0 && x + cell <= width) maskY(buf, iso, y, x0 + x, x0 + x + cell * 0.86, zTop - (dy + 1) * cell + cell * 0.1, zTop - dy * cell, key, items[i].color);
        });
      cursor += widths[i];
    }
}

function highlight(iso: Iso, desk: number, t: number) {
  const spot = deskSpot(desk);
  if (!spot) return;
  const cx = BAY_X[spot.bay];
  const zf = floorZ(spot.level);
  const c = Math.floor(t * 3) % 2 ? C.goldHi : C.gold;
  const w = 1.4 / S;
  iso.top(cx - 21, 0.6, cx + 21, 0.6 + w * 2, zf, c);
  iso.top(cx - 21, 22.6, cx + 21, 22.6 + w * 2, zf, c);
  iso.top(cx - 21, 0.6, cx - 21 + w * 2, 23, zf, c);
  iso.top(cx + 21 - w * 2, 0.6, cx + 21, 23, zf, c);
}

export function animPass(buf: PixelBuffer, iso: Iso, b: Built, t: number, d: SceneData) {
  for (const s of b.screens) {
    if (s.kind === 'desk') candles(buf, iso, s, d.deskSeries.get(s.desk!));
    else if (s.kind === 'side') lineChart(buf, iso, s, d.sideSeries?.get(s.desk!) ?? d.deskSeries.get(s.desk!));
    else if (s.kind === 'terminal') lineChart(buf, iso, s, d.terminalSeries[s.slot!]);
    else crt(buf, iso, s, t, d.stale);
  }
  // Lobby board and the LED strip along every floor.
  scrollText(buf, iso, b.ticker.y, b.ticker.x0, b.ticker.x1, b.ticker.z1, d.ticker, Math.floor(t * 12), C.amberDim);
  b.bands.forEach((band, i) => {
    const rot = d.ticker.length ? [...d.ticker.slice(i * 3 % d.ticker.length), ...d.ticker.slice(0, i * 3 % d.ticker.length)] : [];
    scrollText(buf, iso, Y, -5, X, band.z0 + 4.4, rot, t * (9 + (i % 3) * 2) + i * 37, C.ledKey, 0.86);
  });
  // Server LEDs.
  const step = Math.floor(t * 4);
  b.leds.forEach((cell, i) => {
    const r = hash(i, step + (i % 5));
    const c = d.stale ? (r > 0.5 ? C.amber : C.ledOff) : r > 0.97 ? C.ledRed : r > 0.3 ? C.ledGreen : C.ledOff;
    for (const k of cell) if (buf.data[k] === C.ledOff || buf.data[k] === C.ledGreen || buf.data[k] === C.ledRed || buf.data[k] === C.amber) buf.data[k] = c;
  });
  // Espresso steam.
  for (const [sx, sy] of b.steam)
    for (let k = 0; k < 5; k++) {
      const p = (t * 0.6 + k / 5) % 1;
      const wob = Math.round(Math.sin((t + k) * 3) * S);
      const y = Math.round(sy - p * 12 * S);
      const a = 0.6 * (1 - p);
      for (let dx = -1; dx <= 2; dx++) for (let dy = 0; dy <= 1; dy++) buf.tint(sx + wob + dx, y + dy, 0xffffffff, a * (dx === -1 || dx === 2 ? 0.5 : 1));
    }
  // The HR cat.
  if (b.cat[0]) {
    const tail = Math.floor(t / 1.4) % 2;
    const blink = Math.floor(t * 1.3) % 7 === 0;
    blitAt(buf, CATS[tail * 2 + (blink ? 1 : 0)], b.cat[0], b.cat[1]);
  }
  if (d.hotDesk !== null) highlight(iso, d.hotDesk, t);
}

/** Revolving door: the panes turn while someone is going through. Drawn over the front layer. */
export function doorPass(iso: Iso, b: Built, t: number, spinning: boolean) {
  const { x, y0, y1, z0, z1 } = b.door;
  if (!x) return;
  const width = y1 - y0;
  const phase = spinning ? Math.floor(t * 10) : 0;
  for (let k = 0; k < 3; k++) {
    const y = y0 + ((k * 5 + phase) % width);
    iso.faceX(x, y, y + 0.5, z0, z1, C.goldLo);
  }
  iso.faceX(x, y0, y1, z1 - 0.6, z1, C.gold);
}

/** A company helicopter crosses the top of the tower every so often. */
export function heliPass(buf: PixelBuffer, b: Built, t: number) {
  const period = 34;
  const p = (t % period) / 9;
  if (p > 1) return;
  const x = Math.round(W + 60 - p * (W + 180));
  const y = Math.round(b.towerTop + 60 * S + Math.sin(p * 6) * 4);
  const img = HELI[Math.floor(t * 20) % 4];
  blitAt(buf, img, x, y);
}

export function marker(buf: PixelBuffer, sx: number, sy: number, t: number) {
  const bob = Math.round(Math.sin(t * 4) * S);
  const y = sy + bob;
  const rows = ['bbbbbbbbbbb', '.bbbbbbbbb.', '..bbbbbbb..', '...bbbbb...', '....bbb....', '.....b.....'];
  rows.forEach((r, j) =>
    r.split('').forEach((ch, i) => {
      if (ch === 'b') buf.set(sx - 5 + i, y + j, j === 0 ? C.goldHi : C.gold);
    }),
  );
}
