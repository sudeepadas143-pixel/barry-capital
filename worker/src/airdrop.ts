/**
 * The rules for sending an Investor. Every comment that contains the phrase
 * goes through here, one at a time, and every decision is written to the
 * audit log with the comment, the wallet and the balance it was judged on.
 */
import { env } from './env.js';
import * as chain from './chain.js';
import { audit, getJson, k, redis, type MintRecord } from './store.js';

/** The chain calls, swappable in tests. */
export const deps = {
  holdsInvestor: chain.holdsInvestor,
  mintInvestor: chain.mintInvestor,
  tokenBalance: chain.tokenBalance,
  tokenPrice: chain.tokenPrice,
};

export interface Comment {
  id: string;
  userAddress: string;
  message: string;
  timestamp?: string;
  username?: string;
}

const seen = (c: Comment) => redis<string | null>('SET', k(`seen:${c.id}`), '1', 'NX', 'EX', 14 * 86400);

async function paused(): Promise<boolean> {
  return env.pausedByEnv() || (await redis<string | null>('GET', k('paused'))) === '1';
}

/** Check the wallet's holding in USD, right now. */
async function holding(owner: string) {
  const [amount, price] = await Promise.all([deps.tokenBalance(owner), deps.tokenPrice()]);
  return { amount, price, usd: amount * price };
}

export async function handle(c: Comment): Promise<void> {
  if (!c?.id || !c.userAddress || typeof c.message !== 'string') return;
  if (!c.message.toLowerCase().includes(env.phrase())) return;
  if ((await seen(c)) !== 'OK') return; // already handled this comment
  const who = c.userAddress;
  const base = { comment: c.id, text: c.message.slice(0, 140), wallet: who, postedAt: c.timestamp };

  if (!(await redis<number>('EXISTS', k(`reg:${who}`)))) return audit({ ...base, result: 'ignored', why: 'wallet not registered on the site' });
  if (await paused()) return audit({ ...base, result: 'skipped', why: 'minting is paused' });
  if (await getJson<MintRecord>(`minted:${who}`)) return audit({ ...base, result: 'skipped', why: 'already sent an Investor' });
  try {
    if (await deps.holdsInvestor(who)) return audit({ ...base, result: 'skipped', why: 'wallet already holds an Investor' });
  } catch (e) {
    return audit({ ...base, result: 'error', why: `could not check holdings: ${(e as Error).message}` });
  }

  // First balance check, when the comment is seen.
  let h;
  try {
    h = await holding(who);
  } catch (e) {
    return audit({ ...base, result: 'error', why: `could not read balance: ${(e as Error).message}` });
  }
  if (h.usd < env.minUsd()) return audit({ ...base, result: 'refused', why: `holds $${h.usd.toFixed(2)}, needs $${env.minUsd()}`, ...h });

  // Take a number. If that goes past the cap, give it back and stop.
  const n = await redis<number>('INCR', k('hired'));
  if (n > env.cap()) {
    await redis('DECR', k('hired'));
    return audit({ ...base, result: 'refused', why: `all ${env.cap()} are hired` });
  }

  // Second balance check, right before sending, so selling after commenting doesn't count.
  try {
    h = await holding(who);
  } catch (e) {
    await redis('DECR', k('hired'));
    return audit({ ...base, result: 'error', why: `could not re-read balance: ${(e as Error).message}` });
  }
  if (h.usd < env.minUsd()) {
    await redis('DECR', k('hired'));
    return audit({ ...base, result: 'refused', why: `holds $${h.usd.toFixed(2)} at mint time, needs $${env.minUsd()}`, ...h });
  }

  try {
    const { sig, asset } = await deps.mintInvestor(who, n);
    const rec: MintRecord = { at: Date.now(), n, sig, asset };
    await redis('SET', k(`minted:${who}`), JSON.stringify(rec));
    await audit({ ...base, result: 'minted', n, sig, asset, ...h });
  } catch (e) {
    // We don't know for sure the transaction failed, so keep the number taken
    // and flag it for a look rather than risk sending two.
    await redis('SET', k(`review:${who}`), JSON.stringify({ n, at: Date.now(), error: (e as Error).message }));
    await audit({ ...base, result: 'error', why: `mint failed or unconfirmed: ${(e as Error).message}`, n, ...h });
  }
}

/** One at a time, in the order comments arrive. */
let queue = Promise.resolve();
export function enqueue(c: Comment) {
  queue = queue.then(() => handle(c)).catch((e) => console.error('handler crashed', e));
  return queue;
}
