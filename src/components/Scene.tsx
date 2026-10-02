import { useCallback, useEffect, useRef, useState } from 'react';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { useNavigate } from 'react-router-dom';
import { DESK_COUNT, FIRM_NAME, PARTNER_NAME } from '../../firm.config';
import { useFirm } from '../hooks/useFirm';
import { usePanel } from '../hooks/usePanel';
import { fmtPct, pad2 } from '../format';
import { Director } from '../scene/actors';
import { loadCustomArt } from '../scene/artswap';
import { sceneData } from '../scene/data';
import { hitDesk, proceduralHotspots, type Hotspots } from '../scene/hotspots';
import { H, W } from '../scene/layout';
import { CanvasBackend, Renderer, type CustomArt } from '../scene/renderer';
import { figureSrc } from '../scene/sprites';
import { spriteCanvas, type SpriteSrc } from '../scene/surface';
import { POSE_FRAMES, SEATED_POSES, type Pose } from '../art/figure';
import { PARTNER_LOOK } from '../art/partner';
import type { FirmState } from '../sim/types';

interface Props {
  hot?: number | null;
  onHover?: (desk: number | null) => void;
}

const FPS = 15;
/** Upper bound on device pixels per scene pixel, to keep memory sane on big screens. */
const MAX_K = 2;

/** Wait for the faces the building uses for its signs and tickers. */
async function fontsReady() {
  if (typeof document === 'undefined' || !document.fonts) return;
  try {
    await Promise.all([
      document.fonts.load("500 20px 'EB Garamond'"),
      document.fonts.load("600 20px 'Inter Tight'"),
      document.fonts.load("600 20px 'JetBrains Mono'"),
    ]);
  } catch {
    /* draw with fallbacks */
  }
}

/** Render everyone's likely poses in idle time, so new poses don't stutter the first time. */
function prewarm(state: FirmState, k: number): () => void {
  const jobs: SpriteSrc[] = [];
  const desk: Pose[] = [...SEATED_POSES, 'hips', 'arms', 'point', 'celebrate', 'walk', 'back'];
  for (const tr of [...state.traders.filter((x) => x.desk), ...state.mine.slice(0, 1)])
    for (const p of desk) for (let f = 0; f < POSE_FRAMES[p]; f++) jobs.push(figureSrc(tr.look, p, f));
  const boss: Pose[] = ['walk', 'back', 'stand', 'arms', 'hips', 'watch', 'drink', 'putt', 'call', 'point'];
  for (const p of boss) for (let f = 0; f < POSE_FRAMES[p]; f++) jobs.push(figureSrc(PARTNER_LOOK, p, f, true));
  let stop = false;
  let handle = 0;
  const hasIdle = typeof window.requestIdleCallback === 'function';
  const idle = (fn: () => void) => (hasIdle ? window.requestIdleCallback(fn, { timeout: 500 }) : setTimeout(fn, 16) as unknown as number);
  const step = () => {
    if (stop) return;
    const t0 = performance.now();
    while (jobs.length && performance.now() - t0 < 10) spriteCanvas(jobs.shift()!, k);
    if (jobs.length) handle = idle(step);
  };
  handle = idle(step);
  return () => {
    stop = true;
    if (hasIdle) window.cancelIdleCallback(handle);
    else clearTimeout(handle);
  };
}

export function Scene({ hot = null, onHover }: Props) {
  const { state, byId, now } = useFirm();
  const { open } = usePanel();
  const navigate = useNavigate();
  const reduced = useReducedMotion();

  const wrap = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const renderer = useRef<Renderer | null>(null);
  const custom = useRef<CustomArt | undefined>(undefined);
  const hotspots = useRef<Hotspots | null>(null);
  const director = useRef(new Director());
  const [dims, setDims] = useState({ w: W, h: H });
  const [label, setLabel] = useState<{ text: string; x: number; y: number } | null>(null);
  const [ready, setReady] = useState(false);
  const [k, setK] = useState(0);

  // Latest values for the animation loop.
  const live = useRef({ state, byId, now, hot });
  live.current = { state, byId, now, hot };

  // Load custom art (if any) and fonts once.
  useEffect(() => {
    let cancelled = false;
    Promise.all([loadCustomArt(), fontsReady()]).then(([{ custom: c, hotspots: hs }]) => {
      if (cancelled) return;
      custom.current = c;
      hotspots.current = hs ?? proceduralHotspots();
      setDims({ w: c?.bg.w ?? W, h: c?.bg.h ?? H });
      setReady(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const draw = useCallback(
    (t: number) => {
      const r = renderer.current;
      if (!r) return;
      const { state, byId, now, hot } = live.current;
      const d = director.current;
      d.sync(state, byId, now, t);
      const actors = d.actors(state, t, reduced);
      const t0 = performance.now();
      r.render(t, { ...sceneData(state), hotDesk: hot }, actors, !reduced && d.doorBusy(t));
      if (canvas.current) canvas.current.dataset.frameMs = (performance.now() - t0).toFixed(1);
    },
    [reduced],
  );

  // Match the backing store to the device's pixels; redraw the static layers when that changes.
  useEffect(() => {
    const el = wrap.current;
    if (!el || !ready) return;
    let timer = 0;
    const fit = () => {
      const dpr = window.devicePixelRatio || 1;
      const next = Math.min(MAX_K, Math.max(0.5, (el.clientWidth * dpr) / dims.w));
      setK((prev) => (prev && Math.abs(next - prev) / prev < 0.02 ? prev : next));
    };
    fit();
    const ro = new ResizeObserver(() => {
      window.clearTimeout(timer);
      timer = window.setTimeout(fit, 120);
    });
    ro.observe(el);
    return () => {
      ro.disconnect();
      window.clearTimeout(timer);
    };
  }, [dims, ready]);

  useEffect(() => {
    const c = canvas.current;
    if (!c || !ready || !k) return;
    c.width = Math.round(dims.w * k);
    c.height = Math.round(dims.h * k);
    const t0 = performance.now();
    renderer.current = new Renderer(new CanvasBackend(c, k, dims.w, dims.h), custom.current);
    c.dataset.buildMs = (performance.now() - t0).toFixed(0);
    draw(reduced ? 0 : performance.now() / 1000);
    return reduced ? undefined : prewarm(live.current.state, k);
  }, [k, ready, dims, draw, reduced]);

  // The loop: paused when hidden or scrolled away; a single frame under reduced motion.
  useEffect(() => {
    if (!ready || !k) return;
    if (reduced) {
      draw(0);
      return;
    }
    let raf = 0;
    let last = 0;
    let visible = true;
    const tick = (ms: number) => {
      raf = requestAnimationFrame(tick);
      if (!visible || document.hidden) return;
      if (ms - last < 1000 / FPS) return;
      last = ms;
      draw(ms / 1000);
    };
    raf = requestAnimationFrame(tick);
    const io = new IntersectionObserver((e) => (visible = e[0]?.isIntersecting ?? true));
    if (wrap.current) io.observe(wrap.current);
    return () => {
      cancelAnimationFrame(raf);
      io.disconnect();
    };
  }, [ready, k, reduced, draw]);

  // Under reduced motion, redraw when the data changes.
  useEffect(() => {
    if (reduced && ready && k) draw(0);
  }, [reduced, ready, k, draw, state.tick, hot]);

  const toNative = (e: React.PointerEvent | React.MouseEvent) => {
    const r = canvas.current!.getBoundingClientRect();
    return { x: ((e.clientX - r.left) * dims.w) / r.width, y: ((e.clientY - r.top) * dims.h) / r.height, cx: e.clientX - r.left, cy: e.clientY - r.top };
  };

  const describe = (desk: number) => {
    if (desk === DESK_COUNT + 1) {
      const m = state.mine[0];
      return m ? `${pad2(desk)} · ${m.name} · ${fmtPct(m.resultPct)}` : `${pad2(desk)} · spare desk`;
    }
    const t = state.traders.find((x) => x.desk === desk);
    return t ? `${pad2(desk)} · ${t.name} · ${fmtPct(t.resultPct)}` : `${pad2(desk)} · empty for now`;
  };

  const onMove = (e: React.PointerEvent) => {
    if (!hotspots.current || e.pointerType === 'touch') return;
    const p = toNative(e);
    const d = hitDesk(hotspots.current, p.x, p.y);
    if (d !== hot) onHover?.(d);
    setLabel(d ? { text: describe(d), x: p.cx, y: p.cy } : null);
  };

  const onClick = (e: React.MouseEvent) => {
    if (!hotspots.current) return;
    const p = toNative(e);
    const d = hitDesk(hotspots.current, p.x, p.y);
    if (d === null) return;
    if (d === DESK_COUNT + 1) {
      const m = state.mine[0];
      if (m) open(m.id);
      else navigate('/hire');
      return;
    }
    const t = state.traders.find((x) => x.desk === d);
    if (t) open(t.id);
  };

  return (
    <figure className="scene">
      <div ref={wrap} className="scene-frame" style={{ aspectRatio: `${dims.w} / ${dims.h}` }}>
        <canvas
          ref={canvas}
          className="scene-canvas"
          style={{ cursor: hot ? 'pointer' : 'default' }}
          role="img"
          aria-label={`Cutaway of the ${FIRM_NAME} building: a server room, the lobby, four floors of trading desks and ${PARTNER_NAME}'s office at the top. Traders can be opened from the desk list below.`}
          onPointerMove={onMove}
          onPointerLeave={() => {
            onHover?.(null);
            setLabel(null);
          }}
          onClick={onClick}
        />
        {label && (
          <span className="scene-label" style={{ left: label.x, top: label.y }} aria-hidden="true">
            {label.text}
          </span>
        )}
      </div>
      <figcaption className="scene-caption">
        <button hidden={reduced} type="button" className="replay" onClick={() => director.current.replay(state, performance.now() / 1000)}>
          <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M13.5 8a5.5 5.5 0 1 1-1.7-4M13.5 2v3.2h-3.2" />
          </svg>
          replay the opening bell
        </button>
      </figcaption>
    </figure>
  );
}
