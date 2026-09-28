/**
 * Optional hand-drawn art. If /public/art/building.png and /public/art/hotspots.json
 * exist at build time they replace the procedural building; if
 * /public/art/sprites/sprites.json exists its sheets replace the procedural
 * sprites. See ART_GUIDE.md for sizes, key colours and the JSON schemas.
 */
import art from 'virtual:art';
import { PixelBuffer } from './buffer';
import type { Hotspots } from './hotspots';
import type { CustomArt } from './renderer';
import { setSpriteOverrides, type Pose } from './sprites';

/** Exact RGB key colours used in custom sprite sheets, mapped to palette slots. */
export const SPRITE_KEYS: Record<string, string> = {
  '#000000': 'o',
  '#ff0000': 's',
  '#aa0000': 'S',
  '#00ff00': 'h',
  '#aaffaa': 'H',
  '#0000ff': 'u',
  '#0000aa': 'U',
  '#6666ff': 'v',
  '#000055': 'p',
  '#ffffff': 'w',
  '#cccccc': 'W',
  '#ffff00': 't',
  '#aaaa00': 'T',
  '#333333': 'k',
  '#ff66ff': 'm',
  '#555555': 'b',
  '#ffaa00': 'g',
  '#aa5500': 'x',
  '#773300': 'X',
  '#ffddaa': 'n',
};

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((res, rej) => {
    const img = new Image();
    img.onload = () => res(img);
    img.onerror = rej;
    img.src = src;
  });
}

function toBuffer(img: HTMLImageElement): PixelBuffer {
  const c = document.createElement('canvas');
  c.width = img.naturalWidth;
  c.height = img.naturalHeight;
  const ctx = c.getContext('2d')!;
  ctx.drawImage(img, 0, 0);
  const d = ctx.getImageData(0, 0, c.width, c.height);
  const buf = new PixelBuffer(c.width, c.height);
  const src = new Uint32Array(d.data.buffer);
  // Treat anything under half alpha as transparent; keep the rest opaque.
  for (let i = 0; i < src.length; i++) buf.data[i] = src[i] >>> 24 >= 128 ? src[i] | 0xff000000 : 0;
  return buf;
}

async function loadSprites(): Promise<void> {
  const res = await fetch('/art/sprites/sprites.json');
  if (!res.ok) return;
  const m = (await res.json()) as { frameWidth: number; frameHeight: number; poses: Record<string, { src: string; frames: number }> };
  const keyOf = new Map<number, string>();
  for (const [hex, k] of Object.entries(SPRITE_KEYS)) keyOf.set(parseInt(hex.slice(1), 16), k);
  const out = new Map<Pose, string[][]>();
  for (const [pose, spec] of Object.entries(m.poses)) {
    const img = await loadImage(`/art/sprites/${spec.src}`);
    const buf = toBuffer(img);
    const frames: string[][] = [];
    for (let f = 0; f < spec.frames; f++) {
      const rows: string[] = [];
      for (let y = 0; y < m.frameHeight; y++) {
        let r = '';
        for (let x = 0; x < m.frameWidth; x++) {
          const c = buf.get(f * m.frameWidth + x, y);
          if (!c) {
            r += '.';
            continue;
          }
          const rgb = ((c & 255) << 16) | (((c >>> 8) & 255) << 8) | ((c >>> 16) & 255);
          r += keyOf.get(rgb) ?? '.';
        }
        rows.push(r);
      }
      frames.push(rows);
    }
    out.set(pose as Pose, frames);
  }
  setSpriteOverrides(out);
}

export interface LoadedArt {
  custom?: CustomArt;
  hotspots?: Hotspots;
}

export async function loadCustomArt(): Promise<LoadedArt> {
  const out: LoadedArt = {};
  try {
    if (art.sprites) await loadSprites();
  } catch {
    /* fall back to procedural sprites */
  }
  if (!art.building || !art.hotspots) return out;
  try {
    const [img, hs] = await Promise.all([loadImage('/art/building.png'), fetch('/art/hotspots.json').then((r) => r.json() as Promise<Hotspots>)]);
    const bg = toBuffer(img);
    const fg = art.foreground ? toBuffer(await loadImage('/art/foreground.png')) : undefined;
    out.hotspots = { ...hs, width: bg.w, height: bg.h };
    out.custom = {
      bg,
      fg,
      seats: new Map(hs.desks.map((d) => [d.desk, d.seat])),
      partner: hs.partner,
    };
  } catch {
    return {};
  }
  return out;
}
