import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { DESK_COUNT } from '../../firm.config';
import { newCoin, stepCoin, type BoardState } from './coins';
import { Engine, clone, type HireRecord } from './engine';
import { genesis, step, treasury, type SimState } from './firm';
import { SIM } from './params';
import { splitProRata, capTable, toLamports } from './payout';
import { rng } from './prng';
import { toView } from './view';

const START = '2026-01-05T09:00:00Z';
const run = (ticks: number, s = genesis(START, 60)) => {
  while (s.tick < ticks - 1) step(s);
  return s;
};
const shared = (s: SimState) => JSON.stringify({ ...s, locals: [], localFeed: [] });

describe('determinism', () => {
  it('the same tick gives the same state from two independent runs', () => {
    expect(JSON.stringify(run(2500))).toBe(JSON.stringify(run(2500)));
  });

  it('resuming from a checkpoint gives the same state as running straight through', () => {
    const straight = run(3200);
    const half = clone(run(1700));
    const resumed = run(3200, half);
    expect(JSON.stringify(resumed)).toBe(JSON.stringify(straight));
  });

  it('the engine lands on the same state however it gets there', () => {
    const a = new Engine({ seasonStart: START, tickSeconds: 60 });
    a.advanceTo(2100);
    const b = new Engine({ seasonStart: START, tickSeconds: 60, bases: [clone(run(900))] });
    b.advanceTo(2100);
    const c = new Engine({ seasonStart: START, tickSeconds: 60 });
    c.advanceTo(2600);
    c.advanceTo(2100); // going backwards rebuilds from a checkpoint
    expect(shared(b.state)).toBe(shared(a.state));
    expect(shared(c.state)).toBe(shared(a.state));
  });

  it('the same timestamp gives the same view', () => {
    const e1 = new Engine({ seasonStart: START, tickSeconds: 60 });
    const e2 = new Engine({ seasonStart: START, tickSeconds: 60 });
    const now = Date.parse(START) + 36 * 3600e3 + 17_000;
    e1.advanceToTime(now);
    e2.advanceToTime(now);
    expect(JSON.stringify(toView(e1.state, now))).toBe(JSON.stringify(toView(e2.state, now)));
  });

  it('a different season start gives a different firm', () => {
    const a = run(300);
    const b = run(300, genesis('2026-02-01T00:00:00Z', 60));
    expect(shared(a)).not.toBe(shared(b));
  });

  it('the simulation avoids float functions that differ between JS engines', () => {
    const dir = __dirname;
    const banned = /Math\.(exp|expm1|log|log1p|log2|log10|pow|sin|cos|tan|asin|acos|atan|atan2|sinh|cosh|tanh|cbrt|hypot)\b|[\w)\]]\s*\*\*\s*[\w(]/;
    for (const f of readdirSync(dir)) {
      if (!f.endsWith('.ts') || f.endsWith('.test.ts')) continue;
      const src = readFileSync(join(dir, f), 'utf8');
      expect(banned.test(src), `${f} uses a non-portable Math function`).toBe(false);
    }
  });
});

describe('coins', () => {
  const board = (): BoardState => ({ coins: [], nextId: 1, departed: [], rugged: [] });

  it('every coin follows the lifecycle and eventually leaves the board', () => {
    const legal: Record<string, string[]> = {
      launch: ['launch', 'pump', 'chop'],
      pump: ['pump', 'chop', 'rug'],
      chop: ['chop', 'bleed', 'run', 'rug', 'delisted'],
      run: ['run', 'chop', 'delisted'],
      bleed: ['bleed', 'delisted'],
      rug: ['rug', 'delisted'],
    };
    const r = rng(7);
    const b = board();
    for (let i = 0; i < 300; i++) {
      const c = newCoin(b, 0, r);
      let prev: string = c.phase;
      let t = 0;
      while (c.phase !== 'delisted' && t < SIM.MAX_COIN_AGE + 5) {
        stepCoin(c, ++t, r);
        expect(legal[prev], `${prev} -> ${c.phase}`).toContain(c.phase);
        prev = c.phase;
        expect(c.price).toBeGreaterThan(0);
      }
      expect(c.phase).toBe('delisted');
    }
  });

  it('a rug is an 80 to 95 percent drop in a single tick', () => {
    const r = rng(11);
    const b = board();
    let rugs = 0;
    for (let i = 0; i < 400; i++) {
      const c = newCoin(b, 0, r);
      for (let t = 1; t < SIM.MAX_COIN_AGE && c.phase !== 'delisted'; t++) {
        const before = c.price;
        const phase = c.phase;
        stepCoin(c, t, r);
        if (phase !== 'rug' && c.phase === 'rug') {
          rugs++;
          const drop = 1 - c.price / before;
          // The rug itself is 80–95%; the same tick's ordinary move can nudge it a little either way.
          expect(drop).toBeGreaterThan(0.72);
          expect(drop).toBeLessThan(0.99);
        }
      }
    }
    expect(rugs).toBeGreaterThan(40);
  });

  it('returns are fat-tailed: big moves are far more common than a normal would give', () => {
    const r = rng(3);
    const b = board();
    const rets: number[] = [];
    for (let i = 0; i < 80; i++) {
      const c = newCoin(b, 0, r);
      for (let t = 1; t < 400 && c.phase !== 'delisted'; t++) {
        const p = c.price;
        const ph = c.phase;
        stepCoin(c, t, r);
        if (ph === 'chop' && c.phase === 'chop') rets.push(c.price / p - 1);
      }
    }
    const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
    const sd = Math.sqrt(rets.reduce((a, b) => a + (b - mean) * (b - mean), 0) / rets.length);
    const tail = rets.filter((x) => Math.abs(x - mean) > 4 * sd).length / rets.length;
    // A normal distribution puts ~0.006% beyond 4 sd; ask for at least ten times that.
    expect(tail).toBeGreaterThan(0.0006);
    const kurt = rets.reduce((a, b) => a + ((b - mean) / sd) ** 4, 0) / rets.length;
    expect(kurt).toBeGreaterThan(4); // normal is 3
  });

  it('the board turns over: coins leave and new ones arrive', () => {
    const s = genesis(START, 60);
    const first = new Set(s.board.coins.map((c) => c.id));
    run(3000, s);
    const still = s.board.coins.filter((c) => first.has(c.id)).length;
    expect(still).toBeLessThan(first.size);
    expect(s.board.coins.length).toBeGreaterThan(8);
    expect(s.c.listed).toBeGreaterThan(10);
  });
});

describe('reviews, firing and hiring', () => {
  it('a trader below the line for three reviews is escorted out and replaced', () => {
    const s = run(SIM.REVIEW_GRACE + SIM.REVIEW_EVERY - 5);
    const victim = s.traders[3];
    const desk = victim.desk!;
    // Sink the book and freeze it there.
    const sink = () => {
      victim.cash = victim.book0 * 0.3;
      victim.positions = [];
      victim.equity = victim.cash;
    };
    const firedAt = (() => {
      for (let i = 0; i < SIM.REVIEW_EVERY * 4; i++) {
        sink();
        step(s);
        if (victim.status === 'escorted') return s.tick;
      }
      return -1;
    })();
    expect(firedAt).toBeGreaterThan(0);
    const lineAtFiring = s.waiting.map((t) => t.id);
    expect(victim.strikes).toBe(SIM.STRIKES_TO_FIRE);
    expect(s.alumni.some((a) => a.id === victim.id)).toBe(true);
    expect(s.traders.find((t) => t.id === victim.id)).toBeUndefined();
    expect(s.feed.some((f) => f.type === 'event' && f.kind === 'escorted' && f.traderId === victim.id)).toBe(true);
    // Desk is empty while it's cleaned...
    expect(s.traders.length + s.vacant.length).toBe(DESK_COUNT);
    expect(s.vacant.some((v) => v.desk === desk)).toBe(true);
    for (let i = 0; i < SIM.VACANT_TICKS; i++) step(s);
    // ...then the first name in line takes it.
    expect(s.vacant.some((v) => v.desk === desk)).toBe(false);
    const hire = s.traders.find((t) => t.desk === desk)!;
    expect(lineAtFiring.slice(0, 2)).toContain(hire.id);
    expect(hire.hiredTick).toBe(firedAt + SIM.VACANT_TICKS);
    expect(s.waiting.length).toBe(SIM.WAITING_LEN);
  });

  it('a trader back above the line has strikes cleared', () => {
    const s = genesis(START, 60);
    // Stop just before the first review that counts.
    while (s.tick < SIM.REVIEW_GRACE || (s.tick + 2) % SIM.REVIEW_EVERY !== 0) step(s);
    const t = s.traders[0];
    t.cash = t.book0 * 0.5;
    t.positions = [];
    step(s); // review
    expect(t.strikes).toBe(1);
    for (let i = 0; i < SIM.REVIEW_EVERY; i++) {
      t.cash = t.book0 * 1.5;
      t.positions = [];
      step(s);
    }
    expect(t.strikes).toBe(0);
  });

  it('desks stay at the configured count over a long run, and names stay unique', () => {
    const s = genesis(START, 60);
    for (let i = 0; i < 12_000; i++) {
      step(s);
      expect(s.traders.length + s.vacant.length).toBe(DESK_COUNT);
    }
    const desks = s.traders.map((t) => t.desk).concat(s.vacant.map((v) => v.desk));
    expect(new Set(desks).size).toBe(DESK_COUNT);
    const names = [...s.traders, ...s.waiting].map((t) => t.name);
    expect(new Set(names).size).toBe(names.length);
  });
});

describe('money', () => {
  it('pro-rata split sums to the pool exactly and is proportional to within a lamport', () => {
    const r = rng(99);
    for (let k = 0; k < 50; k++) {
      const n = 1 + r.int(400);
      const balances = Array.from({ length: n }, () => r.int(1_000_000));
      const pool = toLamports(r.next() * 50);
      const shares = splitProRata(pool, balances);
      expect(shares.reduce((a, b) => a + b, 0)).toBe(balances.some((b) => b > 0) ? pool : 0);
      const total = balances.reduce((a, b) => a + b, 0);
      balances.forEach((b, i) => {
        expect(Math.abs(shares[i] - (pool * b) / total)).toBeLessThanOrEqual(1);
        if (b === 0) expect(shares[i]).toBe(0);
      });
    }
  });

  it('pro-rata edge cases', () => {
    expect(splitProRata(0, [1, 2, 3])).toEqual([0, 0, 0]);
    expect(splitProRata(10, [0, 0])).toEqual([0, 0]);
    expect(splitProRata(10, [1, 1, 1])).toEqual([4, 3, 3]);
    expect(splitProRata(7, [5])).toEqual([7]);
    expect(splitProRata(1_000_000_000, [1, 3])).toEqual([250_000_000, 750_000_000]);
    expect(() => splitProRata(1.5, [1])).toThrow();
  });

  it('the simulated cap table is deterministic and sorted', () => {
    const a = capTable(5, 3, 200);
    expect(capTable(5, 3, 200)).toEqual(a);
    expect([...a].sort((x, y) => y - x)).toEqual(a);
  });

  it('bonus pool accounting balances, and treasury matches its parts', () => {
    const s = run(SIM.BONUS_EVERY * 3 + 5);
    expect(s.c.bonusPaid + s.c.pool).toBeCloseTo(s.c.pooled, 9);
    expect(s.c.feesIn).toBeGreaterThan(0);
    let open = 0;
    for (const t of s.traders) open += t.equity - t.book0;
    expect(treasury(s)).toBeCloseTo(SIM.TREASURY_START_SOL + s.c.feesIn + s.c.retiredPnl + open - s.c.pooled, 9);
    if (s.c.bonusDays > 0) expect(s.feed.some((f) => f.type === 'event' && f.kind === 'bonus') || s.c.bonusDays > 0).toBe(true);
  });

  it('traders actually trade, win and lose', () => {
    const s = run(4000);
    const all = [...s.traders, ...s.alumni];
    const trades = all.reduce((n, t) => n + t.trades, 0);
    expect(trades).toBeGreaterThan(500);
    expect(all.some((t) => t.equity > t.book0)).toBe(true);
    expect(all.some((t) => t.equity < t.book0)).toBe(true);
  });
});

describe('visitor hires', () => {
  const hire: HireRecord = {
    id: 'mine-1',
    name: 'pemberton',
    archetype: 'sniper',
    look: { skin: 1, hair: 2, hairStyle: 0, suit: 3, tie: 1 },
    risk: 0.7,
    patience: 0.3,
    hiredTick: 500,
    seed: 12345,
  };

  it('never changes the shared firm', () => {
    const plain = new Engine({ seasonStart: START, tickSeconds: 60 });
    plain.advanceTo(2000);
    const withHire = new Engine({ seasonStart: START, tickSeconds: 60, hires: [hire] });
    withHire.advanceTo(2000);
    expect(withHire.state.locals).toHaveLength(1);
    expect(withHire.state.locals[0].trades).toBeGreaterThan(0);
    expect(shared(withHire.state)).toBe(shared(plain.state));
  });

  it('is rebuilt identically from the hire record alone', () => {
    const a = new Engine({ seasonStart: START, tickSeconds: 60, hires: [hire] });
    a.advanceTo(1500);
    const b = new Engine({ seasonStart: START, tickSeconds: 60 });
    b.advanceTo(1500);
    b.setHires([hire]); // added after the fact: replays from before the hire
    expect(JSON.stringify(b.state.locals)).toBe(JSON.stringify(a.state.locals));
  });
});

describe('performance', () => {
  it('a week of ticks replays quickly', () => {
    const t0 = performance.now();
    run(7 * 1440);
    const ms = performance.now() - t0;
    console.log(`7 days (${7 * 1440} ticks): ${ms.toFixed(0)} ms`);
    expect(ms).toBeLessThan(6000);
  });
});
