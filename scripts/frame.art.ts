import { mkdirSync, writeFileSync } from 'node:fs';
import { it } from 'vitest';
import { SEASON_START, TICK_SECONDS } from '../firm.config';
import { Engine } from '../src/sim/engine';
import { toView } from '../src/sim/view';
import { Director } from '../src/scene/actors';
import { Renderer } from '../src/scene/renderer';
import { sceneData } from '../src/scene/data';
import { encodePng } from '../src/scene/png';

it('renders a live frame', () => {
  const e = new Engine({ seasonStart: SEASON_START, tickSeconds: TICK_SECONDS });
  const now = Date.parse('2026-09-28T15:00:00Z');
  e.advanceToTime(now);
  const state = toView(e.state, now);
  const byId = new Map([...state.traders, ...state.alumni, ...state.waiting].map((t) => [t.id, t]));
  const d = new Director();
  d.sync(state, byId, now, 0);
  const r = new Renderer();
  mkdirSync('art-out', { recursive: true });
  for (const [name, t, hot, replay] of [['frame', 3.3, 5, false], ['replay', 9, null, true]] as const) {
    if (replay) d.replay(state, 0);
    const actors = d.actors(state, t, false);
    const f = r.render(t, { ...sceneData(state), hotDesk: hot }, actors, d.doorBusy(t));
    writeFileSync(`art-out/${name}.png`, encodePng(f, 2));
  }
});

it('zoomed crop', async () => {
  const { PixelBuffer } = await import('../src/scene/buffer');
  const e = new Engine({ seasonStart: SEASON_START, tickSeconds: TICK_SECONDS });
  const now = Date.parse('2026-09-28T15:00:00Z');
  e.advanceToTime(now);
  const state = toView(e.state, now);
  const d = new Director();
  const r = new Renderer();
  const f = r.render(3.3, { ...sceneData(state), hotDesk: 5 }, d.actors(state, 3.3, false), false);
  const crop = (x0: number, y0: number, w: number, h: number) => {
    const b = new PixelBuffer(w, h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) b.data[y * w + x] = f.get(x0 + x, y0 + y);
    return b;
  };
  writeFileSync('art-out/zoom-desks.png', encodePng(crop(300, 560, 520, 330), 2));
});
