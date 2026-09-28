import { useEffect, useRef } from 'react';
import type { Look } from '../sim/types';
import { headshotGrid, HEAD_H, HEAD_W } from '../art/headshot';
import { paletteFor, type PaletteMap } from '../art/palette';
import { sprite, type Pose } from '../scene/sprites';

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

/** A full-body sprite, drawn at native size and scaled up with crisp pixels. */
export function Figure({
  look,
  pose = 'stand',
  frame = 0,
  scale = 4,
  glasses,
  label,
}: {
  look: Look;
  pose?: Pose;
  frame?: number;
  scale?: number;
  glasses?: boolean;
  label?: string;
}) {
  const ref = useRef<HTMLCanvasElement>(null);
  const img = sprite(look, pose, frame, glasses);
  useEffect(() => {
    const c = ref.current;
    const ctx = c?.getContext('2d');
    if (!c || !ctx) return;
    const data = ctx.createImageData(img.w, img.h);
    new Uint32Array(data.data.buffer).set(img.px);
    ctx.clearRect(0, 0, c.width, c.height);
    ctx.putImageData(data, 0, 0);
  }, [img]);
  return (
    <canvas
      ref={ref}
      width={img.w}
      height={img.h}
      className="pixel"
      style={{ width: img.w * scale, height: img.h * scale }}
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    />
  );
}
