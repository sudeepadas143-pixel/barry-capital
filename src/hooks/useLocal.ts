/**
 * Small shared stores backed by localStorage, so every component sees the
 * same follows and visit history, and other tabs stay in step.
 */
import { useCallback, useEffect, useRef, useSyncExternalStore } from 'react';
import type { FirmState, Trader } from '../sim/types';
import { key, read, write } from '../storage';

function createStore<T>(name: string, fallback: T) {
  let value = read<T>(name, fallback);
  const subs = new Set<() => void>();
  const emit = () => subs.forEach((f) => f());
  if (typeof window !== 'undefined')
    window.addEventListener('storage', (e) => {
      if (e.key === key(name)) {
        value = read<T>(name, fallback);
        emit();
      }
    });
  return {
    get: () => value,
    set(v: T) {
      value = v;
      write(name, v);
      emit();
    },
    subscribe(f: () => void) {
      subs.add(f);
      return () => subs.delete(f);
    },
  };
}

// ---------------------------------------------------------------- follows

export interface Follow {
  id: string;
  name: string;
  /** Epoch ms when followed. */
  since: number;
  /** Result when followed, for "since you started following". */
  startPct: number;
}

const follows = createStore<Follow[]>('follows', []);

export function useFollows() {
  const list = useSyncExternalStore(follows.subscribe, follows.get, follows.get);
  const isFollowing = useCallback((id: string) => list.some((f) => f.id === id), [list]);
  const toggle = useCallback(
    (t: Trader) => {
      const cur = follows.get();
      follows.set(cur.some((f) => f.id === t.id) ? cur.filter((f) => f.id !== t.id) : [...cur, { id: t.id, name: t.name, since: Date.now(), startPct: t.resultPct }]);
    },
    [],
  );
  const remove = useCallback((id: string) => follows.set(follows.get().filter((f) => f.id !== id)), []);
  return { list, isFollowing, toggle, remove };
}

// ---------------------------------------------------------------- visits

export interface TraderSnap {
  name: string;
  resultPct: number;
  trades: number;
  status: Trader['status'];
}

export interface VisitSnap {
  at: number;
  tick: number;
  treasury: number;
  fired: number;
  hired: number;
  bonusPaid: number;
  traders: Record<string, TraderSnap>;
}

function snap(s: FirmState, ids: Set<string>): VisitSnap {
  const traders: Record<string, TraderSnap> = {};
  for (const t of [...s.traders, ...s.alumni, ...s.mine])
    if (ids.has(t.id) || t.local) traders[t.id] = { name: t.name, resultPct: t.resultPct, trades: t.trades, status: t.status };
  return {
    at: s.at,
    tick: s.tick,
    treasury: s.treasurySol,
    fired: s.counts.fired,
    hired: s.counts.hired,
    bonusPaid: s.bonus.totalPaidSol,
    traders,
  };
}

/** The previous visit (read once per page load), and a saver for this one. */
const previous = read<VisitSnap | null>('visit', null);

export function useVisit(state: FirmState, followIds: string[]) {
  const latest = useRef({ state, followIds });
  latest.current = { state, followIds };
  useEffect(() => {
    const save = () => write('visit', snap(latest.current.state, new Set(latest.current.followIds)));
    // Don't overwrite the last visit until this one has lasted a moment.
    const first = window.setTimeout(save, 15_000);
    const id = window.setInterval(save, 60_000);
    const onHide = () => document.visibilityState === 'hidden' && save();
    document.addEventListener('visibilitychange', onHide);
    window.addEventListener('pagehide', save);
    return () => {
      window.clearTimeout(first);
      window.clearInterval(id);
      document.removeEventListener('visibilitychange', onHide);
      window.removeEventListener('pagehide', save);
    };
  }, []);
  return previous;
}
