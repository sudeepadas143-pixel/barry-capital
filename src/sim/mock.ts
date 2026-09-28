/**
 * M1 placeholder state. Replaced by the seeded engine in M2.
 */
import { DESK_COUNT } from '../../firm.config';
import type { ArchetypeId, Coin, FirmState, Rule, Trade, Trader } from './types';

const SEATED: [string, ArchetypeId][] = [
  ['whitlock', 'permabull'],
  ['osei', 'trend'],
  ['castellano', 'dip'],
  ['lindqvist', 'sniper'],
  ['marsh', 'diamond'],
  ['adebayo', 'fiver'],
  ['varga', 'intern'],
  ['halloran', 'quant'],
  ['beaumont', 'stops'],
  ['rourke', 'narrative'],
  ['tanaka', 'averager'],
];

const WAITING: [string, ArchetypeId][] = [
  ['pryce', 'contrarian'],
  ['mendes', 'sniper'],
  ['frost', 'fiver'],
];

const RESULTS = [-4.6, 7.9, 0, 0.2, -2.3, -1.7, -0.4, 0, -2.1, 0, 12.4];

const COINS: [string, string][] = [
  ['LOAF', 'Loaf of Cat'],
  ['GRAVY', 'Gravy Train'],
  ['MOTH', 'Moth Lamp'],
  ['PUDDLE', 'Big Puddle'],
  ['SOCKS', 'Lost Socks'],
  ['SPORK', 'Spork Finance'],
  ['KETTLE', 'Kettle'],
  ['HONK', 'Goose Protocol'],
  ['CRUMB', 'Crumb'],
  ['FERN', 'Office Fern'],
  ['CLAMS', 'Clams'],
  ['YAWN', 'Yawn'],
];

const look = (i: number) => ({
  skin: i % 6,
  hair: (i * 3) % 7,
  hairStyle: i % 4,
  suit: (i * 5) % 6,
  tie: (i * 7) % 6,
});

const makeTrader = (
  name: string,
  archetype: ArchetypeId,
  i: number,
  desk: number | null,
  status: Trader['status'],
): Trader => ({
  id: name,
  name,
  desk,
  archetype,
  look: look(i),
  status,
  hiredTick: 0,
  resultPct: desk ? RESULTS[i] ?? 0 : 0,
  pnlSol: desk ? (RESULTS[i] ?? 0) * 0.1 : 0,
  bookSol: 10,
  strikes: desk && (RESULTS[i] ?? 0) < -2 ? 1 : 0,
  openPositions: 2,
  underWater: (RESULTS[i] ?? 0) < 0 ? 1 : 0,
});

const RULES: Rule[] = [
  { code: '4.2', text: 'Buy any coin up forty percent in the hour. Ask no follow-up questions.' },
  { code: '1.1', text: 'Sell at plus five. Do not look at it again.' },
  { code: '7.0', text: 'If the ticker is an animal, the thesis writes itself.' },
  { code: '2.3', text: 'A thirty percent drop is a discount, not a signal.' },
];

const REASONS = [
  'The chart looked like a staircase.',
  'Up five percent. That is the job.',
  'Four-letter ticker. Four is a stable number.',
  'Nobody else on the floor owned it.',
  'Bought the dip. Then the other dip.',
  'Model said yes. The model is two lines.',
];

export function mockState(now: number): FirmState {
  const traders = SEATED.map(([n, a], i) => makeTrader(n, a, i, i + 1, 'seated'));
  const waiting = WAITING.map(([n, a], i) => makeTrader(n, a, i + 20, null, 'waiting'));
  const coins: Coin[] = COINS.map(([ticker, name], i) => ({
    id: ticker,
    ticker,
    name,
    price: 0.00001 * (i + 1),
    change1h: ((i * 37) % 60) - 25,
    phase: 'chop',
    listedTick: 0,
  }));
  const feed: Trade[] = Array.from({ length: 24 }, (_, i) => {
    const t = traders[(i * 5) % DESK_COUNT];
    return {
      id: `m${i}`,
      tick: 1000 - i,
      at: now - (22 + i * 71) * 1000,
      traderId: t.id,
      ticker: COINS[(i * 7) % COINS.length][0],
      side: i % 3 === 0 ? 'SELL' : 'BUY',
      sizeSol: 0.25 + (i % 4) * 0.25,
      price: 0.00002,
      reason: REASONS[i % REASONS.length],
      rule: RULES[i % RULES.length],
    };
  });
  return {
    tick: 1000,
    at: now,
    traders,
    waiting,
    alumni: [],
    coins,
    feed,
    treasurySol: 112.4,
    feesInSol: 3.218,
    shredder: 1307,
    lobby: 412,
    passedOn: 895,
    underWater: 263,
    underReview: 4,
    bonus: { poolSol: 1.84, lastAt: now - 3 * 3600e3, lastPaidSol: 2.1, holders: 1480, nextAt: now + 5 * 3600e3 },
    boardReadAt: now - 60_000,
    feedStale: false,
    partnerFloor: 'lobby',
    nextReviewAt: now + 40 * 60_000,
  };
}
