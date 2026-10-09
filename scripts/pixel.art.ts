import { mkdirSync, writeFileSync } from 'node:fs';
import { it } from 'vitest';
import { PixelBuffer, rgba } from '../src/scene/buffer';
import { encodePng } from '../src/scene/png';
import { PARTNER_LOOK } from '../src/art/partner';
import { traderFromWallet } from '../src/wallet';
import {
  ACCESSORIES, BACKGROUNDS, EXPRESSIONS, FACIAL_HAIR, GRID, HAIR_COLORS, HAIR_STYLES, HEADS, OUTFITS,
  portraitFromLook, renderPortrait, type Layer, type Portrait,
} from '../src/art/pixel';
import { SKINS } from '../src/art/palette';

const base: Portrait = {
  background: BACKGROUNDS[0].hex, head: 'round', skin: SKINS[1], expression: 'content', hair: 'part',
  hairColor: HAIR_COLORS[1].hex, facial: 'none', outfit: { ...OUTFITS[0] }, accessories: [],
};

function sheet(rows: Layer[][], name: string, gap = 2) {
  const cols = Math.max(...rows.map((r) => r.length));
  const W = cols * (GRID + gap) + gap, H = rows.length * (GRID + gap) + gap;
  const buf = new PixelBuffer(W, H);
  buf.data.fill(rgba('#f6f4ee'));
  rows.forEach((r, j) => r.forEach((l, i) => {
    for (let y = 0; y < GRID; y++) for (let x = 0; x < GRID; x++) buf.data[(gap + j * (GRID + gap) + y) * W + gap + i * (GRID + gap) + x] = l[y * GRID + x];
  }));
  writeFileSync(`art-out/${name}.png`, encodePng(buf, 8));
}

it('pixel portraits', () => {
  mkdirSync('art-out', { recursive: true });
  const traders = Array.from({ length: 10 }, (_, i) => portraitFromLook(traderFromWallet(`seed${i * 7 + 3}`).look));
  sheet([
    [renderPortrait(portraitFromLook(PARTNER_LOOK, true)), ...traders.map(renderPortrait)],
    HEADS.map((h, i) => renderPortrait({ ...base, head: h.id, skin: SKINS[i], hair: 'bald' })),
    EXPRESSIONS.map((e) => renderPortrait({ ...base, expression: e.id })),
    HAIR_STYLES.slice(0, 8).map((h, i) => renderPortrait({ ...base, hair: h.id, hairColor: HAIR_COLORS[i].hex })),
    HAIR_STYLES.slice(8).map((h, i) => renderPortrait({ ...base, hair: h.id, hairColor: HAIR_COLORS[(i + 3) % 8].hex, background: BACKGROUNDS[i].hex })),
    OUTFITS.map((o) => renderPortrait({ ...base, outfit: { ...o } })),
    [...FACIAL_HAIR.map((f) => renderPortrait({ ...base, facial: f.id, hair: 'crop' })), ...ACCESSORIES.slice(1, 6).map((a) => renderPortrait({ ...base, accessories: [{ id: a.id }] }))],
    ACCESSORIES.slice(6).map((a) => renderPortrait({ ...base, accessories: [{ id: a.id }], background: BACKGROUNDS[7].hex })),
  ], 'pixel-sheet');
});
