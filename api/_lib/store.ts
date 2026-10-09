/**
 * The hire records, in Upstash Redis over its REST API (no client library).
 * Shared with the airdrop worker, which uses the same keys.
 *
 * Keys (all prefixed `si:`):
 *   reg:<address>     JSON { at }                 registered, waiting for the comment
 *   minted:<address>  JSON { at, asset, sig, n }  the Investor was sent
 *   trader:<address>  JSON TraderConfig           set once, then locked
 *   hired             integer                     how many Investors have been sent
 *   paused            "1" when minting is paused (the kill switch)
 *   log               list of JSON audit entries, newest first
 */
const URL_ = process.env.UPSTASH_REDIS_REST_URL ?? process.env.KV_REST_API_URL;
const TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN ?? process.env.KV_REST_API_TOKEN;

export const storeReady = () => !!URL_ && !!TOKEN;

export async function redis<T = unknown>(...cmd: (string | number)[]): Promise<T> {
  if (!URL_ || !TOKEN) throw new Error('store not configured');
  const res = await fetch(URL_, {
    method: 'POST',
    headers: { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(cmd),
  });
  const data = (await res.json()) as { result?: T; error?: string };
  if (data.error) throw new Error(data.error);
  return data.result as T;
}

export const key = (k: string) => `si:${k}`;

export async function getJson<T>(k: string): Promise<T | null> {
  const v = await redis<string | null>('GET', key(k));
  return v ? (JSON.parse(v) as T) : null;
}

export function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}

/** A loose per-IP limit, so nobody can fill the store from a script. */
export async function limited(req: Request, bucket: string, perMinute: number): Promise<boolean> {
  const ip = (req.headers.get('x-forwarded-for') ?? 'unknown').split(',')[0].trim();
  const k = key(`rate:${bucket}:${ip}:${Math.floor(Date.now() / 60000)}`);
  const n = await redis<number>('INCR', k);
  if (n === 1) await redis('EXPIRE', k, 120);
  return n > perMinute;
}
