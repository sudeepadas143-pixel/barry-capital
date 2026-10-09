import { isSolanaAddress } from '../src/base58';
import { validateTrader } from '../src/investor';
import { statusFor } from './_lib/status';
import { json, key, limited, redis } from './_lib/store';

/**
 * POST /api/trader { address, trader } : set up the trader for an address
 * that holds an Investor. Saved once, then locked.
 */
export async function POST(req: Request): Promise<Response> {
  let body: { address?: unknown; trader?: unknown };
  try {
    body = (await req.json()) as typeof body;
  } catch {
    return json({ error: 'Send JSON with an address and a trader.' }, 400);
  }
  const address = String(body.address ?? '').trim();
  if (!isSolanaAddress(address)) return json({ error: 'That isn’t a Solana address.' }, 400);
  const v = validateTrader(body.trader, Date.now());
  if (!v.ok) return json({ error: v.error }, 400);
  try {
    if (await limited(req, 'trader', 10)) return json({ error: 'Too many tries. Wait a minute.' }, 429);
    const status = await statusFor(address);
    if (status.state === 'hired') return json({ ...status, error: 'This trader is already set up, and it’s locked.' }, 409);
    if (status.state !== 'minted') return json({ ...status, error: 'This address doesn’t hold an Investor yet.' }, 403);
    const set = await redis<string | null>('SET', key(`trader:${address}`), JSON.stringify(v.trader), 'NX');
    if (set !== 'OK') return json({ ...(await statusFor(address)), error: 'This trader is already set up, and it’s locked.' }, 409);
    return json(await statusFor(address));
  } catch {
    return json({ error: 'The hiring desk is down for a moment.' }, 503);
  }
}
