import { isSolanaAddress } from '../src/base58';
import { statusFor } from './_lib/status';
import { json } from './_lib/store';

/** GET /api/status?address=… : the hire count, and where this address is in the flow. */
export async function GET(req: Request): Promise<Response> {
  const a = new URL(req.url).searchParams.get('address')?.trim() || null;
  if (a && !isSolanaAddress(a)) return json({ error: 'That isn’t a Solana address.' }, 400);
  try {
    return json(await statusFor(a));
  } catch {
    return json({ error: 'The hiring desk is down for a moment.' }, 503);
  }
}
