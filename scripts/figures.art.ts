import { mkdirSync, writeFileSync } from 'node:fs';
import { it } from 'vitest';
import { PixelBuffer } from '../src/scene/buffer';
import { encodePng } from '../src/scene/png';
import { renderBust, renderFigure, type Pose } from '../src/art/figure';
import { dress } from '../src/art/traits';
import { STARTING_ROSTER } from '../src/sim/names';
import { PARTNER_LOOK } from '../src/art/partner';
import type { Look } from '../src/sim/types';
import { blitAt } from '../src/art/props';

function paste(buf: PixelBuffer, img: { w: number; h: number; px: Uint32Array }, x0: number, y0: number) {
  blitAt(buf, img, x0 + img.w / 2, y0 + img.h);
}

export const rosterLooks = (): [string, Look, boolean][] => [
  ...STARTING_ROSTER.map(([name, arch], i): [string, Look, boolean] => [name, dress({ skin: [0, 4, 2, 0, 3, 5, 1, 0, 1, 2, 3][i], hair: [3, 0, 0, 3, 4, 0, 6, 1, 1, 2, 0][i], hairStyle: 0, suit: [0, 1, 2, 4, 5, 0, 1, 4, 3, 1, 2][i], tie: i % 6 }, arch, i * 7919 + 13, name), false]),
  ['barry', PARTNER_LOOK, true],
];

it('figure contact sheets', () => {
  mkdirSync('art-out', { recursive: true });
  const poses: [Pose, number][] = [['stand', 0], ['walk', 1], ['sit', 0], ['leanback', 0], ['phone', 1], ['point', 0], ['coffee', 0], ['celebrate', 1], ['slump', 0], ['box', 2], ['back', 2], ['stretch', 1], ['rub', 0], ['mobile', 0], ['eat', 0], ['tie', 0], ['chat', 1], ['hips', 0], ['arms', 0], ['watch', 0], ['drink', 0], ['putt', 1], ['call', 2]];
  const looks = rosterLooks();
  for (const scale of [1.5, 4]) {
    const cw = Math.ceil(42 * scale);
    const ch = Math.ceil(66 * scale);
    const list = scale > 2 ? looks.slice(0, 6) : looks;
    const buf = new PixelBuffer(poses.length * cw, list.length * ch);
    buf.rect(0, 0, buf.w, buf.h, 0xffeef4f6);
    list.forEach(([, l, g], j) => poses.forEach(([p, f], i) => {
      const img = renderFigure(l, p, f, { scale, glasses: g, ss: 3 });
      paste(buf, img, i * cw + (cw - img.w) / 2, j * ch + (ch - img.h));
    }));
    writeFileSync(`art-out/figures-${scale}x.png`, encodePng(buf, scale < 2 ? 2 : 1));
  }
  const busts = new PixelBuffer(looks.length * 110, 110);
  busts.rect(0, 0, busts.w, busts.h, 0xffeef4f6);
  looks.forEach(([, l, g], i) => paste(busts, renderBust(l, 100, g, 2), i * 110 + 5, 5));
  writeFileSync('art-out/busts.png', encodePng(busts, 1));
});
