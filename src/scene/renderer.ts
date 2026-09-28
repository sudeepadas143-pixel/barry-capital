/**
 * Composes one frame at native resolution:
 * background → animated key colours → seated actors → desks → walkers
 * → facade and lot → revolving door → people outside → hover marker.
 */
import { PixelBuffer, Sparse } from './buffer';
import { buildScene, type Built } from './building';
import { animPass, doorPass, marker, type SceneData } from './anim';
import type { Actor } from './actors';
import { Iso } from './iso';
import { H, OX, OY, W } from './layout';
import { sprite, type SpriteImage } from './sprites';

export interface CustomArt {
  bg: PixelBuffer;
  fg?: PixelBuffer;
  /** Seat points by desk, when the art supplies its own hotspots. */
  seats?: Map<number, [number, number]>;
  partner?: Record<string, [number, number]>;
  sprites?: (a: Actor) => SpriteImage | null;
}

function blit(dst: PixelBuffer, img: SpriteImage, sx: number, sy: number) {
  const x0 = Math.round(sx - img.w / 2);
  const y0 = Math.round(sy - img.h);
  for (let y = 0; y < img.h; y++) {
    const dy = y0 + y;
    if (dy < 0 || dy >= dst.h) continue;
    for (let x = 0; x < img.w; x++) {
      const c = img.px[y * img.w + x];
      if (!c) continue;
      const dx = x0 + x;
      if (dx < 0 || dx >= dst.w) continue;
      dst.data[dy * dst.w + dx] = c;
    }
  }
}

export class Renderer {
  readonly built: Built;
  readonly frame: PixelBuffer;
  readonly iso: Iso;
  private fg: Sparse;
  private front: Sparse;
  private custom?: CustomArt;
  private customFg?: Sparse;

  constructor(custom?: CustomArt) {
    this.built = buildScene();
    this.frame = new PixelBuffer(custom?.bg.w ?? W, custom?.bg.h ?? H);
    this.iso = new Iso(this.frame, OX, OY);
    this.fg = new Sparse(this.built.fg);
    this.front = new Sparse(this.built.front);
    this.custom = custom;
    if (custom?.fg) this.customFg = new Sparse(custom.fg);
  }

  private screenPoint(a: Actor): [number, number] {
    if (this.custom?.seats && a.layer === 'seated' && a.desk !== undefined) {
      const p = this.custom.seats.get(a.desk);
      if (p) return p;
    }
    if (this.custom?.partner && a.id === 'partner') {
      const p = this.custom.partner[a.spot ?? ''] ?? Object.values(this.custom.partner)[0];
      if (p) return p;
    }
    return this.iso.at(a.x, a.y, a.z);
  }

  private drawActor(a: Actor) {
    const img = this.custom?.sprites?.(a) ?? sprite(a.look, a.pose, a.frame, a.glasses);
    const [sx, sy] = this.screenPoint(a);
    blit(this.frame, img, sx, sy + 1);
  }

  render(t: number, data: SceneData, actors: Actor[], doorSpin: boolean): PixelBuffer {
    const f = this.frame;
    const custom = this.custom;
    f.data.set(custom ? custom.bg.data : this.built.bg.data);
    if (!custom) animPass(f, this.iso, this.built, t, data);
    for (const a of actors) if (a.layer === 'seated' && (!custom || a.desk !== undefined)) this.drawActor(a);
    if (custom) this.customFg?.draw(f);
    else this.fg.draw(f);
    for (const a of actors) if (a.layer === 'walk' && (!custom || a.id === 'partner')) this.drawActor(a);
    if (!custom) {
      this.front.draw(f);
      doorPass(this.iso, this.built, t, doorSpin);
      for (const a of actors) if (a.layer === 'outside') this.drawActor(a);
    }
    if (data.hotDesk !== null) {
      const a = actors.find((x) => x.desk === data.hotDesk && x.layer === 'seated');
      if (a) {
        const [sx, sy] = this.screenPoint(a);
        marker(f, sx, sy - 62, t);
      }
    }
    return f;
  }
}
