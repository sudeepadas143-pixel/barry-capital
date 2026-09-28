import { useEffect, useState } from 'react';

/** Current time, refreshed every `ms` while the tab is visible. */
export function useNow(ms = 1000): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    let id: number | undefined;
    const start = () => {
      stop();
      setNow(Date.now());
      id = window.setInterval(() => setNow(Date.now()), ms);
    };
    const stop = () => {
      if (id !== undefined) window.clearInterval(id);
      id = undefined;
    };
    const onVis = () => (document.hidden ? stop() : start());
    start();
    document.addEventListener('visibilitychange', onVis);
    return () => {
      stop();
      document.removeEventListener('visibilitychange', onVis);
    };
  }, [ms]);
  return now;
}
