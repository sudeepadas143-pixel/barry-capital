/**
 * The airdrop bot. Start with `npm start` (Railway does this for you).
 * It watches the chat, checks each "mint me an investor" comment against the
 * rules in airdrop.ts, and mints. GET / shows whether it's healthy.
 */
import { createServer } from 'node:http';
import { env } from './env.js';
import { chain } from './chain.js';
import { redis, k } from './store.js';
import { watch } from './watch.js';

// Fail fast on missing settings, before connecting to anything.
for (const f of [env.rpc, env.secret, env.tokenMint, env.collection, env.tree, env.redisUrl, env.redisToken]) f();
const payer = chain().identity.publicKey.toString();
console.log(`airdrop wallet: ${payer}`);
console.log(`token: ${env.tokenMint()}  collection: ${env.collection()}  tree: ${env.tree()}`);
console.log(`phrase: "${env.phrase()}"  minimum: $${env.minUsd()}  cap: ${env.cap()}`);

const state = watch();
const started = Date.now();

createServer(async (_req, res) => {
  let hired = '?';
  let paused = false;
  try {
    hired = String((await redis<string | null>('GET', k('hired'))) ?? 0);
    paused = env.pausedByEnv() || (await redis<string | null>('GET', k('paused'))) === '1';
  } catch {
    /* store down: report what we have */
  }
  const body = { ok: state.connected, chat: state, hired, cap: env.cap(), paused, wallet: payer, upSince: new Date(started).toISOString() };
  res.writeHead(state.connected ? 200 : 503, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(body, null, 2));
}).listen(Number(process.env.PORT ?? 8080));

// A heartbeat in the logs every five minutes, with a warning if the chat has gone quiet.
setInterval(() => {
  const quiet = Date.now() - (state.lastEventAt || started);
  console.log(`heartbeat: connected=${state.connected} messages=${state.seen} quiet=${Math.round(quiet / 1000)}s`);
  if (quiet > 15 * 60_000) console.warn('heartbeat: no chat events for 15 minutes. Check that pump.fun chat still works.');
}, 5 * 60_000);
