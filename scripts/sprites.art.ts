import { mkdirSync, writeFileSync } from 'node:fs';
import { expect, it } from 'vitest';
import { PixelBuffer } from '../src/scene/buffer';
import { encodePng } from '../src/scene/png';
import { poseGrid, sprite, type Pose } from '../src/scene/sprites';

it('sprite contact sheet', () => {
  const poses: [Pose, number][] = [['stand', 0], ['walk', 1], ['walk', 3], ['back', 0], ['back', 1], ['sit', 0], ['sit', 1], ['celebrate', 0], ['celebrate', 1], ['slump', 0], ['box', 1], ['backbox', 0]];
  for (const [p, f] of poses) for (let hs = 0; hs < 4; hs++) {
    const g = poseGrid(p, f, hs, hs === 3);
    for (const r of g) expect(r.length, `${p} ${f} ${hs}: "${r}"`).toBe(15);
  }
  const looks = Array.from({ length: 6 }, (_, i) => ({ skin: i, hair: (i * 3) % 7, hairStyle: i % 4, suit: (i * 5) % 6, tie: (i * 7) % 6 }));
  const buf = new PixelBuffer(poses.length * 18 + 4, looks.length * 30 + 4);
  buf.rect(0, 0, buf.w, buf.h, 0xffeef4f6);
  looks.forEach((l, j) =>
    poses.forEach(([p, f], i) => {
      const s = sprite(l, p, f, j === 0);
      const ox = 2 + i * 18;
      const oy = 2 + j * 30 + (27 - s.h);
      for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) if (s.px[y * s.w + x]) buf.set(ox + x, oy + y, s.px[y * s.w + x]);
    }),
  );
  mkdirSync('art-out', { recursive: true });
  writeFileSync('art-out/sprites.png', encodePng(buf, 4));
});
