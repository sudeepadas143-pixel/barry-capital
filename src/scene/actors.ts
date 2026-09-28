/**
 * Who is where, and doing what. Seated traders follow the leaderboard;
 * scripted walks cover arrivals, the replay, and escorts out of the building.
 */
import { PARTNER_LOOK } from '../art/partner';
import type { FirmState, Look, Trader } from '../sim/types';
import { DESK_COUNT } from '../../firm.config';
import { BAY_X, CORRIDOR_Y, DESK, ELEVATOR, PARTNER_SPOTS, SEAT_Y, deskSpot, floorZ } from './layout';
import type { Pose } from './sprites';

export interface Actor {
  id: string;
  look: Look;
  glasses?: boolean;
  level: number;
  x: number;
  y: number;
  z: number;
  pose: Pose;
  frame: number;
  layer: 'seated' | 'walk' | 'outside';
  desk?: number;
  /** For the partner: the named spot currently occupied. */
  spot?: string;
}

interface Waypoint {
  level: number;
  x: number;
  y: number;
}

interface Segment {
  from: Waypoint;
  to: Waypoint;
  t0: number;
  t1: number;
  hidden: boolean;
}

interface Script {
  id: string;
  look: Look;
  glasses?: boolean;
  start: number;
  segs: Segment[];
  end: number;
  carry: boolean;
  /** Desk reserved while walking in; the seat shows empty until arrival. */
  seatDesk?: number;
  /** Stay visible, standing at the final point, until this time. */
  linger?: number;
}

const SPEED = 26; // world units per second
const DOOR_IN = { x: 214, y: 14 };
const OUTSIDE: Waypoint[] = [
  { level: 0, x: 256, y: 40 },
  { level: 0, x: 256, y: 12 },
  { level: 0, x: 246, y: 12 },
  { level: 0, x: DOOR_IN.x, y: 12 },
];

export function lotZ(x: number): number {
  if (x >= 248) return 0;
  if (x >= 245) return 3;
  return floorZ(0);
}

function arrivalPath(desk: number): Waypoint[] {
  const spot = deskSpot(desk)!;
  const cx = BAY_X[spot.bay];
  const side = cx + 18;
  const pts: Waypoint[] = [...OUTSIDE, { level: 0, x: 200, y: CORRIDOR_Y }, { level: 0, x: 10, y: CORRIDOR_Y }, { level: 0, x: 3, y: 13 }];
  pts.push({ level: spot.level, x: 3, y: 13 }, { level: spot.level, x: 10, y: CORRIDOR_Y }, { level: spot.level, x: side, y: CORRIDOR_Y }, { level: spot.level, x: side, y: SEAT_Y }, { level: spot.level, x: cx, y: SEAT_Y });
  return pts;
}

function exitPath(desk: number): Waypoint[] {
  return [...arrivalPath(desk)].reverse();
}

function buildSegments(pts: Waypoint[], start: number): { segs: Segment[]; end: number } {
  const segs: Segment[] = [];
  let t = start;
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i];
    const b = pts[i + 1];
    if (a.level !== b.level) {
      const dur = 1.2 + 0.45 * Math.abs(a.level - b.level);
      segs.push({ from: a, to: b, t0: t, t1: t + dur, hidden: true });
      t += dur;
      continue;
    }
    // Axis-aligned legs: x first, then y.
    const mid = { level: a.level, x: b.x, y: a.y };
    for (const [p, q] of [
      [a, mid],
      [mid, b],
    ] as const) {
      const d = Math.abs(q.x - p.x) + Math.abs(q.y - p.y);
      if (!d) continue;
      segs.push({ from: p, to: q, t0: t, t1: t + d / SPEED, hidden: false });
      t += d / SPEED;
    }
  }
  return { segs, end: t };
}

function inDeskBay(x: number, y: number): boolean {
  if (y >= DESK.y1) return false;
  return BAY_X.some((cx) => x > cx - 22 && x < cx + 22);
}

export class Director {
  private scripts: Script[] = [];
  private seen = new Set<string>();
  private replayUntil = 0;
  private primed = false;

  /** Replay everyone walking in, one by one. */
  replay(state: FirmState, t: number) {
    this.scripts = this.scripts.filter((s) => s.carry);
    const seated = [...state.traders, ...state.mine.slice(0, 1).map((m) => ({ ...m, desk: DESK_COUNT + 1 }))]
      .filter((x) => x.desk)
      .sort((a, b) => a.desk! - b.desk!);
    seated.forEach((tr, i) => {
      const { segs, end } = buildSegments(arrivalPath(tr.desk!), t + 0.6 + i * 1.15);
      this.scripts.push({ id: tr.id, look: tr.look, start: t + 0.6 + i * 1.15, segs, end, carry: false, seatDesk: tr.desk! });
    });
    this.replayUntil = t + 0.6 + seated.length * 1.15 + 18;
  }

  /** Pick up hires and departures from the feed as they happen. */
  sync(state: FirmState, byId: Map<string, Trader>, now: number, t: number) {
    for (const f of state.feed) {
      if (f.type !== 'event' || (f.kind !== 'escorted' && f.kind !== 'hired') || !f.traderId) continue;
      if (this.seen.has(f.id)) continue;
      this.seen.add(f.id);
      const age = (now - f.at) / 1000;
      // On first load, only animate what happened in the last minute.
      if (age > 60 || age < 0) continue;
      const tr = byId.get(f.traderId);
      if (!tr || !tr.desk) continue;
      const start = t + (this.primed ? 0 : 0.5);
      if (f.kind === 'escorted') {
        const { segs, end } = buildSegments(exitPath(tr.desk), start + 1.2);
        this.scripts.push({ id: `${tr.id}:out`, look: tr.look, start, segs, end, carry: true });
      } else {
        const { segs, end } = buildSegments(arrivalPath(tr.desk), start);
        this.scripts.push({ id: tr.id, look: tr.look, start, segs, end, carry: false, seatDesk: tr.desk });
      }
    }
    const mine = state.mine[0];
    if (mine && !this.seen.has(`hire:${mine.id}`)) {
      this.seen.add(`hire:${mine.id}`);
      if (this.primed && state.tick - mine.hiredTick <= 2) {
        const desk = DESK_COUNT + 1;
        const { segs, end } = buildSegments(arrivalPath(desk), t + 0.3);
        this.scripts.push({ id: mine.id, look: mine.look, start: t + 0.3, segs, end, carry: false, seatDesk: desk });
      }
    }
    this.primed = true;
    this.scripts = this.scripts.filter((s) => t < s.end + 0.2);
  }

  /** True while someone is passing through the revolving door. */
  doorBusy(t: number): boolean {
    return this.scripts.some((s) =>
      s.segs.some((g) => !g.hidden && t >= g.t0 && t <= g.t1 && g.from.level === 0 && Math.max(g.from.x, g.to.x) >= 230 && Math.min(g.from.x, g.to.x) <= 246),
    );
  }

  actors(state: FirmState, t: number, reduced: boolean): Actor[] {
    const out: Actor[] = [];
    const walking = new Set<string>();
    const pending = new Set<number>();

    for (const s of this.scripts) {
      if (s.seatDesk) pending.add(s.seatDesk);
      walking.add(s.id);
      if (t < s.start) continue;
      const seg = s.segs.find((g) => t >= g.t0 && t < g.t1);
      if (!seg) {
        if (t >= s.end) {
          if (s.seatDesk) pending.delete(s.seatDesk);
          continue;
        }
        // Standing up / pausing before the first leg.
        const p = s.segs[0]?.from;
        if (!p) continue;
        out.push(this.walker(s, p.level, p.x, p.y, 'stand', 0));
        continue;
      }
      if (seg.hidden) continue;
      const k = (t - seg.t0) / (seg.t1 - seg.t0);
      const x = seg.from.x + (seg.to.x - seg.from.x) * k;
      const y = seg.from.y + (seg.to.y - seg.from.y) * k;
      const away = seg.to.x < seg.from.x || seg.to.y < seg.from.y;
      const frame = reduced ? 0 : Math.floor(t * 11) % 8;
      const pose: Pose = s.carry ? (away ? 'backbox' : 'box') : away ? 'back' : 'walk';
      out.push(this.walker(s, seg.from.level, x, y, pose, frame));
    }

    // Seated traders.
    const seated = state.traders.filter((x) => x.desk);
    const ranked = [...seated].sort((a, b) => b.resultPct - a.resultPct);
    const top = ranked[0];
    const bottom = ranked[ranked.length - 1];
    const sitters: Trader[] = [...seated];
    if (state.mine[0]) sitters.push({ ...state.mine[0], desk: DESK_COUNT + 1 });
    for (const tr of sitters) {
      const desk = tr.desk!;
      if (pending.has(desk) || walking.has(tr.id)) continue;
      const spot = deskSpot(desk);
      if (!spot) continue;
      const phase = (desk * 1.7) % 5;
      let pose: Pose = 'sit';
      let frame = 2;
      if (!reduced) {
        const cyc = (t + phase) % 7;
        frame = cyc < 5 ? Math.floor(t * 6 + desk) % 2 : 2;
      }
      if (tr === top && top.resultPct > 0 && ((t + phase) % 9 < 2.6 || reduced)) {
        pose = 'celebrate';
        frame = reduced ? 0 : Math.floor(t * 3) % 2;
      } else if (tr === bottom && bottom.resultPct < -5) {
        pose = 'slump';
        frame = reduced ? 0 : Math.floor(t / 1.6) % 2;
      }
      out.push({ id: tr.id, look: tr.look, level: spot.level, x: spot.x, y: SEAT_Y, z: spot.z, pose, frame, layer: 'seated', desk });
    }

    // The managing partner.
    out.push(this.partner(state, t, reduced));
    return out;
  }

  private walker(s: Script, level: number, x: number, y: number, pose: Pose, frame: number): Actor {
    const outside = level === 0 && x > 238;
    const z = level === 0 && x > 236 ? lotZ(x) : floorZ(level);
    return {
      id: s.id,
      look: s.look,
      glasses: s.glasses,
      level,
      x,
      y,
      z,
      pose,
      frame,
      layer: outside ? 'outside' : inDeskBay(x, y) ? 'seated' : 'walk',
    };
  }

  private partner(state: FirmState, t: number, reduced: boolean): Actor {
    const replaying = t < this.replayUntil;
    const key = replaying ? 'lobby' : state.partnerFloor;
    const spot = PARTNER_SPOTS[key] ?? PARTNER_SPOTS.office;
    let x = replaying ? 204 : spot.x;
    const y = replaying ? CORRIDOR_Y : spot.y;
    let pose: Pose = key === 'server' ? 'back' : 'stand';
    let frame = 0;
    if (!replaying && spot.pace && !reduced) {
      // Pace back and forth with pauses at each end.
      const period = 10;
      const p = (t % period) / period;
      const seg = p < 0.35 ? p / 0.35 : p < 0.5 ? 1 : p < 0.85 ? 1 - (p - 0.5) / 0.35 : 0;
      x = spot.x - spot.pace / 2 + seg * spot.pace;
      const moving = (p < 0.35 || (p >= 0.5 && p < 0.85));
      if (moving) {
        pose = p < 0.35 ? 'walk' : 'back';
        frame = Math.floor(t * 11) % 8;
      }
    }
    return {
      id: 'partner',
      look: PARTNER_LOOK,
      glasses: true,
      level: spot.level,
      x,
      y,
      z: floorZ(spot.level),
      pose,
      frame,
      layer: 'walk',
      spot: key,
    };
  }
}

export const ELEVATOR_Y = ELEVATOR;
