/**
 * Paper traders. Each archetype has its own entry, exit, hold time and sizing.
 * Every trade carries a short desk note and the rule that fired.
 */
import { PARTNER_NAME } from '../../firm.config';
import { ARCHETYPES } from './archetypes';
import { change1h, ma, maxHist, type CoinState } from './coins';
import { THEME_LABEL, THEMES, type Theme } from './names';
import { SIM } from './params';
import type { Rng } from './prng';
import type { ArchetypeId, Look, Rule, Side, Trade } from './types';

export interface Position {
  coinId: number;
  ticker: string;
  qty: number;
  /** SOL spent, including adds. */
  cost: number;
  entryTick: number;
  adds: number;
  /** Hold limit for this position, in ticks. */
  hold: number;
}

export interface TraderState {
  id: string;
  name: string;
  archetype: ArchetypeId;
  look: Look;
  seed: number;
  status: 'seated' | 'escorted' | 'waiting';
  desk: number | null;
  hiredTick: number;
  leftTick?: number;
  book0: number;
  cash: number;
  positions: Position[];
  strikes: number;
  trades: number;
  wins: number;
  losses: number;
  /** Equity at the last mark. */
  equity: number;
  /** 0..1 */
  risk: number;
  patience: number;
  recent: Trade[];
  /** True for a visitor's own hire; never part of the shared state. */
  local?: boolean;
}

interface Behaviour {
  /** Chance per tick of looking for a new entry. */
  act: number;
  maxPos: number;
  /** Fraction of equity per entry at risk = 0.5. */
  size: number;
  tp: number | null;
  sl: number | null;
  hold: number | null;
}

export const BEHAVIOUR: Record<ArchetypeId, Behaviour> = {
  permabull: { act: 0.18, maxPos: 5, size: 0.16, tp: 1.0, sl: null, hold: 900 },
  trend: { act: 0.3, maxPos: 3, size: 0.2, tp: 0.6, sl: 0.2, hold: 120 },
  dip: { act: 0.22, maxPos: 3, size: 0.18, tp: 0.2, sl: 0.4, hold: 400 },
  sniper: { act: 0.6, maxPos: 3, size: 0.12, tp: 0.5, sl: 0.3, hold: 18 },
  diamond: { act: 0.05, maxPos: 7, size: 0.1, tp: null, sl: null, hold: null },
  fiver: { act: 0.3, maxPos: 3, size: 0.2, tp: 0.05, sl: 0.25, hold: 600 },
  intern: { act: 0.12, maxPos: 4, size: 0.05, tp: null, sl: null, hold: null },
  quant: { act: 0.4, maxPos: 3, size: 0.18, tp: 0.8, sl: 0.25, hold: 240 },
  stops: { act: 0.3, maxPos: 3, size: 0.2, tp: 0.12, sl: 0.06, hold: 120 },
  narrative: { act: 0.2, maxPos: 4, size: 0.15, tp: 0.4, sl: 0.35, hold: 300 },
  averager: { act: 0.1, maxPos: 2, size: 0.1, tp: 0.1, sl: null, hold: null },
  contrarian: { act: 0.15, maxPos: 3, size: 0.16, tp: 0.3, sl: 0.3, hold: 360 },
};

type RuleKey = 'entry' | 'tp' | 'sl' | 'time' | 'signal' | 'delist' | 'add' | 'intern' | 'exit';

const RULES: Record<ArchetypeId, Partial<Record<RuleKey, Rule>> & { entry: Rule }> = {
  permabull: {
    entry: { code: '1.1', text: 'Buy coins that are going up. Sideways counts as about to go up.' },
    tp: { code: '1.4', text: 'Sell at +100%.' },
    time: { code: '1.9', text: 'Close anything held longer than fifteen hours.' },
  },
  trend: {
    entry: { code: '2.1', text: 'Buy the coin that is up the most in the last hour, if it is up at least 25%.' },
    signal: { code: '2.2', text: 'Sell when the hourly change turns negative.' },
    tp: { code: '2.4', text: 'Take profit at +60%.' },
    sl: { code: '2.5', text: 'Stop out at −20%.' },
    time: { code: '2.6', text: 'Close after two hours.' },
  },
  dip: {
    entry: { code: '3.1', text: 'Buy anything 30% or more below its high for the hour.' },
    tp: { code: '3.2', text: 'Sell the bounce at +20%.' },
    sl: { code: '3.3', text: 'Cut it at −40%.' },
    time: { code: '3.5', text: 'If it hasn’t bounced in seven hours, sell.' },
  },
  sniper: {
    entry: { code: '4.1', text: 'Buy within two minutes of a coin going up on the board.' },
    tp: { code: '4.2', text: 'Sell at +50%.' },
    sl: { code: '4.3', text: 'Stop out at −30%.' },
    time: { code: '4.4', text: 'Never hold anything longer than eighteen minutes.' },
  },
  diamond: {
    entry: { code: '5.1', text: 'Buy coins that have been on the board for less than two hours.' },
    delist: { code: '5.9', text: 'Only sell when the coin drops off the board.' },
  },
  fiver: {
    entry: { code: '6.1', text: 'Buy coins moving a little: between −5% and +20% on the hour.' },
    tp: { code: '6.2', text: 'Sell at +5%.' },
    sl: { code: '6.3', text: 'Stop out at −25%.' },
    time: { code: '6.4', text: 'Close after ten hours.' },
  },
  intern: {
    entry: { code: 'INT-1', text: 'Use your judgement.' },
    intern: { code: 'INT-2', text: `Sell when it feels right. If you’re not sure, ask someone (not ${PARTNER_NAME}).` },
  },
  quant: {
    entry: { code: 'Q-1', text: 'Buy when the 5-minute average crosses above the 20-minute average.' },
    signal: { code: 'Q-2', text: 'Sell when it crosses back below.' },
    tp: { code: 'Q-3', text: 'Take profit at +80%.' },
    sl: { code: 'Q-4', text: 'Stop out at −25%.' },
    time: { code: 'Q-5', text: 'Close after four hours.' },
  },
  stops: {
    entry: { code: 'R-1', text: 'Buy coins up more than 10% on the hour, with a stop in straight away.' },
    tp: { code: 'R-2', text: 'Take profit at +12%.' },
    sl: { code: 'R-3', text: 'Hard stop at −6%. No exceptions.' },
    time: { code: 'R-4', text: 'Close after two hours.' },
  },
  narrative: {
    entry: { code: 'N-1', text: 'Buy coins that fit today’s theme.' },
    tp: { code: 'N-2', text: 'Sell at +40%.' },
    sl: { code: 'N-3', text: 'Stop out at −35%.' },
    time: { code: 'N-4', text: 'Close after five hours.' },
  },
  averager: {
    entry: { code: 'A-1', text: 'Buy coins that are down on the hour.' },
    add: { code: 'A-2', text: 'Buy the same again every 20% further down, up to three times.' },
    tp: { code: 'A-3', text: 'Sell everything at +10% on the average price.' },
  },
  contrarian: {
    entry: { code: 'C-1', text: 'Only buy coins no other desk is holding.' },
    tp: { code: 'C-2', text: 'Sell at +30%.' },
    sl: { code: 'C-3', text: 'Stop out at −30%.' },
    time: { code: 'C-4', text: 'Close after six hours.' },
  },
};

/** The standing rules for a method, in the order they're usually applied. */
export function rulesFor(a: ArchetypeId): Rule[] {
  const r = RULES[a];
  const order: RuleKey[] = ['entry', 'add', 'tp', 'sl', 'signal', 'time', 'intern', 'delist'];
  return order.map((k) => r[k]).filter((x): x is Rule => !!x);
}

const DELIST_RULE: Rule = { code: 'F-0', text: 'If a coin drops off the board, close the position at the last price.' };
const ESCORT_RULE: Rule = { code: 'HR-3', text: 'When a trader is let go, everything is closed at market first.' };

const pctText = (v: number) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(0)}%`;

/** A short desk note explaining a buy, from the numbers that triggered it. */
function buyNote(t: TraderState, c: CoinState, ctx: TradeCtx, r: Rng): string {
  const hour = change1h(c);
  const age = ctx.tick - c.listedTick;
  switch (t.archetype) {
    case 'permabull':
      return hour > 20 ? `Up ${pctText(hour)} on the hour and still going.` : `Going up (${pctText(hour)} on the hour).`;
    case 'trend':
      return `Biggest gainer this hour, ${pctText(hour)}.`;
    case 'dip':
      return `${Math.round((1 - c.price / Math.max(c.price, maxHist(c))) * 100)}% below the hour’s high.`;
    case 'sniper':
      return age < 1 ? 'Bought the minute it went up on the board.' : `Bought ${age} min after it went up on the board.`;
    case 'diamond':
      return `New to the board (${age} min). Long hold.`;
    case 'fiver':
      return `Steady, ${pctText(hour)} on the hour.`;
    case 'intern':
      return r.pick(['No reason given.', 'Saw it trending.', 'Asked the next desk.', 'Liked the name.']);
    case 'quant':
      return '5-min average crossed above the 20-min.';
    case 'stops':
      return `Up ${pctText(hour)}. Stop at −${Math.round((params(t).sl ?? 0.06) * 100)}%.`;
    case 'narrative':
      return `Fits today’s theme (${THEME_LABEL[c.theme]}).`;
    case 'averager':
      return `Down ${pctText(hour).slice(1)} on the hour. First buy.`;
    case 'contrarian':
      return 'No other desk holds it.';
  }
}

function sellNote(key: 'tp' | 'sl' | 'time' | 'signal' | 'delist' | 'intern' | 'escort', a: ArchetypeId, r: Rng): string {
  switch (key) {
    case 'tp':
      return 'Hit the profit target.';
    case 'sl':
      return 'Stop-loss hit.';
    case 'time':
      return 'Held as long as the rules allow.';
    case 'signal':
      return a === 'quant' ? 'Averages crossed back.' : 'Hourly change turned negative.';
    case 'delist':
      return 'Dropped off the board. Closed at the last price.';
    case 'intern':
      return r.pick(['Sold. No reason given.', 'Got nervous and sold.', 'Sold after asking around.']);
    case 'escort':
      return 'Closed out on the way out.';
  }
}

export function themeOfDay(seed: number, tick: number): Theme {
  const day = Math.floor(tick / 1440);
  return THEMES[(seed + day) % THEMES.length];
}

export function markEquity(t: TraderState, prices: Map<number, CoinState>): number {
  let v = t.cash;
  for (const p of t.positions) {
    const c = prices.get(p.coinId);
    v += c ? p.qty * c.price : 0;
  }
  t.equity = v;
  return v;
}

export function resultPct(t: TraderState): number {
  return t.book0 > 0 ? (t.equity / t.book0 - 1) * 100 : 0;
}

export interface TradeCtx {
  tick: number;
  /** Epoch ms when this tick's trades become visible. */
  stampBase: number;
  tickMs: number;
  seed: number;
  coins: CoinState[];
  byId: Map<number, CoinState>;
  heldBy: Map<number, number>;
  emit: (t: Trade) => void;
  seq: { n: number };
}

function params(t: TraderState) {
  const b = BEHAVIOUR[t.archetype];
  const r = t.risk;
  const p = t.patience;
  return {
    act: b.act * 0.35,
    maxPos: b.maxPos,
    size: b.size * (0.5 + r),
    tp: b.tp === null ? null : b.tp * (0.5 + p),
    sl: b.sl === null ? null : b.sl * (0.5 + r),
    hold: b.hold === null ? null : Math.max(3, Math.round(b.hold * (0.3 + p * 1.4))),
  };
}

function record(
  t: TraderState,
  ctx: TradeCtx,
  r: Rng,
  side: Side,
  c: CoinState,
  sizeSol: number,
  reason: string,
  rule: Rule,
  pnlPct?: number,
) {
  const trade: Trade = {
    id: `${ctx.tick}.${ctx.seq.n++}`,
    tick: ctx.tick,
    at: ctx.stampBase + Math.floor(r.next() * ctx.tickMs),
    traderId: t.id,
    ticker: c.ticker,
    side,
    sizeSol,
    price: c.price,
    pnlPct,
    reason,
    rule,
    local: t.local || undefined,
  };
  t.trades++;
  t.recent.unshift(trade);
  if (t.recent.length > 5) t.recent.pop();
  ctx.emit(trade);
}

export function buy(t: TraderState, c: CoinState, sol: number, ctx: TradeCtx, r: Rng, rule: Rule, reason: string) {
  if (sol <= 0 || sol > t.cash) return;
  t.cash -= sol;
  const existing = t.positions.find((p) => p.coinId === c.id);
  const cost = SIM.TRADE_COST + (ctx.tick - c.listedTick <= 2 ? SIM.LAUNCH_SLIPPAGE : 0);
  const qty = (sol * (1 - cost)) / c.price;
  if (existing) {
    existing.qty += qty;
    existing.cost += sol;
    existing.adds++;
  } else {
    const hold = params(t).hold;
    t.positions.push({
      coinId: c.id,
      ticker: c.ticker,
      qty,
      cost: sol,
      entryTick: ctx.tick,
      adds: 0,
      hold: hold === null ? 0 : Math.max(3, Math.round(hold * (0.6 + r.next() * 0.8))),
    });
    ctx.heldBy.set(c.id, (ctx.heldBy.get(c.id) ?? 0) + 1);
  }
  if (!t.local) c.everHeld = true;
  record(t, ctx, r, 'BUY', c, sol, reason, rule);
}

export function sell(
  t: TraderState,
  p: Position,
  price: number,
  c: CoinState | undefined,
  ctx: TradeCtx,
  r: Rng,
  rule: Rule,
  reason: string,
) {
  const proceeds = p.qty * price * (1 - SIM.TRADE_COST);
  const pnl = (proceeds / p.cost - 1) * 100;
  t.cash += proceeds;
  t.positions = t.positions.filter((x) => x !== p);
  ctx.heldBy.set(p.coinId, Math.max(0, (ctx.heldBy.get(p.coinId) ?? 1) - 1));
  if (pnl >= 0) t.wins++;
  else t.losses++;
  const coin = c ?? ({ ticker: p.ticker, price } as CoinState);
  record(t, ctx, r, 'SELL', coin, proceeds, reason, rule, pnl);
}

function pickEntry(t: TraderState, ctx: TradeCtx, r: Rng): CoinState | null {
  const held = new Set(t.positions.map((p) => p.coinId));
  const open = ctx.coins.filter((c) => !held.has(c.id) && c.phase !== 'rug');
  if (!open.length) return null;
  const pickFrom = (xs: CoinState[]) => (xs.length ? r.pick(xs) : null);
  switch (t.archetype) {
    case 'permabull':
      return pickFrom(open.filter((c) => c.phase === 'pump' || c.phase === 'run' || change1h(c) > 5));
    case 'trend': {
      let best: CoinState | null = null;
      let bv = 25;
      for (const c of open) {
        const v = change1h(c);
        if (v > bv) {
          bv = v;
          best = c;
        }
      }
      return best;
    }
    case 'dip':
      return pickFrom(open.filter((c) => ctx.tick - c.listedTick > 10 && c.price < maxHist(c) * 0.7));
    case 'sniper':
      return pickFrom(open.filter((c) => ctx.tick - c.listedTick <= 2));
    case 'diamond':
      return pickFrom(open.filter((c) => ctx.tick - c.listedTick < 120));
    case 'fiver':
      return pickFrom(
        open.filter((c) => {
          const v = change1h(c);
          return v > -5 && v < 20;
        }),
      );
    case 'intern':
      return pickFrom(open);
    case 'quant':
      return pickFrom(open.filter((c) => ma(c, 5) > ma(c, 20) && ma(c, 5, 1) <= ma(c, 20, 1)));
    case 'stops':
      return pickFrom(open.filter((c) => change1h(c) > 10));
    case 'narrative': {
      const theme = themeOfDay(ctx.seed, ctx.tick);
      return pickFrom(open.filter((c) => c.theme === theme));
    }
    case 'averager':
      return pickFrom(open.filter((c) => change1h(c) < 0));
    case 'contrarian':
      return pickFrom(open.filter((c) => (ctx.heldBy.get(c.id) ?? 0) === 0));
  }
}

function ruleFor(a: ArchetypeId, key: RuleKey): Rule {
  return RULES[a][key] ?? RULES[a].entry;
}

/** One tick of decisions for one seated trader. */
export function actTrader(t: TraderState, ctx: TradeCtx, r: Rng) {
  const pr = params(t);
  const a = t.archetype;

  // Exits, checked every tick.
  for (const p of [...t.positions]) {
    const c = ctx.byId.get(p.coinId);
    if (!c) continue;
    const value = p.qty * c.price;
    const gain = value / p.cost - 1;
    const age = ctx.tick - p.entryTick;
    let key: 'tp' | 'sl' | 'time' | 'signal' | 'intern' | null = null;

    if (a === 'averager') {
      if (pr.tp !== null && gain >= pr.tp) key = 'tp';
      else if (gain <= -0.2 * (p.adds + 1) && p.adds < 3 && t.cash > p.cost / (p.adds + 1)) {
        buy(t, c, Math.min(t.cash, SIM.MAX_TRADE_SOL, p.cost / (p.adds + 1)), ctx, r, ruleFor(a, 'add'), `Down ${Math.round(-gain * 100)}% from entry. Added.`);
        continue;
      }
    } else if (a === 'intern') {
      if (r.chance(0.02)) key = 'intern';
    } else {
      if (pr.tp !== null && gain >= pr.tp) key = 'tp';
      else if (pr.sl !== null && gain <= -pr.sl) key = 'sl';
      else if (p.hold > 0 && age >= p.hold) key = 'time';
      else if (a === 'trend' && age > 5 && change1h(c) < 0) key = 'signal';
      else if (a === 'quant' && age > 3 && ma(c, 5) < ma(c, 20)) key = 'signal';
    }
    if (key) {
      const rule = key === 'intern' ? ruleFor(a, 'intern') : ruleFor(a, key);
      sell(t, p, c.price, c, ctx, r, rule, sellNote(key, a, r));
    }
  }

  // Entries.
  if (t.positions.length >= pr.maxPos) return;
  if (!r.chance(pr.act)) return;
  const size = Math.min(t.cash, SIM.MAX_TRADE_SOL, t.equity * pr.size * (0.7 + r.next() * 0.6));
  if (size < t.book0 * 0.01) return;
  const c = pickEntry(t, ctx, r);
  if (!c) return;
  buy(t, c, size, ctx, r, ruleFor(a, 'entry'), buyNote(t, c, ctx, r));
}

/** Close a position whose coin left the board. */
export function settleDeparted(t: TraderState, c: CoinState, ctx: TradeCtx, r: Rng) {
  for (const p of [...t.positions]) {
    if (p.coinId !== c.id) continue;
    const rule = t.archetype === 'diamond' ? ruleFor('diamond', 'delist') : DELIST_RULE;
    sell(t, p, c.price, c, ctx, r, rule, sellNote('delist', t.archetype, r));
  }
}

export function liquidate(t: TraderState, ctx: TradeCtx, r: Rng) {
  for (const p of [...t.positions]) {
    const c = ctx.byId.get(p.coinId);
    sell(t, p, c ? c.price : 0, c, ctx, r, ESCORT_RULE, sellNote('escort', t.archetype, r));
  }
}

export function newTrader(
  id: string,
  name: string,
  archetype: ArchetypeId,
  look: Look,
  seed: number,
  book: number,
  opts: Partial<Pick<TraderState, 'risk' | 'patience' | 'local' | 'status'>> = {},
): TraderState {
  const base = ARCHETYPES[archetype];
  return {
    id,
    name,
    archetype,
    look,
    seed,
    status: opts.status ?? 'waiting',
    desk: null,
    hiredTick: -1,
    book0: book,
    cash: book,
    positions: [],
    strikes: 0,
    trades: 0,
    wins: 0,
    losses: 0,
    equity: book,
    risk: opts.risk ?? base.risk,
    patience: opts.patience ?? base.patience,
    recent: [],
    local: opts.local,
  };
}
