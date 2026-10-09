import { mkdirSync, writeFileSync } from 'node:fs';
import { it } from 'vitest';
import { PixelBuffer, rgba } from '../src/scene/buffer';
import { encodePng } from '../src/scene/png';
import { renderBust } from '../src/art/figure';
import { blitAt } from '../src/art/props';
import { PARTNER_LOOK } from '../src/art/partner';

it('steve profile pictures', () => {
  mkdirSync('art-out', { recursive: true });
  const size = 1000;
  const bust = renderBust(PARTNER_LOOK, 900, true, 3);
  for (const [name, bg] of [['paper', '#f6f4ee'], ['navy', '#1f2c45'], ['green', '#2f6b45']] as const) {
    const buf = new PixelBuffer(size, size);
    buf.rect(0, 0, size, size, rgba(bg));
    blitAt(buf, bust, size / 2, size + 20);
    writeFileSync(`art-out/steve-pfp-${name}.png`, encodePng(buf, 1));
  }
});
