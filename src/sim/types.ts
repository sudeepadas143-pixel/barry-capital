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
}

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
}

export interface BonusDay {
  poolSol: number;
  lastAt: number | null;
  lastPaidSol: number;
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
  /** Newest first. */
  feed: Trade[];
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
  partnerFloor: FloorId;
  nextReviewAt: number;
}
