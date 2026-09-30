import { expect, it } from 'vitest';
import { poseGrid, type Pose } from '../src/scene/sprites';

it('hand-drawn sprite grids stay 15 wide', () => {
  const poses: [Pose, number][] = [['stand', 0], ['walk', 1], ['walk', 3], ['back', 0], ['back', 1], ['sit', 0], ['sit', 1], ['celebrate', 0], ['celebrate', 1], ['slump', 0], ['box', 1], ['backbox', 0]];
  for (const [p, f] of poses)
    for (let hs = 0; hs < 4; hs++) {
      const g = poseGrid(p, f, hs, hs === 3);
      for (const r of g) expect(r.length, `${p} ${f} ${hs}: "${r}"`).toBe(15);
    }
});
