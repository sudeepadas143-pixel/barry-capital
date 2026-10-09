/** The same Upstash keys the website's API uses (see api/_lib/store.ts in the site). */
import { env } from './env.js';

export async function redis<T = unknown>(...cmd: (string | number)[]): Promise<T> {
  const res = await fetch(env.redisUrl(), {
    method: 'POST',
    headers: { Authorization: `Bearer ${env.redisToken()}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(cmd),
  });
  const data = (await res.json()) as { result?: T; error?: string };
  if (data.error) throw new Error(`store: ${data.error}`);
  return data.result as T;
}

export const k = (s: string) => `si:${s}`;

export async function getJson<T>(key: string): Promise<T | null> {
  const v = await redis<string | null>('GET', k(key));
  return v ? (JSON.parse(v) as T) : null;
}

export interface MintRecord {
  at: number;
  n: number;
  sig: string;
  asset?: string;
}

/** One line per decision, newest first, capped at 20,000 entries. */
export async function audit(entry: Record<string, unknown>) {
  const line = JSON.stringify({ at: new Date().toISOString(), ...entry });
  console.log(line);
  try {
    await redis('LPUSH', k('log'), line);
    await redis('LTRIM', k('log'), 0, 19_999);
  } catch (e) {
    console.error('could not write the audit log', e);
  }
}
