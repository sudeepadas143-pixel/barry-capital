import { useEffect, useRef } from 'react';
import type { Look } from '../sim/types';
import { headshotGrid, HEAD_H, HEAD_W } from '../art/headshot';
import { paletteFor, type PaletteMap } from '../art/palette';

export function paintGrid(
  ctx: CanvasRenderingContext2D,
  grid: string[],
  pal: PaletteMap,
  ox = 0,
  oy = 0,
  flip = false,
) {
  const w = grid[0]?.length ?? 0;
  for (let y = 0; y < grid.length; y++) {
    const row = grid[y];
    for (let x = 0; x < row.length; x++) {
      const k = row[x];
      if (k === '.' || k === ' ') continue;
      const c = pal[k];
      if (!c) continue;
      ctx.fillStyle = c;
      ctx.fillRect(ox + (flip ? w - 1 - x : x), oy + y, 1, 1);
    }
  }
}

interface Props {
  look: Look;
  size?: number;
  glasses?: boolean;
  className?: string;
  label?: string;
}

/** A trader's headshot, drawn at 16x16 and upscaled with crisp pixels. */
export function Headshot({ look, size = 32, glasses, className, label }: Props) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const ctx = ref.current?.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, HEAD_W, HEAD_H);
    paintGrid(ctx, headshotGrid(look.hairStyle, glasses), paletteFor(look));
  }, [look.skin, look.hair, look.hairStyle, look.suit, look.tie, glasses]);
  return (
    <canvas
      ref={ref}
      width={HEAD_W}
      height={HEAD_H}
      className={`pixel ${className ?? ''}`}
      style={{ width: size, height: size }}
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    />
  );
}
