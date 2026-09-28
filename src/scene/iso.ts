/**
 * 2:1 isometric projection onto a PixelBuffer.
 * World axes: +x runs down-right on screen, +y runs down-left, +z is up.
 * One world unit along x or y is one screen pixel across and half a pixel down.
 */
import { PixelBuffer } from './buffer';

export interface BoxColors {
  top: number;
  /** The face at y = y1, facing down-left. */
  left: number;
  /** The face at x = x1, facing down-right. */
  right: number;
  /** Optional light edge along the top face's front edges. */
  hi?: number;
  /** Optional dark line down the front corner and along the bottom. */
  lo?: number;
}

export class Iso {
  constructor(
    public buf: PixelBuffer,
    public ox: number,
    public oy: number,
  ) {}

  sx(x: number, y: number) {
    return this.ox + x - y;
  }
  sy(x: number, y: number, z: number) {
    return this.oy + (x + y) / 2 - z;
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
      const sx = Math.round(this.sx(x1, y1)) - 1;
      const yTop = Math.floor(this.sy(x1, y1, z1));
      const yBot = Math.ceil(this.sy(x1, y1, z0));
      for (let y = yTop + 1; y < yBot; y++) this.buf.set(sx, y, c.lo);
    }
  }

  /** A 1px line along the top-front edge (y = y1) of a surface at height z. */
  lineTopY(y: number, x0: number, x1: number, z: number, c: number) {
    for (let x = x0; x < x1; x++) {
      const sx = Math.floor(this.sx(x, y));
      this.buf.set(sx, Math.floor(this.sy(x + 0.5, y, z)), c);
    }
  }

  /** A 1px line along the top-front edge (x = x1). */
  lineTopX(x: number, y0: number, y1: number, z: number, c: number) {
    for (let y = y0; y < y1; y++) {
      const sx = Math.floor(this.sx(x, y + 1));
      this.buf.set(sx, Math.floor(this.sy(x, y + 0.5, z)), c);
    }
  }

  /** Paint pixels on a y-plane face in face space: u along x, v up in z. */
  onY(y: number, x: number, z: number, c: number) {
    this.buf.set(Math.floor(this.sx(x, y)), Math.floor(this.sy(x + 0.5, y, z + 0.5)), c);
  }

  /** Paint pixels on an x-plane face: u along y, v up in z. */
  onX(x: number, y: number, z: number, c: number) {
    this.buf.set(Math.floor(this.sx(x, y + 1)), Math.floor(this.sy(x, y + 0.5, z + 0.5)), c);
  }

  /** Vertical run on a y-plane face at world x, from z0 up to z1 (exclusive). */
  runY(y: number, x: number, z0: number, z1: number, c: number) {
    for (let z = z0; z < z1; z++) this.onY(y, x, z, c);
  }

  runX(x: number, y: number, z0: number, z1: number, c: number) {
    for (let z = z0; z < z1; z++) this.onX(x, y, z, c);
  }

  /** Screen point for a world point, rounded to pixels. */
  at(x: number, y: number, z: number): [number, number] {
    return [Math.round(this.sx(x, y)), Math.round(this.sy(x, y, z))];
  }
}
