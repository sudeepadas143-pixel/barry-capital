import { mkdirSync, writeFileSync } from 'node:fs';
import { it } from 'vitest';
import { PixelBuffer } from '../src/scene/buffer';
import { encodePng } from '../src/scene/png';
import { renderBust, renderFigure, type Pose } from '../src/art/figure';

function paste(buf: PixelBuffer, img: { w: number; h: number; px: Uint32Array }, x0: number, y0: number) {
  for (let y = 0; y < img.h; y++) for (let x = 0; x < img.w; x++) if (img.px[y * img.w + x]) buf.set(x0 + x, y0 + y, img.px[y * img.w + x]);
}

it('figure contact sheets', () => {
  mkdirSync('art-out', { recursive: true });
  const poses: [Pose, number][] = [['stand', 0], ['walk', 1], ['walk', 3], ['walk', 5], ['back', 2], ['sit', 0], ['sit', 1], ['celebrate', 0], ['celebrate', 1], ['slump', 0], ['box', 2], ['backbox', 0]];
  const looks = Array.from({ length: 6 }, (_, i) => ({ skin: i, hair: (i * 3) % 7, hairStyle: i % 4, suit: (i * 5) % 6, tie: (i * 7) % 6 }));
  for (const scale of [1, 3]) {
    const cw = Math.ceil(32 * scale) + 4;
    const ch = Math.ceil(60 * scale) + 4;
    const buf = new PixelBuffer(poses.length * cw, looks.length * ch);
    buf.rect(0, 0, buf.w, buf.h, 0xffeef4f6);
    looks.forEach((l, j) => poses.forEach(([p, f], i) => {
      const img = renderFigure(l, p, f, { scale, glasses: j === 4 });
      paste(buf, img, i * cw + (cw - img.w) / 2, j * ch + (ch - img.h));
    }));
    writeFileSync(`art-out/figures-${scale}x.png`, encodePng(buf, scale === 1 ? 4 : 1));
  }
  const busts = new PixelBuffer(6 * 100, 100);
  busts.rect(0, 0, busts.w, busts.h, 0xffeef4f6);
  looks.forEach((l, i) => paste(busts, renderBust(l, 90, i === 4), i * 100 + 5, 5));
  writeFileSync('art-out/busts.png', encodePng(busts, 1));
});
