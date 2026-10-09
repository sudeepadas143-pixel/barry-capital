/**
 * Day-to-day controls.
 *
 *   npx tsx scripts/admin.ts pause            stop minting now (the kill switch)
 *   npx tsx scripts/admin.ts resume           start again
 *   npx tsx scripts/admin.ts log [20]         the latest decisions, newest first
 *   npx tsx scripts/admin.ts check <wallet>   would this wallet get one right now? (doesn't mint)
 *   npx tsx scripts/admin.ts count            how many have been sent
 *   npx tsx scripts/admin.ts send <wallet>    send one by hand (a retry, or a test-network rehearsal).
 *                                             Still one per wallet and within the cap; skips the comment and balance checks.
 */
import { env } from '../src/env.js';
import { holdsInvestor, mintInvestor, tokenBalance, tokenPrice } from '../src/chain.js';
import { audit } from '../src/store.js';
import { getJson, k, redis } from '../src/store.js';

const [cmd, arg] = process.argv.slice(2);
switch (cmd) {
  case 'pause':
    await redis('SET', k('paused'), '1');
    console.log('Paused. The bot will skip every comment until you resume.');
    break;
  case 'resume':
    await redis('DEL', k('paused'));
    console.log('Resumed.');
    break;
  case 'log': {
    const lines = await redis<string[]>('LRANGE', k('log'), 0, Number(arg ?? 20) - 1);
    for (const l of lines) console.log(l);
    break;
  }
  case 'count':
    console.log(`${(await redis<string | null>('GET', k('hired'))) ?? 0}/${env.cap()} Investors Hired`);
    break;
  case 'check': {
    if (!arg) throw new Error('Give a wallet address.');
    const [reg, minted, holds, amount, price] = await Promise.all([
      redis<number>('EXISTS', k(`reg:${arg}`)),
      getJson(`minted:${arg}`),
      holdsInvestor(arg),
      tokenBalance(arg),
      tokenPrice(),
    ]);
    console.log({ registered: !!reg, alreadySent: !!minted, holdsInvestor: holds, tokens: amount, usd: +(amount * price).toFixed(2), enough: amount * price >= env.minUsd() });
    break;
  }
  case 'send': {
    if (!arg) throw new Error('Give a wallet address.');
    if (await getJson(`minted:${arg}`)) throw new Error('That wallet was already sent an Investor.');
    const n = await redis<number>('INCR', k('hired'));
    if (n > env.cap()) {
      await redis('DECR', k('hired'));
      throw new Error(`All ${env.cap()} are hired.`);
    }
    const { sig, asset } = await mintInvestor(arg, n);
    await redis('SET', k(`minted:${arg}`), JSON.stringify({ at: Date.now(), n, sig, asset }));
    await redis('DEL', k(`review:${arg}`));
    await audit({ wallet: arg, result: 'minted', n, sig, asset, by: 'hand' });
    console.log(`Sent Investor #${n} to ${arg}: ${sig}`);
    break;
  }
  default:
    console.log('Commands: pause, resume, log [n], check <wallet>, count, send <wallet>');
}
