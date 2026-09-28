/**
 * Paper traders. Each archetype has its own entry, exit, hold time and sizing.
 * Every trade carries a deadpan reason and the rule that fired. None of it is advice.
 */
import { PARTNER_NAME } from '../../firm.config';
import { ARCHETYPES } from './archetypes';
import { change1h, ma, maxHist, type CoinState } from './coins';
import { THEMES, type Theme } from './names';
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
    entry: { code: '1.1', text: 'If it is going up, buy it. If it is going sideways, it is about to go up.' },
    tp: { code: '1.4', text: 'Sell half of nothing at plus one hundred percent. In practice, sell.' },
    time: { code: '1.9', text: 'After fifteen hours, admit the position has become a personality and close it.' },
  },
  trend: {
    entry: { code: '2.1', text: 'Buy the coin up the most in the last hour, provided it is up at least twenty-five percent.' },
    signal: { code: '2.2', text: 'When the hour turns red, leave. Do not say goodbye.' },
    tp: { code: '2.4', text: 'Take profit at plus sixty. The floor will be talking about something else by then.' },
    sl: { code: '2.5', text: 'Out at minus twenty. Trends are not personal.' },
    time: { code: '2.6', text: 'Two hours is a long time to agree with everyone.' },
  },
  dip: {
    entry: { code: '3.1', text: 'Buy anything thirty percent below its high for the hour. A discount is a discount.' },
    tp: { code: '3.2', text: 'Sell the bounce at plus twenty.' },
    sl: { code: '3.3', text: 'At minus forty, concede that it was not a dip. It was the floor.' },
    time: { code: '3.5', text: 'If the bounce has not come in seven hours, it is not coming.' },
  },
  sniper: {
    entry: { code: '4.1', text: 'Enter any coin within two minutes of listing. Read the name afterwards.' },
    tp: { code: '4.2', text: 'Out at plus fifty. The first minute pays for the rest.' },
    sl: { code: '4.3', text: 'Out at minus thirty. Somebody was faster.' },
    time: { code: '4.4', text: 'Nothing is held past eighteen minutes. Lunch is at noon.' },
  },
  diamond: {
    entry: { code: '5.1', text: 'Buy young coins. Do not sell them.' },
    delist: { code: '5.9', text: 'A position is closed only when the coin is. This is not an exception.' },
  },
  fiver: {
    entry: { code: '6.1', text: 'Buy a coin that is moving, but not so much that anyone has noticed.' },
    tp: { code: '6.2', text: 'Sell at plus five. Do not look at it again.' },
    sl: { code: '6.3', text: 'At minus twenty-five, sell, and have a quiet word with yourself.' },
    time: { code: '6.4', text: 'Ten hours without five percent is a sign.' },
  },
  intern: {
    entry: { code: 'INT-1', text: 'Use judgement.' },
    intern: { code: 'INT-2', text: `Sell when it feels right. Ask someone if unsure. Do not ask ${PARTNER_NAME}.` },
  },
  quant: {
    entry: { code: 'Q-1', text: 'Buy when the five-minute average crosses above the twenty-minute average.' },
    signal: { code: 'Q-2', text: 'Sell when it crosses back. The model does not have feelings, and neither should you.' },
    tp: { code: 'Q-3', text: 'Take profit at plus eighty. The model has never seen this. Nobody has.' },
    sl: { code: 'Q-4', text: 'Out at minus twenty-five. Recalibrate on Monday.' },
    time: { code: 'Q-5', text: 'Four hours is outside the backtest.' },
  },
  stops: {
    entry: { code: 'R-1', text: 'Buy strength above ten percent. Protect it immediately.' },
    tp: { code: 'R-2', text: 'Take plus twelve. Nobody was ever fired for plus twelve.' },
    sl: { code: 'R-3', text: 'Hard stop at minus six. No exceptions, no second looks, no lunch.' },
    time: { code: 'R-4', text: 'Two hours of exposure is plenty of exposure.' },
  },
  narrative: {
    entry: { code: 'N-1', text: 'Buy coins that fit today’s theme. The chart is a detail.' },
    tp: { code: 'N-2', text: 'Sell at plus forty, when the story is fully priced in.' },
    sl: { code: 'N-3', text: 'At minus thirty-five, the story has changed. Change with it.' },
    time: { code: 'N-4', text: 'A story told for five hours is no longer a story.' },
  },
  averager: {
    entry: { code: 'A-1', text: 'Buy a red coin. Red is where the value is.' },
    add: { code: 'A-2', text: 'Every further twenty percent down, buy the same again. Conviction compounds.' },
    tp: { code: 'A-3', text: 'At plus ten on the average, sell everything and mention it at lunch.' },
  },
  contrarian: {
    entry: { code: 'C-1', text: 'Buy only what no one else on the floor owns.' },
    tp: { code: 'C-2', text: 'Sell at plus thirty, ideally while someone else is buying.' },
    sl: { code: 'C-3', text: 'At minus thirty, accept that the room may have had a point.' },
    time: { code: 'C-4', text: 'Six hours alone with a coin is enough.' },
  },
};

/** The standing rules for a method, in the order they're usually applied. */
export function rulesFor(a: ArchetypeId): Rule[] {
  const r = RULES[a];
  const order: RuleKey[] = ['entry', 'add', 'tp', 'sl', 'signal', 'time', 'intern', 'delist'];
  return order.map((k) => r[k]).filter((x): x is Rule => !!x);
}

const DELIST_RULE: Rule = { code: 'F-0', text: 'When a coin leaves the board, the position leaves with it, at whatever the last price was.' };
const ESCORT_RULE: Rule = { code: 'HR-3', text: 'On a third strike, positions are closed at market before the box is handed over.' };

const BUY_REASONS: Record<ArchetypeId, string[]> = {
  permabull: ['Up only. Loaded the boat.', 'Bears are poor. Buying.', 'Sized up. Obviously.', 'This is the bottom. Every price is the bottom.', 'Adding. Tell me when it stops going up.'],
  trend: ['Whole floor is in it. So am I.', 'Top of the board. I only buy winners.', 'Chasing? I prefer "leading".', 'The trend is my friend. My only friend.'],
  dip: ['Blood in the streets. My favourite colour.', 'Down thirty. I call that a sale.', 'You panic, I buy. Circle of life.', 'Caught the knife. With one hand.'],
  sniper: ['In before you blinked.', 'Listed a minute ago. I was here at second four.', "Didn't read the name. Didn't need to.", 'Fastest hands on the floor. Check the tape.'],
  diamond: ['Buying. Selling is for tourists.', 'Long-term position. Very long. Forever.', 'Diamond hands. Look it up.', 'My grandchildren will thank me.'],
  fiver: ['Five percent before your coffee cools.', 'Quick one. Watch this.', "In and out. Nobody's getting hurt."],
  intern: ['Told the desk I had a guy. I do not have a guy.', 'Bought it. Hope that was okay.', 'Saw it trending. Sort of. On my phone.', 'Big day for me.'],
  quant: ['The model says yes. The model is never wrong.', 'Signal fired. Emotions are for retail.', 'Two lines crossed. That is science.'],
  stops: ['Risk managed. Ego intact.', 'In, with a stop tighter than my collar.', 'Calculated. Everything is calculated.'],
  narrative: ["I don't read charts. Charts read me.", 'The story sells itself. So do I.', 'Vibes are immaculate. Buying.', 'Narrative is alpha. Write that down.'],
  averager: ['Buying red. Red is a discount.', 'Starting small. I will not stay small.', 'Conviction, first tranche.'],
  contrarian: ['Everyone hates it. Perfect.', 'The floor is wrong again. Buying.', "I'm early. I'm always early."],
};

const SELL_REASONS: Record<'tp' | 'sl' | 'time' | 'signal' | 'delist' | 'intern' | 'escort', string[]> = {
  tp: ['Printed. Next.', 'Called it. You saw.', "Took profit. You're welcome.", 'Ring the bell.', 'Booked. Drinks on me. Not really.'],
  sl: ['Market is wrong. Leaving anyway.', 'Tactical retreat.', 'Stopped. Irrelevant.', "That wasn't a loss. That was tuition."],
  time: ['Bored. Out.', 'Too slow for this desk.', 'Clock ran out. The chart will regret it.'],
  signal: ['Trend flipped. I flipped first.', 'Model said out. The model is never wrong.', 'Saw it coming. Obviously.'],
  delist: ['Coin died. I did not.', 'Held to the end. Legends do.', "Closed at the last print. It's fine. Totally fine."],
  intern: ['Sold. Was that right?', 'Someone yelled "sell". I think at me.', 'Panicked. Professionally.', 'Took a profit. Or a loss. Checking.'],
  escort: ['Closing on the way out. Still a good trade.', 'Liquidated. Security was very polite.'],
};

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
        buy(t, c, Math.min(t.cash, SIM.MAX_TRADE_SOL, p.cost / (p.adds + 1)), ctx, r, ruleFor(a, 'add'), r.pick(['Down twenty. Added.', 'Averaged down. Again.', 'Conviction, topped up.']));
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
      sell(t, p, c.price, c, ctx, r, rule, r.pick(SELL_REASONS[key]));
    }
  }

  // Entries.
  if (t.positions.length >= pr.maxPos) return;
  if (!r.chance(pr.act)) return;
  const size = Math.min(t.cash, SIM.MAX_TRADE_SOL, t.equity * pr.size * (0.7 + r.next() * 0.6));
  if (size < t.book0 * 0.01) return;
  const c = pickEntry(t, ctx, r);
  if (!c) return;
  buy(t, c, size, ctx, r, ruleFor(a, 'entry'), r.pick(BUY_REASONS[a]));
}

/** Close a position whose coin left the board. */
export function settleDeparted(t: TraderState, c: CoinState, ctx: TradeCtx, r: Rng) {
  for (const p of [...t.positions]) {
    if (p.coinId !== c.id) continue;
    const rule = t.archetype === 'diamond' ? ruleFor('diamond', 'delist') : DELIST_RULE;
    sell(t, p, c.price, c, ctx, r, rule, r.pick(SELL_REASONS.delist));
  }
}

export function liquidate(t: TraderState, ctx: TradeCtx, r: Rng) {
  for (const p of [...t.positions]) {
    const c = ctx.byId.get(p.coinId);
    sell(t, p, c ? c.price : 0, c, ctx, r, ESCORT_RULE, r.pick(SELL_REASONS.escort));
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
