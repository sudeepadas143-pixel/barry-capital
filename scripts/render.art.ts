import { mkdirSync, writeFileSync } from 'node:fs';
import { it } from 'vitest';
import { PixelBuffer } from '../src/scene/buffer';
import { buildPixelScene } from '../src/scene/building';
import { encodePng } from '../src/scene/png';

it('renders the building', () => {
  const s = buildPixelScene();
  const out = new PixelBuffer(s.bg.w, s.bg.h);
  out.over(s.bg);
  out.over(s.fg);
  out.over(s.front);
  mkdirSync('art-out', { recursive: true });
  writeFileSync('art-out/building.png', encodePng(out, 2));
  writeFileSync('art-out/building-1x.png', encodePng(out, 1));
});
