import { useCallback, useEffect, useState } from 'react';
import { INVESTORS_CAP } from '../../firm.config';
import type { StatusResponse, TraderConfig } from '../investor';
import { read, write } from '../storage';

const CLOSED: StatusResponse = { state: 'closed', hired: 0, cap: INVESTORS_CAP, reason: 'Hiring opens when the token launches.' };

async function call(path: string, body?: unknown): Promise<StatusResponse & { error?: string }> {
  try {
    const res = await fetch(path, body === undefined ? undefined : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const data = (await res.json()) as StatusResponse & { error?: string };
    if (!res.ok && !data.state) return { ...CLOSED, reason: data.error ?? CLOSED.reason, error: data.error };
    return data;
  } catch {
    return CLOSED;
  }
}

/**
 * The visitor's place in the hire flow. The address they gave is remembered in
 * this browser so they can come back to it; the record itself lives with the
 * hiring desk (the API), so any device with the same address sees the same thing.
 */
export function useHireStatus() {
  const [address, setAddressState] = useState<string>(() => read('investor-address', ''));
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (a = address) => {
    const s = await call(`/api/status${a ? `?address=${encodeURIComponent(a)}` : ''}`);
    setStatus(s);
    return s;
  }, [address]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // While we wait for the comment, look again every 15 seconds.
  useEffect(() => {
    if (status?.state !== 'pending') return;
    const id = window.setInterval(() => refresh(), 15_000);
    return () => window.clearInterval(id);
  }, [status?.state, refresh]);

  const register = useCallback(async (a: string) => {
    setBusy(true);
    setError(null);
    const s = await call('/api/register', { address: a });
    setBusy(false);
    if (s.error) setError(s.error);
    else {
      write('investor-address', a);
      setAddressState(a);
    }
    setStatus(s);
    return s;
  }, []);

  const saveTrader = useCallback(async (trader: Omit<TraderConfig, 'hiredAt'>) => {
    setBusy(true);
    setError(null);
    const s = await call('/api/trader', { address, trader });
    setBusy(false);
    if (s.error) setError(s.error);
    setStatus(s);
    return s;
  }, [address]);

  const forget = useCallback(() => {
    write('investor-address', '');
    setAddressState('');
    setError(null);
    refresh('');
  }, [refresh]);

  return { address, status, busy, error, register, saveTrader, forget, refresh };
}
