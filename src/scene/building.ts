/**
 * Draws the procedural building into layers. Static art only; anything that
 * moves is painted later over key-coloured regions (see anim.ts).
 */
import { FIRM_NAME } from '../../firm.config';
import { PixelBuffer, mixColor } from './buffer';
import { renderBust } from '../art/figure';
import { blitAt, renderPlant } from '../art/props';
import { PARTNER_LOOK } from '../art/partner';
import { C } from './colors';
import { drawText, textWidth } from './font';
import { Iso } from './iso';
import {
  BAY_X,
  DESK,
  ELEVATOR,
  FH,
  GROUND_DEPTH,
  H,
  INTERIOR,
  LEVELS,
  LOT,
  OX,
  OY,
  ROOF_Z,
  S,
  ST,
  W,
  X,
  Y,
  base,
  floorZ,
  type Level,
} from './layout';
import {
  CAMERA,
  FLAG,
  GLOBE,
  LAMP_HEAD,
  PIGEON,
  WATER_TOWER,
  stampAt,
} from './props';

const PLANTS = {
  palm: renderPlant('palm'),
  fern: renderPlant('fern'),
  succulent: renderPlant('succulent'),
  shrub: renderPlant('shrub'),
  flowers: renderPlant('flowers'),
};

export interface ScreenSpec {
  kind: 'desk' | 'terminal' | 'crt';
  desk?: number;
  slot?: number;
  /** Plane y = y, x0..x1, z0..z1. */
  y: number;
  x0: number;
  x1: number;
  z0: number;
  z1: number;
}

export interface Built {
  bg: PixelBuffer;
  fg: PixelBuffer;
  front: PixelBuffer;
  screens: ScreenSpec[];
  ticker: { y: number; x0: number; x1: number; z0: number; z1: number };
  /** Pixel indices of each server LED. */
  leds: number[][];
  steam: [number, number][];
  cat: [number, number];
  antenna: [number, number];
  pendulum: [number, number];
  door: { x: number; y0: number; y1: number; z0: number; z1: number };
}

const stone = { top: C.stoneTop, left: C.stoneL, right: C.stoneR, hi: C.stoneHi };
const wood = { top: C.woodTop, left: C.woodL, right: C.woodR, hi: C.woodHi };
const steel = { top: C.steelHi, left: C.steel, right: C.steelLo };
const leather = { top: C.leatherHi, left: C.leather, right: C.leatherLo };
const bezel = { top: C.bezelHi, left: C.bezel, right: C.screenOff };

/** Lines on a y-plane face, for panel seams and wainscoting. */
function hLineY(iso: Iso, y: number, x0: number, x1: number, z: number, c: number) {
  iso.hlineY(y, x0, x1, z, c);
}
function hLineX(iso: Iso, x: number, y0: number, y1: number, z: number, c: number) {
  iso.hlineX(x, y0, y1, z, c);
}
function rectY(iso: Iso, y: number, x0: number, x1: number, z0: number, z1: number, c: number) {
  iso.faceY(y, x0, x1, z0, z1, c);
}
function rectX(iso: Iso, x: number, y0: number, y1: number, z0: number, z1: number, c: number) {
  iso.faceX(x, y0, y1, z0, z1, c);
}
/** A 1px line between two world points (screen-space). */
function line3(iso: Iso, a: [number, number, number], b: [number, number, number], c: number) {
  const [ax, ay] = iso.p(...a);
  const [bx, by] = iso.p(...b);
  iso.buf.poly([[ax, ay], [bx, by], [bx, by + 1], [ax, ay + 1]], c);
}
/** A block of S×S pixels at a screen point. */
function blk(buf: PixelBuffer, x: number, y: number, c: number) {
  buf.rect(x, y, S, S, c);
}
function textY(iso: Iso, y: number, x0: number, zTop: number, s: string, c: number) {
  drawText(s, (dx, dy) => iso.onY(y, x0 + dx, zTop - dy, c));
}
function vline(iso: Iso, x: number, y: number, z0: number, z1: number, c: number) {
  const sx = Math.floor(iso.sx(x, y));
  const a = Math.floor(iso.sy(x, y, z1));
  const b = Math.floor(iso.sy(x, y, z0));
  for (let yy = a; yy < b; yy++) iso.buf.set(sx, yy, c);
}
function hash(a: number, b: number) {
  let h = (a * 374761393 + b * 668265263) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

// ---------------------------------------------------------------- floors & walls

function walls(iso: Iso, l: Level) {
  const zf = floorZ(l.index);
  const zc = base(l.index) + FH;
  const server = l.kind === 'server';
  const back = server ? C.stoneLine : C.wall;
  const side = server ? C.stoneDark : C.wallSide;
  iso.faceY(0, 0, X, zf, zc, back);
  iso.faceX(0, 0, Y, zf, zc, side);
  if (server) {
    // Concrete block courses.
    for (let z = zf + 4; z < zc; z += 5) hLineY(iso, 0, 0, X, z, C.stoneDark);
    for (let z = zf + 4; z < zc; z += 5) hLineX(iso, 0, 0, Y, z, C.baseLine);
    // Pipes along the left wall.
    hLineX(iso, 0, 0, Y, zf + 30, C.steelLo);
    hLineX(iso, 0, 0, Y, zf + 31, C.steel);
    hLineX(iso, 0, 0, Y, zf + 27, C.red);
    return;
  }
  const lobby = l.kind === 'lobby';
  const wainH = lobby ? 9 : 7;
  rectY(iso, 0, 0, X, zf, zf + wainH, C.wainscot);
  rectX(iso, 0, 0, Y, zf, zf + wainH, C.wainscotLo);
  hLineY(iso, 0, 0, X, zf + wainH, C.brass);
  hLineX(iso, 0, 0, Y, zf + wainH, C.brassLo);
  hLineY(iso, 0, 0, X, zf, C.wainscotLo);
  // Wainscot panels.
  for (let x = 6; x < X; x += 12) {
    iso.vlineY(0, x, zf + 2, zf + wainH - 1, C.wainscotHi);
  }
  // Pilasters on the back wall.
  for (const x of lobby ? [36, 148] : [34, 78, 122, 166]) {
    rectY(iso, 0, x - 1, x + 2, zf + wainH + 1, zc, C.wallShade);
    iso.vlineY(0, x - 1, zf + wainH + 1, zc, C.stoneHi);
  }
}

function floorSurface(iso: Iso, l: Level) {
  const zf = floorZ(l.index);
  if (l.kind === 'lobby') {
    for (let x = 0; x < X; x += 8)
      for (let y = 0; y < Y; y += 8) iso.top(x, y, Math.min(X, x + 8), Math.min(Y, y + 8), zf, ((x + y) / 8) % 2 ? C.marbleB : C.marbleA);
    // Veins.
    for (let i = 0; i < 40; i++) {
      const x = Math.floor(hash(i, 3) * X);
      const y = Math.floor(hash(i, 7) * Y);
      line3(iso, [x, y, zf], [x + 2, y + 1, zf], C.marbleVein);
    }
    // Runner to the elevator.
    iso.top(10, 17, X - 20, 23, zf, C.red);
    line3(iso, [10, 17, zf], [X - 20, 17, zf], C.brassLo);
    line3(iso, [10, 22.5, zf], [X - 20, 22.5, zf], C.brassLo);
    return;
  }
  if (l.kind === 'server') {
    iso.top(0, 0, X, Y, zf, C.steel);
    for (let x = 0; x < X; x += 12) line3(iso, [x, 0, zf], [x, Y, zf], C.steelLo);
    for (let y = 0; y < Y; y += 12) line3(iso, [0, y, zf], [X, y, zf], C.steelLo);
    return;
  }
  iso.top(0, 0, X, Y, zf, C.carpet);
  // Carpet pattern: a small repeating diamond.
  for (let x = 2; x < X; x += 8)
    for (let y = 2; y < Y; y += 6) {
      const [sx, sy] = iso.at(x + ((y / 6) % 2) * 4, y, zf);
      iso.buf.rect(sx, sy, 2, 1, C.carpetHi);
    }
  if (l.kind === 'office') {
    // A red rug under the partner's desk.
    iso.top(92, 2, 176, 22, zf, C.red);
    iso.top(95, 4, 173, 20, zf, C.redHi);
    iso.top(98, 6, 170, 18, zf, C.red);
    for (let x = 100; x < 168; x += 6) {
      iso.dot(x, 12, zf, C.brass);
    }
  }
}

function slabBand(iso: Iso, l: Level) {
  const zb = base(l.index);
  iso.faceY(Y, -5, X, zb, zb + ST, C.stoneL);
  hLineY(iso, Y, -5, X, zb + ST - 1, C.stoneHi);
  hLineY(iso, Y, -5, X, zb, C.stoneLine);
  // Dentils under the band.
  if (l.index >= 1) for (let x = -3; x < X; x += 4) iso.onY(Y, x, zb + 1, C.stoneLine);
  // Left wall section (the cut through the end wall).
  iso.faceY(Y, -5, 0, zb + ST, zb + FH, C.stoneL);
  iso.vlineY(Y, -1, zb + ST, zb + FH, C.stoneR);
}

function elevator(iso: Iso, l: Level) {
  const zf = floorZ(l.index);
  const { y0, y1 } = ELEVATOR;
  rectX(iso, 0, y0 - 1, y1 + 1, zf, zf + 27, C.brassLo);
  rectX(iso, 0, y0, y1, zf, zf + 26, C.brass);
  const mid = Math.floor((y0 + y1) / 2);
  iso.vlineX(0, mid, zf, zf + 26, C.brassLo);
  iso.hlineX(0, y0 + 1, y1 - 1, zf + 24, C.brassHi);
  iso.vlineX(0, y0 + 1, zf + 2, zf + 22, C.brassHi);
  iso.vlineX(0, mid + 1, zf + 2, zf + 22, C.brassHi);
  // Floor indicator: a small brass plate with the level label.
  rectX(iso, 0, mid - 3, mid + 4, zf + 29, zf + 36, C.woodDark);
  const label = l.label;
  const w = textWidth(label);
  drawText(label, (dx, dy) => iso.onX(0, mid + Math.floor(w / 2) - dx, zf + 34 - dy, C.amber));
}

// ---------------------------------------------------------------- furniture

function chair(iso: Iso, cx: number, zf: number) {
  // Star base.
  iso.box(cx - 1, 4, zf, cx + 1, 6, zf + 4, steel);
  iso.box(cx - 4, 2, zf + 4, cx + 4, 8, zf + 6, leather);
  iso.box(cx - 4, 1, zf + 6, cx + 4, 3, zf + 18, leather);
  iso.lineTopY(3, cx - 4, cx + 4, zf + 18, C.leatherHi);
}

function wallScreen(iso: Iso, x0: number, x1: number, z0: number, z1: number, screens: ScreenSpec[], spec: Omit<ScreenSpec, 'y' | 'x0' | 'x1' | 'z0' | 'z1'>) {
  rectY(iso, 0, x0 - 1, x1 + 1, z0 - 1, z1 + 1, C.bezel);
  rectY(iso, 0, x0, x1, z0, z1, C.screen);
  hLineY(iso, 0, x0 - 1, x1 + 1, z1, C.bezelHi);
  screens.push({ ...spec, y: 0, x0, x1, z0, z1 });
}

function desk(iso: Iso, fg: Iso, cx: number, zf: number, n: number, pencilled: boolean, variant: number) {
  const { y0, y1, h, half } = DESK;
  if (pencilled) {
    // A folding card table and a reserved card.
    fg.box(cx - 10, y0, zf + h - 1, cx + 10, y1, zf + h, { top: C.woodHi, left: C.woodL, right: C.woodR });
    for (const [x, y] of [
      [cx - 9, y1 - 1],
      [cx + 8, y1 - 1],
    ])
      vline(fg, x, y, zf, zf + h - 1, C.steelLo);
    fg.box(cx - 3, y0 + 2, zf + h, cx + 3, y0 + 3, zf + h + 4, { top: C.paper, left: C.paper, right: C.paperShade });
    // Folding chair.
    iso.box(cx - 3, 3, zf + 5, cx + 3, 7, zf + 6, steel);
    iso.box(cx - 3, 2, zf + 6, cx + 3, 3, zf + 14, steel);
    vline(iso, cx - 3, 7, zf, zf + 5, C.steelLo);
    vline(iso, cx + 2, 7, zf, zf + 5, C.steelLo);
  } else {
    chair(iso, cx, zf);
    fg.box(cx - half, y0, zf, cx + half, y1, zf + h, wood);
    // Modesty panel grooves and a brass edge.
    for (const x of [cx - half + 3, cx + half - 3]) fg.vlineY(y1, x, zf + 1, zf + h - 1, C.woodR);
    hLineY(fg, y1, cx - half, cx + half, zf + h - 1, C.brassLo);
    // Numbered brass plaque.
    const label = String(n).padStart(2, '0');
    rectY(fg, y1, cx - 5, cx + 4, zf + 1, zf + 7, C.brass);
    hLineY(fg, y1, cx - 5, cx + 4, zf + 6, C.brassHi);
    textY(fg, y1, cx - 4, zf + 6, label, C.woodDark);
    // Laptop: base and the back of the lid.
    fg.box(cx - 4, y0 + 1, zf + h, cx + 4, y0 + 4, zf + h + 1, steel);
    fg.box(cx - 4, y0, zf + h + 1, cx + 4, y0 + 1, zf + h + 4, { top: C.steelHi, left: C.steel, right: C.steelLo });
    fg.onY(y0 + 1, cx, zf + h + 2, C.steelHi);
    // Mug or plant, lamp, paper.
    if (variant % 2 === 0) {
      fg.box(cx - 12, y0 + 2, zf + h, cx - 10, y0 + 4, zf + h + 3, { top: C.coffee, left: C.white, right: C.paperShade });
    } else {
      const [sx, sy] = fg.at(cx - 11, y0 + 3, zf + h);
      blitAt(fg.buf, PLANTS.succulent, sx, sy + S);
    }
    fg.box(cx - 9, y0 + 1, zf + h, cx - 5, y0 + 5, zf + h + 1 + (variant % 3), { top: C.paper, left: C.paperShade, right: C.paperShade });
    // Brass lamp.
    fg.box(cx + 9, y0 + 1, zf + h, cx + 12, y0 + 3, zf + h + 1, { top: C.brassHi, left: C.brass, right: C.brassLo });
    vline(fg, cx + 10, y0 + 2, zf + h + 1, zf + h + 8, C.brassLo);
    fg.box(cx + 8, y0 + 1, zf + h + 7, cx + 13, y0 + 4, zf + h + 9, { top: C.leafHi, left: C.leaf, right: C.leafLo });
  }
}

const RUGS: number[][] = [
  [C.leafLo, C.leaf, C.brass, rgbaMul(C.leafLo)],
  [C.leather, C.leatherHi, C.brass, rgbaMul(C.leather)],
  [C.woodL, C.woodTop, C.cream, rgbaMul(C.woodL)],
  [C.slateLo, C.slate, C.brassHi, rgbaMul(C.slateLo)],
];

function rgbaMul(c: number) {
  return mixColor(c, C.ink, 0.35);
}

function wallDecor(iso: Iso, x0: number, zf: number, kind: number) {
  if (kind === 0) {
    // A framed landscape.
    rectY(iso, 0, x0, x0 + 10, zf + 9, zf + 17, C.woodDark);
    rectY(iso, 0, x0 + 1, x0 + 9, zf + 10, zf + 16, C.sky);
    rectY(iso, 0, x0 + 1, x0 + 9, zf + 10, zf + 12, C.grass);
    iso.onY(0, x0 + 3, zf + 12, C.grassLo);
    iso.onY(0, x0 + 4, zf + 13, C.grassLo);
    iso.onY(0, x0 + 6, zf + 14, C.white);
  } else if (kind === 1) {
    // A wall clock.
    rectY(iso, 0, x0 + 2, x0 + 8, zf + 10, zf + 16, C.brassLo);
    rectY(iso, 0, x0 + 3, x0 + 7, zf + 11, zf + 15, C.cream);
    iso.onY(0, x0 + 5, zf + 13, C.ink);
    iso.onY(0, x0 + 5, zf + 14, C.ink);
    iso.onY(0, x0 + 6, zf + 13, C.ink);
  } else {
    // A framed certificate with a red seal.
    rectY(iso, 0, x0, x0 + 9, zf + 9, zf + 17, C.brassLo);
    rectY(iso, 0, x0 + 1, x0 + 8, zf + 10, zf + 16, C.paper);
    hLineY(iso, 0, x0 + 2, x0 + 7, zf + 14, C.paperShade);
    hLineY(iso, 0, x0 + 2, x0 + 6, zf + 12, C.paperShade);
    iso.onY(0, x0 + 6, zf + 11, C.red);
  }
}

function partition(iso: Iso, x: number, zf: number) {
  iso.faceX(x, 1, 14, zf, zf + 15, C.glass, 0.45);
  hLineX(iso, x, 1, 14, zf + 14, C.glassFrame);
  hLineX(iso, x, 1, 14, zf, C.glassFrame);
  iso.vlineX(x, 13, zf, zf + 15, C.glassFrame);
  // Reflection streaks.
  for (let i = 0; i < 5; i++) iso.onX(x, 4 + i, zf + 6 + i, C.glassHi);
}

function kitchen(iso: Iso, zf: number, out: Built) {
  iso.box(170, 1, zf, 206, 7, zf + 10, wood);
  iso.box(169, 0, zf + 10, 207, 8, zf + 11, stone);
  // Coffee machine.
  iso.box(174, 2, zf + 11, 181, 6, zf + 19, { top: C.steelHi, left: C.bezel, right: C.screenOff });
  iso.onY(6, 175, zf + 16, C.ledRed);
  iso.box(176, 5, zf + 11, 178, 6, zf + 13, { top: C.coffee, left: C.white, right: C.paperShade });
  out.steam.push(iso.at(177, 4, zf + 20));
  // A kettle and a bowl of fruit.
  iso.box(186, 2, zf + 11, 190, 5, zf + 15, steel);
  iso.box(194, 2, zf + 11, 200, 6, zf + 13, { top: C.redHi, left: C.red, right: C.red });
  // Water cooler.
  iso.box(194, 12, zf, 200, 17, zf + 13, { top: C.cream, left: C.cream, right: C.paperShade });
  iso.box(195, 13, zf + 13, 199, 16, zf + 20, { top: C.waterHi, left: C.water, right: C.water });
  iso.onY(17, 196, zf + 9, C.ledRed);
  iso.onY(17, 198, zf + 9, C.candleUp);
}

function hr(iso: Iso, zf: number, out: Built) {
  for (const x0 of [170, 178]) {
    iso.box(x0, 1, zf, x0 + 8, 7, zf + 16, steel);
    for (const z of [zf + 4, zf + 8, zf + 12]) {
      hLineY(iso, 7, x0, x0 + 8, z, C.steelLo);
      iso.onY(7, x0 + 3, z + 2, C.brass);
      iso.onY(7, x0 + 4, z + 2, C.brass);
    }
  }
  out.cat = iso.at(174, 4, zf + 16);
  // Headshot corner: backdrop and a camera on a tripod.
  rectY(iso, 0, 190, 212, zf, zf + 20, C.steelHi);
  iso.top(190, 0, 212, 10, zf, C.steelHi);
  const [sx, sy] = iso.at(200, 16, zf);
  stampAt(iso.buf, CAMERA, sx, sy);
  // A stool.
  iso.box(197, 5, zf, 203, 9, zf + 7, wood);
}

function compliance(iso: Iso, zf: number) {
  iso.box(170, 1, zf, 188, 6, zf + 22, wood);
  const colors = [C.red, C.navy, C.leaf, C.brass, C.steelLo, C.red, C.navy];
  for (let row = 0; row < 3; row++) {
    const z0 = zf + 2 + row * 7;
    rectY(iso, 6, 171, 187, z0, z0 + 6, C.woodDark);
    for (let x = 171; x < 187; x += 2) rectY(iso, 6, x, x + 1, z0, z0 + 5, colors[(x + row * 3) % colors.length]);
  }
  // Review table: an in-tray, a very large stamp.
  iso.box(192, 9, zf, 210, 16, zf + 8, wood);
  iso.box(194, 10, zf + 8, 200, 14, zf + 10, { top: C.paper, left: C.paperShade, right: C.paperShade });
  iso.box(204, 11, zf + 8, 208, 14, zf + 10, { top: C.red, left: C.red, right: C.redHi });
  iso.box(205, 12, zf + 10, 207, 13, zf + 15, wood);
}

function terminalBoard(iso: Iso, zf: number, out: Built) {
  iso.box(172, 6, zf, 174, 8, zf + 6, steel);
  iso.box(206, 6, zf, 208, 8, zf + 6, steel);
  iso.box(170, 6, zf + 6, 210, 8, zf + 27, bezel);
  let slot = 0;
  for (let r = 0; r < 2; r++)
    for (let c = 0; c < 3; c++) {
      const x0 = 172 + c * 13;
      const z0 = zf + 8 + (1 - r) * 10;
      rectY(iso, 8, x0, x0 + 11, z0, z0 + 8, C.screen);
      out.screens.push({ kind: 'terminal', slot: slot++, y: 8, x0, x1: x0 + 11, z0, z1: z0 + 8 });
    }
}

function office(iso: Iso, zf: number, out: Built) {
  // Safe (the treasury).
  iso.box(38, 1, zf, 52, 9, zf + 16, { top: C.screenOff, left: C.bezel, right: C.screen });
  const [dx, dy] = iso.at(45, 9, zf + 9);
  for (const [a, b] of [
    [0, -2],
    [-1, -1],
    [1, -1],
    [-2, 0],
    [2, 0],
    [-1, 1],
    [1, 1],
    [0, 2],
  ])
    blk(iso.buf, dx + a * S, dy + b * S, C.brass);
  blk(iso.buf, dx, dy, C.brassHi);
  hLineY(iso, 9, 39, 51, zf + 15, C.bezelHi);
  // Portrait on the wall.
  rectY(iso, 0, 72, 86, zf + 5, zf + 19, C.brassLo);
  rectY(iso, 0, 73, 85, zf + 6, zf + 18, C.wainscotLo);
  {
    // The partner's portrait, sheared to lie flat on the wall.
    const bust = renderBust(PARTNER_LOOK, 22, true);
    const [px, py] = iso.at(73.5, 0, zf + 17.5);
    for (let j = 0; j < bust.h; j++)
      for (let i = 0; i < bust.w; i++) {
        const c = bust.px[j * bust.w + i];
        if (c) iso.buf.set(px + i, py + j + Math.floor(i / 2), c);
      }
  }
  // Globe.
  const [gx, gy] = iso.at(76, 14, zf);
  stampAt(iso.buf, GLOBE, gx, gy);
  // Partner's desk and chair.
  iso.box(124, 2, zf + 5, 136, 8, zf + 7, leather);
  iso.box(124, 1, zf + 7, 136, 3, zf + 21, leather);
  iso.box(126, 4, zf, 134, 6, zf + 5, steel);
  iso.box(110, 10, zf, 150, 17, zf + 10, wood);
  iso.box(109, 9, zf + 10, 151, 18, zf + 11, { top: C.leafLo, left: C.woodL, right: C.woodR, hi: C.brass });
  // Banker's lamp, papers, a fountain pen.
  iso.box(141, 11, zf + 11, 146, 13, zf + 12, { top: C.brass, left: C.brass, right: C.brassLo });
  vline(iso, 143, 12, zf + 12, zf + 16, C.brassLo);
  iso.box(139, 11, zf + 16, 148, 14, zf + 18, { top: C.leafHi, left: C.leaf, right: C.leafLo });
  iso.box(116, 12, zf + 11, 124, 16, zf + 12, { top: C.paper, left: C.paperShade, right: C.paperShade });
  // Bookshelf.
  iso.box(170, 0, zf, 206, 5, zf + 19, wood);
  const books = [C.red, C.navy, C.leaf, C.brass, C.cream, C.leatherHi, C.navy];
  for (let row = 0; row < 3; row++) {
    const z0 = zf + 1 + row * 6;
    rectY(iso, 5, 171, 205, z0, z0 + 5, C.woodDark);
    for (let x = 171; x < 205; x++) if (hash(x, row) > 0.25) rectY(iso, 5, x, x + 1, z0, z0 + 3 + Math.floor(hash(x, row + 9) * 2.5), books[Math.floor(hash(x, row + 4) * books.length)]);
  }
  // Grandfather clock.
  iso.box(24, 1, zf, 30, 5, zf + 25, wood);
  rectY(iso, 5, 25, 29, zf + 18, zf + 23, C.cream);
  iso.onY(5, 27, zf + 21, C.ink);
  iso.onY(5, 27, zf + 20, C.ink);
  rectY(iso, 5, 26, 28, zf + 4, zf + 15, C.woodDark);
  out.pendulum = iso.at(27, 5, zf + 14);
  // Armchair and a plant.
  iso.box(60, 12, zf, 70, 20, zf + 5, leather);
  iso.box(60, 11, zf + 5, 70, 13, zf + 12, leather);
  iso.box(59, 12, zf + 5, 61, 20, zf + 8, leather);
  const [fx, fy] = iso.at(212, 18, zf);
  blitAt(iso.buf, PLANTS.palm, fx, fy);
}

function lobby(iso: Iso, zf: number, out: Built) {
  // Brass lettering on a walnut panel.
  const name = FIRM_NAME.toUpperCase();
  const tw = textWidth(name);
  const x0 = 92 - Math.floor(tw / 2);
  rectY(iso, 0, x0 - 4, x0 + tw + 4, zf + 11, zf + 20, C.wainscotLo);
  textY(iso, 0, x0, zf + 18, name, C.brassHi);
  // LED ticker board.
  rectY(iso, 0, 38, 148, zf + 3, zf + 10, C.bezel);
  rectY(iso, 0, 39, 147, zf + 4, zf + 9, C.amberDim);
  out.ticker = { y: 0, x0: 39, x1: 147, z0: zf + 4, z1: zf + 9 };
  // Reception.
  iso.box(156, 3, zf, 196, 10, zf + 10, wood);
  iso.box(155, 2, zf + 10, 197, 11, zf + 11, { top: C.stoneTop, left: C.stoneL, right: C.stoneR, hi: C.brass });
  hLineY(iso, 10, 156, 196, zf + 5, C.brass);
  iso.box(170, 4, zf + 11, 176, 7, zf + 12, { top: C.paper, left: C.paperShade, right: C.paperShade });
  iso.box(184, 4, zf + 11, 187, 6, zf + 17, { top: C.brassHi, left: C.brass, right: C.brassLo });
  // Palms and a bench.
  for (const [x, y] of [
    [28, 20],
    [150, 18],
  ]) {
    const [sx, sy] = iso.at(x, y, zf);
    blitAt(iso.buf, PLANTS.palm, sx, sy);
  }
  iso.box(70, 13, zf, 110, 17, zf + 5, leather);
  iso.box(72, 12, zf, 74, 17, zf + 3, steel);
}

function server(iso: Iso, zf: number, out: Built) {
  for (let i = 0; i < 9; i++) {
    const x0 = 96 + i * 13;
    if (x0 + 11 > 212) break;
    iso.box(x0, 1, zf, x0 + 11, 7, zf + 20, { top: C.bezelHi, left: C.bezel, right: C.screenOff });
    for (let row = 0; row < 6; row++) {
      const z = zf + 3 + row * 3;
      hLineY(iso, 7, x0 + 1, x0 + 10, z - 1, C.screenOff);
      for (let k = 0; k < 3; k++) {
        const x = x0 + 2 + k * 3;
        iso.onY(7, x, z, C.ledOff);
        const cell: number[] = [];
        iso.cellY(7, x, z, (px, py) => cell.push(py * iso.buf.w + px));
        out.leds.push(cell);
      }
    }
  }
  // Cable tray.
  hLineY(iso, 0, 90, 212, zf + 24, C.steelLo);
  // Barry's post: a small desk with a CRT and a folding chair.
  iso.box(44, 3, zf, 66, 9, zf + 9, steel);
  iso.box(48, 3, zf + 9, 60, 8, zf + 19, { top: C.cream, left: C.cream, right: C.paperShade });
  rectY(iso, 8, 50, 58, zf + 11, zf + 17, C.screen);
  out.screens.push({ kind: 'crt', y: 8, x0: 50, x1: 58, z0: zf + 11, z1: zf + 17 });
  iso.box(70, 9, zf + 5, 78, 14, zf + 6, steel);
  iso.box(70, 8, zf + 6, 78, 9, zf + 14, steel);
  // Mop bucket and a desk fan.
  iso.box(24, 14, zf, 30, 19, zf + 6, { top: C.navy, left: C.brass, right: C.brassLo });
  vline(iso, 27, 16, zf + 6, zf + 22, C.woodHi);
  iso.box(62, 4, zf + 9, 65, 7, zf + 13, steel);
}

// ---------------------------------------------------------------- outside

function foundation(iso: Iso) {
  const zb = base(-1);
  iso.faceY(Y, -5, X, -GROUND_DEPTH, zb, C.earthL);
  for (let i = 0; i < 80; i++) {
    const x = Math.floor(hash(i, 11) * (X + 5)) - 5;
    const z = -GROUND_DEPTH + Math.floor(hash(i, 12) * (GROUND_DEPTH + zb));
    iso.onY(Y, x, z, i % 3 ? C.earthDot : C.stoneBits);
  }
}

function roof(iso: Iso, out: Built) {
  const zr = ROOF_Z;
  // Roof slab and cornice.
  iso.box(-5, 0, zr, X, Y, zr + ST, { top: C.roof, left: C.stoneL, right: C.stoneR });
  iso.box(-7, 0, zr + 2, X, Y + 2, zr + 5, { top: C.stoneTop, left: C.stoneL, right: C.stoneR, hi: C.stoneHi });
  for (let x = -5; x < X; x += 3) iso.onY(Y + 2, x, zr + 2, C.stoneLine);
  const zt = zr + ST;
  // Roof surface texture.
  for (let x = 4; x < X; x += 10) line3(iso, [x, 2, zt], [x, Y - 2, zt], C.roofLine);
  // Parapet along the back and left edges (the front is low so the roof reads).
  iso.box(-5, 0, zt, X, 2, zt + 5, stone);
  iso.box(-5, 0, zt, -3, Y, zt + 5, stone);
  iso.box(-3, Y - 2, zt, X, Y, zt + 3, stone);
  // Skylight.
  iso.box(120, 6, zt, 150, 16, zt + 3, { top: C.glass, left: C.steel, right: C.steelLo });
  for (let x = 124; x < 150; x += 6) {
    const [sx, sy] = iso.at(x, 6, zt + 3);
    for (let k = 0; k < 5 * S; k++) iso.buf.set(sx - k, sy + Math.floor(k / 2), C.glassHi);
  }
  // HVAC unit.
  iso.box(80, 4, zt, 100, 16, zt + 9, steel);
  for (const z of [zt + 3, zt + 5, zt + 7]) iso.hlineY(16, 83, 97, z, C.steelLo);
  // Elevator bulkhead with a slate roof.
  iso.box(196, 3, zt, 226, 21, zt + 16, stone);
  hLineY(iso, 21, 196, 226, zt + 1, C.stoneLine);
  rectY(iso, 21, 204, 210, zt, zt + 11, C.woodL);
  iso.onY(21, 209, zt + 5, C.brass);
  const zs = zt + 16;
  iso.buf.poly([iso.p(194, 23, zs), iso.p(228, 23, zs), iso.p(228, 12, zs + 11), iso.p(194, 12, zs + 11)], C.slate);
  iso.buf.poly([iso.p(228, 1, zs), iso.p(228, 23, zs), iso.p(228, 12, zs + 11)], C.slateLo);
  for (let k = 0; k < 11; k += 2) line3(iso, [194, 23 - k, zs + k], [228, 23 - k, zs + k], C.slateLine);
  line3(iso, [194, 12, zs + 11], [228, 12, zs + 11], C.slateHi);
  // Water tower.
  const [wx, wy] = iso.at(30, 12, zt);
  stampAt(iso.buf, WATER_TOWER, wx, wy);
  // Antenna.
  const [ax, ay] = iso.at(60, 6, zt);
  iso.buf.rect(ax, ay - 30 * S, 1, 30 * S, C.iron);
  for (const k of [10, 18, 24]) iso.buf.rect(ax - S, ay - k * S, 2 * S + 1, 1, C.iron);
  out.antenna = [ax, ay - 30 * S];
  // Flag on the front corner.
  const [fx, fy] = iso.at(168, 20, zt);
  iso.buf.rect(fx, fy - 20 * S, 1, 20 * S, C.steelHi);
  const [gx, gy] = iso.at(168, 20, zt + 20);
  stampAt(iso.buf, FLAG, gx + 3 * S, gy + FLAG.length * S);
  // Pigeons.
  for (const [x, y] of [
    [140, 22],
    [146, 22],
  ]) {
    const [sx, sy] = iso.at(x, y, zt + 3);
    stampAt(iso.buf, PIGEON, sx, sy);
  }
}

function facade(iso: Iso, out: Built) {
  const x = X;
  const xo = X + 6;
  const top = ROOF_Z + ST + 5;
  const bottom = -GROUND_DEPTH + 5;
  // The wall: outer face, thickness at the cut, and the top.
  iso.faceX(xo, 0, Y, bottom, top, C.stoneR);
  iso.faceY(Y, x, xo, bottom, top, C.stoneL);
  iso.top(x, 0, xo, Y, top, C.stoneTop);
  iso.vlineY(Y, x, bottom, top, C.stoneHi);
  // Coursing lines.
  for (let z = bottom + 3; z < top; z += 6) hLineX(iso, xo, 0, Y, z, C.stoneLine);
  for (const l of LEVELS) {
    const zb = base(l.index);
    const zf = floorZ(l.index);
    // Ledge.
    iso.box(xo, -1, zb, xo + 2, Y + 1, zb + 3, { top: C.stoneTop, left: C.stoneL, right: C.stoneR, hi: C.stoneHi });
    if (l.kind === 'lobby') {
      // Revolving door with a navy canopy.
      const y0 = 5;
      const y1 = 19;
      rectX(iso, xo, y0 - 1, y1 + 1, zf, zf + 28, C.brassLo);
      rectX(iso, xo, y0, y1, zf, zf + 26, C.glass);
      out.door = { x: xo, y0, y1, z0: zf, z1: zf + 26 };
      iso.box(xo, y0 - 2, zf + 27, xo + 7, y1 + 2, zf + 30, { top: C.navy, left: C.navy, right: C.slateLo });
      hLineX(iso, xo + 7, y0 - 2, y1 + 2, zf + 27, C.brass);
      continue;
    }
    if (l.kind === 'server') {
      rectX(iso, xo, 0, Y, zb, zb + FH, C.baseR);
      for (let z = zb + 4; z < zb + FH; z += 6) hLineX(iso, xo, 0, Y, z, C.baseLine);
      // Barred window.
      rectX(iso, xo, 8, 16, zb + 34, zb + 42, C.screenOff);
      for (let y = 9; y < 16; y += 2) iso.vlineX(xo, y, zb + 34, zb + 42, C.iron);
      continue;
    }
    // Two windows per floor.
    for (const [y0, y1] of [
      [3, 10],
      [14, 21],
    ]) {
      rectX(iso, xo, y0 - 1, y1 + 1, zf + 9, zf + 36, C.stoneLine);
      rectX(iso, xo, y0, y1, zf + 10, zf + 35, C.sky);
      iso.vlineX(xo, Math.floor((y0 + y1) / 2), zf + 10, zf + 35, C.stoneR);
      hLineX(iso, xo, y0, y1, zf + 22, C.stoneR);
      for (let k = 0; k < 6; k++) iso.onX(xo, y1 - 2 - Math.floor(k / 2), zf + 26 + k, C.skyHi);
      // Sill.
      hLineX(iso, xo, y0 - 1, y1 + 1, zf + 9, C.stoneHi);
    }
  }
  // Top cornice.
  iso.box(xo, -2, top - 4, xo + 3, Y + 2, top, { top: C.stoneTop, left: C.stoneL, right: C.stoneR, hi: C.stoneHi });
}

function lot(iso: Iso) {
  const { x0, x1, y0, y1 } = LOT;
  // Ground block with an earth section.
  iso.faceY(y1, x0, x1, -GROUND_DEPTH, 0, C.earthL);
  iso.faceX(x1, y0, y1, -GROUND_DEPTH, 0, C.earthR);
  hLineY(iso, y1, x0, x1, -1, C.grassLo);
  hLineX(iso, x1, y0, y1, -1, C.grassLo);
  for (let i = 0; i < 40; i++) {
    const z = -GROUND_DEPTH + Math.floor(hash(i, 21) * (GROUND_DEPTH - 3));
    iso.onY(y1, x0 + Math.floor(hash(i, 22) * (x1 - x0)), z, C.earthDot);
    iso.onX(x1, y0 + Math.floor(hash(i, 23) * (y1 - y0)), z, i % 2 ? C.earthDot : C.stoneBits);
  }
  iso.top(x0, y0, x1, y1, 0, C.grass);
  for (let i = 0; i < 60; i++) {
    iso.dot(x0 + Math.floor(hash(i, 31) * (x1 - x0)), y0 + Math.floor(hash(i, 32) * (y1 - y0)), 0, i % 2 ? C.grassHi : C.grassLo, 1 + (i % 2));
  }
  // Paving: landing, path to the street.
  iso.top(x0 + 6, 2, 262, 22, 0, C.sidewalk);
  iso.top(250, 2, 262, y1, 0, C.sidewalk);
  for (let y = 4; y < y1; y += 4) line3(iso, [250, y, 0], [262, y, 0], C.sidewalkLine);
  line3(iso, [256, 2, 0], [256, y1, 0], C.sidewalkLine);
  // Steps up to the door.
  iso.box(x0 + 6, 2, 0, x0 + 12, 22, 3, { top: C.sidewalk, left: C.sidewalkL, right: C.sidewalkR, hi: C.stoneHi });
  iso.box(x0 + 6, 3, 3, x0 + 9, 21, 5, { top: C.sidewalk, left: C.sidewalkL, right: C.sidewalkR, hi: C.stoneHi });
  // Shrubs and flowers.
  for (const [x, y] of [
    [240, -2],
    [252, -3],
    [266, 0],
    [268, 10],
  ]) {
    const [sx, sy] = iso.at(x, y, 0);
    blitAt(iso.buf, PLANTS.shrub, sx, sy);
  }
  for (const [x, y] of [
    [245, 26],
    [266, 20],
    [266, 26],
    [258, -2],
  ]) {
    const [sx, sy] = iso.at(x, y, 0);
    blitAt(iso.buf, PLANTS.flowers, sx, sy);
  }
  // Shredder bin by the fence.
  iso.box(238, 22, 0, 245, 28, 10, { top: C.binLo, left: C.bin, right: C.binLo, hi: C.binHi });
  iso.box(237, 21, 10, 246, 29, 11, { top: C.binHi, left: C.bin, right: C.binLo });
  hLineY(iso, 28, 239, 244, 8, C.binLo);
  iso.onY(28, 241, 9, C.paper);
  iso.onY(28, 242, 9, C.paper);
  iso.onY(29, 243, 11, C.paper);
  const [bx, by] = iso.at(241, 29, 4);
  drawText('S', (dx, dy) => blk(iso.buf, bx + dx * S, by + (dy - 2) * S, C.paper));
  // Lamppost.
  const [lx, ly] = iso.at(268, -2, 0);
  iso.buf.rect(lx - 1, ly - 32 * S, 2, 32 * S, C.iron);
  iso.buf.rect(lx - S, ly - S, 2 * S + 1, S, C.iron);
  stampAt(iso.buf, LAMP_HEAD, lx, ly - 31 * S);
  // Iron fence along the two front edges, with a gate gap at the path.
  const posts: [number, number][] = [];
  for (let x = x0 + 1; x < x1; x += 3) if (x < 250 || x > 262) posts.push([x, y1 - 1]);
  for (let y = y0 + 1; y < y1; y += 3) posts.push([x1 - 1, y]);
  for (const [x, y] of posts) vline(iso, x, y, 0, 7, C.iron);
  for (const z of [6.5, 3]) {
    const c = z > 5 ? C.ironHi : C.iron;
    line3(iso, [x0 + 1, y1 - 1, z], [250, y1 - 1, z], c);
    line3(iso, [263, y1 - 1, z], [x1 - 1, y1 - 1, z], c);
    line3(iso, [x1 - 1, y0 + 1, z], [x1 - 1, y1 - 1, z], c);
  }
  // Gate posts.
  for (const x of [249, 263]) {
    const [sx, sy] = iso.at(x, y1 - 1, 0);
    iso.buf.rect(sx - 1, sy - 10 * S, S + 1, 10 * S, C.stoneR);
    blk(iso.buf, sx - 1, sy - 10 * S - S, C.brass);
  }
}

export function buildScene(): Built {
  const bg = new PixelBuffer(W, H);
  const fg = new PixelBuffer(W, H);
  const front = new PixelBuffer(W, H);
  const out: Built = {
    bg,
    fg,
    front,
    screens: [],
    ticker: { y: 0, x0: 0, x1: 0, z0: 0, z1: 0 },
    leds: [],
    steam: [],
    cat: [0, 0],
    antenna: [0, 0],
    pendulum: [0, 0],
    door: { x: 0, y0: 0, y1: 0, z0: 0, z1: 0 },
  };
  const b = new Iso(bg, OX, OY);
  const f = new Iso(fg, OX, OY);
  const fr = new Iso(front, OX, OY);

  foundation(b);
  for (const l of LEVELS) {
    const zf = floorZ(l.index);
    walls(b, l);
    floorSurface(b, l);
    elevator(b, l);
    if (l.kind === 'desks') {
      const rug = RUGS[(l.index - 1) % RUGS.length];
      l.desks.forEach((d, bay) => {
        const cx = BAY_X[bay];
        if (d !== 0) {
          b.top(cx - 19, 1, cx + 19, 22, zf, rug[0]);
          b.top(cx - 17, 2, cx + 17, 21, zf, rug[1]);
          b.top(cx - 15, 3, cx + 15, 20, zf, rug[0]);
          for (let x = cx - 13; x < cx + 14; x += 4) {
            const [sx, sy] = b.at(x, 19, zf);
            bg.set(sx, sy, rug[2]);
          }
          // Shadow in front of the desk.
          b.top(cx - DESK.half, DESK.y1, cx + DESK.half + 1, DESK.y1 + 2, zf, rug[3]);
          wallDecor(b, cx + 9, zf, (d + l.index) % 3);
        }
        if (d !== 0) wallScreen(b, cx - 20, cx - 8, zf + 8, zf + 17, out.screens, { kind: 'desk', desk: d });
        else {
          // A framed notice where the screen would be.
          rectY(b, 0, cx - 19, cx - 9, zf + 9, zf + 16, C.cream);
          hLineY(b, 0, cx - 19, cx - 9, zf + 16, C.brassLo);
          textY(b, 0, cx - 18, zf + 15, '12', C.brassLo);
        }
        desk(b, f, cx, zf, d, d === 0, d + l.index);
      });
      for (const x of [78, 122]) partition(b, x, zf);
      partition(b, 166, zf);
      if (l.feature === 'kitchen') kitchen(b, zf, out);
      if (l.feature === 'hr') hr(b, zf, out);
      if (l.feature === 'compliance') compliance(b, zf);
      if (l.feature === 'terminal') terminalBoard(b, zf, out);
      // A potted fern by the elevator.
      const [sx, sy] = b.at(26, 20, zf);
      blitAt(bg, PLANTS.fern, sx, sy);
    }
    if (l.kind === 'office') office(b, zf, out);
    if (l.kind === 'lobby') lobby(b, zf, out);
    if (l.kind === 'server') server(b, zf, out);
    slabBand(b, l);
  }
  roof(b, out);
  facade(fr, out);
  lot(fr);
  return out;
}

export const INTERIOR_H = INTERIOR;
