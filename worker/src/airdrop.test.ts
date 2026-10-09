/** The airdrop rules, against a fake store and a fake chain. `npx tsx --test src/airdrop.test.ts` */
import assert from 'node:assert/strict';
import { beforeEach, test } from 'node:test';

process.env.UPSTASH_REDIS_REST_URL = 'https://store.test';
process.env.UPSTASH_REDIS_REST_TOKEN = 't';
process.env.TOKEN_MINT = 'Mint1111111111111111111111111111111111111111';
process.env.INVESTORS_CAP = '3';

const db = new Map<string, string>();
const list: string[] = [];
globalThis.fetch = (async (_u: string, init: { body: string }) => {
  const [cmd, k, v, a, b] = JSON.parse(init.body) as string[];
  let result: unknown = null;
  if (cmd === 'GET') result = db.get(k) ?? null;
  if (cmd === 'EXISTS') result = db.has(k) ? 1 : 0;
  if (cmd === 'SET') result = a === 'NX' && db.has(k) ? null : (db.set(k, v), 'OK');
  if (cmd === 'INCR' || cmd === 'DECR') {
    const n = Number(db.get(k) ?? 0) + (cmd === 'INCR' ? 1 : -1);
    db.set(k, String(n));
    result = n;
  }
  if (cmd === 'LPUSH') list.unshift(v);
  void b;
  return new Response(JSON.stringify({ result }));
}) as typeof fetch;

const { deps, handle } = await import('./airdrop.js');
let balance = 1_000_000;
let price = 0.00001; // $10 for 1M tokens
let holds = false;
const mints: [string, number][] = [];
deps.tokenBalance = async () => balance;
deps.tokenPrice = async () => price;
deps.holdsInvestor = async () => holds;
deps.mintInvestor = async (owner, n) => (mints.push([owner, n]), { sig: `sig${n}` });

const W = 'Wallet1111111111111111111111111111111111111';
let id = 0;
const say = (msg: string, who = W) => handle({ id: String(++id), userAddress: who, message: msg });
const last = () => JSON.parse(list[0]) as Record<string, unknown>;

beforeEach(() => {
  db.clear();
  list.length = 0;
  mints.length = 0;
  balance = 1_000_000;
  price = 0.00001;
  holds = false;
});

test('mints to a registered wallet holding $5 that posts the phrase', async () => {
  db.set(`si:reg:${W}`, '{}');
  await say('gm, MINT ME AN INVESTOR please');
  assert.deepEqual(mints, [[W, 1]]);
  assert.equal(last().result, 'minted');
  assert.equal(db.get('si:hired'), '1');
  assert.ok(db.get(`si:minted:${W}`));
});

test('ignores comments without the phrase, and unregistered wallets', async () => {
  await say('mint me an investor');
  assert.equal(last().result, 'ignored');
  db.set(`si:reg:${W}`, '{}');
  await say('just vibes');
  assert.equal(mints.length, 0);
});

test('refuses under $5, and does not count the slot', async () => {
  db.set(`si:reg:${W}`, '{}');
  balance = 100_000; // $1
  await say('mint me an investor');
  assert.equal(last().result, 'refused');
  assert.equal(mints.length, 0);
  assert.equal(db.get('si:hired') ?? '0', '0');
});

test('one per wallet: the store and the chain both stop a second', async () => {
  db.set(`si:reg:${W}`, '{}');
  await say('mint me an investor');
  await say('mint me an investor');
  assert.equal(mints.length, 1);
  const V = 'Other11111111111111111111111111111111111111';
  db.set(`si:reg:${V}`, '{}');
  holds = true;
  await say('mint me an investor', V);
  assert.equal(mints.length, 1);
  assert.match(String(last().why), /already holds/);
});

test('the same comment is never handled twice', async () => {
  db.set(`si:reg:${W}`, '{}');
  const c = { id: 'same', userAddress: W, message: 'mint me an investor' };
  await handle(c);
  db.delete(`si:minted:${W}`);
  await handle(c);
  assert.equal(mints.length, 1);
});

test('the pause switch stops minting', async () => {
  db.set(`si:reg:${W}`, '{}');
  db.set('si:paused', '1');
  await say('mint me an investor');
  assert.equal(mints.length, 0);
  assert.match(String(last().why), /paused/);
});

test('stops at the cap', async () => {
  for (let i = 0; i < 4; i++) {
    const w = `W${i}`.padEnd(44, '1');
    db.set(`si:reg:${w}`, '{}');
    await say('mint me an investor', w);
  }
  assert.equal(mints.length, 3);
  assert.equal(db.get('si:hired'), '3');
  assert.match(String(last().why), /all 3/);
});

test('re-checks the balance right before minting', async () => {
  db.set(`si:reg:${W}`, '{}');
  let calls = 0;
  deps.tokenBalance = async () => (++calls === 1 ? 1_000_000 : 0); // sold straight after commenting
  await say('mint me an investor');
  deps.tokenBalance = async () => balance;
  assert.equal(mints.length, 0);
  assert.match(String(last().why), /at mint time/);
  assert.equal(db.get('si:hired'), '0');
});
