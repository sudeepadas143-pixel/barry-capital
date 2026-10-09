import { useEffect, useState } from 'react';
import { PRICE_URL, TOKEN_LAUNCHED, TOKEN_MINT, TOKEN_SUPPLY } from '../../firm.config';

/**
 * The token's live market cap in USD, from a read-only public price feed.
 * Null until the token is launched or the first price arrives.
 */
export function useMarketCap(everyMs = 30_000) {
  const [cap, setCap] = useState<number | null>(null);
  useEffect(() => {
    if (!TOKEN_LAUNCHED) return;
    let stop = false;
    const read = async () => {
      try {
        const res = await fetch(PRICE_URL.replace('{mint}', TOKEN_MINT));
        const data = (await res.json()) as Record<string, { usdPrice?: number }>;
        const price = data[TOKEN_MINT]?.usdPrice;
        if (!stop && typeof price === 'number') setCap(price * TOKEN_SUPPLY);
      } catch {
        // Keep the last value; try again next round.
      }
    };
    read();
    const id = window.setInterval(read, everyMs);
    return () => {
      stop = true;
      window.clearInterval(id);
    };
  }, [everyMs]);
  return cap;
}

export function fmtUsdShort(n: number): string {
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}
