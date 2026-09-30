/**
 * Draws the procedural building into layers: a glass-and-steel trading tower
 * on a street off Wall Street, cut open along its long face. Static art only;
 * anything that moves is painted later over key-coloured regions (anim.ts).
 */
import { FIRM_NAME } from '../../firm.config';
import { PixelBuffer, mixColor } from './buffer';
import { renderBust } from '../art/figure';
import { renderBell, renderBull, renderCamera, renderGlobe, renderPlant, type PlantKind } from '../art/props';
import { PARTNER_LOOK } from '../art/partner';
import { C } from './colors';
import { Iso, type BoxColors } from './iso';
import { PixelSurface, type Pt, type SpriteSrc, type Surface, type TextOpts } from './surface';
import {
  BAY_X,
  DESK,
  ELEVATOR,
  FH,
  GROUND_DEPTH,
  H,
  LEVELS,
  LOT,
  OX,
  OY,
  ROOF_Z,
  S,
  ST,
  TOWER_H,
  W,
  X,
  Y,
  base,
  floorZ,
  type Level,
} from './layout';

/** Supersampling for painted props: more samples when the pixels are coarse. */
export const ssFor = (scale: number) => (scale >= 6 ? 2 : 3);

const plant = (kind: PlantKind): SpriteSrc => ({ id: `plant:${kind}`, render: (k) => renderPlant(kind, S * k, ssFor(S * k)) });
const PLANTS = {
  palm: plant('palm'),
  fern: plant('fern'),
  succulent: plant('succulent'),
  shrub: plant('shrub'),
  flowers: plant('flowers'),
};
const BULL: SpriteSrc = { id: 'bull', render: (k) => renderBull(S * 1.35 * k, ssFor(S * k)) };
const GLOBE: SpriteSrc = { id: 'globe', render: (k) => renderGlobe(S * k, ssFor(S * k)) };
const CAMERA: SpriteSrc = { id: 'camera', render: (k) => renderCamera(S * k, ssFor(S * k)) };
const BELL: SpriteSrc = { id: 'bell', render: (k) => renderBell(S * k, ssFor(S * k)) };
const PORTRAIT: SpriteSrc = { id: 'portrait', render: (k) => renderBust(PARTNER_LOOK, Math.round(13 * S * k), true, ssFor(S * k)) };

const MONO = (size: number, color: number, weight = 600): TextOpts => ({ font: 'mono', size, color, weight, align: 'center' });

export interface ScreenSpec {
  kind: 'desk' | 'side' | 'terminal' | 'crt';
  desk?: number;
  slot?: number;
  /** 'y': plane y = y spanning x0..x1. 'x': plane x = x spanning y0..y1 (x0/x1 then hold y0/y1). */
  plane?: 'y' | 'x';
  x?: number;
  y: number;
  x0: number;
  x1: number;
  z0: number;
  z1: number;
}

export interface Built {
  screens: ScreenSpec[];
  ticker: { y: number; x0: number; x1: number; z0: number; z1: number };
  /** LED ticker strips along the cut edge of each floor. */
  bands: { level: number; z0: number }[];
  /** Screen quads of each server LED. */
  leds: Pt[][];
  steam: [number, number][];
  cat: [number, number];
  antenna: [number, number];
  pendulum: [number, number];
  door: { x: number; y0: number; y1: number; z0: number; z1: number };
  /** Screen row where the tower has fully faded out. */
  towerTop: number;
}

const steel: BoxColors = { top: C.steelHi, left: C.steel, right: C.steelLo };
const chrome: BoxColors = { top: C.mull, left: C.steelHi, right: C.steel };
const leather: BoxColors = { top: rgba2('#3a2f2b'), left: rgba2('#2a2220'), right: rgba2('#1c1716') };
const bezel: BoxColors = { top: C.bezelHi, left: C.bezel, right: C.screenOff };
const walnut: BoxColors = { top: C.walnutHi, left: C.walnut, right: C.walnutLo };
const blackTop: BoxColors = { top: C.deskTop, left: C.walnut, right: C.walnutLo, hi: C.deskTopHi };
const granite: BoxColors = { top: C.graniteL, left: C.granite, right: C.graniteD, hi: C.graniteHi };
const marbleWhite: BoxColors = { top: C.marbleA, left: C.marbleB, right: C.marbleVein, hi: C.white };

function rgba2(hex: string) {
  const n = parseInt(hex.slice(1), 16);
  return ((255 << 24) | ((n & 255) << 16) | (((n >> 8) & 255) << 8) | ((n >> 16) & 255)) >>> 0;
}

/** A 1px line between two world points (screen-space). */
function line3(iso: Iso, a: [number, number, number], b: [number, number, number], c: number, th = 1) {
  const [ax, ay] = iso.p(...a);
  const [bx, by] = iso.p(...b);
  iso.buf.poly([[ax, ay], [bx, by], [bx, by + th], [ax, ay + th]], c);
}
function vline(iso: Iso, x: number, y: number, z0: number, z1: number, c: number, w = 1) {
  const sx = Math.floor(iso.sx(x, y));
  const a = Math.floor(iso.sy(x, y, z1));
  const b = Math.floor(iso.sy(x, y, z0));
  iso.buf.rect(sx, a, w, b - a, c);
}
function hash(a: number, b: number) {
  let h = (a * 374761393 + b * 668265263) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

// ---------------------------------------------------------------- windows onto the city

/** Floor-to-ceiling glass on the back wall, looking down on the city. */
function cityWindow(iso: Iso, zf: number, x0: number, x1: number, seed: number) {
  const top = zf + 30;
  const horizon = zf + 13;
  iso.faceY(0, x0, x1, horizon, top, C.skyTop);
  iso.faceY(0, x0, x1, horizon, zf + 18, C.skyMid);
  iso.faceY(0, x0, x1, zf + 1, horizon, C.skyLow);
  // Distant towers, their tops below eye level. We are very high up.
  let x = x0;
  let i = 0;
  while (x < x1) {
    const w = 4 + Math.floor(hash(seed + i, 1) * 9);
    const hgt = 4 + Math.floor(hash(seed + i, 2) * 12);
    const col = [C.cityA, C.cityB, C.cityC][i % 3];
    const xe = Math.min(x1, x + w);
    iso.faceY(0, x, xe, zf + 1, zf + hgt, col);
    iso.faceY(0, x, xe, zf + hgt - 0.6, zf + hgt, C.cityRoof);
    for (let wx = x + 1; wx < xe - 0.5; wx += 1.5)
      for (let wz = zf + 2; wz < zf + hgt - 1.5; wz += 1.6)
        if (hash(wx * 7 + i, wz * 3) > 0.55) iso.faceY(0, wx, wx + 0.6, wz, wz + 0.7, hash(wx, wz) > 0.8 ? C.cityLit : mixColor(col, C.white, 0.35));
    if (hash(seed + i, 3) > 0.8) vline(iso, x + w / 2, 0, zf + hgt, zf + hgt + 4, C.mullDk);
    x = xe + (hash(seed + i, 4) > 0.6 ? 1 + Math.floor(hash(seed + i, 5) * 3) : 0);
    i++;
  }
  // Reflections across the glass.
  for (let k = 0; k < (x1 - x0) / 18; k++) {
    const rx = x0 + 6 + k * 18 + hash(seed, k) * 6;
    line3(iso, [rx, 0, zf + 4], [rx + 4, 0, zf + 16], mixColor(C.skyLow, C.white, 0.6), 2);
  }
  // Mullions.
  for (let mx = x0; mx <= x1; mx += 12) {
    iso.faceY(0, mx - 0.35, mx + 0.35, zf, top, C.mull);
    iso.vlineY(0, mx + 0.35, zf, top, C.mullLo);
  }
  iso.faceY(0, x0, x1, zf, zf + 1, C.mull);
  iso.hlineY(0, x0, x1, zf + 1, C.mullLo);
}

// ---------------------------------------------------------------- floors & walls

function walls(iso: Iso, l: Level) {
  const zf = floorZ(l.index);
  const zc = base(l.index) + FH;
  if (l.kind === 'server') {
    iso.faceY(0, 0, X, zf, zc, C.granite);
    iso.faceX(0, 0, Y, zf, zc, C.graniteD);
    for (let z = zf + 5; z < zc; z += 5) iso.hlineY(0, 0, X, z, C.graniteD);
    // Cable ladders and cold-air ducts.
    iso.faceY(0, 0, X, zf + 22, zf + 24, C.steelLo);
    iso.faceX(0, 0, Y, zf + 26, zf + 28, C.rackBlue);
    return;
  }
  if (l.kind === 'lobby') {
    // Travertine above walnut wainscot, with gold reveals: an old-money banking hall.
    iso.faceY(0, 0, X, zf, zc, C.marbleB);
    iso.faceX(0, 0, Y, zf, zc, C.marbleVein);
    for (let z = zf + 10; z < zc; z += 6) iso.hlineY(0, 0, X, z, C.marbleVein);
    for (let x = 6; x < X; x += 16) iso.vlineY(0, x, zf + 4, zc, C.marbleVein);
    for (let x = 12; x < X; x += 24) {
      // Pilasters.
      iso.faceY(0, x - 1.4, x + 1.4, zf, zc, C.marbleA);
      iso.vlineY(0, x + 1.4, zf, zc, C.stoneLine);
    }
    iso.faceY(0, 0, X, zf, zf + 4, C.walnut);
    iso.faceX(0, 0, Y, zf, zf + 4, C.walnutLo);
    for (let x = 4; x < X; x += 12) iso.faceY(0, x, x + 8, zf + 1, zf + 3.2, C.walnutHi);
    iso.hlineY(0, 0, X, zf + 4, C.gold);
    iso.hlineY(0, 0, X, zc - 3, C.gold);
    return;
  }
  // Office floors: glass to the city on the back wall, walnut on the end wall.
  iso.faceY(0, 0, X, zf, zc, C.skyTop);
  cityWindow(iso, zf, 0, X, l.index * 97);
  iso.faceX(0, 0, Y, zf, zc, C.walnut);
  for (let y = 3; y < Y; y += 5) {
    iso.faceX(0, y, y + 0.4, zf, zc, C.walnutHi);
  }
  iso.faceX(0, 0, Y, zf, zf + 1.2, C.walnutLo);
}

function floorSurface(iso: Iso, l: Level) {
  const zf = floorZ(l.index);
  if (l.kind === 'lobby') {
    // Cream and black marble in a diamond checker, gold inlay, red runner to the lifts.
    for (let x = 0; x < X; x += 6)
      for (let y = 0; y < Y; y += 6) iso.top(x, y, Math.min(X, x + 6), Math.min(Y, y + 6), zf, ((x + y) / 6) % 2 ? C.marbleA : C.marbleB);
    for (let x = 3; x < X; x += 12)
      for (let y = 3; y < Y; y += 12) iso.top(x - 1, y - 1, x + 1, y + 1, zf, C.marbleK);
    for (let i = 0; i < 70; i++) {
      const x = hash(i, 3) * X;
      const y = hash(i, 7) * Y;
      line3(iso, [x, y, zf], [x + 3 + hash(i, 9) * 4, y + 1 + hash(i, 8) * 2, zf], C.marbleVein);
    }
    iso.top(8, 17, X - 20, 17.6, zf, C.gold);
    iso.top(8, 22.4, X - 20, 23, zf, C.gold);
    iso.top(8, 17.6, X - 20, 22.4, zf, rgba2('#7a2127'));
    return;
  }
  if (l.kind === 'server') {
    for (let x = 0; x < X; x += 6)
      for (let y = 0; y < Y; y += 6) iso.top(x, y, x + 6, y + 6, zf, ((x + y) / 6) % 2 ? C.steel : C.steelHi);
    iso.top(40, 9, 212, 15, zf, C.rackBlue);
    return;
  }
  if (l.kind === 'office') {
    // Herringbone walnut.
    for (let x = 0; x < X; x += 4)
      for (let y = 0; y < Y; y += 2) iso.top(x + ((y / 2) % 2) * 2, y, x + ((y / 2) % 2) * 2 + 4, y + 2, zf, (x / 4 + y / 2) % 2 ? C.plank : C.plank2);
    return;
  }
  // Trading floors: carpet tiles.
  for (let x = 0; x < X; x += 6)
    for (let y = 0; y < Y; y += 6) iso.top(x, y, Math.min(X, x + 6), Math.min(Y, y + 6), zf, ((x + y) / 6) % 2 ? C.carpetT : C.carpetT2);
}

/** Soft shade where the floor meets the back and end walls. */
function occlusion(iso: Iso, zf: number) {
  const steps = [0.16, 0.1, 0.06, 0.03];
  steps.forEach((a, i) => {
    iso.top(0, i * 0.9, X, (i + 1) * 0.9, zf, C.shadow, a);
    iso.top(i * 0.9, 0, (i + 1) * 0.9, Y, zf, C.shadow, a * 0.8);
  });
  // And a darker band on the wall just above the floor.
  iso.faceY(0.05, 0, X, zf, zf + 0.8, C.shadow, 0.12);
}

/** The cut edge of each floor: an LED ticker between steel trims, or granite at the base. */
function slabBand(iso: Iso, l: Level, out: Built) {
  const zb = base(l.index);
  if (l.index <= 0) {
    iso.faceY(Y, -5, X, zb, zb + ST, C.granite);
    iso.hlineY(Y, -5, X, zb + ST - 0.4, C.graniteHi);
  } else {
    iso.faceY(Y, -5, X, zb, zb + ST, C.ledKey);
    iso.faceY(Y, -5, X, zb + ST - 0.5, zb + ST, C.ledTrim);
    iso.faceY(Y, -5, X, zb, zb + 0.4, C.mullDk);
    out.bands.push({ level: l.index, z0: zb + 0.4 });
  }
  // Steel column at the cut end wall.
  iso.faceY(Y, -5, 0, zb + ST, zb + FH, C.steel);
  iso.faceY(Y, -1.2, 0, zb + ST, zb + FH, C.steelLo);
  iso.faceY(Y, -5, -4.2, zb + ST, zb + FH, C.steelHi);
}

function elevator(iso: Iso, l: Level) {
  const zf = floorZ(l.index);
  const { y0, y1 } = ELEVATOR;
  const mid = Math.floor((y0 + y1) / 2);
  iso.faceX(0, y0 - 1, y1 + 1, zf, zf + 28, C.gold);
  iso.faceX(0, y0, y1, zf, zf + 27, C.steelHi);
  iso.faceX(0, mid, mid + 0.3, zf, zf + 27, C.steelLo);
  for (let y = y0 + 1; y < y1; y += 1.5) iso.faceX(0, y, y + 0.2, zf + 1, zf + 26, mixColor(C.steelHi, C.white, 0.35));
  // Floor indicator.
  iso.faceX(0, mid - 3, mid + 4, zf + 29.5, zf + 35.5, C.ledKey);
  iso.textX(0, mid + 0.5, zf + 30.7, l.label, MONO(6, C.amber));
}

// ---------------------------------------------------------------- furniture

function chair(iso: Iso, cx: number, zf: number) {
  iso.box(cx - 1, 4, zf, cx + 1, 6, zf + 4, chrome);
  iso.box(cx - 5, 2, zf + 4, cx + 5, 8, zf + 6.5, leather);
  iso.box(cx - 5, 0.6, zf + 6.5, cx + 5, 2.8, zf + 21, leather);
  iso.lineTopY(2.8, cx - 5, cx + 5, zf + 21, rgba2('#4a3d38'));
  iso.box(cx - 6, 2.6, zf + 9, cx - 5, 7.6, zf + 10, leather);
  iso.box(cx + 5, 2.6, zf + 9, cx + 6, 7.6, zf + 10, leather);
}

function wallScreen(iso: Iso, x0: number, x1: number, z0: number, z1: number, screens: ScreenSpec[], spec: Omit<ScreenSpec, 'y' | 'x0' | 'x1' | 'z0' | 'z1'>) {
  iso.faceY(0.2, x0 - 0.8, x1 + 0.8, z0 - 0.8, z1 + 0.8, C.bezel);
  iso.faceY(0.2, x0, x1, z0, z1, C.screen);
  iso.hlineY(0.2, x0 - 0.8, x1 + 0.8, z1 + 0.5, C.bezelHi);
  screens.push({ ...spec, y: 0.2, x0, x1, z0, z1 });
}

function desk(iso: Iso, fg: Iso, cx: number, zf: number, n: number, pencilled: boolean, variant: number, out: Built) {
  const { y0, y1, half } = DESK;
  const h = 7;
  if (pencilled) {
    // A folding card table, a reserved card and a folding chair. Nobody fights over it.
    fg.box(cx - 10, y0, zf + h - 1, cx + 10, y1, zf + h, { top: C.woodHi, left: C.woodL, right: C.woodR });
    vline(fg, cx - 9, y1 - 1, zf, zf + h - 1, C.steelLo, 2);
    vline(fg, cx + 8, y1 - 1, zf, zf + h - 1, C.steelLo, 2);
    fg.box(cx - 3, y0 + 2, zf + h, cx + 3, y0 + 2.6, zf + h + 4, { top: C.paper, left: C.paper, right: C.paperShade });
    fg.faceY(y0 + 2.6, cx - 2.2, cx + 2.2, zf + h + 2.4, zf + h + 2.9, C.red);
    iso.box(cx - 3, 3, zf + 5, cx + 3, 7, zf + 6, steel);
    iso.box(cx - 3, 2, zf + 6, cx + 3, 3, zf + 14, steel);
    vline(iso, cx - 3, 7, zf, zf + 5, C.steelLo, 2);
    vline(iso, cx + 2, 7, zf, zf + 5, C.steelLo, 2);
    return;
  }
  chair(iso, cx, zf);
  // The desk: black glass top, walnut front, a brass plate.
  fg.box(cx - half - 1, y0, zf, cx + half + 1, y1, zf + h, blackTop);
  fg.faceY(y1, cx - half - 1, cx + half + 1, zf + 0.5, zf + h - 0.8, C.walnut);
  for (const x of [cx - half + 3, cx + half - 3]) fg.vlineY(y1, x, zf + 0.5, zf + h - 0.8, C.walnutLo);
  fg.faceY(y1, cx - half - 1, cx + half + 1, zf + h - 0.8, zf + h - 0.4, C.gold);
  const label = String(n).padStart(2, '0');
  fg.faceY(y1, cx - 4.5, cx + 4.5, zf + 0.8, zf + 6, C.goldLo);
  fg.faceY(y1, cx - 4, cx + 4, zf + 1.2, zf + 5.6, C.gold);
  fg.textY(y1, cx, zf + 2, label, MONO(4.6, C.walnutLo));
  // Keyboard, mouse, a phone turret with lit keys.
  fg.box(cx - 5, y0 + 2, zf + h, cx + 4, y0 + 4, zf + h + 0.6, { top: rgba2('#2c2f36'), left: rgba2('#1c1e23'), right: rgba2('#15171b') });
  for (let x = cx - 4.5; x < cx + 3.5; x += 1) fg.top(x, y0 + 2.4, x + 0.6, y0 + 3.6, zf + h + 0.6, rgba2('#454a54'));
  fg.box(cx + 5.5, y0 + 2.4, zf + h, cx + 6.8, y0 + 3.8, zf + h + 0.6, { top: C.steelHi, left: C.steel, right: C.steelLo });
  fg.box(cx - 11, y0 + 1, zf + h, cx - 6.5, y0 + 5, zf + h + 1.8, { top: rgba2('#2c2f36'), left: rgba2('#1c1e23'), right: rgba2('#15171b') });
  for (let i = 0; i < 4; i++) fg.top(cx - 10.4 + i, y0 + 1.6, cx - 10 + i, y0 + 2.2, zf + h + 1.8, i % 2 ? C.ledGreen : C.amber);
  // Coffee or a small gold bull on the desk.
  if (variant % 3 === 0) {
    fg.box(cx + 8, y0 + 2, zf + h, cx + 10, y0 + 4, zf + h + 3, { top: C.coffee, left: C.white, right: C.paperShade });
    fg.faceY(y0 + 4, cx + 8, cx + 10, zf + h + 1, zf + h + 2, C.red);
  } else if (variant % 3 === 1) {
    fg.box(cx + 8, y0 + 2, zf + h, cx + 11, y0 + 3.4, zf + h + 1.5, { top: C.goldHi, left: C.gold, right: C.goldLo });
    fg.box(cx + 7.4, y0 + 2.2, zf + h + 1, cx + 8.2, y0 + 3.2, zf + h + 2.4, { top: C.goldHi, left: C.gold, right: C.goldLo });
  } else {
    const [sx, sy] = fg.at(cx + 9, y0 + 3, zf + h);
    fg.buf.sprite(PLANTS.succulent, sx, sy + S);
  }
  // Monitors: a pair on the left, angled to face the trader (screens visible),
  // and a pair on the right with their backs to us.
  const mz = zf + h;
  fg.box(cx - half - 0.6, y0 + 0.5, mz, cx - half + 1.2, y0 + 5.5, mz + 1, chrome);
  fg.box(cx - half - 0.4, y0 - 1, mz + 1, cx - half + 1, y0 + 6.5, mz + 11, bezel);
  fg.faceX(cx - half + 1, y0 - 0.6, y0 + 6.1, mz + 1.6, mz + 10.4, C.screen);
  out.screens.push({ kind: 'side', desk: n, plane: 'x', x: cx - half + 1, y: 0, x0: y0 - 0.6, x1: y0 + 6.1, z0: mz + 1.6, z1: mz + 10.4 });
  fg.box(cx + half - 1, y0 - 1, mz + 1, cx + half + 0.4, y0 + 6.5, mz + 11, { top: C.bezelHi, left: C.bezel, right: rgba2('#3a3f48') });
  fg.box(cx + half - 1.2, y0 + 0.5, mz, cx + half + 0.6, y0 + 5.5, mz + 1, chrome);
  fg.faceX(cx + half + 0.4, y0 + 2.2, y0 + 3.4, mz + 5.2, mz + 6.4, C.steelHi);
}

function partition(iso: Iso, x: number, zf: number) {
  iso.faceX(x, 1, 14, zf, zf + 16, C.frost, 0.5);
  iso.faceX(x, 1, 14, zf + 7, zf + 7.8, C.white, 0.5);
  iso.hlineX(x, 1, 14, zf + 15.6, C.mull);
  iso.faceX(x, 13.4, 14, zf, zf + 16, C.mull);
  for (let i = 0; i < 6; i++) iso.faceX(x, 3 + i * 0.8, 3.4 + i * 0.8, zf + 8 + i, zf + 9 + i, C.glassRR);
}

function espressoBar(iso: Iso, zf: number, out: Built) {
  iso.box(170, 1, zf, 206, 7, zf + 10, walnut);
  iso.box(169, 0.5, zf + 10, 207, 8, zf + 11, marbleWhite);
  iso.box(174, 2, zf + 11, 182, 6, zf + 20, chrome);
  iso.faceY(6, 175, 181, zf + 13, zf + 18, C.screenOff);
  iso.faceY(6, 176, 177, zf + 17, zf + 17.8, C.ledRed);
  iso.box(177, 5, zf + 11, 179, 6, zf + 13, { top: C.coffee, left: C.white, right: C.paperShade });
  out.steam.push(iso.at(178, 4, zf + 21));
  iso.box(188, 2, zf + 11, 190, 4, zf + 17, { top: rgba2('#6b1f24'), left: rgba2('#4a1418'), right: rgba2('#35101a') });
  iso.box(191, 2, zf + 11, 193, 4, zf + 16, { top: C.glassR, left: C.glassL, right: C.glassM });
  iso.box(196, 2, zf + 11, 204, 6, zf + 12.5, { top: C.goldHi, left: C.gold, right: C.goldLo });
  // Bar stools.
  for (const x of [178, 190, 202]) {
    iso.box(x - 0.4, 11.4, zf, x + 0.4, 12.2, zf + 8, chrome);
    iso.box(x - 2.2, 10, zf + 8, x + 2.2, 13.6, zf + 9, leather);
  }
}

function hr(iso: Iso, zf: number, out: Built) {
  for (const x0 of [170, 178]) {
    iso.box(x0, 1, zf, x0 + 8, 7, zf + 16, steel);
    for (const z of [zf + 4, zf + 8, zf + 12]) {
      iso.hlineY(7, x0, x0 + 8, z, C.steelLo);
      iso.faceY(7, x0 + 3, x0 + 5, z + 1.6, z + 2.2, C.gold);
    }
  }
  out.cat = iso.at(174, 4, zf + 16);
  // A neat stack of flat-packed boxes, for when they're needed.
  for (let k = 0; k < 5; k++) iso.box(188, 3, zf + k * 1.2, 200, 12, zf + k * 1.2 + 1.1, { top: C.boxHi, left: C.box, right: C.boxLo });
  // Headshot corner.
  iso.faceY(0.2, 202, 213, zf, zf + 20, C.steelHi);
  const [sx, sy] = iso.at(206, 16, zf);
  iso.buf.sprite(CAMERA, sx, sy);
}

function compliance(iso: Iso, zf: number) {
  iso.box(170, 1, zf, 188, 6, zf + 20, walnut);
  const colors = [C.red, C.navy, C.leaf, C.gold, C.steelLo, C.red, C.navy];
  for (let row = 0; row < 3; row++) {
    const z0 = zf + 2 + row * 6;
    iso.faceY(6, 171, 187, z0, z0 + 5, C.walnutLo);
    for (let x = 171; x < 187; x += 1.5) iso.faceY(6, x, x + 1.1, z0, z0 + 4.2 + (x % 3) * 0.3, colors[Math.floor(x + row * 3) % colors.length]);
  }
  // A review table and a very large paper shredder, working hard.
  iso.box(192, 9, zf, 210, 16, zf + 8, walnut);
  iso.box(194, 10, zf + 8, 200, 14, zf + 10, { top: C.paper, left: C.paperShade, right: C.paperShade });
  iso.box(204, 11, zf + 8, 208, 14, zf + 10, { top: C.red, left: C.red, right: C.redHi });
  iso.box(202, 17.5, zf, 208, 21, zf + 9, { top: C.steelHi, left: C.steel, right: C.steelLo });
  iso.box(202.5, 17.8, zf + 9, 207.5, 20.6, zf + 9.6, { top: C.screenOff, left: C.steelLo, right: C.steelLo });
  for (let i = 0; i < 6; i++) iso.faceY(21, 202.6 + i * 0.9, 203.1 + i * 0.9, zf + 3, zf + 8, C.paper);
  iso.faceY(21, 206.6, 207.4, zf + 7.6, zf + 8.2, C.ledGreen);
}

function terminalWall(iso: Iso, zf: number, out: Built) {
  iso.box(168, 5, zf, 172, 8, zf + 6, steel);
  iso.box(206, 5, zf, 210, 8, zf + 6, steel);
  iso.box(166, 5.5, zf + 6, 212, 8, zf + 28, bezel);
  let slot = 0;
  for (let r = 0; r < 2; r++)
    for (let c = 0; c < 3; c++) {
      const x0 = 168 + c * 14.6;
      const z0 = zf + 8 + (1 - r) * 10;
      iso.faceY(8, x0, x0 + 13.6, z0, z0 + 9.2, C.screen);
      out.screens.push({ kind: 'terminal', slot: slot++, y: 8, x0, x1: x0 + 13.6, z0, z1: z0 + 9.2 });
    }
  // The bell. Rung on bonus day, and sometimes for no reason.
  iso.box(150, 18, zf, 152, 20, zf + 14, { top: C.goldHi, left: C.gold, right: C.goldLo });
  iso.box(147, 18.4, zf + 14, 155, 19.6, zf + 15, walnut);
  const [bx, by] = iso.at(151, 19, zf + 15);
  iso.buf.sprite(BELL, bx, by);
}

function office(iso: Iso, zf: number, out: Built) {
  // Putting green by the window.
  iso.top(28, 10, 74, 22, zf, C.green);
  iso.top(30, 11, 72, 21, zf, C.greenHi);
  iso.top(62, 13.6, 64, 15.2, zf, C.ink);
  vline(iso, 63, 14.4, zf, zf + 12, C.white, 2);
  iso.faceY(14.4, 63.3, 67, zf + 9, zf + 12, C.red);
  for (const [x, y] of [[36, 17], [44, 18.4]]) iso.dot(x, y, zf + 0.6, C.white, S);
  // The safe (the treasury).
  iso.box(82, 1, zf, 96, 9, zf + 16, { top: C.screenOff, left: C.bezel, right: C.screen });
  const [dx, dy] = iso.at(89, 9, zf + 9);
  iso.buf.ellipse(dx, dy, 2.8 * S, 2.8 * S, C.goldLo);
  iso.buf.ellipse(dx, dy, 2.4 * S, 2.4 * S, C.gold);
  iso.buf.ellipse(dx, dy, 1.6 * S, 1.6 * S, C.bezel);
  iso.buf.ellipse(dx, dy, 0.7 * S, 0.7 * S, C.goldHi);
  // Handle.
  iso.faceY(9, 91.5, 94, zf + 8.6, zf + 9.4, C.steelHi);
  iso.hlineY(9, 83, 95, zf + 15, C.bezelHi);
  // Portrait of the partner, sheared to sit flat on the glass... on an easel of walnut.
  iso.faceY(0.3, 102, 118, zf + 4, zf + 20, C.gold);
  iso.faceY(0.3, 103, 117, zf + 5, zf + 19, C.walnutLo);
  {
    // Painted flat on the wall: sheared to follow the plane.
    const [px, py] = iso.p(103.5, 0.3, zf + 18.5);
    iso.buf.sprite(PORTRAIT, 0, 0, { a: 1, b: 0.5, c: 0, d: 1, e: px, f: py });
  }
  // Globe bar.
  const [gx, gy] = iso.at(78, 16, zf);
  iso.buf.sprite(GLOBE, gx, gy);
  // Partner's desk: a slab of walnut, a green leather inlay, a banker's lamp, a decanter.
  iso.box(124, 1.6, zf + 5, 136, 8, zf + 7.5, leather);
  iso.box(124, 0.4, zf + 7.5, 136, 2.6, zf + 24, leather);
  iso.box(126, 4, zf, 134, 6, zf + 5, chrome);
  iso.box(108, 10, zf, 152, 17, zf + 10, walnut);
  iso.box(107, 9, zf + 10, 153, 18, zf + 11, { top: C.walnutHi, left: C.walnut, right: C.walnutLo, hi: C.gold });
  iso.top(112, 10.5, 146, 16.5, zf + 11, C.leafLo);
  iso.box(141, 11, zf + 11, 146, 13, zf + 12, { top: C.gold, left: C.gold, right: C.goldLo });
  vline(iso, 143, 12, zf + 12, zf + 16, C.goldLo, 2);
  iso.box(139, 11, zf + 16, 148, 14, zf + 18, { top: C.leafHi, left: C.leaf, right: C.leafLo });
  iso.box(116, 12, zf + 11, 124, 16, zf + 12, { top: C.paper, left: C.paperShade, right: C.paperShade });
  iso.box(128, 12, zf + 11, 131, 15, zf + 15, { top: C.glassRR, left: rgba2('#b0773a'), right: rgba2('#8a5a2a') });
  // Cigar box.
  iso.box(132, 13, zf + 11, 137, 16, zf + 12.6, walnut);
  // Leather sofa.
  iso.box(166, 12, zf, 206, 20, zf + 5, leather);
  iso.box(166, 10.6, zf + 5, 206, 12.6, zf + 13, leather);
  iso.box(164.6, 11, zf, 166.6, 20, zf + 9, leather);
  iso.box(205.6, 11, zf, 207.6, 20, zf + 9, leather);
  const [fx, fy] = iso.at(214, 18, zf);
  iso.buf.sprite(PLANTS.palm, fx, fy);
  out.pendulum = [0, 0];
}

function lobby(iso: Iso, zf: number, out: Built) {
  // Brass lettering on the walnut wall.
  const name = FIRM_NAME.toUpperCase();
  const sign: TextOpts = { font: 'serif', size: 7.6, color: C.goldHi, weight: 500, align: 'center', spacing: 1.1 };
  const tw = iso.buf.measure(name, sign);
  // Black granite fascia so the brass reads against the travertine.
  const z0 = zf + 6.5;
  iso.faceY(0.15, 112 - tw / 2 - 4.4, 112 + tw / 2 + 4.4, z0 - 0.4, z0 + 8.6, C.gold);
  iso.faceY(0.18, 112 - tw / 2 - 4, 112 + tw / 2 + 4, z0, z0 + 8.2, C.marbleK);
  iso.textY(0.2, 112 + 0.25, z0 + 1.6, name, { ...sign, color: C.goldLo });
  iso.textY(0.2, 112, z0 + 1.9, name, sign);
  // Security desk in white marble, with the ticker running along its front.
  iso.box(160, 3, zf, 198, 10, zf + 10, marbleWhite);
  iso.box(159, 2, zf + 10, 199, 11, zf + 11, { top: C.deskTop, left: C.graniteD, right: C.graniteD, hi: C.gold });
  iso.faceY(10, 161, 197, zf + 2.6, zf + 9.4, C.gold);
  iso.faceY(10, 161.5, 196.5, zf + 3, zf + 9, C.bezel);
  iso.faceY(10, 162, 196, zf + 3.4, zf + 8.6, C.amberDim);
  out.ticker = { y: 10, x0: 162, x1: 196, z0: zf + 3.4, z1: zf + 8.6 };
  iso.box(172, 4, zf + 11, 176, 6, zf + 15, bezel);
  // Turnstiles.
  for (const x of [128, 136, 144]) {
    iso.box(x - 1, 14.5, zf, x + 1, 24, zf + 8, chrome);
    iso.faceX(x + 1, 16, 22, zf + 3, zf + 7, C.glassR, 0.6);
  }
  // The bull, on a granite plinth.
  iso.box(14, 3, zf, 60, 14, zf + 3, granite);
  iso.faceY(14, 28, 46, zf + 0.8, zf + 2.2, C.gold);
  const [bx, by] = iso.at(38, 8.5, zf + 3);
  iso.buf.sprite(BULL, bx, by);
  for (const [x, y] of [
    [64, 21],
    [224, 20],
  ]) {
    const [sx, sy] = iso.at(x, y, zf);
    iso.buf.sprite(PLANTS.palm, sx, sy);
  }
}

function server(iso: Iso, zf: number, out: Built) {
  for (let i = 0; i < 9; i++) {
    const x0 = 96 + i * 13;
    if (x0 + 11 > 212) break;
    iso.box(x0, 1, zf, x0 + 11, 7, zf + 20, { top: C.bezelHi, left: C.bezel, right: C.screenOff });
    for (let row = 0; row < 6; row++) {
      const z = zf + 3 + row * 3;
      iso.hlineY(7, x0 + 1, x0 + 10, z - 1, C.screenOff);
      for (let k = 0; k < 4; k++) {
        const x = x0 + 1.6 + k * 2.2;
        iso.faceY(7, x, x + 0.8, z, z + 0.8, C.ledOff);
        out.leds.push(iso.quadY(7, x, x + 0.8, z, z + 0.8));
      }
    }
  }
  iso.box(44, 3, zf, 66, 9, zf + 9, steel);
  iso.box(48, 3, zf + 9, 60, 8, zf + 19, { top: C.cream, left: C.cream, right: C.paperShade });
  iso.faceY(8, 50, 58, zf + 11, zf + 17, C.screen);
  out.screens.push({ kind: 'crt', y: 8, x0: 50, x1: 58, z0: zf + 11, z1: zf + 17 });
  iso.box(70, 9, zf + 5, 78, 14, zf + 6, steel);
  iso.box(70, 8, zf + 6, 78, 9, zf + 14, steel);
}

// ---------------------------------------------------------------- outside

function foundation(iso: Iso) {
  const zb = base(-1);
  iso.faceY(Y, -5, X, -GROUND_DEPTH, zb, C.earthL);
  for (let i = 0; i < 120; i++) {
    const x = hash(i, 11) * (X + 5) - 5;
    const z = -GROUND_DEPTH + hash(i, 12) * (GROUND_DEPTH + zb);
    iso.faceY(Y, x, x + 0.7, z, z + 0.7, i % 3 ? C.earthDot : C.stoneBits);
  }
}

/** The rest of the tower, rising past the top of the frame. */
function tower(iso: Iso, out: Built) {
  const z0 = ROOF_Z;
  const z1 = ROOF_Z + TOWER_H;
  // Front glass (the floors above aren't ours, so they're not cut open).
  iso.faceY(Y, -5, X, z0, z1, C.glassM);
  for (let z = z0; z < z1; z += FH / 2) {
    iso.faceY(Y, -5, X, z, z + 2, C.glassD);
    iso.hlineY(Y, -5, X, z + 2, C.mullLo);
  }
  for (let x = -5; x < X; x += 6) iso.faceY(Y, x, x + 0.35, z0, z1, C.mull);
  // Sky reflected across the glass, in long diagonals.
  for (let k = 0; k < 9; k++) {
    const x = 8 + k * 26;
    iso.buf.poly([iso.p(x, Y, z0 + 4), iso.p(x + 10, Y, z0 + 4), iso.p(x + 26, Y, z1), iso.p(x + 16, Y, z1)], C.glassL, 0.55);
    iso.buf.poly([iso.p(x + 2, Y, z0 + 4), iso.p(x + 4, Y, z0 + 4), iso.p(x + 20, Y, z1), iso.p(x + 18, Y, z1)], C.glassRR, 0.45);
  }
  // The first slab above us is still an LED band, to match the floors below.
  iso.faceY(Y, -5, X, z0, z0 + ST, C.ledKey);
  iso.faceY(Y, -5, X, z0 + ST - 0.5, z0 + ST, C.ledTrim);
  out.bands.push({ level: 6, z0: z0 + 0.4 });
  out.towerTop = Math.floor(iso.sy(0, 0, z1));
}

/**
 * Fade the tower out as it rises. On a vertical plane, world height is a
 * linear function of screen position, so a straight gradient along the
 * direction of increasing z fades by height exactly.
 */
function fadeTower(bg: Iso, fr: Iso) {
  const z1 = ROOF_Z + TOWER_H;
  const zs = ROOF_Z + 16;
  const s = bg.s;
  const grad = (p: Pt, gx: number, gy: number, dz: number): [Pt, Pt] => {
    // Screen offset that raises z by dz along the gradient (gx, gy).
    const n2 = gx * gx + gy * gy;
    return [p, [p[0] + (gx * dz) / n2, p[1] + (gy * dz) / n2]];
  };
  // Front glass: plane y = Y. z = (sx − ox)/(2s) + Y − (sy − oy)/s.
  const [fa, fb] = grad(bg.p(0, Y, z1), 1 / (2 * s), -1 / s, zs - z1);
  bg.buf.fade(bg.quadY(Y, -6, X + 0.5, zs, z1 + 60), fa, fb);
  // The facade layer: the steel edge on the front plane and the glass end wall (plane x = xo).
  const xo = X + 6;
  fr.buf.fade(fr.quadY(Y, X - 0.5, xo + 0.5, zs, z1 + 60), fa, fb);
  const [ea, eb] = grad(fr.p(xo, 0, z1), -1 / (2 * s), -1 / s, zs - z1);
  fr.buf.fade(fr.quadX(xo, -1, Y + 1, zs, z1 + 60), ea, eb);
}

function facade(iso: Iso, out: Built) {
  const xo = X + 6;
  const top = ROOF_Z + TOWER_H;
  const bottom = -GROUND_DEPTH + 5;
  // Glass curtain wall on the end, with its thickness showing at the cut.
  iso.faceX(xo, 0, Y, bottom, top, C.glassD);
  iso.faceY(Y, X, xo, bottom, top, C.steel);
  iso.faceY(Y, X, X + 0.6, bottom, top, C.steelHi);
  for (let z = 0; z < top; z += FH / 2) {
    iso.faceX(xo, 0, Y, z, z + 2.2, C.glassD);
    iso.hlineX(xo, 0, Y, z + 2.2, C.mull);
  }
  for (let y = 0; y <= Y; y += 4) iso.faceX(xo, y, y + 0.35, 0, top, C.mull);
  iso.faceX(xo, 0, Y, 0, top, C.glassM, 0.5);
  // Reflections.
  for (let k = 0; k < 14; k++) {
    const z = 10 + k * 26;
    iso.buf.poly([iso.p(xo, 0, z), iso.p(xo, 0, z + 5), iso.p(xo, Y, z + 20), iso.p(xo, Y, z + 15)], C.glassR, 0.4);
  }
  // Granite base, lobby glazing and the revolving door with a canopy.
  const zb = base(-1);
  iso.faceX(xo, 0, Y, bottom, floorZ(0), C.granite);
  iso.hlineX(xo, 0, Y, floorZ(0) - 0.5, C.graniteHi);
  for (let z = zb + 4; z < 0; z += 6) iso.hlineX(xo, 0, Y, z, C.graniteD);
  const zf = floorZ(0);
  iso.faceX(xo, 0, Y, zf, zf + 38, C.glassL);
  for (let y = 0; y <= Y; y += 6) iso.faceX(xo, y, y + 0.5, zf, zf + 38, C.steelHi);
  const y0 = 5;
  const y1 = 19;
  iso.faceX(xo, y0 - 1, y1 + 1, zf, zf + 28, C.gold);
  iso.faceX(xo, y0, y1, zf, zf + 26, C.glassR);
  out.door = { x: xo, y0, y1, z0: zf, z1: zf + 26 };
  iso.box(xo, y0 - 3, zf + 28, xo + 9, y1 + 3, zf + 31, { top: rgba2('#1f2c45'), left: rgba2('#1f2c45'), right: rgba2('#141c2e') });
  iso.hlineX(xo + 9, y0 - 3, y1 + 3, zf + 28.6, C.gold);
  iso.textX(xo + 9, (y0 + y1) / 2, zf + 28.8, 'BC', { font: 'serif', size: 3, color: C.goldHi, weight: 500, align: 'center', spacing: 0.3 });
}

function street(iso: Iso) {
  const { x0, x1, y0, y1 } = LOT;
  const road = y1 - 8;
  // Ground block with the street's cross-section.
  iso.faceY(y1, x0, x1, -GROUND_DEPTH, 0, C.earthL);
  iso.faceX(x1, y0, y1, -GROUND_DEPTH, 0, C.earthR);
  iso.faceY(y1, x0, x1, -8, 0, C.graniteD);
  iso.faceX(x1, y0, y1, -8, 0, C.granite);
  for (let i = 0; i < 40; i++) {
    const z = -GROUND_DEPTH + hash(i, 21) * (GROUND_DEPTH - 10);
    iso.faceY(y1, x0 + hash(i, 22) * (x1 - x0), x0 + hash(i, 22) * (x1 - x0) + 0.7, z, z + 0.7, C.earthDot);
    iso.faceX(x1, y0 + hash(i, 23) * (y1 - y0), y0 + hash(i, 23) * (y1 - y0) + 0.7, z, z + 0.7, i % 2 ? C.earthDot : C.stoneBits);
  }
  // Sidewalk slabs.
  for (let x = x0; x < x1; x += 6)
    for (let y = y0; y < road; y += 6) iso.top(x, y, Math.min(x1, x + 6), Math.min(road, y + 6), 0, ((x + y) / 6) % 2 ? C.sidewalk : C.sidewalkL);
  // Curb and road.
  iso.top(x0, road, x1, road + 1, 0, C.curb);
  iso.top(x0, road + 1, x1, y1, 0, C.asphalt);
  for (let x = x0 + 2; x < x1; x += 8) iso.top(x, y1 - 1.6, x + 4, y1 - 1, 0, C.paint);
  // Steps up to the door.
  iso.box(x0 + 6, 2, 0, x0 + 12, 22, 3, { top: C.graniteL, left: C.granite, right: C.graniteD, hi: C.graniteHi });
  iso.box(x0 + 6, 3, 3, x0 + 9, 21, 5, { top: C.graniteL, left: C.granite, right: C.graniteD, hi: C.graniteHi });
  // Planters with shrubs, steel bollards.
  for (const [x, y] of [
    [252, -3],
    [266, -3],
  ]) {
    iso.box(x - 4, y - 2, 0, x + 4, y + 3, 3, granite);
    const [sx, sy] = iso.at(x, y + 0.5, 3);
    iso.buf.sprite(PLANTS.shrub, sx, sy);
  }
  for (let x = 250; x < 272; x += 5) iso.box(x, road - 2, 0, x + 1, road - 1, 4, chrome);
  // A street sign and a lamp.
  const [lx, ly] = iso.at(268, 12, 0);
  iso.buf.rect(lx - 1.2, ly - 34 * S, 2.4, 34 * S, C.iron);
  iso.buf.rect(lx - 3 * S, ly - 34 * S, 6 * S, S, C.iron);
  iso.buf.rect(lx - 2.6 * S, ly - 33 * S, 5.2 * S, S * 0.8, C.amber);
  // Street sign, square to the viewer like the real ones on corners.
  const label: TextOpts = { font: 'sans', size: 12, color: C.paint, weight: 600, align: 'center', spacing: 0.6 };
  const sw = iso.buf.measure('WALL ST', label) + 12;
  iso.buf.rect(lx - sw / 2 - 1, ly - 24 * S - 1, sw + 2, 20, C.paint);
  iso.buf.rect(lx - sw / 2, ly - 24 * S, sw, 18, C.signGreen);
  iso.buf.text('WALL ST', { a: 1, b: 0, c: 0, d: 1, e: lx, f: ly - 24 * S + 13.5 }, label);
  // The shredder bin by the curb.
  iso.box(240, 20, 0, 247, 26, 10, { top: C.binLo, left: C.bin, right: C.binLo, hi: C.binHi });
  iso.box(239, 19, 10, 248, 27, 11, { top: C.binHi, left: C.bin, right: C.binLo });
  iso.faceY(26, 242, 245, 9, 9.6, C.paper);
  iso.faceY(27, 243, 244, 11, 12, C.paper);
  // A yellow cab, waiting for someone important.
  cab(iso, 244, road + 1.4);
}

function cab(iso: Iso, x: number, y: number) {
  const L = 24;
  const Wd = 9;
  const body: BoxColors = { top: C.taxi, left: C.taxi, right: C.taxiS, hi: C.taxiHi };
  // Wheels.
  for (const wx of [x + 4, x + L - 6]) {
    iso.box(wx, y + Wd - 0.6, 0, wx + 3, y + Wd, 3, { top: C.ink, left: C.ink, right: C.ink });
    iso.faceY(y + Wd, wx + 0.8, wx + 2.2, 0.8, 2.2, C.steel);
  }
  iso.box(x, y, 1.5, x + L, y + Wd, 5.5, body);
  iso.box(x + 5, y + 0.8, 5.5, x + L - 6, y + Wd - 0.8, 9, body);
  // Windows.
  iso.faceY(y + Wd - 0.8, x + 5.8, x + 11.5, 5.9, 8.6, C.glassM);
  iso.faceY(y + Wd - 0.8, x + 12.3, x + L - 6.8, 5.9, 8.6, C.glassM);
  iso.faceY(y + Wd - 0.8, x + 6, x + 7, 6.2, 8.4, C.glassRR);
  iso.faceX(x + L - 6, y + 1.4, y + Wd - 1.4, 5.9, 8.6, C.glassD);
  iso.faceY(y + Wd, x, x + L, 3.2, 3.6, C.ink);
  // Checker stripe and the roof light.
  for (let k = 0; k < 10; k++) iso.faceY(y + Wd, x + 6 + k * 1.2, x + 6.6 + k * 1.2, 2.2, 2.8, k % 2 ? C.ink : C.paint);
  iso.box(x + 11, y + 3, 9, x + 15, y + 6, 10.6, { top: C.paint, left: C.paint, right: C.curb });
  iso.faceX(x + L, y + 1, y + 2.4, 3.4, 4.4, C.amber);
  iso.faceX(x + L, y + Wd - 2.4, y + Wd - 1, 3.4, 4.4, C.amber);
}

/** Surfaces the building draws into, back to front. */
export interface Layers {
  bg: Surface;
  fg: Surface;
  front: Surface;
}

/** Draw the building into three layers and return what the animation pass needs. */
export function buildScene(layers: Layers): Built {
  const out: Built = {
    screens: [],
    ticker: { y: 0, x0: 0, x1: 0, z0: 0, z1: 0 },
    bands: [],
    leds: [],
    steam: [],
    cat: [0, 0],
    antenna: [0, 0],
    pendulum: [0, 0],
    door: { x: 0, y0: 0, y1: 0, z0: 0, z1: 0 },
    towerTop: 0,
  };
  const b = new Iso(layers.bg, OX, OY);
  const f = new Iso(layers.fg, OX, OY);
  const fr = new Iso(layers.front, OX, OY);

  foundation(b);
  for (const l of LEVELS) {
    const zf = floorZ(l.index);
    walls(b, l);
    floorSurface(b, l);
    occlusion(b, zf);
    elevator(b, l);
    if (l.kind === 'desks') {
      l.desks.forEach((d, bay) => {
        const cx = BAY_X[bay];
        if (d !== 0) {
          wallScreen(b, cx - 21, cx - 8, zf + 7, zf + 18, out.screens, { kind: 'desk', desk: d });
          b.top(cx - DESK.half - 1, DESK.y1, cx + DESK.half + 2, DESK.y1 + 2, zf, C.carpetLine);
        } else {
          b.faceY(0.2, cx - 19, cx - 9, zf + 9, zf + 16, C.cream);
          b.hlineY(0.2, cx - 19, cx - 9, zf + 15.6, C.goldLo);
          b.textY(0.2, cx - 14, zf + 10.6, '12', { font: 'serif', size: 7, color: C.goldLo, weight: 500, align: 'center' });
        }
        desk(b, f, cx, zf, d, d === 0, d + l.index, out);
      });
      for (const x of [78, 122, 166]) partition(b, x, zf);
      if (l.feature === 'kitchen') espressoBar(b, zf, out);
      if (l.feature === 'hr') hr(b, zf, out);
      if (l.feature === 'compliance') compliance(b, zf);
      if (l.feature === 'terminal') terminalWall(b, zf, out);
      const [sx, sy] = b.at(26, 20, zf);
      layers.bg.sprite(PLANTS.fern, sx, sy);
    }
    if (l.kind === 'office') office(b, zf, out);
    if (l.kind === 'lobby') lobby(b, zf, out);
    if (l.kind === 'server') server(b, zf, out);
    slabBand(b, l, out);
  }
  facade(fr, out);
  tower(b, out);
  street(fr);
  fadeTower(b, fr);
  return out;
}

/** The whole building rendered into pixel buffers (Node scripts, tests, hotspots). */
export function buildPixelScene(): { built: Built; bg: PixelBuffer; fg: PixelBuffer; front: PixelBuffer } {
  const bg = new PixelBuffer(W, H);
  const fg = new PixelBuffer(W, H);
  const front = new PixelBuffer(W, H);
  const built = buildScene({ bg: new PixelSurface(bg), fg: new PixelSurface(fg), front: new PixelSurface(front) });
  return { built, bg, fg, front };
}
