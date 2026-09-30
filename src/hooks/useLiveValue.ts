import { useEffect, useRef, useState } from 'react';

/**
 * A number that creeps upward between sim updates. `base` is the latest real
 * value, and `perMs` the rate it usually grows at. Every second or so the shown
 * value steps forward by a small, slightly uneven amount; it never goes
 * backwards, and it snaps to the real value whenever that overtakes it.
 */
export function useLiveValue(base: number, perMs: number, reduced: boolean): number {
  const [shown, setShown] = useState(base);
  const since = useRef({ base, at: performance.now() });
  if (since.current.base !== base) since.current = { base, at: performance.now() };

  useEffect(() => {
    if (reduced || !(perMs > 0)) {
      setShown((v) => Math.max(v, base));
      return;
    }
    let timer = 0;
    const step = () => {
      const { base: b, at } = since.current;
      // Cap the run-ahead at one minute's worth, so a paused tab doesn't drift.
      const ahead = Math.min(60_000, performance.now() - at) * perMs;
      const wobble = 0.85 + Math.random() * 0.3;
      setShown((v) => Math.max(v, b + ahead * wobble));
      timer = window.setTimeout(step, 900 + Math.random() * 900);
    };
    step();
    return () => window.clearTimeout(timer);
  }, [base, perMs, reduced]);

  return Math.max(shown, base);
}
