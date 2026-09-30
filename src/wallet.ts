/**
 * Solana wallet addresses on the hire page. Everything here runs in the
 * browser: the address is checked, turned into a trader, and saved in this
 * browser only. Nothing is signed, connected or sent anywhere, and a public
 * address is all the page ever asks for.
 */
import { BUILD_NAMES, EYES_NAMES, FACE_NAMES, HAIRS, NECK_NAMES, OUTFIT_NAMES, SHIRTS, SKINS, SUITS, TIES } from './art/palette';
import { ARCHETYPE_IDS } from './sim/archetypes';
import { SURNAMES } from './sim/names';
import { hashString, rng } from './sim/prng';
import type { ArchetypeId, Look } from './sim/types';

const ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';

/** Decode base58, or null if it contains characters outside the alphabet. */
export function base58Decode(s: string): Uint8Array | null {
  let zeros = 0;
  while (zeros < s.length && s[zeros] === '1') zeros++;
  // Little-endian base-256 digits of the value.
  const digits: number[] = [];
  for (const ch of s.slice(zeros)) {
    const v = ALPHABET.indexOf(ch);
    if (v < 0) return null;
    let carry = v;
    for (let i = 0; i < digits.length; i++) {
      carry += digits[i] * 58;
      digits[i] = carry & 0xff;
      carry >>= 8;
    }
    while (carry) {
      digits.push(carry & 0xff);
      carry >>= 8;
    }
  }
  const out = new Uint8Array(zeros + digits.length);
  for (let i = 0; i < digits.length; i++) out[zeros + i] = digits[digits.length - 1 - i];
  return out;
}

export type WalletCheck =
  | { kind: 'empty' }
  | { kind: 'ok'; address: string }
  | { kind: 'secret'; message: string }
  | { kind: 'invalid'; message: string };

/**
 * Accept a public address; refuse anything that looks like a private key or a
 * recovery phrase, and say why.
 */
export function checkWallet(input: string): WalletCheck {
  const s = input.trim();
  if (!s) return { kind: 'empty' };
  const words = s.split(/\s+/);
  if (words.length >= 12) return { kind: 'secret', message: 'That looks like a recovery phrase. Never paste one into a website. We only need your public address.' };
  if (/^\[\s*\d+\s*(,\s*\d+\s*){15,}\]$/.test(s)) return { kind: 'secret', message: 'That looks like a private key. Never paste one into a website. We only need your public address.' };
  if (words.length > 1) return { kind: 'invalid', message: 'A wallet address is one word, with no spaces.' };
  const bytes = base58Decode(s);
  if (!bytes) return { kind: 'invalid', message: 'That isn’t a Solana address. Addresses use letters and numbers, without 0, O, I or l.' };
  if (bytes.length === 64 || s.length > 60) return { kind: 'secret', message: 'That looks like a private key. Never paste one into a website. We only need your public address.' };
  if (bytes.length !== 32) return { kind: 'invalid', message: 'That isn’t a Solana address. It should be 32 to 44 characters long.' };
  return { kind: 'ok', address: s };
}

export const shortAddress = (a: string) => `${a.slice(0, 4)}…${a.slice(-4)}`;

export interface WalletTrader {
  seed: number;
  name: string;
  archetype: ArchetypeId;
  look: Look;
  risk: number;
  patience: number;
}

/** The trader a wallet makes. The same address always gives the same trader. */
export function traderFromWallet(address: string): WalletTrader {
  const seed = hashString(`wallet|${address}`);
  const r = rng(seed);
  const fem = r.chance(0.35);
  const archetype = r.pick(ARCHETYPE_IDS);
  const look: Look = {
    skin: r.int(SKINS.length),
    hair: r.int(HAIRS.length),
    hairStyle: fem ? r.pick([9, 10, 11, 12, 3, 13]) : r.pick([0, 1, 2, 3, 4, 5, 6, 7, 8, 13]),
    suit: r.int(SUITS.length),
    tie: r.int(TIES.length),
    fem,
    build: r.int(BUILD_NAMES.length),
    height: r.int(3),
    face: fem || r.chance(0.45) ? 0 : 1 + r.int(FACE_NAMES.length - 1),
    outfit: r.int(OUTFIT_NAMES.length),
    shirt: r.int(SHIRTS.length),
    neck: r.int(NECK_NAMES.length),
    eyes: r.chance(0.45) ? 0 : 1 + r.int(EYES_NAMES.length - 1),
    watch: r.chance(0.6),
  };
  return {
    seed,
    name: SURNAMES[r.int(SURNAMES.length)],
    archetype,
    look,
    risk: 0.2 + r.next() * 0.7,
    patience: 0.15 + r.next() * 0.8,
  };
}
