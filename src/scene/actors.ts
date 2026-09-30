/**
 * Who is where, and doing what. Seated traders cycle through desk habits
 * weighted by method, time of day and how their day is going; now and then
 * one goes for a coffee or takes the lift. Scripted walks cover arrivals, the
 * replay and escorts out. The partner has a routine on each floor.
 */
import { PARTNER_LOOK } from '../art/partner';
import type { ArchetypeId, FirmState, Look, Trader } from '../sim/types';
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
  /** Stop here for a while, in this pose. */
  hold?: { pose: Pose; dur: number };
  /** Out of sight (in the lift) while holding. */
  away?: boolean;
}

interface Segment {
  from: Waypoint;
  to: Waypoint;
  t0: number;
  t1: number;
  hidden: boolean;
  /** Standing still in a pose rather than walking. */
  pose?: Pose;
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

function buildSegments(pts: Waypoint[], start: number, speed = SPEED): { segs: Segment[]; end: number } {
  const segs: Segment[] = [];
  let t = start;
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i];
    if (a.hold) {
      segs.push({ from: a, to: a, t0: t, t1: t + a.hold.dur, hidden: !!a.away, pose: a.hold.pose });
      t += a.hold.dur;
    }
    if (i === pts.length - 1) break;
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
      segs.push({ from: p, to: q, t0: t, t1: t + d / speed, hidden: false });
      t += d / speed;
    }
  }
  return { segs, end: t };
}

function inDeskBay(x: number, y: number): boolean {
  if (y >= DESK.y1) return false;
  return BAY_X.some((cx) => x > cx - 22 && x < cx + 22);
}

function hashInt(a: number, b: number) {
  let h = (a * 374761393 + b * 668265263) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return (h ^ (h >>> 16)) >>> 0;
}
const h01 = (a: number, b: number) => hashInt(a, b) / 4294967296;

/** How often each desk habit comes up, before method and mood. */
const BASE: Partial<Record<Pose, number>> = {
  sit: 4,
  phone: 1.6,
  leanback: 1.1,
  point: 0.7,
  coffee: 1,
  stretch: 0.5,
  rub: 0.4,
  mobile: 0.9,
  eat: 0.3,
  tie: 0.4,
  chat: 0.9,
  hips: 0.5,
  arms: 0.4,
};
const BY_METHOD: Record<ArchetypeId, Partial<Record<Pose, number>>> = {
  permabull: { leanback: 2, chat: 1, phone: 0.5 },
  trend: { phone: 2, point: 1, chat: 0.6 },
  dip: { phone: 1, rub: 0.6, hips: 0.4 },
  sniper: { phone: 2, sit: 1.5, eat: -0.2 },
  diamond: { leanback: 2.5, mobile: 1 },
  fiver: { point: 1, stretch: 0.5 },
  intern: { mobile: 1.8, coffee: 1, tie: 0.4 },
  quant: { sit: 3, arms: 0.6, phone: -1.2 },
  stops: { sit: 1.5, hips: 1, tie: 0.5 },
  narrative: { chat: 2, phone: 0.5, leanback: 0.5 },
  averager: { rub: 1, phone: 1, coffee: 0.6 },
  contrarian: { arms: 1.5, leanback: 1 },
};

const frameFor = (pose: Pose, t: number, into: number, desk: number): number => {
  switch (pose) {
    case 'sit':
      return into % 5 < 3.6 ? Math.floor(t * 6 + desk) % 2 : 2;
    case 'phone':
    case 'call':
      return Math.floor(t * 2.4 + desk) % 4;
    case 'coffee':
      return into % 4 < 1.2 ? 0 : into % 4 < 2 ? 1 : 2;
    case 'eat':
      return into % 3 < 1 ? 0 : into % 3 < 1.8 ? 1 : 2;
    case 'drink':
      return into % 4 < 1.4 ? 0 : 1;
    case 'putt':
      return Math.floor(t * 1.6) % 4;
    case 'point':
    case 'celebrate':
      return Math.floor(t * 3) % 2;
    case 'chat':
      return Math.floor(t * 2.2) % 2;
    case 'rub':
      return Math.floor(t * 1.5) % 2;
    case 'stand':
    case 'hips':
    case 'arms':
      return Math.floor(t / 1.8) % 2;
    default:
      return Math.floor(t / 1.3) % 2;
  }
};

/** What a seated trader is doing right now. */
function mood(tr: Trader, desk: number, t: number, hour: number, reduced: boolean, isTop: boolean, isBottom: boolean): { pose: Pose; frame: number } {
  if (reduced) return { pose: isBottom && tr.resultPct < -5 ? 'slump' : isTop && tr.resultPct > 0 ? 'leanback' : 'sit', frame: 0 };
  const w: Partial<Record<Pose, number>> = { ...BASE };
  for (const [k, v] of Object.entries(BY_METHOD[tr.archetype] ?? {})) w[k as Pose] = Math.max(0, (w[k as Pose] ?? 0) + (v as number));
  // Lunch at the desk; the long afternoon.
  if (hour >= 12 && hour < 14) w.eat = (w.eat ?? 0) + 2.5;
  if (hour < 10) w.coffee = (w.coffee ?? 0) + 1.2;
  if (hour >= 17) {
    w.stretch = (w.stretch ?? 0) + 0.8;
    w.rub = (w.rub ?? 0) + 0.8;
    w.tie = (w.tie ?? 0) + 0.6;
  }
  // How the day is going.
  if (tr.resultPct > 5) w.leanback = (w.leanback ?? 0) + 1.5;
  if (isTop && tr.resultPct > 0) w.celebrate = 1.8;
  if (tr.resultPct < -5) {
    w.phone = (w.phone ?? 0) + 0.8;
    w.hips = (w.hips ?? 0) + 0.6;
    w.leanback = Math.max(0, (w.leanback ?? 0) - 1);
  }
  if (isBottom && tr.resultPct < -5) w.slump = 4;
  else if (tr.resultPct < -15) w.slump = 1.5;
  const len = 7 + (desk % 4);
  const phase = (desk * 1.7) % len;
  const slot = Math.floor((t + phase) / len);
  const into = (t + phase) % len;
  const entries = Object.entries(w).filter(([, v]) => (v as number) > 0) as [Pose, number][];
  const total = entries.reduce((a, [, v]) => a + v, 0);
  let r = h01(desk * 131 + slot, 17) * total;
  let pose: Pose = 'sit';
  for (const [k, v] of entries) {
    r -= v;
    if (r < 0) {
      pose = k;
      break;
    }
  }
  return { pose, frame: frameFor(pose, t, into, desk) };
}

/** A trader's walk from the desk to the espresso bar or the lift and back. */
function errandPath(desk: number, kind: 'coffee' | 'lift'): Waypoint[] {
  const spot = deskSpot(desk)!;
  const cx = BAY_X[spot.bay];
  const l = spot.level;
  const side = cx + 18;
  const out: Waypoint[] = [
    { level: l, x: cx, y: SEAT_Y, hold: { pose: 'stretch', dur: 0.8 } },
    { level: l, x: side, y: SEAT_Y },
    { level: l, x: side, y: CORRIDOR_Y },
  ];
  const there: Waypoint[] =
    kind === 'coffee'
      ? [{ level: l, x: 184, y: CORRIDOR_Y }, { level: l, x: 184, y: 15, hold: { pose: 'back', dur: 4.5 } }, { level: l, x: 184, y: CORRIDOR_Y, hold: { pose: 'coffee', dur: 1.2 } }]
      : [{ level: l, x: 10, y: CORRIDOR_Y }, { level: l, x: 3, y: 13, hold: { pose: 'back', dur: 12 }, away: true }, { level: l, x: 10, y: CORRIDOR_Y }];
  return [...out, ...there, { level: l, x: side, y: CORRIDOR_Y }, { level: l, x: side, y: SEAT_Y }, { level: l, x: cx, y: SEAT_Y }];
}

interface Routine {
  x: number;
  y: number;
  pose: Pose;
  dur: number;
}

/** What the partner does on each floor, on a loop. */
const ROUTINES: Record<string, Routine[]> = {
  office: [
    { x: 122, y: 20, pose: 'drink', dur: 7 },
    { x: 122, y: 20, pose: 'watch', dur: 2.5 },
    { x: 52, y: 20, pose: 'putt', dur: 9 },
    { x: 150, y: 21, pose: 'call', dur: 8 },
    { x: 96, y: 21, pose: 'arms', dur: 4 },
  ],
  terminal: [
    { x: 190, y: 20, pose: 'arms', dur: 6 },
    { x: 178, y: 20, pose: 'point', dur: 3 },
    { x: 200, y: 21, pose: 'call', dur: 7 },
    { x: 190, y: 20, pose: 'watch', dur: 2.5 },
  ],
  review: [
    { x: 56, y: 21, pose: 'arms', dur: 4 },
    { x: 100, y: 21, pose: 'hips', dur: 4 },
    { x: 144, y: 21, pose: 'point', dur: 3 },
    { x: 180, y: 21, pose: 'watch', dur: 2.5 },
  ],
  compliance: [
    { x: 190, y: 20, pose: 'arms', dur: 5 },
    { x: 196, y: 22, pose: 'watch', dur: 2.5 },
    { x: 182, y: 21, pose: 'hips', dur: 4 },
  ],
  hr: [
    { x: 186, y: 20, pose: 'call', dur: 6 },
    { x: 196, y: 22, pose: 'arms', dur: 4 },
  ],
  lobby: [
    { x: 66, y: 17, pose: 'hips', dur: 4 },
    { x: 150, y: 19, pose: 'watch', dur: 2.5 },
    { x: 178, y: 16, pose: 'call', dur: 6 },
    { x: 110, y: 20, pose: 'arms', dur: 3 },
  ],
  server: [
    { x: 74, y: 12, pose: 'back', dur: 6 },
    { x: 84, y: 16, pose: 'arms', dur: 4 },
    { x: 74, y: 14, pose: 'watch', dur: 2.5 },
  ],
};
const PARTNER_SPEED = 13;

export class Director {
  private scripts: Script[] = [];
  private errandSlot = -1;
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
    this.errands(state, t);
  }

  /** Every so often, someone gets up for a coffee or takes the lift. */
  private errands(state: FirmState, t: number) {
    const slot = Math.floor(t / 14);
    if (slot === this.errandSlot) return;
    this.errandSlot = slot;
    if (h01(slot, 91) < 0.35) return;
    const seated = state.traders.filter((x) => x.desk && !this.scripts.some((s) => s.id === x.id || s.seatDesk === x.desk));
    if (!seated.length) return;
    const tr = seated[hashInt(slot, 7) % seated.length];
    const spot = deskSpot(tr.desk!);
    if (!spot) return;
    const kind = spot.level === 1 || h01(slot, 13) < 0.25 ? 'coffee' : 'lift';
    if (kind === 'coffee' && spot.level !== 1) return;
    const { segs, end } = buildSegments(errandPath(tr.desk!, kind), t + 0.2, 16);
    this.scripts.push({ id: tr.id, look: tr.look, start: t + 0.2, segs, end, carry: false, seatDesk: tr.desk! });
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
      if (seg.pose) {
        out.push(this.walker(s, seg.from.level, seg.from.x, seg.from.y, seg.pose, reduced ? 0 : frameFor(seg.pose, t, t - seg.t0, 0)));
        continue;
      }
      const k = (t - seg.t0) / (seg.t1 - seg.t0);
      const x = seg.from.x + (seg.to.x - seg.from.x) * k;
      const y = seg.from.y + (seg.to.y - seg.from.y) * k;
      const away = seg.to.x < seg.from.x || seg.to.y < seg.from.y;
      const frame = reduced ? 0 : Math.floor(t * 11) % 8;
      const pose: Pose = s.carry ? (away ? 'backbox' : 'box') : away ? 'back' : 'walk';
      out.push(this.walker(s, seg.from.level, x, y, pose, frame));
    }

    // Seated traders: each one's habits rotate, weighted by method, the hour and how the day is going.
    const hour = new Date(state.at).getHours();
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
      let m = mood(tr, desk, t, hour, reduced, tr === top, tr === bottom);
      // A fresh trade: straight on the phone to confirm it, or a small fist in the air.
      const last = tr.recent[0];
      if (!reduced && last && state.at - last.at >= 0 && state.at - last.at < 4000) {
        const pose: Pose = last.side === 'SELL' && (last.pnlPct ?? 0) > 20 ? 'celebrate' : 'phone';
        m = { pose, frame: frameFor(pose, t, 0, desk) };
      }
      out.push({ id: tr.id, look: tr.look, level: spot.level, x: spot.x, y: SEAT_Y, z: spot.z, pose: m.pose, frame: m.frame, layer: 'seated', desk });
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
    const base = { id: 'partner', look: PARTNER_LOOK, glasses: true, level: spot.level, z: floorZ(spot.level), layer: 'walk' as const, spot: key };
    const steps = ROUTINES[key];
    if (replaying || reduced || !steps) {
      // Greeting everyone at the door, or standing still.
      return { ...base, x: replaying ? 204 : spot.x, y: replaying ? CORRIDOR_Y : spot.y, pose: replaying ? 'arms' : key === 'server' ? 'back' : 'stand', frame: reduced ? 0 : frameFor('arms', t, 0, 0) };
    }
    // Walk the loop: from each stop to the next, then hold the pose there.
    const legs = steps.map((s, i) => {
      const prev = steps[(i + steps.length - 1) % steps.length];
      return { s, prev, walk: (Math.abs(s.x - prev.x) + Math.abs(s.y - prev.y)) / PARTNER_SPEED };
    });
    const period = legs.reduce((a, l) => a + l.walk + l.s.dur, 0);
    let u = t % period;
    for (const { s, prev, walk } of legs) {
      if (u < walk) {
        // Axis-aligned: along x first, then y.
        const dx = Math.abs(s.x - prev.x) / PARTNER_SPEED;
        const alongX = u < dx;
        const k = alongX ? (dx ? u / dx : 1) : (u - dx) / Math.max(1e-6, walk - dx);
        const x = alongX ? prev.x + (s.x - prev.x) * k : s.x;
        const y = alongX ? prev.y : prev.y + (s.y - prev.y) * k;
        const away = alongX ? s.x < prev.x : s.y < prev.y;
        return { ...base, x, y, pose: away ? 'back' : 'walk', frame: Math.floor(t * 9) % 8 };
      }
      u -= walk;
      if (u < s.dur) return { ...base, x: s.x, y: s.y, pose: s.pose, frame: frameFor(s.pose, t, u, 0) };
      u -= s.dur;
    }
    return { ...base, x: spot.x, y: spot.y, pose: 'stand', frame: 0 };
  }
}

export const ELEVATOR_Y = ELEVATOR;
