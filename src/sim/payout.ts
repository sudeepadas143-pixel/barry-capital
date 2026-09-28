/**
 * Bonus day arithmetic. Display only: nothing is ever sent anywhere.
 * Everything is in integer lamports so the split always sums to the pool exactly.
 */
import { rng, mix } from './prng';

export const LAMPORTS = 1_000_000_000;

export const toLamports = (sol: number) => Math.round(sol * LAMPORTS);
export const toSol = (lamports: number) => lamports / LAMPORTS;

/**
 * Split `pool` lamports across `balances` in proportion. Floors each share, then
 * hands the leftover lamports to the largest remainders (ties to the earlier holder).
 */
export function splitProRata(pool: number, balances: readonly number[]): number[] {
  if (!Number.isSafeInteger(pool) || pool < 0) throw new Error('pool must be a non-negative integer');
  const total = balances.reduce((a, b) => a + BigInt(Math.max(0, Math.floor(b))), 0n);
  if (total === 0n || pool === 0) return balances.map(() => 0);
  const P = BigInt(pool);
  const shares: bigint[] = [];
  const rems: { i: number; rem: bigint }[] = [];
  let given = 0n;
  balances.forEach((b, i) => {
    const bal = BigInt(Math.max(0, Math.floor(b)));
    const num = P * bal;
    const s = num / total;
    shares.push(s);
    rems.push({ i, rem: num % total });
    given += s;
  });
  let left = P - given;
  rems.sort((a, b) => (a.rem === b.rem ? a.i - b.i : a.rem > b.rem ? -1 : 1));
  for (let k = 0; left > 0n; k++, left--) shares[rems[k].i] += 1n;
  return shares.map(Number);
}

/** Number of simulated token holders at a tick. Grows slowly through the season. */
export function holderCount(seed: number, tick: number): number {
  const t = Math.max(0, tick);
  return 900 + Math.floor(Math.sqrt(t) * 9) + (mix(seed, Math.floor(t / 60)) % 40);
}

/** A seeded, simulated cap table: integer token balances, heavy at the top. */
export function capTable(seed: number, day: number, n: number): number[] {
  const r = rng(mix(seed, 0x0b0 + day));
  const out: number[] = [];
  for (let i = 0; i < n; i++) {
    const u = 1 - r.next();
    out.push(Math.floor(40_000 / Math.sqrt(u)) + r.int(5_000));
  }
  return out.sort((a, b) => b - a);
}
