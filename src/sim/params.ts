/**
 * Simulation tuning. Changing any of these changes the whole season's history,
 * so bump VERSION when you do (it invalidates cached snapshots).
 */
export const SIM = {
  VERSION: 11,

  /** Firm capital at the start of the season, SOL. */
  TREASURY_START_SOL: 100,
  /** Each desk's paper book on hire, SOL. */
  BOOK_SOL: 5,
  /** Largest single paper trade, SOL. Memecoin liquidity is thin. */
  MAX_TRADE_SOL: 2,
  /** Swap fee plus slippage, charged on every buy and sell. */
  TRADE_COST: 0.01,
  /** Extra slippage for buying in a coin's first two minutes, when everyone else is too. */
  LAUNCH_SLIPPAGE: 0.03,

  /** Coins on the board. */
  BOARD_TARGET: 16,
  BOARD_MAX: 20,
  /** Price history kept per coin, in ticks. Also the "1h" window at 60s ticks. */
  HISTORY: 60,
  /** Coins go quiet after this many ticks if nothing else happened. */
  MAX_COIN_AGE: 2880,
  WARMUP_TICKS: 240,

  /** Performance reviews. */
  REVIEW_EVERY: 60,
  REVIEW_LINE_PCT: -35,
  /** New hires skip reviews for this many ticks. */
  REVIEW_GRACE: 180,
  STRIKES_TO_FIRE: 3,
  /** Desk sits empty while it's cleaned. */
  VACANT_TICKS: 4,
  WAITING_LEN: 5,

  /** Bonus day: share of profit above the high-water mark moved into the pool at each review, paid out daily. */
  BONUS_SHARE: 0.2,
  BONUS_EVERY: 1440,

  /** The firm's own token: simulated volume per tick and the creator fee rate. */
  TOKEN_VOLUME_MEAN_SOL: 9,
  CREATOR_FEE_RATE: 0.001,

  /** Chance per tick that the price feed goes stale. */
  OUTAGE_P: 0.0015,

  FEED_KEEP: 120,
  ALUMNI_KEEP: 24,
  CHECKPOINT_EVERY: 1000,
} as const;
