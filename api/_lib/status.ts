import { INVESTORS_CAP, TOKEN_LAUNCHED } from '../../firm.config';
import type { StatusResponse, TraderConfig } from '../../src/investor';
import { getJson, redis, storeReady } from './store';

export async function statusFor(address: string | null): Promise<StatusResponse> {
  const base = { hired: 0, cap: INVESTORS_CAP };
  if (!TOKEN_LAUNCHED || !storeReady()) return { ...base, state: 'closed', reason: 'Hiring opens when the token launches.' };
  const [hiredRaw, paused] = await Promise.all([redis<string | null>('GET', 'si:hired'), redis<string | null>('GET', 'si:paused')]);
  const hired = Number(hiredRaw ?? 0);
  const out = { ...base, hired };
  if (address) {
    const minted = await getJson<{ at: number; asset?: string }>(`minted:${address}`);
    if (minted) {
      const trader = await getJson<TraderConfig>(`trader:${address}`);
      return { ...out, state: trader ? 'hired' : 'minted', mintedAt: minted.at, asset: minted.asset, trader: trader ?? undefined };
    }
  }
  if (paused === '1') return { ...out, state: 'closed', reason: 'Hiring is paused for a moment. Try again soon.' };
  if (hired >= INVESTORS_CAP) return { ...out, state: 'closed', reason: `All ${INVESTORS_CAP.toLocaleString('en-US')} Investors are hired.` };
  if (address && (await redis<number>('EXISTS', `si:reg:${address}`))) return { ...out, state: 'pending' };
  return { ...out, state: 'none' };
}
