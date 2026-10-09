/**
 * Keeps a running SimState in step with the clock. Catch-up starts from the
 * latest usable checkpoint: one baked in at build time, a snapshot this browser
 * saved earlier, or an in-memory checkpoint. All paths give identical state.
 */
import { SimulatedPriceSource, type PriceSource } from './coins';
import { genesis, seedFor, step, tickAt, type SimState } from './firm';
import { SIM } from './params';
import { newTrader, type TraderState } from './traders';
import type { ArchetypeId, Look } from './types';

/** What the visitor chose on /hire. Enough to rebuild the trader from scratch. */
export interface HireRecord {
  id: string;
  name: string;
  archetype: ArchetypeId;
  look: Look;
  risk: number;
  patience: number;
  hiredTick: number;
  seed: number;
  /** A public Solana address the visitor chose to build the trader from. Kept in this browser only. */
  wallet?: string;
  /** Set when the trader belongs to an Investor NFT: saved with the hiring desk and locked. */
  investor?: boolean;
}

export function localTrader(h: HireRecord): TraderState {
  const t = newTrader(h.id, h.name, h.archetype, h.look, h.seed, SIM.BOOK_SOL, {
    risk: h.risk,
    patience: h.patience,
    local: true,
    status: 'seated',
  });
  t.hiredTick = h.hiredTick;
  t.desk = null;
  return t;
}

export const clone = (s: SimState): SimState => JSON.parse(JSON.stringify(s));

export interface EngineOpts {
  seasonStart: string;
  tickSeconds: number;
  source?: PriceSource;
  /** Candidate starting points; the latest compatible one with tick <= target wins. */
  bases?: (SimState | null | undefined)[];
  hires?: HireRecord[];
}

export class Engine {
  state: SimState;
  readonly seed: number;
  private source: PriceSource;
  private cps = new Map<number, string>();
  private pending: HireRecord[] = [];
  private seasonStart: string;

  constructor(private opts: EngineOpts) {
    this.seasonStart = opts.seasonStart;
    this.seed = seedFor(opts.seasonStart);
    this.source = opts.source ?? SimulatedPriceSource;
    this.state = genesis(opts.seasonStart, opts.tickSeconds);
    this.saveCheckpoint(this.state);
    let best: SimState | null = null;
    for (const b of opts.bases ?? []) {
      if (!b || !this.compatible(b)) continue;
      this.saveCheckpoint(b);
      if (!best || b.tick > best.tick) best = b;
    }
    if (best) {
      const s = clone(best);
      s.locals ??= [];
      s.localFeed ??= [];
      this.state = s;
    }
    this.pending = [...(opts.hires ?? [])];
  }

  get startMs() {
    return this.state.startMs;
  }
  get tickMs() {
    return this.state.tickMs;
  }

  compatible(b: SimState): boolean {
    return b.v === SIM.VERSION && b.seed === this.seed && b.tickMs === this.opts.tickSeconds * 1000;
  }

  private saveCheckpoint(s: SimState) {
    const bare = { ...s, locals: [], localFeed: [] };
    this.cps.set(s.tick, JSON.stringify(bare));
    if (this.cps.size > 240) {
      const keys = [...this.cps.keys()].sort((a, b) => a - b);
      this.cps.delete(keys[1]); // keep genesis
    }
  }

  private bestCheckpoint(maxTick: number): SimState {
    let best = -Infinity;
    for (const k of this.cps.keys()) if (k <= maxTick && k > best) best = k;
    return best === -Infinity ? genesis(this.seasonStart, this.opts.tickSeconds) : JSON.parse(this.cps.get(best)!);
  }

  /** Current tick for a wall-clock time. */
  tickFor(now: number): number {
    return tickAt(this.state.startMs, this.state.tickMs, now);
  }

  /** Advance (or rebuild) to `target`. */
  advanceTo(target: number) {
    const hires = this.pending;
    // A hire from before our current point needs a replay from before it was made.
    const earliestMissing = hires
      .filter((h) => !this.state.locals.some((l) => l.id === h.id))
      .reduce((m, h) => Math.min(m, h.hiredTick), Infinity);
    let s = this.state;
    if (s.tick > target || earliestMissing <= s.tick) {
      const from = Math.min(target, earliestMissing - 1);
      s = this.bestCheckpoint(from);
      // Carry over hires that were already running before that point: rebuilt below.
      s.locals = [];
      s.localFeed = [];
    }
    const want = new Map(hires.map((h) => [h.id, h]));
    for (const l of s.locals) want.delete(l.id);
    // Hires whose start is already behind us (e.g. a restored snapshot) join now.
    for (const h of [...want.values()]) {
      if (h.hiredTick <= s.tick) {
        s.locals.push(localTrader({ ...h, hiredTick: Math.max(h.hiredTick, s.tick) }));
        want.delete(h.id);
      }
    }
    while (s.tick < target) {
      const next = s.tick + 1;
      for (const h of [...want.values()]) {
        if (h.hiredTick === next) {
          s.locals.push(localTrader(h));
          want.delete(h.id);
        }
      }
      step(s, this.source);
      if (s.tick % SIM.CHECKPOINT_EVERY === 0) this.saveCheckpoint(s);
    }
    this.state = s;
  }

  advanceToTime(now: number) {
    this.advanceTo(Math.max(-1, this.tickFor(now)));
  }

  setHires(hires: HireRecord[]) {
    this.pending = [...hires];
    const ids = new Set(hires.map((h) => h.id));
    const before = this.state.locals.length;
    this.state.locals = this.state.locals.filter((l) => ids.has(l.id));
    if (this.state.locals.length !== before) {
      this.state.localFeed = this.state.localFeed.filter((f) => f.type !== 'trade' || ids.has(f.traderId));
    }
    this.advanceTo(this.state.tick);
  }

  snapshot(): string {
    return JSON.stringify(this.state);
  }
}
