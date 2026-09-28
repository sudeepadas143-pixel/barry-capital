/**
 * Seeded randomness. Integer-only mixing (Math.imul, shifts) so every engine
 * produces the same sequence. The simulation only uses + - * / and sqrt on
 * floats, which IEEE-754 rounds identically everywhere.
 */

export function hashString(s: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

export function mix(a: number, b: number): number {
  let h = (a ^ Math.imul(b | 0, 0x9e3779b1)) >>> 0;
  h = Math.imul(h ^ (h >>> 16), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return (h ^ (h >>> 16)) >>> 0;
}

export interface Rng {
  /** [0, 1) */
  next(): number;
  int(n: number): number;
  range(a: number, b: number): number;
  chance(p: number): boolean;
  pick<T>(arr: readonly T[]): T;
  /** Approximately standard normal (Irwin–Hall, 4 draws). */
  normal(): number;
  /** Fat-tailed shock: mostly normal, sometimes a Pareto(α=2) jump. */
  fat(jumpP?: number): number;
}

export function rng(seed: number): Rng {
  let a = seed >>> 0;
  const next = () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const r: Rng = {
    next,
    int: (n) => Math.floor(next() * n),
    range: (lo, hi) => lo + (hi - lo) * next(),
    chance: (p) => next() < p,
    pick: (arr) => arr[Math.floor(next() * arr.length)],
    normal: () => (next() + next() + next() + next() - 2) * 1.7320508075688772,
    fat: (jumpP = 0.04) => {
      if (next() < jumpP) {
        const u = 1 - next(); // (0, 1]
        const size = Math.min(10, (1 / Math.sqrt(u) - 1) * 1.6); // Pareto tail, α = 2
        return next() < 0.5 ? -size : size;
      }
      return r.normal();
    },
  };
  return r;
}

/** One stream per (seed, tick, purpose). */
export function tickRng(seed: number, tick: number, stream: number): Rng {
  return rng(mix(mix(seed, tick), stream));
}
