/**
 * Screen-space hit areas for each desk, in native pixels. The procedural
 * building computes them from the layout; custom art supplies them in
 * /art/hotspots.json with the same shape.
 */
import { Iso } from './iso';
import { PixelBuffer } from './buffer';
import { BAY_X, DESKS, H, INTERIOR, OX, OY, W, Y, floorZ, PARTNER_SPOTS } from './layout';

export type Pt = [number, number];

export interface DeskHotspot {
  desk: number;
  polygon: Pt[];
  /** Bottom-centre of a seated trader, in native pixels. */
  seat: Pt;
}

export interface Hotspots {
  width: number;
  height: number;
  desks: DeskHotspot[];
  partner?: Record<string, Pt>;
}

function hull(points: Pt[]): Pt[] {
  const p = [...points].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cross = (o: Pt, a: Pt, b: Pt) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower: Pt[] = [];
  for (const q of p) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], q) <= 0) lower.pop();
    lower.push(q);
  }
  const upper: Pt[] = [];
  for (let i = p.length - 1; i >= 0; i--) {
    const q = p[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], q) <= 0) upper.pop();
    upper.push(q);
  }
  return [...lower.slice(0, -1), ...upper.slice(0, -1)];
}

export function proceduralHotspots(): Hotspots {
  const iso = new Iso(new PixelBuffer(1, 1), OX, OY);
  const desks = DESKS.map((d) => {
    const cx = BAY_X[d.bay];
    const zf = floorZ(d.level);
    const pts: Pt[] = [];
    for (const x of [cx - 22, cx + 22]) for (const y of [0, Y]) for (const z of [zf, zf + INTERIOR - 12]) pts.push(iso.at(x, y, z));
    return { desk: d.desk, polygon: hull(pts), seat: iso.at(cx, d.y, zf) };
  });
  const partner: Record<string, Pt> = {};
  for (const [k, s] of Object.entries(PARTNER_SPOTS)) partner[k] = iso.at(s.x, s.y, floorZ(s.level));
  return { width: W, height: H, desks, partner };
}

export function inside(poly: Pt[], x: number, y: number): boolean {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}

export function hitDesk(h: Hotspots, x: number, y: number): number | null {
  for (const d of h.desks) if (inside(d.polygon, x, y)) return d.desk;
  return null;
}
