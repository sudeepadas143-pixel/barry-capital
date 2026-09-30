import type { Trader } from '../sim/types';

/** Where a trader stands at the next review: top, next out, their place, or new. */
export function standingText(t: Trader): string {
  if (t.local) return 'not reviewed';
  if (t.status !== 'seated') return '';
  if (t.nextOut) return 'next out';
  if (t.rank === 1) return 'top';
  if (t.rank) return `#${t.rank}`;
  return 'new';
}

export function Standing({ t }: { t: Trader }) {
  const text = standingText(t);
  if (!text) return null;
  const cls = t.nextOut ? 'chip chip-out' : t.rank === 1 ? 'chip chip-top' : 'chip';
  return (
    <span className={cls} title={t.nextOut ? 'Bottom of the board: goes at the next review if nothing changes' : undefined}>
      {text.toUpperCase()}
    </span>
  );
}
