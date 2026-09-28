/**
 * Who is where, and doing what. Seated traders follow the leaderboard;
 * scripted walks cover arrivals, the replay, and escorts out of the building.
 */
import { PARTNER_LOOK } from '../art/partner';
import type { ArchetypeId, FirmState, Look, Trader } from '../sim/types';
import { SAYS } from '../copy';
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

export interface Speech {
  text: string;
  tone: 'buy' | 'win' | 'loss' | 'smug' | 'partner';
}

function hashInt(a: number, b: number) {
  let h = (a * 374761393 + b * 668265263) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return (h ^ (h >>> 16)) >>> 0;
}
const h01 = (a: number, b: number) => hashInt(a, b) / 4294967296;

const BASE: Partial<Record<Pose, number>> = { sit: 4, phone: 2, leanback: 1.5, point: 1, coffee: 1.4 };
const BY_METHOD: Record<ArchetypeId, Partial<Record<Pose, number>>> = {
  permabull: { leanback: 2.5, phone: 1 },
  trend: { phone: 3, point: 1 },
  dip: { phone: 1.5 },
  sniper: { phone: 2.5, sit: 1 },
  diamond: { leanback: 3 },
  fiver: { point: 1.5 },
  intern: { coffee: 2.5, phone: 1 },
  quant: { sit: 3, point: 1.5, phone: -1.5 },
  stops: { sit: 2.5 },
  narrative: { leanback: 1.5, point: 1.5 },
  averager: { phone: 1.5, coffee: 1 },
  contrarian: { leanback: 2.5 },
};
const SAY_FOR: Partial<Record<Pose, keyof typeof SAYS>> = { phone: 'phone', celebrate: 'win', leanback: 'smug', slump: 'loss', point: 'point', coffee: 'coffee' };
const TONE: Record<keyof typeof SAYS, Speech['tone']> = { phone: 'buy', win: 'win', smug: 'smug', loss: 'loss', point: 'buy', coffee: 'smug', partner: 'partner' };

/** What a seated trader is doing right now. */
function mood(tr: Trader, desk: number, t: number, reduced: boolean, isTop: boolean, isBottom: boolean): { pose: Pose; frame: number; say?: Speech } {
  const w: Partial<Record<Pose, number>> = { ...BASE };
  for (const [k, v] of Object.entries(BY_METHOD[tr.archetype] ?? {})) w[k as Pose] = Math.max(0, (w[k as Pose] ?? 0) + (v as number));
  if (tr.resultPct > 5) w.leanback = (w.leanback ?? 0) + 2;
  if (isTop && tr.resultPct > 0) w.celebrate = 3.5;
  if (tr.resultPct < -5) w.phone = (w.phone ?? 0) + 1;
  if (isBottom && tr.resultPct < -5) w.slump = 6;
  else if (tr.resultPct < -15) w.slump = 2;
  const len = 6 + (desk % 4);
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
  if (reduced) return { pose: isBottom && tr.resultPct < -5 ? 'slump' : isTop && tr.resultPct > 0 ? 'leanback' : 'sit', frame: 0 };
  const frame =
    pose === 'sit' ? (into % 5 < 3.6 ? Math.floor(t * 6 + desk) % 2 : 2)
    : pose === 'phone' ? Math.floor(t * 2.6 + desk) % 4
    : pose === 'leanback' ? Math.floor(t / 1.5) % 2
    : pose === 'point' ? Math.floor(t * 3) % 2
    : pose === 'coffee' ? (into % 4 < 1.2 ? 0 : into % 4 < 2 ? 1 : 2)
    : pose === 'celebrate' ? Math.floor(t * 3) % 2
    : Math.floor(t / 1.6) % 2;
  const cat = SAY_FOR[pose];
  let say: Speech | undefined;
  if (cat && into < 3.4 && h01(desk * 7 + slot, 29) < 0.5) {
    const lines = SAYS[cat];
    say = { text: lines[hashInt(desk + slot * 13, 3) % lines.length], tone: TONE[cat] };
  }
  return { pose, frame, say };
}

export class Director {
  /** Speech bubbles for the current frame, by actor id. */
  speech = new Map<string, Speech>();
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

    // Seated traders: each one's mood rotates, weighted by method and by how the day is going.
    this.speech = new Map();
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
      const m = mood(tr, desk, t, reduced, tr === top, tr === bottom);
      out.push({ id: tr.id, look: tr.look, level: spot.level, x: spot.x, y: SEAT_Y, z: spot.z, pose: m.pose, frame: m.frame, layer: 'seated', desk });
      // Speech: fresh trades first, then whatever the mood says.
      const last = tr.recent[0];
      if (last && state.at - last.at >= 0 && state.at - last.at < 4500) {
        const pct = last.pnlPct !== undefined ? ` ${last.pnlPct >= 0 ? '+' : '−'}${Math.abs(last.pnlPct).toFixed(0)}%` : '';
        this.speech.set(tr.id, { text: last.side === 'BUY' ? `Long $${last.ticker}.` : `Out of $${last.ticker}${pct}.`, tone: last.side === 'BUY' ? 'buy' : (last.pnlPct ?? 0) >= 0 ? 'win' : 'loss' });
      } else if (m.say) this.speech.set(tr.id, m.say);
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
    let frame = reduced ? 0 : Math.floor(t / 2.4) % 2;
    const talk = Math.floor(t / 23);
    if (!reduced && t % 23 < 3.6) this.speech.set('partner', { text: SAYS.partner[hashInt(talk, 5) % SAYS.partner.length], tone: 'partner' });
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
