/**
 * Per-frame paint over the static layers: charts on every screen, the LED
 * tickers, server lights, steam, the cat, the helicopter and the hover marker.
 * Each screen is drawn clipped to its own glass.
 */
import { mixColor } from './buffer';
import { ssFor, type Built, type ScreenSpec } from './building';
import { C } from './colors';
import type { Iso } from './iso';
import { BAY_X, S, W, X, Y, deskSpot, floorZ } from './layout';
import { renderCat, renderHeli } from '../art/props';
import type { Pt, SpriteSrc, Surface, TextOpts } from './surface';

const CAT: SpriteSrc[] = [0, 1, 2, 3].map((i) => ({
  id: `cat:${i}`,
  render: (k) => renderCat(i >> 1, !!(i & 1), S * k, ssFor(S * k)),
}));
const HELI: SpriteSrc[] = [0, 1, 2, 3].map((f) => ({ id: `heli:${f}`, render: (k) => renderHeli(f, S * k, ssFor(S * k)) }));

export interface TickerItem {
  text: string;
  color: number;
}

export interface SceneData {
  /** Changes whenever the charts need redrawing (the sim tick). */
  version?: number;
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

/** Maps chart space (u left to right as seen on screen, z up) onto a screen's plane. */
type Map2 = (u: number, z: number) => Pt;

function planeOf(iso: Iso, s: ScreenSpec): { at: Map2; u0: number; u1: number; quad: Pt[] } {
  if (s.plane === 'x') {
    const x = s.x!;
    // On an x-plane, left to right on screen runs toward smaller y.
    const at: Map2 = (u, z) => iso.p(x, s.x1 - (u - s.x0), z);
    return { at, u0: s.x0, u1: s.x1, quad: iso.quadX(x, s.x0, s.x1, s.z0, s.z1) };
  }
  const at: Map2 = (u, z) => iso.p(u, s.y, z);
  return { at, u0: s.x0, u1: s.x1, quad: iso.quadY(s.y, s.x0, s.x1, s.z0, s.z1) };
}

function box(buf: Surface, at: Map2, u0: number, u1: number, z0: number, z1: number, c: number, alpha = 1) {
  buf.poly([at(u0, z1), at(u1, z1), at(u1, z0), at(u0, z0)], c, alpha);
}

/** A polyline of the given thickness (in plane units), as one quad per segment. */
function line(buf: Surface, at: Map2, pts: [number, number][], th: number, c: number) {
  for (let i = 0; i < pts.length - 1; i++) {
    const [u0, z0] = pts[i];
    const [u1, z1] = pts[i + 1];
    buf.poly([at(u0, z0 + th / 2), at(u1, z1 + th / 2), at(u1, z1 - th / 2), at(u0, z0 - th / 2)], c);
  }
}

function candles(buf: Surface, iso: Iso, s: ScreenSpec, series: number[] | undefined) {
  const { at, u0, u1, quad } = planeOf(iso, s);
  const { z0, z1 } = s;
  const h = z1 - z0;
  buf.clip(quad, () => {
    for (const f of [0.25, 0.5, 0.75]) box(buf, at, u0, u1, z0 + h * f, z0 + h * f + 0.12, C.screenGrid);
    if (!series || series.length < 4) {
      box(buf, at, u0 + 0.6, u1 - 0.6, z0 + h / 2, z0 + h / 2 + 0.3, C.amberDim);
      return;
    }
    const step = 0.9;
    const n = Math.max(1, Math.floor((u1 - u0 - 0.8) / step));
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
    const zr = (v: number) => z0 + 0.8 + ((v - lo) / span) * (h - 1.8);
    bars.forEach((b, i) => {
      const x = u0 + 0.5 + i * step;
      const col = b.c >= b.o ? C.candleUp : C.candleDown;
      box(buf, at, x + 0.26, x + 0.38, zr(b.l), zr(b.h), mixColor(col, C.screen, 0.25));
      const top = Math.max(zr(b.o), zr(b.c));
      const bot = Math.min(zr(b.o), zr(b.c));
      box(buf, at, x, x + 0.64, bot, Math.max(top, bot + 0.22), col);
    });
    // Last price, dashed, with a tag.
    const last = zr(series[series.length - 1]);
    for (let u = u0; u < u1; u += 0.9) box(buf, at, u, Math.min(u1, u + 0.5), last - 0.06, last + 0.06, mixColor(C.amber, C.screen, 0.2));
    box(buf, at, u1 - 2.2, u1, last - 0.55, last + 0.55, C.amber);
  });
}

function lineChart(buf: Surface, iso: Iso, s: ScreenSpec, series: number[] | undefined) {
  if (!series || series.length < 2) return;
  const { at, u0, u1, quad } = planeOf(iso, s);
  const { z0, z1 } = s;
  const lo = Math.min(...series);
  const hi = Math.max(...series);
  const span = hi - lo || 1;
  const col = series[series.length - 1] >= series[0] ? C.candleUp : C.candleDown;
  const n = Math.min(series.length, Math.max(8, Math.floor((u1 - u0) * 1.6)));
  const pts: [number, number][] = [];
  for (let i = 0; i < n; i++) {
    const v = series[Math.floor((i / (n - 1)) * (series.length - 1))];
    pts.push([u0 + 0.3 + (i / (n - 1)) * (u1 - u0 - 0.6), z0 + 0.8 + ((v - lo) / span) * (z1 - z0 - 1.8)]);
  }
  buf.clip(quad, () => {
    box(buf, at, u0, u1, z0 + (z1 - z0) / 2, z0 + (z1 - z0) / 2 + 0.1, C.screenGrid);
    // Area under the line, then the line.
    buf.poly([...pts.map(([u, z]) => at(u, z)), at(pts[pts.length - 1][0], z0), at(pts[0][0], z0)], col, 0.18);
    line(buf, at, pts, 0.32, col);
  });
}

function crt(buf: Surface, iso: Iso, s: ScreenSpec, t: number, stale: boolean) {
  const { at, quad } = planeOf(iso, s);
  const { x0, x1, z0, z1 } = s;
  buf.clip(quad, () => {
    if (stale) {
      for (let k = 0; k < 40; k++) {
        const x = x0 + hash(k, Math.floor(t * 8)) * (x1 - x0 - 0.4);
        const z = z0 + hash(k + 99, Math.floor(t * 8)) * (z1 - z0 - 0.4);
        box(buf, at, x, x + 0.35, z, z + 0.35, mixColor(C.screen, C.steelHi, 0.5));
      }
      if (Math.floor(t * 2) % 2 === 0) box(buf, at, x0 + 1, x1 - 1, z0 + 2.4, z0 + 3.1, C.ledRed);
      return;
    }
    const scroll = Math.floor(t * 3);
    for (let r = 0; r < 6; r++) {
      const len = 1 + hash(r + scroll, 3) * (x1 - x0 - 2.5);
      box(buf, at, x0 + 0.8, x0 + 0.8 + len, z1 - 1 - r * 0.9, z1 - 0.62 - r * 0.9, C.candleUp);
    }
  });
}

/** Scrolling text along a y-plane strip. `offset` is in world units. */
function scrollText(buf: Surface, iso: Iso, y: number, x0: number, x1: number, z0: number, z1: number, items: TickerItem[], offset: number, size: number) {
  if (!items.length) return;
  const opts = (c: number): TextOpts => ({ font: 'mono', size, color: c, weight: 600 });
  const gap = size * 1.6;
  const base0 = z0 + (z1 - z0 - size * 0.72) / 2;
  if (buf.ticker) {
    let done = false;
    buf.clip(iso.quadY(y, x0, x1, z0, z1), () => {
      done = buf.ticker!(items, opts(0), gap, iso.planeY(y, x0, base0), offset, x1 - x0);
    });
    if (done) return;
  }
  const widths = items.map((it) => buf.measure(it.text, opts(it.color)) + gap);
  const total = widths.reduce((a, c) => a + c, 0);
  const width = x1 - x0;
  let cursor = -(((offset % total) + total) % total);
  const base = base0;
  buf.clip(iso.quadY(y, x0, x1, z0, z1), () => {
    for (let rep = 0; rep < 6 && cursor < width; rep++)
      for (let i = 0; i < items.length && cursor < width; i++) {
        if (cursor + widths[i] > 0) iso.textY(y, x0 + cursor, base, items[i].text, opts(items[i].color));
        cursor += widths[i];
      }
  });
}

function highlight(iso: Iso, desk: number, t: number) {
  const spot = deskSpot(desk);
  if (!spot) return;
  const cx = BAY_X[spot.bay];
  const zf = floorZ(spot.level);
  const a = 0.55 + 0.35 * Math.sin(t * 5);
  const w = 0.5;
  iso.top(cx - 21, 0.6, cx + 21, 23, zf, C.gold, 0.12);
  iso.top(cx - 21, 0.6, cx + 21, 0.6 + w, zf, C.gold, a);
  iso.top(cx - 21, 23 - w, cx + 21, 23, zf, C.gold, a);
  iso.top(cx - 21, 0.6, cx - 21 + w, 23, zf, C.gold, a);
  iso.top(cx + 21 - w, 0.6, cx + 21, 23, zf, C.gold, a);
}

/** Everything that moves on the background layer (drawn before seated traders). */
export function animPass(buf: Surface, iso: Iso, b: Built, t: number, d: SceneData) {
  for (const s of b.screens) if (s.kind === 'crt') crt(buf, iso, s, t, d.stale);
  // The security desk's ticker and the LED strip along every floor.
  const tk = b.ticker;
  scrollText(buf, iso, tk.y, tk.x0, tk.x1, tk.z0, tk.z1, d.ticker, t * 7, 4);
  b.bands.forEach((band, i) => {
    const rot = d.ticker.length ? [...d.ticker.slice((i * 3) % d.ticker.length), ...d.ticker.slice(0, (i * 3) % d.ticker.length)] : [];
    scrollText(buf, iso, Y, -5, X, band.z0, band.z0 + 4.1, rot, t * (7 + (i % 3) * 1.5) + i * 37, 3.6);
  });
  // Server LEDs.
  const step = Math.floor(t * 4);
  b.leds.forEach((quad, i) => {
    const r = hash(i, step + (i % 5));
    const c = d.stale ? (r > 0.5 ? C.amber : C.ledOff) : r > 0.97 ? C.ledRed : r > 0.3 ? C.ledGreen : C.ledOff;
    buf.poly(quad, c);
  });
  // Espresso steam.
  for (const [sx, sy] of b.steam)
    for (let k = 0; k < 5; k++) {
      const p = (t * 0.6 + k / 5) % 1;
      const wob = Math.sin((t + k) * 3) * S;
      buf.ellipse(sx + wob, sy - p * 12 * S, (0.8 + p * 1.2) * S, (0.6 + p) * S, C.white, 0.45 * (1 - p));
    }
  // The HR cat.
  if (b.cat[0]) {
    const tail = Math.floor(t / 1.4) % 2;
    const blink = Math.floor(t * 1.3) % 7 === 0;
    buf.sprite(CAT[tail * 2 + (blink ? 1 : 0)], b.cat[0], b.cat[1]);
  }
  if (d.hotDesk !== null) highlight(iso, d.hotDesk, t);
}

/** Wall and terminal charts. They only change with the data, so the renderer caches them. */
export function wallCharts(buf: Surface, iso: Iso, b: Built, d: SceneData) {
  for (const s of b.screens) {
    if (s.kind === 'desk') candles(buf, iso, s, d.deskSeries.get(s.desk!));
    else if (s.kind === 'terminal') lineChart(buf, iso, s, d.terminalSeries[s.slot!]);
  }
}

/** Screens that sit on the desks themselves (drawn after the desk layer). */
export function deskScreens(buf: Surface, iso: Iso, b: Built, d: SceneData) {
  for (const s of b.screens) if (s.kind === 'side') lineChart(buf, iso, s, d.sideSeries?.get(s.desk!) ?? d.deskSeries.get(s.desk!));
}

/** Revolving door: the panes turn while someone is going through. Drawn over the front layer. */
export function doorPass(iso: Iso, b: Built, t: number, spinning: boolean) {
  const { x, y0, y1, z0, z1 } = b.door;
  if (!x) return;
  const width = y1 - y0;
  const phase = spinning ? (t * 10) % width : 0;
  for (let k = 0; k < 3; k++) {
    const y = y0 + ((k * 5 + phase) % width);
    iso.faceX(x, y, y + 0.4, z0, z1, C.goldLo);
  }
  iso.faceX(x, y0, y1, z1 - 0.6, z1, C.gold);
}

/** A company helicopter crosses the top of the tower every so often. */
export function heliPass(buf: Surface, b: Built, t: number) {
  const period = 34;
  const p = (t % period) / 9;
  if (p > 1) return;
  const x = W + 60 - p * (W + 180);
  const y = b.towerTop + 60 * S + Math.sin(p * 6) * 4;
  buf.sprite(HELI[Math.floor(t * 20) % 4], x, y);
}

export function marker(buf: Surface, sx: number, sy: number, t: number) {
  const y = sy + Math.sin(t * 4) * S;
  const w = 4.5 * S;
  buf.poly([[sx - w, y], [sx + w, y], [sx, y + 1.7 * w]], C.gold);
  buf.poly([[sx - w, y], [sx + w, y], [sx + w * 0.8, y + 0.9], [sx - w * 0.8, y + 0.9]], C.goldHi);
}
