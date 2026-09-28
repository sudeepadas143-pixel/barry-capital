import { createContext, useContext, useMemo, type ReactNode } from 'react';
import type { FirmState, Trader } from '../sim/types';
import { mockState } from '../sim/mock';
import { useNow } from './useNow';

interface FirmCtx {
  state: FirmState;
  now: number;
  byId: Map<string, Trader>;
}

const Ctx = createContext<FirmCtx | null>(null);

export function FirmProvider({ children }: { children: ReactNode }) {
  const now = useNow(1000);
  // M1: mock state, rebuilt once a minute so "ago" labels move.
  const minute = Math.floor(now / 60000);
  const state = useMemo(() => mockState(minute * 60000 + 30000), [minute]);
  const byId = useMemo(() => {
    const m = new Map<string, Trader>();
    for (const t of [...state.traders, ...state.waiting, ...state.alumni]) m.set(t.id, t);
    return m;
  }, [state]);
  const value = useMemo(() => ({ state, now, byId }), [state, now, byId]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useFirm(): FirmCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error('useFirm outside FirmProvider');
  return v;
}
