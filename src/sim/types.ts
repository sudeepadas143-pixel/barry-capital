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
  /** Optional detail; filled in by `dress()` when missing. */
  build?: number;
  height?: number;
  /** Facial hair: 0 none, 1 stubble, 2 beard, 3 moustache, 4 goatee. */
  face?: number;
  /** 0 suit, 1 pinstripe, 2 fleece vest, 3 shirtsleeves and braces, 4 waistcoat, 5 turtleneck and blazer, 6 double-breasted. */
  outfit?: number;
  shirt?: number;
  /** 0 tie, 1 loosened, 2 bow tie, 3 open collar, 4 lanyard. */
  neck?: number;
  /** 0 none, 1 sunglasses, 2 glasses, 3 headset, 4 earpiece. */
  eyes?: number;
  watch?: boolean;
  cigar?: boolean;
  fem?: boolean;
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
  /** Place on the board among desks up for review, 1 = best. Undefined while new. */
  rank?: number;
  /** Bottom of the board: this trader goes at the next review if nothing changes. */
  nextOut?: boolean;
  /** Tick of this trader's first review, while they're still new. */
  firstReviewTick?: number;
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
  /** Desks up for review at the next one. */
  reviewed: number;
  /** Bottom of the board right now: goes at the next review if nothing changes. */
  nextOutId?: string;
  topId?: string;
  lastReviewAt: number | null;
  theme: string;
  season: { start: number; tick: number; seed: number };
  /** This visitor's own hires. */
  mine: Trader[];
  counts: { fired: number; hired: number; bonusDays: number; listed: number; pitched: number; outages: number; lastOutageAt: number | null };
}
