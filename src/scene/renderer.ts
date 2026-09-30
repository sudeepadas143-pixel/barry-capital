/**
 * Composes one frame:
 * background → screens and tickers → seated actors → desks → desk monitors
 * → walkers → facade and street → revolving door → people outside → helicopter
 * → hover marker.
 *
 * The static layers are drawn once per resolution. In the browser they are
 * canvases at the screen's own pixel density; in Node they are pixel buffers.
 */
import { PixelBuffer, Sparse } from './buffer';
import { buildScene, type Built } from './building';
import { animPass, deskScreens, doorPass, heliPass, marker, wallCharts, type SceneData } from './anim';
import type { Actor } from './actors';
import { Iso } from './iso';
import { H, OX, OY, W } from './layout';
import { figureSrc, scaleNearest, type SpriteImage } from './sprites';
import { CanvasSurface, PixelSurface, makeCanvas, type Surface } from './surface';

export interface CustomArt {
  bg: PixelBuffer;
  fg?: PixelBuffer;
  /** Seat points by desk, when the art supplies its own hotspots. */
  seats?: Map<number, [number, number]>;
  partner?: Record<string, [number, number]>;
  sprites?: (a: Actor) => SpriteImage | null;
}

export type LayerId = 'bg' | 'fg' | 'front';

/** Where frames are drawn: pixels (Node) or canvases (browser). */
export interface Backend {
  /** Device pixels per scene pixel. */
  readonly k: number;
  readonly main: Surface;
  layer(id: LayerId): Surface;
  /** Called once the static layers are drawn. */
  seal(): void;
  begin(): void;
  composite(id: LayerId): void;
  /** Composite a layer plus whatever `draw` adds, redrawing the addition only when `key` changes. */
  live(id: LayerId, key: string, draw: (s: Surface) => void): void;
}

export class PixelBackend implements Backend {
  readonly k = 1;
  readonly frame: PixelBuffer;
  readonly main: PixelSurface;
  private bufs: Record<LayerId, PixelBuffer>;
  private sparse: Partial<Record<LayerId, Sparse>> = {};
  constructor(w = W, h = H) {
    this.frame = new PixelBuffer(w, h);
    this.main = new PixelSurface(this.frame);
    this.bufs = { bg: new PixelBuffer(w, h), fg: new PixelBuffer(w, h), front: new PixelBuffer(w, h) };
  }
  layer(id: LayerId) {
    return new PixelSurface(this.bufs[id]);
  }
  buffer(id: LayerId) {
    return this.bufs[id];
  }
  seal() {
    this.sparse.fg = new Sparse(this.bufs.fg);
    this.sparse.front = new Sparse(this.bufs.front);
  }
  begin() {
    this.frame.data.set(this.bufs.bg.data);
  }
  composite(id: LayerId) {
    if (id === 'bg') return;
    this.sparse[id]?.draw(this.frame);
  }
  live(id: LayerId, _key: string, draw: (s: Surface) => void) {
    this.composite(id);
    draw(this.main);
  }
}

export class CanvasBackend implements Backend {
  readonly main: CanvasSurface;
  private layers = {} as Record<LayerId, CanvasSurface>;
  constructor(
    canvas: HTMLCanvasElement,
    readonly k: number,
    w = W,
    h = H,
  ) {
    this.main = new CanvasSurface(canvas, w, h, k);
    for (const id of ['bg', 'fg', 'front'] as LayerId[]) this.layers[id] = new CanvasSurface(makeCanvas(canvas.width, canvas.height), w, h, k);
  }
  layer(id: LayerId) {
    return this.layers[id];
  }
  seal() {}
  begin() {
    this.main.reset();
    this.main.clear();
  }
  composite(id: LayerId) {
    this.main.draw(this.layers[id]);
  }
  private lives: Partial<Record<LayerId, { s: CanvasSurface; key: string }>> = {};
  live(id: LayerId, key: string, draw: (s: Surface) => void) {
    let l = this.lives[id];
    if (!l) {
      const base = this.layers[id];
      l = { s: new CanvasSurface(makeCanvas(base.canvas.width, base.canvas.height), base.w, base.h, this.k), key: '' };
      this.lives[id] = l;
    }
    if (l.key !== key) {
      l.s.reset();
      l.s.clear();
      l.s.draw(this.layers[id]);
      draw(l.s);
      l.key = key;
    }
    this.main.draw(l.s);
  }
}

export class Renderer {
  readonly built: Built | null;
  readonly iso: Iso;
  constructor(
    readonly backend: Backend,
    private custom?: CustomArt,
  ) {
    if (custom) {
      backend.layer('bg').image(custom.bg);
      if (custom.fg) backend.layer('fg').image(custom.fg);
      this.built = null;
    } else {
      this.built = buildScene({ bg: backend.layer('bg'), fg: backend.layer('fg'), front: backend.layer('front') });
    }
    backend.seal();
    this.iso = new Iso(backend.main, OX, OY);
  }

  screenPoint(a: Actor): [number, number] {
    if (this.custom?.seats && a.layer === 'seated' && a.desk !== undefined) {
      const p = this.custom.seats.get(a.desk);
      if (p) return p;
    }
    if (this.custom?.partner && a.id === 'partner') {
      const p = this.custom.partner[a.spot ?? ''] ?? Object.values(this.custom.partner)[0];
      if (p) return p;
    }
    return this.iso.p(a.x, a.y, a.z);
  }

  private drawActor(a: Actor) {
    const [sx, sy] = this.screenPoint(a);
    // A soft contact shadow under anyone standing.
    if (a.layer !== 'seated') {
      this.backend.main.ellipse(sx, sy + 0.5, 6.5 * 3, 2.4 * 3, 0xff1d1c19, 0.18);
      this.backend.main.ellipse(sx, sy + 0.5, 4 * 3, 1.4 * 3, 0xff1d1c19, 0.16);
    }
    const img = this.custom?.sprites?.(a);
    const src = img ? { id: `custom:${a.id}:${a.pose}:${a.frame}`, render: (k: number) => scaleNearest(img, k) } : figureSrc(a.look, a.pose, a.frame, a.glasses);
    this.backend.main.sprite(src, sx, sy + 1);
  }

  render(t: number, data: SceneData, actors: Actor[], doorSpin: boolean) {
    const { backend, built, custom } = this;
    const main = backend.main;
    backend.begin();
    const key = String(data.version ?? Math.random());
    if (built) backend.live('bg', key, (s) => wallCharts(s, this.iso, built, data));
    else backend.composite('bg');
    if (built) animPass(main, this.iso, built, t, data);
    for (const a of actors) if (a.layer === 'seated' && (!custom || a.desk !== undefined)) this.drawActor(a);
    if (built) backend.live('fg', key, (s) => deskScreens(s, this.iso, built, data));
    else backend.composite('fg');
    for (const a of actors) if (a.layer === 'walk' && (!custom || a.id === 'partner')) this.drawActor(a);
    if (built) {
      backend.composite('front');
      doorPass(this.iso, built, t, doorSpin);
      for (const a of actors) if (a.layer === 'outside') this.drawActor(a);
      heliPass(main, built, t);
    }
    if (data.hotDesk !== null) {
      const a = actors.find((x) => x.desk === data.hotDesk && x.layer === 'seated');
      if (a) {
        const [sx, sy] = this.screenPoint(a);
        marker(main, sx, sy - 33 * 3, t);
      }
    }
  }
}
