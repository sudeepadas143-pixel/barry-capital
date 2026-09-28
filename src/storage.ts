/**
 * Browser storage, wrapped so a private window or blocked storage never breaks the page.
 * Everything here is a per-visitor convenience; nothing is shared or sent anywhere.
 */
import { FIRM_NAME } from '../firm.config';

const prefix = FIRM_NAME.toLowerCase().replace(/[^a-z0-9]+/g, '-');
export const key = (k: string) => `${prefix}:${k}`;

export function read<T>(k: string, fallback: T): T {
  try {
    const v = localStorage.getItem(key(k));
    return v === null ? fallback : (JSON.parse(v) as T);
  } catch {
    return fallback;
  }
}

export function write(k: string, v: unknown): void {
  try {
    localStorage.setItem(key(k), JSON.stringify(v));
  } catch {
    /* storage full or unavailable */
  }
}

export function readRaw(k: string): string | null {
  try {
    return localStorage.getItem(key(k));
  } catch {
    return null;
  }
}

export function writeRaw(k: string, v: string): void {
  try {
    localStorage.setItem(key(k), v);
  } catch {
    /* storage full or unavailable */
  }
}

export function remove(k: string): void {
  try {
    localStorage.removeItem(key(k));
  } catch {
    /* ignore */
  }
}
