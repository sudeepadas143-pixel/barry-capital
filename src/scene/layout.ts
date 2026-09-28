/**
 * The building as data. Everything the renderer and the actors need to know
 * about where things are lives here, so the art can be re-laid out or swapped.
 *
 * World units: +x down-right, +y down-left, +z up. Rooms are shallow (Y) and
 * tall (interior height) so their contents stay visible through the cutaway.
 */
import { DESK_COUNT } from '../../firm.config';

/** Pixels per world unit. */
export const S = 3;
export const W = 316 * S;
export const H = 560 * S;
export const OX = 32 * S;
export const OY = 352 * S;
/** How far the tower rises above the partner's floor before fading out. */
export const TOWER_H = 58;

/** Building length, depth, floor-to-floor height and slab thickness. */
export const X = 236;
export const Y = 24;
export const FH = 49;
export const ST = 5;
export const INTERIOR = FH - ST;

/** Lot to the right of the building. */
export const LOT = { x0: 236, x1: 272, y0: -6, y1: 30 };
export const GROUND_DEPTH = 55;

export type LevelKind = 'server' | 'lobby' | 'desks' | 'office';
export type Feature = 'kitchen' | 'hr' | 'compliance' | 'terminal' | null;

export interface Level {
  index: number;
  kind: LevelKind;
  feature: Feature;
  label: string;
  /** Desk numbers on this level, in bay order. 0 marks the pencilled-in desk. */
  desks: number[];
}

export const LEVELS: Level[] = [
  { index: -1, kind: 'server', feature: null, label: 'B', desks: [] },
  { index: 0, kind: 'lobby', feature: null, label: 'L', desks: [] },
  { index: 1, kind: 'desks', feature: 'kitchen', label: '2', desks: [1, 2, 3] },
  { index: 2, kind: 'desks', feature: 'hr', label: '3', desks: [4, 5, 6] },
  { index: 3, kind: 'desks', feature: 'compliance', label: '4', desks: [7, 8, 9] },
  { index: 4, kind: 'desks', feature: 'terminal', label: '5', desks: [10, 11, 0] },
  { index: 5, kind: 'office', feature: null, label: '6', desks: [] },
];

export const base = (level: number) => level * FH;
export const floorZ = (level: number) => level * FH + ST;
/** Top of the highest level's ceiling, where the roof slab starts. */
export const ROOF_Z = (LEVELS[LEVELS.length - 1].index + 1) * FH;

/** Bay centres along x. */
export const BAY_X = [56, 100, 144];
export const BAY_W = 44;
export const ELEVATOR = { y0: 7, y1: 19, x: 0 };
export const CORRIDOR_Y = 20;
export const SEAT_Y = 8;
export const DESK = { y0: 11, y1: 17, h: 6, half: 14 };

export interface DeskSpot {
  desk: number;
  level: number;
  bay: number;
  x: number;
  y: number;
  z: number;
}

export const DESKS: DeskSpot[] = (() => {
  const out: DeskSpot[] = [];
  for (const l of LEVELS)
    l.desks.forEach((d, bay) => {
      out.push({ desk: d === 0 ? DESK_COUNT + 1 : d, level: l.index, bay, x: BAY_X[bay], y: SEAT_Y, z: floorZ(l.index) });
    });
  return out;
})();

export const deskSpot = (desk: number) => DESKS.find((d) => d.desk === desk);

/** Where the managing partner stands on each floor. */
export const PARTNER_SPOTS: Record<string, { level: number; x: number; y: number; pace?: number }> = {
  office: { level: 5, x: 120, y: 12, pace: 16 },
  terminal: { level: 4, x: 196, y: 20, pace: 8 },
  review: { level: 4, x: 176, y: 21, pace: 22 },
  compliance: { level: 3, x: 190, y: 20, pace: 6 },
  hr: { level: 2, x: 186, y: 20, pace: 8 },
  lobby: { level: 0, x: 170, y: 18, pace: 24 },
  server: { level: -1, x: 74, y: 12 },
};

/** Revolving door on the right facade, and the path through the lot. */
export const DOOR = { y: 12, inside: { x: 214, y: 14 }, outside: { x: 246, y: 12 } };
export const STREET = { x: 256, y: 34 };
