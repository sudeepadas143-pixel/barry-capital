import type { Look } from '../sim/types';

/** Skin tones, light to deep. */
export const SKINS = ['#f3d2b3', '#e6b48c', '#c98e62', '#a86c45', '#7f4d2f', '#5c3621'];
/** Hair colours. */
export const HAIRS = ['#2b2320', '#4e3122', '#80532c', '#c49a57', '#8f8d88', '#d9d6cf', '#7c3320'];
/** Suits: navy, charcoal, grey, brown, black, olive. */
export const SUITS = ['#26314a', '#3a3a3e', '#5d6169', '#5b4432', '#1f1f23', '#4b4f37'];
/** Ties: burgundy, brass, bottle green, club blue, dusty pink, black. */
export const TIES = ['#8b2f30', '#b88a38', '#3e6a4e', '#3a5580', '#c27b87', '#222226'];

export const SUIT_NAMES = ['navy', 'charcoal', 'flannel grey', 'tobacco', 'black', 'olive'];
export const TIE_NAMES = ['burgundy', 'brass', 'bottle green', 'club blue', 'dusty pink', 'black'];
export const HAIR_NAMES = ['black', 'dark brown', 'chestnut', 'sandy', 'grey', 'white', 'auburn'];
export const HAIR_STYLE_NAMES = [
  'side part',
  'short crop',
  'receding',
  'slicked back',
  'buzz cut',
  'bald',
  'curly top',
  'pompadour',
  'man bun',
  'long',
  'bob',
  'ponytail',
  'bun',
  'afro',
  'curtains',
];
/** Shirts: white, pale blue, pink, lavender, blue stripe. */
export const SHIRTS = ['#f6f3ec', '#cfe0f2', '#f2cfd6', '#ddd3ee', '#d8e6f5'];
export const SHIRT_NAMES = ['white', 'pale blue', 'pink', 'lavender', 'blue stripe'];
/** Fleece vests and turtlenecks. */
export const VESTS = ['#6d737c', '#33405a', '#2a2b30', '#59603f'];
export const OUTFIT_NAMES = ['suit', 'pinstripe suit', 'fleece vest', 'shirtsleeves and braces', 'waistcoat', 'turtleneck and blazer', 'double-breasted'];
export const NECK_NAMES = ['tie', 'loosened tie', 'bow tie', 'open collar', 'lanyard'];
export const EYES_NAMES = ['nothing', 'sunglasses, indoors', 'glasses', 'headset', 'earpiece'];
export const FACE_NAMES = ['clean-shaven', 'stubble', 'short beard', 'moustache', 'goatee'];
export const BUILD_NAMES = ['slim', 'average', 'broad'];

export const INK = '#1d1c19';
export const SHIRT = '#f4f1e8';
export const SHIRT_SHADE = '#d6d1c3';

export function shade(hex: string, amt: number): string {
  const n = parseInt(hex.slice(1), 16);
  const f = (c: number) => Math.max(0, Math.min(255, Math.round(c * (1 + amt))));
  const r = f((n >> 16) & 255);
  const g = f((n >> 8) & 255);
  const b = f(n & 255);
  return `#${((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1)}`;
}

/**
 * Sprite grids are strings of palette keys. This resolves each key to a colour
 * for one character. '.' is transparent.
 */
export type PaletteMap = Record<string, string>;

export function paletteFor(look: Look): PaletteMap {
  const skin = SKINS[look.skin % SKINS.length];
  const hair = HAIRS[look.hair % HAIRS.length];
  const suit = SUITS[look.suit % SUITS.length];
  const tie = TIES[look.tie % TIES.length];
  return {
    o: INK,
    s: skin,
    S: shade(skin, -0.16),
    h: hair,
    H: shade(hair, hair === HAIRS[5] ? -0.12 : 0.28),
    u: suit,
    U: shade(suit, -0.28),
    v: shade(suit, 0.22),
    w: SHIRT,
    W: SHIRT_SHADE,
    t: tie,
    T: shade(tie, -0.25),
    e: '#1d1c19',
    m: shade(skin, -0.32),
    b: '#1f1c1a',
    g: '#b3903f',
  };
}
