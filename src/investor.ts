/**
 * The Investors NFT, as the site and its API both see it. This module is
 * shared by the browser and the serverless functions in /api, so it imports
 * nothing that needs a DOM.
 *
 * Real vs concept: the NFT, the mint and the airdrop are real on-chain
 * actions on real wallets. The trader a holder sets up, and everything that
 * trader "does" on the trading floor, is the site's concept and moves no
 * funds.
 */
import { BUILD_NAMES, EYES_NAMES, FACE_NAMES, HAIRS, HAIR_STYLE_NAMES, NECK_NAMES, OUTFIT_NAMES, SHIRTS, SKINS, SUITS, TIES } from './art/palette.js';
import { ARCHETYPE_IDS } from './sim/archetypes.js';
import type { ArchetypeId, Look } from './sim/types';

/**
 * Where an address is in the hire flow.
 * - closed: the token isn't live yet, or minting is paused
 * - none: not registered
 * - pending: registered, waiting for the comment on pump.fun
 * - minted: the Investor NFT was sent; the trader isn't set up yet
 * - hired: the trader is set up (and locked)
 */
export type HireState = 'closed' | 'none' | 'pending' | 'minted' | 'hired';

export interface TraderConfig {
  name: string;
  archetype: ArchetypeId;
  risk: number;
  patience: number;
  look: Look;
  seed: number;
  /** When the trader was saved, in ms. Every device seats them from this moment. */
  hiredAt: number;
}

export interface StatusResponse {
  state: HireState;
  hired: number;
  cap: number;
  /** Why it's closed, in plain words, when state is 'closed'. */
  reason?: string;
  mintedAt?: number;
  asset?: string;
  trader?: TraderConfig;
}

export const cleanTraderName = (s: string) =>
  s
    .toLowerCase()
    .replace(/[^a-z' -]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 16);

const int = (v: unknown, max: number) => Number.isInteger(v) && (v as number) >= 0 && (v as number) < max;

/** Check a trader sent by a browser. Returns the clean config, or a reason it was refused. */
export function validateTrader(raw: unknown, now: number): { ok: true; trader: TraderConfig } | { ok: false; error: string } {
  if (!raw || typeof raw !== 'object') return { ok: false, error: 'No trader sent.' };
  const r = raw as Record<string, unknown>;
  const name = typeof r.name === 'string' ? cleanTraderName(r.name) : '';
  if (!name) return { ok: false, error: 'A surname, please.' };
  if (!ARCHETYPE_IDS.includes(r.archetype as ArchetypeId)) return { ok: false, error: 'Pick a method.' };
  const unit = (v: unknown) => typeof v === 'number' && v >= 0 && v <= 1;
  if (!unit(r.risk) || !unit(r.patience)) return { ok: false, error: 'Risk and patience run from 0 to 1.' };
  const l = r.look as Record<string, unknown> | undefined;
  if (!l || typeof l !== 'object') return { ok: false, error: 'No look sent.' };
  const ok =
    int(l.skin, SKINS.length) &&
    int(l.hair, HAIRS.length) &&
    int(l.hairStyle, HAIR_STYLE_NAMES.length) &&
    int(l.suit, SUITS.length) &&
    int(l.tie, TIES.length) &&
    int(l.build ?? 1, BUILD_NAMES.length) &&
    int(l.height ?? 1, 3) &&
    int(l.face ?? 0, FACE_NAMES.length) &&
    int(l.outfit ?? 0, OUTFIT_NAMES.length) &&
    int(l.shirt ?? 0, SHIRTS.length) &&
    int(l.neck ?? 0, NECK_NAMES.length) &&
    int(l.eyes ?? 0, EYES_NAMES.length);
  if (!ok) return { ok: false, error: 'That look has an option the site doesn’t have.' };
  const look: Look = {
    skin: l.skin as number,
    hair: l.hair as number,
    hairStyle: l.hairStyle as number,
    suit: l.suit as number,
    tie: l.tie as number,
    build: (l.build as number) ?? 1,
    height: (l.height as number) ?? 1,
    face: (l.face as number) ?? 0,
    outfit: (l.outfit as number) ?? 0,
    shirt: (l.shirt as number) ?? 0,
    neck: (l.neck as number) ?? 0,
    eyes: (l.eyes as number) ?? 0,
    watch: !!l.watch,
    fem: !!l.fem,
  };
  const seed = Number.isInteger(r.seed) ? (r.seed as number) >>> 0 : 0;
  return { ok: true, trader: { name, archetype: r.archetype as ArchetypeId, risk: r.risk as number, patience: r.patience as number, look, seed, hiredAt: now } };
}
