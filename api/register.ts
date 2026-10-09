import { isSolanaAddress } from '../src/base58.js';
import { statusFor } from './_lib/status.js';
import { json, key, limited, redis } from './_lib/store.js';

/** POST /api/register { address } : put an address on the list the airdrop worker watches for. */
export async function POST(req: Request): Promise<Response> {
  let address = '';
  try {
    address = String(((await req.json()) as { address?: unknown }).address ?? '').trim();
  } catch {
    return json({ error: 'Send JSON with an address.' }, 400);
  }
  if (!isSolanaAddress(address)) return json({ error: 'That isn’t a Solana address.' }, 400);
  try {
    if (await limited(req, 'register', 20)) return json({ error: 'Too many tries. Wait a minute.' }, 429);
    const status = await statusFor(address);
    if (status.state !== 'none') return json(status);
    await redis('SET', key(`reg:${address}`), JSON.stringify({ at: Date.now() }), 'NX');
    return json({ ...status, state: 'pending' });
  } catch {
    return json({ error: 'The hiring desk is down for a moment.' }, 503);
  }
}
