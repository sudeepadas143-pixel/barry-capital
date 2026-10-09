import { mkdirSync, writeFileSync } from 'node:fs';
import { it } from 'vitest';
import { PixelBuffer } from '../src/scene/buffer';
import { encodePng } from '../src/scene/png';
import { PARTNER_LOOK } from '../src/art/partner';
import { GRID, portraitFromLook, renderPortrait } from '../src/art/pixel';

/** Steve's profile picture, 1024×1024, on a few backgrounds. */
it('steve profile pictures', () => {
  mkdirSync('art-out', { recursive: true });
  for (const [name, bg] of [['brass', '#e2c27c'], ['paper', '#ece5d3'], ['ledger', '#b6caae'], ['night', '#2b3245']] as const) {
    const buf = new PixelBuffer(GRID, GRID);
    buf.data.set(renderPortrait({ ...portraitFromLook(PARTNER_LOOK, true), background: bg }));
    writeFileSync(`art-out/steve-pfp-${name}.png`, encodePng(buf, 32));
  }
});
