import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../firm.config', async (orig) => ({ ...(await orig<typeof import('../../firm.config')>()), TOKEN_LAUNCHED: true }));

const db = new Map<string, string>();
process.env.UPSTASH_REDIS_REST_URL = 'https://store.test';
process.env.UPSTASH_REDIS_REST_TOKEN = 't';
vi.stubGlobal('fetch', async (_url: string, init: { body: string }) => {
  const [cmd, k, v, flag] = JSON.parse(init.body) as string[];
  let result: unknown = null;
  if (cmd === 'GET') result = db.get(k) ?? null;
  if (cmd === 'EXISTS') result = db.has(k) ? 1 : 0;
  if (cmd === 'SET') {
    if (flag === 'NX' && db.has(k)) result = null;
    else {
      db.set(k, v);
      result = 'OK';
    }
  }
  if (cmd === 'INCR') {
    const n = Number(db.get(k) ?? 0) + 1;
    db.set(k, String(n));
    result = n;
  }
  if (cmd === 'EXPIRE') result = 1;
  return new Response(JSON.stringify({ result }));
});

const { GET } = await import('../status');
const { POST: register } = await import('../register');
const { POST: saveTrader } = await import('../trader');

const ADDR = '7HpRv8WbbJ9x2rRqWJq2aT7Y3yWZQm1v5NfH6r4kQzVb';
const call = async (r: Response) => ({ status: r.status, body: (await r.json()) as Record<string, unknown> });
const post = (body: unknown) => new Request('https://x/api', { method: 'POST', body: JSON.stringify(body), headers: { 'x-forwarded-for': '1.1.1.1' } });
const trader = { name: 'Mr Test', archetype: 'sniper', risk: 0.5, patience: 0.5, seed: 9, look: { skin: 1, hair: 1, hairStyle: 3, suit: 0, tie: 0 } };

describe('hire API', () => {
  beforeEach(() => db.clear());

  it('registers a real address once and reports it pending', async () => {
    expect((await call(await GET(new Request(`https://x/api/status?address=${ADDR}`)))).body.state).toBe('none');
    expect((await call(await register(post({ address: ADDR })))).body.state).toBe('pending');
    expect((await call(await register(post({ address: ADDR })))).body.state).toBe('pending');
    expect((await call(await GET(new Request(`https://x/api/status?address=${ADDR}`)))).body).toMatchObject({ state: 'pending', hired: 0, cap: 1111 });
  });

  it('refuses addresses that are not Solana addresses', async () => {
    expect((await call(await register(post({ address: 'hello' })))).status).toBe(400);
    expect((await call(await GET(new Request('https://x/api/status?address=0OIl')))).status).toBe(400);
  });

  it('lets a holder set up a trader once, then locks it', async () => {
    expect((await call(await saveTrader(post({ address: ADDR, trader })))).status).toBe(403);
    db.set(`si:minted:${ADDR}`, JSON.stringify({ at: 1, asset: 'A' }));
    const first = await call(await saveTrader(post({ address: ADDR, trader })));
    expect(first.body.state).toBe('hired');
    expect((first.body.trader as { name: string }).name).toBe('mr test');
    expect((await call(await saveTrader(post({ address: ADDR, trader: { ...trader, name: 'other' } })))).status).toBe(409);
  });

  it('rejects a trader with options the site does not have', async () => {
    db.set(`si:minted:${ADDR}`, JSON.stringify({ at: 1 }));
    const bad = await call(await saveTrader(post({ address: ADDR, trader: { ...trader, look: { ...trader.look, skin: 99 } } })));
    expect(bad.status).toBe(400);
  });

  it('closes when paused or when all 1111 are hired', async () => {
    db.set('si:paused', '1');
    expect((await call(await register(post({ address: ADDR })))).body.state).toBe('closed');
    db.delete('si:paused');
    db.set('si:hired', '1111');
    expect((await call(await register(post({ address: ADDR })))).body).toMatchObject({ state: 'closed', hired: 1111 });
  });
});
