import { DESK_COUNT } from '../../firm.config';
import type { FirmState } from '../sim/types';
import type { SceneData, TickerItem } from './anim';
import { C } from './colors';

/** What the building's screens should show for a given firm state. */
export function sceneData(s: FirmState): SceneData {
  const byTicker = new Map(s.coins.map((c) => [c.ticker, c]));
  const deskSeries = new Map<number, number[]>();
  const sideSeries = new Map<number, number[]>();
  const all = [...s.traders, ...s.mine.slice(0, 1).map((m) => ({ ...m, desk: DESK_COUNT + 1 }))];
  for (const t of all) {
    if (!t.desk) continue;
    const last = t.recent.find((r) => byTicker.has(r.ticker));
    const coin = last ? byTicker.get(last.ticker) : s.coins[(t.desk * 5) % Math.max(1, s.coins.length)];
    if (coin) deskSeries.set(t.desk, coin.hist);
    const other = s.coins[(t.desk * 3 + 1) % Math.max(1, s.coins.length)];
    if (other) sideSeries.set(t.desk, other.hist);
  }
  const movers = [...s.coins].sort((a, b) => Math.abs(b.change1h) - Math.abs(a.change1h)).slice(0, 6);
  const ticker: TickerItem[] = [...s.coins]
    .sort((a, b) => b.listedTick - a.listedTick)
    .map((c) => {
      const v = c.change1h;
      const sign = v > 0.05 ? '+' : v < -0.05 ? '-' : '';
      return {
        text: `$${c.ticker} ${sign}${Math.abs(v).toFixed(1)}%`,
        color: v > 0.05 ? C.candleUp : v < -0.05 ? C.candleDown : C.amber,
      };
    });
  return {
    deskSeries,
    sideSeries,
    terminalSeries: movers.map((c) => c.hist),
    ticker,
    stale: s.feedStale,
    hotDesk: null,
    doorSpin: false,
  };
}
