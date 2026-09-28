/**
 * The firm. `step` advances one tick. State is plain JSON so it can be
 * checkpointed; the same (seed, tick) always yields the same state.
 */
import { DESK_COUNT, PARTNER_NAME, TICK_SECONDS } from '../../firm.config';
import { SimulatedPriceSource, newCoin, type BoardState, type CoinState, type PriceSource } from './coins';
import { STARTING_ROSTER, SURNAMES } from './names';
import { SIM } from './params';
import { holderCount } from './payout';
import { hashString, mix, rng, tickRng, type Rng } from './prng';
import {
  actTrader,
  liquidate,
  markEquity,
  newTrader,
  resultPct,
  settleDeparted,
  type TradeCtx,
  type TraderState,
} from './traders';
import { ARCHETYPE_IDS } from './archetypes';
import type { EventKind, FeedItem, Look, Trade } from './types';

export interface Counters {
  lobby: number;
  passedOn: number;
  ruggedUnheld: number;
  pitched: number;
  listed: number;
  feesIn: number;
  retiredPnl: number;
  pooled: number;
  pool: number;
  bonusPaid: number;
  bonusDays: number;
  lastBonusTick: number;
  lastBonusPaid: number;
  lastReviewTick: number;
  /** High-water mark for the bonus pool. */
  lastReviewTreasury: number;
  fired: number;
  hired: number;
  outages: number;
  lastOutageTick: number;
  lastBonusHolders: number;
}

export interface SimState {
  v: number;
  seed: number;
  startMs: number;
  tickMs: number;
  /** Last completed tick. -1 means nothing has happened yet. */
  tick: number;
  board: BoardState;
  traders: TraderState[];
  waiting: TraderState[];
  alumni: TraderState[];
  vacant: { desk: number; until: number }[];
  feed: FeedItem[];
  c: Counters;
  outageLeft: number;
  lastReadTick: number;
  nameCursor: number;
  /** Client-only hires. Never read by the shared simulation. */
  locals: TraderState[];
  localFeed: FeedItem[];
}

export const seedFor = (seasonStart: string) => hashString(`${seasonStart}|v${SIM.VERSION}`);

function randomLook(r: Rng): Look {
  return { skin: r.int(6), hair: r.int(7), hairStyle: r.int(4), suit: r.int(6), tie: r.int(6) };
}

function lookKey(l: Look) {
  return `${l.skin}${l.hair}${l.hairStyle}${l.suit}`;
}

function nextName(s: SimState, r: Rng): string {
  const inUse = new Set([...s.traders, ...s.waiting, ...s.alumni].map((t) => t.name));
  for (let i = 0; i < SURNAMES.length; i++) {
    const n = SURNAMES[(s.nameCursor + r.int(SURNAMES.length)) % SURNAMES.length];
    if (!inUse.has(n)) {
      s.nameCursor++;
      return n;
    }
  }
  s.nameCursor++;
  return `${SURNAMES[s.nameCursor % SURNAMES.length]} ii`;
}

function candidate(s: SimState, r: Rng): TraderState {
  const name = nextName(s, r);
  // HR prefers methods the floor doesn't already have.
  const count = new Map<string, number>();
  for (const t of [...s.traders, ...s.waiting]) count.set(t.archetype, (count.get(t.archetype) ?? 0) + 1);
  const weights = ARCHETYPE_IDS.map((a) => {
    const n = 1 + (count.get(a) ?? 0);
    return 1 / (n * n);
  });
  const total = weights.reduce((x, y) => x + y, 0);
  let u = r.next() * total;
  let arch = ARCHETYPE_IDS[ARCHETYPE_IDS.length - 1];
  for (let i = 0; i < weights.length; i++) {
    u -= weights[i];
    if (u < 0) {
      arch = ARCHETYPE_IDS[i];
      break;
    }
  }
  return newTrader(`${name}-${s.c.hired + s.waiting.length + s.alumni.length}-${s.tick + 1}`, name, arch, randomLook(r), r.int(0x7fffffff), SIM.BOOK_SOL);
}

export function genesis(seasonStart: string, tickSeconds = TICK_SECONDS): SimState {
  const seed = seedFor(seasonStart);
  const r = rng(mix(seed, 0xfeed));
  const s: SimState = {
    v: SIM.VERSION,
    seed,
    startMs: Date.parse(seasonStart),
    tickMs: tickSeconds * 1000,
    tick: -1,
    board: { coins: [], nextId: 1, departed: [], rugged: [] },
    traders: [],
    waiting: [],
    alumni: [],
    vacant: [],
    feed: [],
    c: {
      lobby: 30,
      passedOn: 0,
      ruggedUnheld: 0,
      pitched: 30,
      listed: 0,
      feesIn: 0,
      retiredPnl: 0,
      pooled: 0,
      pool: 0,
      bonusPaid: 0,
      bonusDays: 0,
      lastBonusTick: -1,
      lastBonusPaid: 0,
      lastReviewTick: -1,
      lastReviewTreasury: SIM.TREASURY_START_SOL,
      fired: 0,
      hired: 0,
      outages: 0,
      lastOutageTick: -1,
      lastBonusHolders: 0,
    },
    outageLeft: 0,
    lastReadTick: -1,
    nameCursor: r.int(SURNAMES.length),
    locals: [],
    localFeed: [],
  };

  // Warm the board up so the first minute of the season isn't eleven coins at launch price.
  const w = rng(mix(seed, 0xa11));
  for (let i = 0; i < SIM.BOARD_TARGET; i++) {
    const c = newCoin(s.board, -SIM.WARMUP_TICKS + i * 12, w);
    c.everHeld = true; // warm-up coins don't count toward the shredder
    s.board.coins.push(c);
  }
  for (let t = -SIM.WARMUP_TICKS; t < 0; t++) {
    SimulatedPriceSource.step(s.board, t, w);
    while (s.board.coins.length < SIM.BOARD_TARGET) {
      const c = newCoin(s.board, t, w);
      c.everHeld = true;
      s.board.coins.push(c);
    }
  }
  s.board.departed = [];
  s.board.rugged = [];

  const used = new Set<string>();
  STARTING_ROSTER.slice(0, DESK_COUNT).forEach(([name, arch], i) => {
    let look = randomLook(r);
    while (used.has(lookKey(look))) look = randomLook(r);
    used.add(lookKey(look));
    const t = newTrader(name, name, arch, look, r.int(0x7fffffff), SIM.BOOK_SOL, { status: 'seated' });
    t.desk = i + 1;
    t.hiredTick = 0;
    s.traders.push(t);
  });
  // Any extra desks beyond the starting roster are filled from the line.
  for (let d = s.traders.length + 1; d <= DESK_COUNT; d++) {
    const t = candidate(s, r);
    t.status = 'seated';
    t.desk = d;
    t.hiredTick = 0;
    s.traders.push(t);
  }
  while (s.waiting.length < SIM.WAITING_LEN) s.waiting.push(candidate(s, r));
  return s;
}

export function treasury(s: SimState): number {
  let open = 0;
  for (const t of s.traders) open += t.equity - t.book0;
  return SIM.TREASURY_START_SOL + s.c.feesIn + s.c.retiredPnl + open - s.c.pooled;
}

const S = {
  coins: 1,
  lobby: 2,
  events: 3,
  fees: 4,
  outage: 5,
  hr: 6,
};

function pushFeed(list: FeedItem[], items: FeedItem[], keep: number) {
  if (!items.length) return;
  items.sort((a, b) => b.at - a.at);
  list.unshift(...items);
  if (list.length > keep) list.length = keep;
}

export function step(s: SimState, source: PriceSource = SimulatedPriceSource): SimState {
  const tick = s.tick + 1;
  s.tick = tick;
  const stampBase = s.startMs + (tick + 1) * s.tickMs;
  const out: FeedItem[] = [];
  const localOut: FeedItem[] = [];
  const er = tickRng(s.seed, tick, S.events);
  let evSeq = 0;
  const event = (kind: EventKind, text: string, traderId?: string) =>
    out.push({
      type: 'event',
      id: `${tick}.e${evSeq++}`,
      kind,
      tick,
      at: stampBase + Math.floor(er.next() * s.tickMs * 0.5),
      text,
      traderId,
    });

  // The feed goes stale now and then; the board doesn't move while it is.
  const or = tickRng(s.seed, tick, S.outage);
  if (s.outageLeft > 0) s.outageLeft--;
  else if (or.chance(SIM.OUTAGE_P)) {
    s.outageLeft = 3 + or.int(7);
    s.c.outages++;
    s.c.lastOutageTick = tick;
    event('stale', `The board went quiet. ${PARTNER_NAME} has gone down to the server room.`);
  }
  const stale = s.outageLeft > 0;

  if (!stale) {
    source.step(s.board, tick, tickRng(s.seed, tick, S.coins));
    s.lastReadTick = tick;
  } else {
    s.board.departed = [];
    s.board.rugged = [];
  }

  // The lobby: pitches arrive, most are passed on, a few are listed.
  const lr = tickRng(s.seed, tick, S.lobby);
  const arrivals = (lr.chance(0.55) ? 1 : 0) + (lr.chance(0.3) ? 1 : 0) + (lr.chance(0.08) ? 1 : 0);
  s.c.lobby += arrivals;
  s.c.pitched += arrivals;
  const passes = (lr.chance(Math.min(0.9, s.c.lobby * 0.02)) ? 1 : 0) + (lr.chance(Math.min(0.5, s.c.lobby * 0.006)) ? 1 : 0);
  const passed = Math.min(passes, s.c.lobby);
  s.c.lobby -= passed;
  s.c.passedOn += passed;
  if (!stale && s.c.lobby > 0 && s.board.coins.length < SIM.BOARD_MAX && lr.chance(s.board.coins.length < SIM.BOARD_TARGET ? 0.5 : 0.04)) {
    s.board.coins.push(newCoin(s.board, tick, lr));
    s.c.lobby--;
    s.c.listed++;
  }

  const byId = new Map<number, CoinState>();
  for (const c of s.board.coins) byId.set(c.id, c);
  for (const c of s.board.departed) byId.set(c.id, c);

  const heldBy = new Map<number, number>();
  for (const t of s.traders) for (const p of t.positions) heldBy.set(p.coinId, (heldBy.get(p.coinId) ?? 0) + 1);

  const seq = { n: 0 };
  const ctx: TradeCtx = {
    tick,
    stampBase,
    tickMs: s.tickMs,
    seed: s.seed,
    coins: s.board.coins,
    byId,
    heldBy,
    seq,
    emit: (t: Trade) => out.push({ type: 'trade', ...t }),
  };

  for (const c of s.board.rugged) {
    const drop = c.hist.length > 1 ? (1 - c.price / c.hist[c.hist.length - 2]) * 100 : 0;
    if (heldBy.get(c.id)) event('rug', `$${c.ticker} fell ${Math.round(drop)}% in a minute. Compliance has been informed.`);
  }

  // Coins that left the board settle at their last price.
  for (const c of s.board.departed) {
    if (!c.everHeld && c.fate === 'rug') s.c.ruggedUnheld++;
    for (const t of s.traders) {
      settleDeparted(t, c, ctx, tickRng(s.seed, tick, t.seed));
    }
  }

  if (!stale) {
    for (const t of s.traders) actTrader(t, ctx, tickRng(s.seed, tick, t.seed));
  }
  for (const t of s.traders) markEquity(t, byId);

  // Refill desks that have finished being cleaned.
  const hr = tickRng(s.seed, tick, S.hr);
  s.vacant = s.vacant.filter((v) => {
    if (v.until > tick) return true;
    const t = s.waiting.shift() ?? candidate(s, hr);
    t.status = 'seated';
    t.desk = v.desk;
    t.hiredTick = tick;
    t.book0 = SIM.BOOK_SOL;
    t.cash = SIM.BOOK_SOL;
    t.equity = SIM.BOOK_SOL;
    s.traders.push(t);
    s.traders.sort((a, b) => (a.desk ?? 0) - (b.desk ?? 0));
    s.c.hired++;
    event('hired', `${t.name} took desk ${String(v.desk).padStart(2, '0')}. Welcome aboard.`, t.id);
    while (s.waiting.length < SIM.WAITING_LEN) s.waiting.push(candidate(s, hr));
    return false;
  });

  // Performance reviews, on the hour.
  if ((tick + 1) % SIM.REVIEW_EVERY === 0) {
    const below: string[] = [];
    const leaving: TraderState[] = [];
    for (const t of s.traders) {
      if (tick - t.hiredTick < SIM.REVIEW_GRACE) continue;
      if (resultPct(t) < SIM.REVIEW_LINE_PCT) {
        t.strikes++;
        below.push(t.name);
        if (t.strikes >= SIM.STRIKES_TO_FIRE) leaving.push(t);
      } else t.strikes = 0;
    }
    for (const t of leaving) {
      liquidate(t, ctx, tickRng(s.seed, tick, t.seed));
      markEquity(t, byId);
      s.c.retiredPnl += t.equity - t.book0;
      t.status = 'escorted';
      t.leftTick = tick;
      s.vacant.push({ desk: t.desk!, until: tick + SIM.VACANT_TICKS });
      s.traders = s.traders.filter((x) => x !== t);
      s.alumni.unshift(t);
      s.c.fired++;
      event('escorted', `${t.name} was escorted out with a box. Desk ${String(t.desk).padStart(2, '0')} is being cleaned.`, t.id);
    }
    if (s.alumni.length > SIM.ALUMNI_KEEP) s.alumni.length = SIM.ALUMNI_KEEP;
    if (below.length && !leaving.length) {
      event('review', below.length === 1 ? `Reviews done. ${below[0]} is below the line.` : `Reviews done. ${below.length} below the line.`);
    }
    // A share of profit above the high-water mark goes into the bonus pool.
    const profit = treasury(s) - s.c.lastReviewTreasury;
    if (profit > 0) {
      const share = profit * SIM.BONUS_SHARE;
      s.c.pool += share;
      s.c.pooled += share;
      s.c.lastReviewTreasury = treasury(s);
    }
    s.c.lastReviewTick = tick;
  }

  // Bonus day.
  if ((tick + 1) % SIM.BONUS_EVERY === 0 && s.c.pool > 0) {
    const holders = holderCount(s.seed, tick);
    const paid = s.c.pool;
    s.c.bonusPaid += paid;
    s.c.lastBonusPaid = paid;
    s.c.lastBonusTick = tick;
    s.c.lastBonusHolders = holders;
    s.c.bonusDays++;
    s.c.pool = 0;
    event('bonus', `Bonus day. ${paid.toFixed(3)} SOL split across ${groupThousands(holders)} holders.`);
  }

  // Creator fees from the firm's own token, simulated.
  const fr = tickRng(s.seed, tick, S.fees);
  const volume = SIM.TOKEN_VOLUME_MEAN_SOL * (0.2 + 1.6 * fr.next()) * (fr.chance(0.02) ? 4 : 1);
  s.c.feesIn += volume * SIM.CREATOR_FEE_RATE;

  // Visitor hires run against the same board, never touching shared state.
  if (s.locals.length) {
    const lctx: TradeCtx = {
      ...ctx,
      heldBy: new Map(heldBy),
      emit: (t: Trade) => localOut.push({ type: 'trade', ...t }),
    };
    for (const t of s.locals) {
      if (t.hiredTick > tick) continue;
      for (const c of s.board.departed) settleDeparted(t, c, lctx, tickRng(t.seed, tick, 1));
      if (!stale && t.hiredTick < tick) actTrader(t, lctx, tickRng(t.seed, tick, 2));
      markEquity(t, byId);
    }
  }

  pushFeed(s.feed, out, SIM.FEED_KEEP);
  pushFeed(s.localFeed, localOut, 40);
  return s;
}

function groupThousands(n: number): string {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

export function tickAt(startMs: number, tickMs: number, now: number): number {
  return Math.floor((now - startMs) / tickMs) - 1;
}
