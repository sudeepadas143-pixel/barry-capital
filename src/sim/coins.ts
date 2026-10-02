/**
 * The coin board. Each coin is listed with a seeded fate and walks through
 * launch → pump → chop → (bleed | run | rug). Returns are fat-tailed.
 */
import { SIM } from './params';
import { COINS, THEME_NOUN, type Theme } from './names';
import type { Rng } from './prng';
import type { CoinPhase } from './types';

export type Fate = 'bleed' | 'run' | 'rug';

export interface CoinState {
  id: number;
  ticker: string;
  name: string;
  theme: Theme;
  price: number;
  ath: number;
  /** Last HISTORY prices, oldest first; the current price is the last entry. */
  hist: number[];
  phase: CoinPhase;
  phaseLeft: number;
  /** Per-tick drift for the current phase, drawn when the phase starts. */
  drift: number;
  fate: Fate;
  listedTick: number;
  /** True once any trader has held it. */
  everHeld: boolean;
  /** Set when the coin has left the board. */
  delistedTick?: number;
}

export interface BoardState {
  coins: CoinState[];
  nextId: number;
  /** Coins that left the board this tick (for the engine to settle positions). */
  departed: CoinState[];
  /** Coins that rugged this tick. */
  rugged: CoinState[];
}

/**
 * Where prices come from. The default is fully simulated and deterministic.
 * A live implementation would overwrite prices from a read-only quote feed;
 * it must never place orders or hold keys.
 */
export interface PriceSource {
  readonly id: string;
  step(board: BoardState, tick: number, rng: Rng): void;
}

interface PhaseSpec {
  /** Drift is drawn uniformly from this range when the phase starts. */
  drift: [number, number];
  vol: number;
  len: [number, number];
}

const PHASES: Record<Exclude<CoinPhase, 'delisted'>, PhaseSpec> = {
  launch: { drift: [-0.06, 0.05], vol: 0.09, len: [2, 6] },
  pump: { drift: [0.004, 0.025], vol: 0.065, len: [6, 40] },
  chop: { drift: [-0.001, 0.002], vol: 0.045, len: [40, 300] },
  bleed: { drift: [-0.0015, -0.0004], vol: 0.03, len: [300, 1200] },
  run: { drift: [0.003, 0.015], vol: 0.055, len: [10, 80] },
  rug: { drift: [-0.03, -0.01], vol: 0.04, len: [3, 8] },
};

function rollFate(r: Rng): Fate {
  const u = r.next();
  return u < 0.5 ? 'bleed' : u < 0.7 ? 'run' : 'rug';
}

function enter(c: CoinState, p: Exclude<CoinPhase, 'delisted'>, r: Rng) {
  const spec = PHASES[p];
  c.phase = p;
  c.phaseLeft = spec.len[0] + r.int(spec.len[1] - spec.len[0] + 1);
  c.drift = spec.drift[0] + (spec.drift[1] - spec.drift[0]) * r.next();
}

export function newCoin(board: BoardState, tick: number, r: Rng): CoinState {
  const taken = new Set(board.coins.map((c) => c.ticker));
  const free = COINS.filter((c) => !taken.has(c.ticker));
  const pick = free.length ? r.pick(free) : r.pick(COINS);
  const ticker = free.length ? pick.ticker : `${pick.ticker.slice(0, 6)}${board.nextId % 100}`;
  const theme = pick.theme;
  const price = 0.00001 * (0.4 + r.next() * 3);
  const hist: number[] = [];
  for (let i = 0; i < SIM.HISTORY; i++) hist.push(price);
  const c: CoinState = {
    id: board.nextId++,
    ticker,
    name: THEME_NOUN[pick.theme],
    theme,
    price,
    ath: price,
    hist,
    phase: 'launch',
    phaseLeft: 0,
    drift: 0,
    fate: rollFate(r),
    listedTick: tick,
    everHeld: false,
  };
  enter(c, 'launch', r);
  return c;
}

function nextPhase(c: CoinState, r: Rng) {
  switch (c.phase) {
    case 'launch':
      // About a third of launches get a pump.
      enter(c, r.chance(0.35) ? 'pump' : 'chop', r);
      return;
    case 'pump':
      enter(c, 'chop', r);
      return;
    case 'chop':
      enter(c, c.fate, r);
      if (c.fate === 'rug') c.price *= 0.05 + r.next() * 0.15; // an 80–95% drop in one tick
      return;
    case 'run':
      c.fate = r.chance(0.55) ? 'bleed' : 'rug';
      enter(c, 'chop', r);
      return;
    case 'bleed':
    case 'rug':
      c.phase = 'delisted';
      return;
  }
}

export function stepCoin(c: CoinState, tick: number, r: Rng) {
  if (c.phase === 'delisted') return;
  const spec = PHASES[c.phase];
  // Surprise rugs can happen at any point before the coin has settled.
  if ((c.phase === 'pump' || c.phase === 'chop') && r.chance(0.0003)) {
    c.fate = 'rug';
    c.phase = 'chop';
    c.phaseLeft = 0;
  }
  const shock = r.fat(0.035);
  // Offset volatility drag so a phase's drift is roughly its compounded direction.
  const ret = c.drift + 0.64 * spec.vol * spec.vol + spec.vol * shock;
  c.price *= Math.max(0.05, 1 + Math.max(-0.6, Math.min(2.5, ret)));
  if (c.price > c.ath) c.ath = c.price;
  c.phaseLeft -= 1;
  if (c.phaseLeft <= 0) nextPhase(c, r);
  if (c.phase === 'bleed' && c.price < c.ath * 0.08) c.phase = 'delisted';
  if (tick - c.listedTick > SIM.MAX_COIN_AGE) c.phase = 'delisted';
  c.hist.push(c.price);
  if (c.hist.length > SIM.HISTORY) c.hist.shift();
}

export const SimulatedPriceSource: PriceSource = {
  id: 'simulated',
  step(board, tick, r) {
    board.departed = [];
    board.rugged = [];
    for (const c of board.coins) {
      const before = c.phase;
      stepCoin(c, tick, r);
      if (c.phase === 'rug' && before !== 'rug') board.rugged.push(c);
    }
    const stay: CoinState[] = [];
    for (const c of board.coins) {
      if (c.phase === 'delisted') {
        c.delistedTick = tick;
        board.departed.push(c);
      } else stay.push(c);
    }
    board.coins = stay;
  },
};

/** Percent change across the kept history window. */
export function change1h(c: CoinState): number {
  const first = c.hist[0];
  return first > 0 ? (c.price / first - 1) * 100 : 0;
}

export function maxHist(c: CoinState): number {
  let m = 0;
  for (const p of c.hist) if (p > m) m = p;
  return m;
}

export function ma(c: CoinState, n: number, offset = 0): number {
  const end = c.hist.length - offset;
  const start = Math.max(0, end - n);
  let s = 0;
  for (let i = start; i < end; i++) s += c.hist[i];
  return s / Math.max(1, end - start);
}
