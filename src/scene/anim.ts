/**
 * Per-frame paint over the static background. Screens, the lobby ticker and
 * server LEDs are drawn only onto their key colours, so anything standing in
 * front of them keeps covering them.
 */
import type { PixelBuffer } from './buffer';
import { mixColor } from './buffer';
import type { Built, ScreenSpec } from './building';
import { C } from './colors';
import { drawText, textWidth } from './font';
import type { Iso } from './iso';
import { BAY_X, deskSpot, floorZ } from './layout';
import { CAT_SIT, CAT_TAIL, stamp, stampAt } from './props';

export interface TickerItem {
  text: string;
  color: number;
}

export interface SceneData {
  /** Price history to show on each desk's wall screen. */
  deskSeries: Map<number, number[]>;
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

function paintY(buf: PixelBuffer, iso: Iso, y: number, x: number, z: number, key: number, c: number) {
  const sx = Math.floor(iso.sx(x, y));
  const sy = Math.floor(iso.sy(x + 0.5, y, z + 0.5));
  if (buf.get(sx, sy) === key) buf.set(sx, sy, c);
}

function candles(buf: PixelBuffer, iso: Iso, s: ScreenSpec, series: number[] | undefined) {
  const { y, x0, x1, z0, z1 } = s;
  // Faint grid.
  for (let x = x0; x < x1; x++) for (const z of [z0 + 2, z0 + 5]) paintY(buf, iso, y, x, z, C.screen, C.screenGrid);
  if (!series || series.length < 4) {
    // No position: a flat line.
    for (let x = x0 + 1; x < x1 - 1; x++) paintY(buf, iso, y, x, z0 + Math.floor((z1 - z0) / 2), C.screen, C.amberDim);
    return;
  }
  const n = Math.max(1, Math.floor((x1 - x0 - 1) / 3));
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
  const zr = (v: number) => z0 + Math.round(((v - lo) / span) * (z1 - z0 - 1));
  bars.forEach((b, i) => {
    const x = x0 + 1 + i * 3;
    const col = b.c >= b.o ? C.candleUp : C.candleDown;
    for (let z = zr(b.l); z <= zr(b.h); z++) paintY(buf, iso, y, x, z, C.screen, mixColor(col, C.screen, 0.35));
    const top = Math.max(zr(b.o), zr(b.c));
    const bot = Math.min(zr(b.o), zr(b.c));
    for (let z = bot; z <= top; z++) {
      paintY(buf, iso, y, x, z, C.screen, col);
      paintY(buf, iso, y, x + 1, z, C.screen, col);
    }
  });
}

function lineChart(buf: PixelBuffer, iso: Iso, s: ScreenSpec, series: number[] | undefined) {
  const { y, x0, x1, z0, z1 } = s;
  if (!series || series.length < 2) return;
  const w = x1 - x0;
  const lo = Math.min(...series);
  const hi = Math.max(...series);
  const span = hi - lo || 1;
  const col = series[series.length - 1] >= series[0] ? C.candleUp : C.candleDown;
  let prev = -1;
  for (let i = 0; i < w; i++) {
    const v = series[Math.floor((i / (w - 1)) * (series.length - 1))];
    const z = z0 + Math.round(((v - lo) / span) * (z1 - z0 - 1));
    const a = prev < 0 ? z : Math.min(prev, z);
    const b = prev < 0 ? z : Math.max(prev, z);
    for (let zz = a; zz <= b; zz++) paintY(buf, iso, y, x0 + i, zz, C.screen, col);
    prev = z;
  }
}

function crt(buf: PixelBuffer, iso: Iso, s: ScreenSpec, t: number, stale: boolean) {
  const { y, x0, x1, z0, z1 } = s;
  if (stale) {
    const on = Math.floor(t * 2) % 2 === 0;
    for (let x = x0; x < x1; x++) for (let z = z0; z < z1; z++) if (hash(x * 7 + z, Math.floor(t * 8)) > 0.6) paintY(buf, iso, y, x, z, C.screen, mixColor(C.screen, C.steelHi, 0.5));
    if (on) for (let x = x0 + 2; x < x1 - 2; x += 2) paintY(buf, iso, y, x, z0 + 2, C.screen, C.ledRed);
    return;
  }
  const scroll = Math.floor(t * 3);
  for (let z = z0; z < z1; z++) {
    const len = 2 + Math.floor(hash(z + scroll, 3) * (x1 - x0 - 3));
    for (let x = x0 + 1; x < x0 + 1 + len; x++) if ((z - z0) % 2 === 0) paintY(buf, iso, y, x, z, C.screen, C.candleUp);
  }
}

function ticker(buf: PixelBuffer, iso: Iso, b: Built, t: number, items: TickerItem[]) {
  const { y, x0, x1, z1 } = b.ticker;
  if (!items.length) return;
  const gap = 8;
  const widths = items.map((it) => textWidth(it.text) + gap);
  const total = widths.reduce((a, c) => a + c, 0);
  const width = x1 - x0;
  const off = Math.floor(t * 14) % total;
  let cursor = -off;
  for (let rep = 0; rep < 3 && cursor < width; rep++)
    for (let i = 0; i < items.length && cursor < width; i++) {
      const start = cursor;
      if (start + widths[i] > 0)
        drawText(items[i].text, (dx, dy) => {
          const x = start + dx;
          if (x >= 0 && x < width) paintY(buf, iso, y, x0 + x, z1 - 1 - dy, C.amberDim, items[i].color);
        });
      cursor += widths[i];
    }
}

function highlight(buf: PixelBuffer, iso: Iso, desk: number, t: number) {
  const spot = deskSpot(desk);
  if (!spot) return;
  const cx = BAY_X[spot.bay];
  const zf = floorZ(spot.level);
  const c = Math.floor(t * 3) % 2 ? C.brassHi : C.brass;
  const plot = (x: number, y: number) => {
    const [sx, sy] = iso.at(x, y, zf);
    buf.set(sx, sy, c);
  };
  for (let x = cx - 21; x <= cx + 21; x++) {
    plot(x, 0.5);
    plot(x, 23);
  }
  for (let y = 1; y < 23; y++) {
    plot(cx - 21, y);
    plot(cx + 21, y);
  }
}

export function animPass(buf: PixelBuffer, iso: Iso, b: Built, t: number, d: SceneData) {
  for (const s of b.screens) {
    if (s.kind === 'desk') candles(buf, iso, s, d.deskSeries.get(s.desk!));
    else if (s.kind === 'terminal') lineChart(buf, iso, s, d.terminalSeries[s.slot!]);
    else crt(buf, iso, s, t, d.stale);
  }
  ticker(buf, iso, b, t, d.ticker);
  // Server LEDs.
  const step = Math.floor(t * 4);
  b.leds.forEach(([x, y], i) => {
    if (buf.get(x, y) !== C.ledOff) return;
    const r = hash(i, step + (i % 5));
    buf.set(x, y, d.stale ? (r > 0.5 ? C.amber : C.ledOff) : r > 0.97 ? C.ledRed : r > 0.3 ? C.ledGreen : C.ledOff);
  });
  // Coffee steam.
  for (const [sx, sy] of b.steam)
    for (let k = 0; k < 3; k++) {
      const p = (t * 0.7 + k / 3) % 1;
      const wob = Math.round(Math.sin((t + k) * 3) * 1);
      buf.tint(sx + wob, Math.round(sy - p * 10), C.white, 0.7 * (1 - p));
    }
  // Cat on the filing cabinet, tail flicking.
  if (b.cat[0]) {
    const [cx, cy] = b.cat;
    stampAt(buf, CAT_SIT, cx, cy);
    const tail = CAT_TAIL[Math.floor(t / 1.4) % 2];
    stamp(buf, tail, cx - 3, cy - 4);
    if (Math.floor(t * 1.3) % 7 === 0) {
      // Blink.
      buf.set(cx - 2, cy - 5, C.cat);
    }
  }
  // Antenna light.
  if (Math.floor(t * 1.2) % 2 === 0) {
    const [ax, ay] = b.antenna;
    buf.set(ax, ay - 1, C.ledRed);
    buf.tint(ax - 1, ay - 1, C.ledRed, 0.4);
    buf.tint(ax + 1, ay - 1, C.ledRed, 0.4);
  }
  // Pendulum.
  const [px, py] = b.pendulum;
  if (px) {
    const sw = [0, 1, 0, -1][Math.floor(t * 2) % 4];
    buf.set(px + sw, py, C.brass);
    buf.set(px + sw, py - 1, C.brassLo);
  }
  if (d.hotDesk !== null) highlight(buf, iso, d.hotDesk, t);
}

/** Revolving door: the panes turn while someone is going through. Drawn over the front layer. */
export function doorPass(iso: Iso, b: Built, t: number, spinning: boolean) {
  const { x, y0, y1, z0, z1 } = b.door;
  if (!x) return;
  const width = y1 - y0;
  const phase = spinning ? Math.floor(t * 10) : 0;
  for (let k = 0; k < 3; k++) {
    const y = y0 + ((k * 5 + phase) % width);
    for (let z = z0; z < z1; z++) iso.onX(x, y, z, C.brassLo);
  }
  for (let y = y0; y < y1; y++) iso.onX(x, y, z1 - 1, C.brass);
}

export function marker(buf: PixelBuffer, sx: number, sy: number, t: number) {
  const bob = Math.round(Math.sin(t * 4)) ;
  const y = sy + bob;
  const rows = ['bbbbb', '.bbb.', '..b..'];
  rows.forEach((r, j) =>
    r.split('').forEach((ch, i) => {
      if (ch === 'b') buf.set(sx - 2 + i, y + j, j === 0 ? C.brassHi : C.brass);
    }),
  );
}
