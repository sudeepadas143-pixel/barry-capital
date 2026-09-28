import { mkdirSync, writeFileSync } from 'node:fs';
import { it } from 'vitest';
import { proceduralHotspots } from '../src/scene/hotspots';
import { PixelBuffer } from '../src/scene/buffer';
import { buildScene } from '../src/scene/building';
import { encodePng } from '../src/scene/png';

it('writes the example hotspots and a reference render for artists', () => {
  mkdirSync('docs', { recursive: true });
  writeFileSync('docs/hotspots.example.json', JSON.stringify(proceduralHotspots(), null, 2) + '\n');
  const s = buildScene();
  const out = new PixelBuffer(s.bg.w, s.bg.h);
  out.over(s.bg);
  out.over(s.fg);
  out.over(s.front);
  writeFileSync('docs/building.reference.png', encodePng(out, 1, 0));
  const bgOnly = new PixelBuffer(s.bg.w, s.bg.h);
  bgOnly.over(s.bg);
  bgOnly.over(s.front);
  writeFileSync('docs/building.no-desks.png', encodePng(bgOnly, 1, 0));
  const fgOnly = new PixelBuffer(s.bg.w, s.bg.h);
  fgOnly.over(s.fg);
  writeFileSync('docs/foreground.reference.png', encodePng(fgOnly, 1, 0));
});
