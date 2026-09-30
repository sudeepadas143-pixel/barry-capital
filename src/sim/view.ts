/**
 * Turns simulation state into what the page reads. Items stamped after `now`
 * are held back, so each minute's trades trickle into the feed as it passes.
 */
import { change1h } from './coins';
import { dress } from '../art/traits';
import { THEME_LABEL } from './names';
import { SIM } from './params';
import { holderCount } from './payout';
import { mix } from './prng';
import { resultPct, themeOfDay, type TraderState } from './traders';
import { rankForReview, treasury, type SimState } from './firm';
import type { Coin, FeedItem, FirmState, FloorId, Trader } from './types';

const ROTATION: FloorId[] = ['office', 'terminal', 'compliance', 'hr', 'lobby', 'terminal', 'lobby'];

export function toTrader(t: TraderState, s: SimState): Trader {
  const byId = new Map(s.board.coins.map((c) => [c.id, c]));
  let underWater = 0;
  for (const p of t.positions) {
    const c = byId.get(p.coinId);
    if (c && p.qty * c.price < p.cost) underWater++;
  }
  return {
    id: t.id,
    name: t.name,
    desk: t.desk,
    archetype: t.archetype,
    look: dress(t.look, t.archetype, t.seed, t.local ? undefined : t.name),
    status: t.status,
    hiredTick: t.hiredTick,
    resultPct: resultPct(t),
    pnlSol: t.equity - t.book0,
    bookSol: t.equity,
    openPositions: t.positions.length,
    underWater,
    trades: t.trades,
    wins: t.wins,
    losses: t.losses,
    leftTick: t.leftTick,
    risk: t.risk,
    patience: t.patience,
    recent: t.recent,
    local: t.local,
  };
}

/** Next tick index `k` (> tick) where (k + 1) is a multiple of `every`. */
function nextBoundary(tick: number, every: number): number {
  return (Math.floor((tick + 1) / every) + 1) * every - 1;
}

export function toView(s: SimState, now: number): FirmState {
  const T = s.tickMs;
  const endOf = (tick: number) => s.startMs + (tick + 1) * T;
  // Who'd go if the next review happened now, and where everyone stands.
  const reviewTick = nextBoundary(s.tick, SIM.REVIEW_EVERY);
  const ranked = rankForReview(s.traders, reviewTick);
  const rankOf = new Map(ranked.map((t, i) => [t.id, i + 1]));
  const nextOut = ranked.length >= SIM.REVIEW_MIN ? ranked[ranked.length - 1].id : undefined;
  const traders = s.traders.map((t) => {
    const v = toTrader(t, s);
    v.rank = rankOf.get(t.id);
    v.nextOut = t.id === nextOut || undefined;
    if (v.rank === undefined && !t.local && t.hiredTick >= 0) {
      // First review: the first boundary at least REVIEW_GRACE ticks after hire.
      let k = nextBoundary(t.hiredTick + SIM.REVIEW_GRACE - 1, SIM.REVIEW_EVERY);
      if (k - t.hiredTick < SIM.REVIEW_GRACE) k += SIM.REVIEW_EVERY;
      v.firstReviewTick = k;
    }
    return v;
  });
  const holders = new Map<number, number>();
  for (const t of s.traders) for (const p of t.positions) holders.set(p.coinId, (holders.get(p.coinId) ?? 0) + 1);

  const coins: Coin[] = s.board.coins.map((c) => ({
    id: String(c.id),
    ticker: c.ticker,
    name: c.name,
    price: c.price,
    change1h: change1h(c),
    phase: c.phase,
    listedTick: c.listedTick,
    hist: c.hist,
    holders: holders.get(c.id) ?? 0,
  }));

  const feed: FeedItem[] = [];
  for (const f of s.feed) if (f.at <= now) feed.push(f);
  for (const f of s.localFeed) if (f.at <= now) feed.push(f);
  feed.sort((a, b) => b.at - a.at);

  const recentFrom = s.tick - 15;
  let underReview = 0;
  for (const f of s.feed) {
    if (f.type !== 'trade' || f.tick < recentFrom) continue;
    if ((f.side === 'SELL' && (f.pnlPct ?? 0) < -20) || f.sizeSol > SIM.BOOK_SOL * 0.25) underReview++;
  }

  const underWater = traders.reduce((n, t) => n + t.underWater, 0);
  const stale = s.outageLeft > 0;
  const tick = s.tick;
  let partnerFloor: FirmState['partnerFloor'];
  if (stale) partnerFloor = 'server';
  else if (tick >= 0 && (tick + 1) % SIM.REVIEW_EVERY < 3 && s.c.lastReviewTick >= 0) partnerFloor = 'review';
  else if (s.c.lastBonusTick >= 0 && tick - s.c.lastBonusTick < 10) partnerFloor = 'office';
  else partnerFloor = ROTATION[mix(s.seed, Math.floor(Math.max(0, tick) / 7)) % ROTATION.length];

  return {
    tick,
    at: now,
    traders,
    waiting: s.waiting.map((t) => toTrader(t, s)),
    alumni: s.alumni.map((t) => toTrader(t, s)),
    coins,
    feed,
    treasurySol: treasury(s),
    feesInSol: s.c.feesIn,
    shredder: s.c.passedOn + s.c.ruggedUnheld,
    lobby: s.c.lobby,
    passedOn: s.c.passedOn,
    underWater,
    underReview,
    bonus: {
      poolSol: s.c.pool,
      lastAt: s.c.lastBonusTick >= 0 ? endOf(s.c.lastBonusTick) : null,
      lastPaidSol: s.c.lastBonusPaid,
      lastHolders: s.c.lastBonusHolders,
      totalPaidSol: s.c.bonusPaid,
      days: s.c.bonusDays,
      holders: holderCount(s.seed, Math.max(0, tick)),
      nextAt: endOf(nextBoundary(tick, SIM.BONUS_EVERY)),
    },
    boardReadAt: s.lastReadTick >= 0 ? endOf(s.lastReadTick) : s.startMs,
    feedStale: stale,
    partnerFloor,
    nextReviewAt: endOf(nextBoundary(tick, SIM.REVIEW_EVERY)),
    reviewed: ranked.length,
    nextOutId: nextOut,
    topId: ranked[0]?.id,
    lastReviewAt: s.c.lastReviewTick >= 0 ? endOf(s.c.lastReviewTick) : null,
    theme: THEME_LABEL[themeOfDay(s.seed, Math.max(0, tick))],
    season: { start: s.startMs, tick, seed: s.seed },
    mine: s.locals.map((t) => toTrader(t, s)),
    counts: {
      fired: s.c.fired,
      hired: s.c.hired,
      bonusDays: s.c.bonusDays,
      listed: s.c.listed,
      pitched: s.c.pitched,
      outages: s.c.outages,
      lastOutageAt: s.c.lastOutageTick >= 0 ? endOf(s.c.lastOutageTick) : null,
    },
  };
}
