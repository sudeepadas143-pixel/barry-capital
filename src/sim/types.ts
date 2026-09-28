/**
 * The shape of the firm at a given tick. The UI only ever reads this.
 * M1 fills it with mock data; M2 computes it from (SEASON_START, tick).
 */

export type ArchetypeId =
  | 'permabull'
  | 'trend'
  | 'dip'
  | 'sniper'
  | 'diamond'
  | 'fiver'
  | 'intern'
  | 'quant'
  | 'stops'
  | 'narrative'
  | 'averager'
  | 'contrarian';

export interface Archetype {
  id: ArchetypeId;
  /** Short title, lower case: "the perma-bull". */
  title: string;
  /** One deadpan sentence. */
  blurb: string;
  /** 0..1 */
  risk: number;
  /** 0..1, how long it holds. */
  patience: number;
}

export interface Look {
  skin: number;
  hair: number;
  hairStyle: number;
  suit: number;
  tie: number;
}

export type CoinPhase = 'launch' | 'pump' | 'chop' | 'bleed' | 'run' | 'rug' | 'delisted';

export interface Coin {
  id: string;
  ticker: string;
  name: string;
  price: number;
  /** Percent change over the last hour of ticks. */
  change1h: number;
  phase: CoinPhase;
  listedTick: number;
  /** Recent prices, oldest first. */
  hist: number[];
  holders: number;
}

export type Side = 'BUY' | 'SELL';

export interface Rule {
  code: string;
  text: string;
}

export interface Trade {
  id: string;
  tick: number;
  /** Epoch ms. */
  at: number;
  traderId: string;
  ticker: string;
  side: Side;
  sizeSol: number;
  price: number;
  /** Realised result for sells, percent. */
  pnlPct?: number;
  reason: string;
  rule: Rule;
  /** A visitor's own hire; only ever shown in that browser. */
  local?: boolean;
}

export type EventKind = 'escorted' | 'hired' | 'bonus' | 'review' | 'stale' | 'rug';

export interface FirmEvent {
  id: string;
  kind: EventKind;
  tick: number;
  at: number;
  text: string;
  traderId?: string;
}

export type FeedItem = ({ type: 'trade' } & Trade) | ({ type: 'event' } & FirmEvent);

export type TraderStatus = 'seated' | 'escorted' | 'waiting';

export interface Trader {
  id: string;
  name: string;
  /** 1..DESK_COUNT when seated. */
  desk: number | null;
  archetype: ArchetypeId;
  look: Look;
  status: TraderStatus;
  hiredTick: number;
  /** Season result, percent of starting book. */
  resultPct: number;
  /** Profit and loss in SOL. */
  pnlSol: number;
  bookSol: number;
  /** Consecutive reviews below the line. */
  strikes: number;
  openPositions: number;
  underWater: number;
  trades: number;
  wins: number;
  losses: number;
  leftTick?: number;
  risk: number;
  patience: number;
  recent: Trade[];
  local?: boolean;
}

export interface BonusDay {
  poolSol: number;
  lastAt: number | null;
  lastPaidSol: number;
  lastHolders: number;
  totalPaidSol: number;
  days: number;
  holders: number;
  nextAt: number;
}

export type FloorId = 'office' | 'terminal' | 'compliance' | 'hr' | 'server' | 'lobby';

export interface FirmState {
  tick: number;
  at: number;
  traders: Trader[];
  /** Trader ids in line for the next vacant desk. */
  waiting: Trader[];
  /** Traders who have left the building, newest first. */
  alumni: Trader[];
  coins: Coin[];
  /** Newest first. Trades and firm events. */
  feed: FeedItem[];
  treasurySol: number;
  feesInSol: number;
  shredder: number;
  lobby: number;
  passedOn: number;
  underWater: number;
  underReview: number;
  bonus: BonusDay;
  /** Epoch ms of the last board read. */
  boardReadAt: number;
  feedStale: boolean;
  partnerFloor: FloorId | 'review';
  nextReviewAt: number;
  lastReviewAt: number | null;
  theme: string;
  season: { start: number; tick: number; seed: number };
  /** This visitor's own hires. */
  mine: Trader[];
  counts: { fired: number; hired: number; bonusDays: number; listed: number; pitched: number; outages: number; lastOutageAt: number | null };
}
