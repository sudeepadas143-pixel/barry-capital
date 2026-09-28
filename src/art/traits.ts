/**
 * Gives every trader a distinct look: build, height, haircut, facial hair,
 * outfit, shirt, neckwear and accessories. The starting roster is dressed by
 * hand; everyone else is dressed from their method plus a hash of their seed,
 * so the same trader always looks the same and the simulation never changes.
 */
import type { ArchetypeId, Look } from '../sim/types';

type Extra = Required<Omit<Look, 'skin' | 'hair' | 'suit' | 'tie'>> & Partial<Pick<Look, 'skin' | 'hair' | 'suit' | 'tie'>>;

/** Hand-dressed starting roster. */
const ROSTER: Record<string, Partial<Extra>> = {
  whitlock: { hairStyle: 3, outfit: 1, shirt: 2, neck: 0, eyes: 0, face: 0, build: 2, height: 2, watch: true, tie: 0 },
  osei: { hairStyle: 7, outfit: 2, shirt: 1, neck: 3, eyes: 3, face: 1, build: 1, height: 1 },
  castellano: { hairStyle: 9, outfit: 0, shirt: 0, neck: 3, eyes: 0, face: 0, build: 0, height: 1, fem: true, watch: true },
  lindqvist: { hairStyle: 11, outfit: 0, shirt: 0, neck: 3, eyes: 1, face: 0, build: 0, height: 2, fem: true, suit: 4 },
  marsh: { hairStyle: 2, outfit: 4, shirt: 4, neck: 0, eyes: 2, face: 2, build: 2, height: 0, watch: true },
  adebayo: { hairStyle: 10, outfit: 0, shirt: 3, neck: 3, eyes: 2, face: 0, build: 0, height: 1, fem: true },
  varga: { hairStyle: 6, outfit: 3, shirt: 0, neck: 4, eyes: 0, face: 0, build: 0, height: 0 },
  halloran: { hairStyle: 5, outfit: 5, shirt: 0, neck: 3, eyes: 2, face: 3, build: 1, height: 1, suit: 4 },
  beaumont: { hairStyle: 0, outfit: 4, shirt: 1, neck: 2, eyes: 2, face: 0, build: 0, height: 1 },
  rourke: { hairStyle: 8, outfit: 5, shirt: 0, neck: 3, eyes: 0, face: 2, build: 1, height: 2 },
  tanaka: { hairStyle: 1, outfit: 3, shirt: 1, neck: 1, eyes: 4, face: 1, build: 1, height: 1, watch: true },
};

/** What each method tends to wear. */
const BY_METHOD: Record<ArchetypeId, { outfits: number[]; necks: number[]; eyes: number[]; hair: number[] }> = {
  permabull: { outfits: [1, 6, 0], necks: [0, 0, 1], eyes: [0, 1], hair: [3, 7, 0] },
  trend: { outfits: [2, 2, 0], necks: [3, 0], eyes: [3, 0, 4], hair: [7, 1, 0] },
  dip: { outfits: [3, 0], necks: [1, 0], eyes: [0, 0, 2], hair: [1, 6, 13] },
  sniper: { outfits: [0, 5], necks: [3, 0], eyes: [1, 4], hair: [4, 1, 3] },
  diamond: { outfits: [4, 6], necks: [0, 2], eyes: [2, 0], hair: [2, 5, 0] },
  fiver: { outfits: [0, 1], necks: [0, 2], eyes: [2, 0], hair: [0, 1] },
  intern: { outfits: [3, 0], necks: [4, 0], eyes: [0, 2], hair: [6, 1, 13] },
  quant: { outfits: [5, 2], necks: [3], eyes: [2, 0], hair: [5, 4, 0] },
  stops: { outfits: [4, 0], necks: [2, 0], eyes: [2], hair: [0, 1] },
  narrative: { outfits: [5, 2], necks: [3], eyes: [0, 1], hair: [8, 7, 13] },
  averager: { outfits: [3, 0], necks: [1], eyes: [0, 4], hair: [1, 2, 6] },
  contrarian: { outfits: [5, 0], necks: [3], eyes: [1, 0], hair: [3, 4, 5] },
};

const FEM_HAIR = [9, 10, 11, 12, 3, 13];

function h(seed: number, k: number): number {
  let x = (seed ^ Math.imul(k + 1, 0x9e3779b1)) >>> 0;
  x = Math.imul(x ^ (x >>> 16), 0x85ebca6b);
  x = Math.imul(x ^ (x >>> 13), 0xc2b2ae35);
  return ((x ^ (x >>> 16)) >>> 0) / 4294967296;
}

const pick = <T,>(arr: T[], r: number) => arr[Math.floor(r * arr.length) % arr.length];

/** Fill in any missing detail on a look. Explicit fields always win. */
export function dress(look: Look, archetype: ArchetypeId | undefined, seed: number, name?: string): Look {
  const hand = name ? ROSTER[name] : undefined;
  const m = BY_METHOD[archetype ?? 'fiver'];
  const fem = look.fem ?? (hand ? !!hand.fem : h(seed, 1) < 0.32);
  const base: Look = {
    ...look,
    fem,
    hairStyle: fem ? pick(FEM_HAIR, h(seed, 2)) : pick(m.hair, h(seed, 2)) ?? look.hairStyle,
    build: fem ? Math.floor(h(seed, 3) * 2) : Math.floor(h(seed, 3) * 3),
    height: Math.floor(h(seed, 4) * 3),
    face: fem ? 0 : h(seed, 5) < 0.5 ? 0 : 1 + Math.floor(h(seed, 6) * 4),
    outfit: pick(m.outfits, h(seed, 7)),
    shirt: Math.floor(h(seed, 8) * 5),
    neck: fem ? pick([3, 3, 0], h(seed, 9)) : pick(m.necks, h(seed, 9)),
    eyes: pick(m.eyes, h(seed, 10)),
    watch: h(seed, 11) < 0.45,
    cigar: false,
  };
  const out: Look = { ...base, ...(hand ?? {}) };
  // Anything set explicitly on the incoming look (e.g. a visitor's choices) wins.
  for (const k of ['build', 'height', 'face', 'outfit', 'shirt', 'neck', 'eyes', 'watch', 'cigar', 'fem'] as const) {
    if (look[k] !== undefined) (out as unknown as Record<string, unknown>)[k] = look[k];
  }
  if (look.fem !== undefined || look.outfit !== undefined) out.hairStyle = look.hairStyle;
  if (out.fem) out.face = 0;
  return out;
}

export const hasDetail = (l: Look) => l.outfit !== undefined;
