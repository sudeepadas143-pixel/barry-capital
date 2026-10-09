import { useEffect, useRef, useState } from 'react';
import type { Look } from '../sim/types';
import { lookKey, renderFigure, type Pose, type SpriteImage } from '../art/figure';
import { GRID, portraitFromLook, renderPortrait, type Layer } from '../art/pixel';

const portraitCache = new Map<string, Layer>();

function dpr() {
  return typeof window === 'undefined' ? 2 : Math.min(3, Math.max(1, window.devicePixelRatio || 1));
}

function paint(c: HTMLCanvasElement | null, img: SpriteImage) {
  const ctx = c?.getContext('2d');
  if (!c || !ctx) return;
  const data = ctx.createImageData(img.w, img.h);
  new Uint32Array(data.data.buffer).set(img.px);
  ctx.clearRect(0, 0, c.width, c.height);
  ctx.putImageData(data, 0, 0);
}

interface Props {
  look: Look;
  size?: number;
  glasses?: boolean;
  className?: string;
  label?: string;
}

/** A trader's pixel portrait. `glasses` marks Steve. */
export function Headshot({ look, size = 32, glasses, className, label }: Props) {
  const ref = useRef<HTMLCanvasElement>(null);
  const key = `${lookKey(look)}|${glasses ? 1 : 0}`;
  let px = portraitCache.get(key);
  if (!px) {
    px = renderPortrait(portraitFromLook(look, !!glasses));
    if (portraitCache.size > 300) portraitCache.clear();
    portraitCache.set(key, px);
  }
  useEffect(() => paint(ref.current, { w: GRID, h: GRID, px: px! }), [px]);
  return (
    <canvas
      ref={ref}
      width={GRID}
      height={GRID}
      className={`figure pixel ${className ?? ''}`}
      style={{ width: size, height: size }}
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    />
  );
}

const figCache = new Map<string, SpriteImage>();

/** A full-length figure. `height` is in CSS pixels. With `animate`, it walks on the spot. */
export function Figure({
  look,
  pose = 'stand',
  height = 140,
  glasses,
  label,
  animate = false,
}: {
  look: Look;
  pose?: Pose;
  height?: number;
  glasses?: boolean;
  label?: string;
  animate?: boolean;
}) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [frame, setFrame] = useState(0);
  useEffect(() => {
    if (!animate) {
      setFrame(0);
      return;
    }
    const id = window.setInterval(() => setFrame((f) => (f + 1) % 8), 110);
    return () => window.clearInterval(id);
  }, [animate]);
  const d = dpr();
  const scale = (height * d) / 60;
  const key = `${lookKey(look)}|${pose}|${frame}|${Math.round(scale * 100)}|${glasses ? 1 : 0}`;
  let img = figCache.get(key);
  if (!img) {
    img = renderFigure(look, pose, frame, { scale, glasses, ss: 2 });
    if (figCache.size > 120) figCache.clear();
    figCache.set(key, img);
  }
  useEffect(() => paint(ref.current, img!), [img]);
  return (
    <canvas
      ref={ref}
      width={img.w}
      height={img.h}
      className="figure"
      style={{ width: img.w / d, height: img.h / d }}
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    />
  );
}
