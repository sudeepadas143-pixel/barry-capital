import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import checkpoint from 'virtual:checkpoint';
import { SEASON_START, TICK_SECONDS } from '../../firm.config';
import { Engine, type HireRecord } from '../sim/engine';
import type { SimState } from '../sim/firm';
import { SIM } from '../sim/params';
import { toView } from '../sim/view';
import type { FirmState, Trader } from '../sim/types';
import { read, readRaw, write, writeRaw } from '../storage';
import { useNow } from './useNow';

const SNAP = `snap:v${SIM.VERSION}`;

interface FirmCtx {
  state: FirmState;
  now: number;
  byId: Map<string, Trader>;
  hires: HireRecord[];
  addHire: (h: Omit<HireRecord, 'hiredTick' | 'id' | 'seed'>) => HireRecord;
  removeHire: (id: string) => void;
  tickFor: (ms: number) => number;
  msForTick: (tick: number) => number;
}

const Ctx = createContext<FirmCtx | null>(null);

function loadSnapshot(): SimState | null {
  const raw = readRaw(SNAP);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as SimState;
  } catch {
    return null;
  }
}

export function FirmProvider({ children }: { children: ReactNode }) {
  const now = useNow(1000);
  const [hires, setHires] = useState<HireRecord[]>(() => read<HireRecord[]>('hires', []));
  const engine = useRef<Engine | null>(null);
  if (!engine.current) {
    const e = new Engine({
      seasonStart: SEASON_START,
      tickSeconds: TICK_SECONDS,
      bases: [checkpoint, loadSnapshot()],
      hires,
    });
    e.advanceToTime(Date.now());
    engine.current = e;
  }
  const e = engine.current;
  const [version, setVersion] = useState(0);

  const tick = e.tickFor(now);
  if (tick !== e.state.tick) e.advanceToTime(now);

  // Save a snapshot now and then, and when the tab goes to the background.
  const lastSaved = useRef(-1);
  useEffect(() => {
    const save = () => {
      writeRaw(SNAP, e.snapshot());
      lastSaved.current = e.state.tick;
    };
    if (e.state.tick - lastSaved.current >= 10) save();
    const onHide = () => document.visibilityState === 'hidden' && save();
    document.addEventListener('visibilitychange', onHide);
    window.addEventListener('pagehide', save);
    return () => {
      document.removeEventListener('visibilitychange', onHide);
      window.removeEventListener('pagehide', save);
    };
  }, [e, e.state.tick]);

  const addHire = useCallback(
    (h: Omit<HireRecord, 'hiredTick' | 'id' | 'seed'>) => {
      const hiredTick = Math.max(0, e.state.tick);
      const rec: HireRecord = {
        ...h,
        id: `mine-${Date.now().toString(36)}`,
        hiredTick,
        seed: (Date.now() ^ Math.floor(Math.random() * 0x7fffffff)) >>> 0,
      };
      const next = [...hires, rec];
      setHires(next);
      write('hires', next);
      e.setHires(next);
      setVersion((v) => v + 1);
      return rec;
    },
    [e, hires],
  );

  const removeHire = useCallback(
    (id: string) => {
      const next = hires.filter((h) => h.id !== id);
      setHires(next);
      write('hires', next);
      e.setHires(next);
      setVersion((v) => v + 1);
    },
    [e, hires],
  );

  const state = useMemo(() => toView(e.state, now), [e, now, e.state.tick, version]);
  const byId = useMemo(() => {
    const m = new Map<string, Trader>();
    for (const t of [...state.traders, ...state.waiting, ...state.alumni, ...state.mine]) m.set(t.id, t);
    return m;
  }, [state]);

  const value = useMemo(
    () => ({
      state,
      now,
      byId,
      hires,
      addHire,
      removeHire,
      tickFor: (ms: number) => e.tickFor(ms),
      msForTick: (t: number) => e.startMs + (t + 1) * e.tickMs,
    }),
    [state, now, byId, hires, addHire, removeHire, e],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useFirm(): FirmCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error('useFirm outside FirmProvider');
  return v;
}
