/**
 * 2:1 isometric projection onto a Surface.
 * World axes: +x runs down-right on screen, +y runs down-left, +z is up.
 * One world unit along x or y is `s` pixels across and `s / 2` down.
 */
import type { Affine, Pt, Surface, TextOpts } from './surface';
import { S } from './layout';

export interface BoxColors {
  top: number;
  /** The face at y = y1, facing down-left. */
  left: number;
  /** The face at x = x1, facing down-right. */
  right: number;
  /** Optional light edge along the top face's front edges. */
  hi?: number;
  /** Optional dark line down the front corner. */
  lo?: number;
}

export class Iso {
  constructor(
    public buf: Surface,
    public ox: number,
    public oy: number,
    public s: number = S,
  ) {}

  sx(x: number, y: number) {
    return this.ox + (x - y) * this.s;
  }
  sy(x: number, y: number, z: number) {
    return this.oy + ((x + y) / 2 - z) * this.s;
  }
  p(x: number, y: number, z: number): [number, number] {
    return [this.sx(x, y), this.sy(x, y, z)];
  }

  /** Horizontal rectangle at height z. */
  top(x0: number, y0: number, x1: number, y1: number, z: number, c: number, alpha = 1) {
    this.buf.poly([this.p(x0, y0, z), this.p(x1, y0, z), this.p(x1, y1, z), this.p(x0, y1, z)], c, alpha);
  }

  /** Vertical face in the plane y = y, spanning x0..x1 and z0..z1 (seen from +y). */
  faceY(y: number, x0: number, x1: number, z0: number, z1: number, c: number, alpha = 1) {
    this.buf.poly([this.p(x0, y, z1), this.p(x1, y, z1), this.p(x1, y, z0), this.p(x0, y, z0)], c, alpha);
  }

  /** Vertical face in the plane x = x, spanning y0..y1 and z0..z1 (seen from +x). */
  faceX(x: number, y0: number, y1: number, z0: number, z1: number, c: number, alpha = 1) {
    this.buf.poly([this.p(x, y0, z1), this.p(x, y1, z1), this.p(x, y1, z0), this.p(x, y0, z0)], c, alpha);
  }

  box(x0: number, y0: number, z0: number, x1: number, y1: number, z1: number, c: BoxColors) {
    this.faceY(y1, x0, x1, z0, z1, c.left);
    this.faceX(x1, y0, y1, z0, z1, c.right);
    this.top(x0, y0, x1, y1, z1, c.top);
    if (c.hi !== undefined) {
      this.lineTopY(y1, x0, x1, z1, c.hi);
      this.lineTopX(x1, y0, y1, z1, c.hi);
    }
    if (c.lo !== undefined) {
      const sx = this.sx(x1, y1);
      this.buf.rect(sx - 1, this.sy(x1, y1, z1), 1, (z1 - z0) * this.s, c.lo);
    }
  }

  /** A 1px line along the front edge (y = y) of a surface at height z. */
  lineTopY(y: number, x0: number, x1: number, z: number, c: number) {
    this.top(x0, y - 2 / this.s, x1, y, z, c);
  }

  /** A 1px line along the front edge (x = x). */
  lineTopX(x: number, y0: number, y1: number, z: number, c: number) {
    this.top(x - 2 / this.s, y0, x, y1, z, c);
  }

  /** One world-unit cell on a y-plane face (u along x, v up in z). */
  onY(y: number, x: number, z: number, c: number) {
    this.faceY(y, x, x + 1, z, z + 1, c);
  }

  /** One world-unit cell on an x-plane face (u along y, v up in z). */
  onX(x: number, y: number, z: number, c: number) {
    this.faceX(x, y, y + 1, z, z + 1, c);
  }

  /** Corners of a y-plane rectangle, for clipping. */
  quadY(y: number, x0: number, x1: number, z0: number, z1: number): Pt[] {
    return [this.p(x0, y, z1), this.p(x1, y, z1), this.p(x1, y, z0), this.p(x0, y, z0)];
  }

  quadX(x: number, y0: number, y1: number, z0: number, z1: number): Pt[] {
    return [this.p(x, y0, z1), this.p(x, y1, z1), this.p(x, y1, z0), this.p(x, y0, z0)];
  }

  /** Text space on a y-plane: u runs along +x, v runs down (−z), origin at (x0, y, z). */
  planeY(y: number, x0: number, z: number): Affine {
    const [e, f] = this.p(x0, y, z);
    return { a: this.s, b: this.s / 2, c: 0, d: this.s, e, f };
  }

  /** Text space on an x-plane, reading left to right on screen (along −y). */
  planeX(x: number, y0: number, z: number): Affine {
    const [e, f] = this.p(x, y0, z);
    return { a: this.s, b: -this.s / 2, c: 0, d: this.s, e, f };
  }

  /** Text on a y-plane with its baseline at height z. */
  textY(y: number, x: number, z: number, str: string, o: TextOpts) {
    this.buf.text(str, this.planeY(y, x, z), o);
  }

  textX(x: number, y: number, z: number, str: string, o: TextOpts) {
    this.buf.text(str, this.planeX(x, y, z), o);
  }

  /** A thin (1px) horizontal line on a y-plane face at height z. */
  hlineY(y: number, x0: number, x1: number, z: number, c: number) {
    this.faceY(y, x0, x1, z, z + 1 / this.s, c);
  }

  hlineX(x: number, y0: number, y1: number, z: number, c: number) {
    this.faceX(x, y0, y1, z, z + 1 / this.s, c);
  }

  /** A thin (1px) vertical line on a y-plane face at x. */
  vlineY(y: number, x: number, z0: number, z1: number, c: number) {
    this.faceY(y, x, x + 1 / this.s, z0, z1, c);
  }

  vlineX(x: number, y: number, z0: number, z1: number, c: number) {
    this.faceX(x, y, y + 1 / this.s, z0, z1, c);
  }

  runY(y: number, x: number, z0: number, z1: number, c: number) {
    this.faceY(y, x, x + 1, z0, z1, c);
  }

  runX(x: number, y: number, z0: number, z1: number, c: number) {
    this.faceX(x, y, y + 1, z0, z1, c);
  }

  /** Screen point for a world point, rounded to pixels. */
  at(x: number, y: number, z: number): [number, number] {
    return [Math.round(this.sx(x, y)), Math.round(this.sy(x, y, z))];
  }

  /** A small square dot of `size` pixels at a world point. */
  dot(x: number, y: number, z: number, c: number, size = this.s) {
    const [sx, sy] = this.at(x, y, z);
    this.buf.rect(sx - Math.floor(size / 2), sy - Math.floor(size / 2), size, size, c);
  }
}
