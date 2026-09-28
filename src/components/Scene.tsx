import { useCallback, useEffect, useRef, useState } from 'react';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { useNavigate } from 'react-router-dom';
import { DESK_COUNT, FIRM_NAME, PARTNER_NAME } from '../../firm.config';
import { useFirm } from '../hooks/useFirm';
import { usePanel } from '../hooks/usePanel';
import { fmtPct, pad2 } from '../format';
import { Director, type Speech } from '../scene/actors';
import { loadCustomArt } from '../scene/artswap';
import { sceneData } from '../scene/data';
import { hitDesk, proceduralHotspots, type Hotspots } from '../scene/hotspots';
import { H, S, W } from '../scene/layout';
import { Renderer } from '../scene/renderer';

interface Props {
  hot?: number | null;
  onHover?: (desk: number | null) => void;
}

const FPS = 12;

interface Bubble extends Speech {
  id: string;
  /** Anchor, as a fraction of the frame. */
  x: number;
  y: number;
}

/** Trades and the partner get the floor first; everyone else fills in. */
const RANK: Record<Speech['tone'], number> = { partner: 0, win: 1, loss: 1, buy: 2, smug: 3 };

export function Scene({ hot = null, onHover }: Props) {
  const { state, byId, now } = useFirm();
  const { open } = usePanel();
  const navigate = useNavigate();
  const reduced = useReducedMotion();

  const wrap = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const renderer = useRef<Renderer | null>(null);
  const hotspots = useRef<Hotspots | null>(null);
  const director = useRef(new Director());
  const native = useRef<HTMLCanvasElement | null>(null);
  const [dims, setDims] = useState({ w: W, h: H });
  const [label, setLabel] = useState<{ text: string; x: number; y: number } | null>(null);
  const [ready, setReady] = useState(false);
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const lastBubbles = useRef({ at: 0, key: '' });

  // Latest values for the animation loop.
  const live = useRef({ state, byId, now, hot });
  live.current = { state, byId, now, hot };

  // Build the renderer once, with custom art if any exists.
  useEffect(() => {
    let cancelled = false;
    loadCustomArt().then(({ custom, hotspots: hs }) => {
      if (cancelled) return;
      renderer.current = new Renderer(custom);
      hotspots.current = hs ?? proceduralHotspots();
      const w = renderer.current.frame.w;
      const h = renderer.current.frame.h;
      const n = document.createElement('canvas');
      n.width = w;
      n.height = h;
      native.current = n;
      setDims({ w, h });
      setReady(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const draw = useCallback((t: number) => {
    const r = renderer.current;
    const c = canvas.current;
    const n = native.current;
    if (!r || !c || !n) return;
    const { state, byId, now, hot } = live.current;
    const d = director.current;
    d.sync(state, byId, now, t);
    const actors = d.actors(state, t, reduced);
    const frame = r.render(t, { ...sceneData(state), hotDesk: hot }, actors, !reduced && d.doorBusy(t));
    const nctx = n.getContext('2d')!;
    nctx.putImageData(frame.toImageData(), 0, 0);
    const ctx = c.getContext('2d')!;
    // Whole-number scales stay pixel-exact; anything else is resampled smoothly.
    const k = c.width / n.width;
    ctx.imageSmoothingEnabled = Math.abs(k - Math.round(k)) > 0.001;
    ctx.imageSmoothingQuality = 'high';
    ctx.clearRect(0, 0, c.width, c.height);
    ctx.drawImage(n, 0, 0, c.width, c.height);

    // Speech bubbles, throttled: they're DOM, so they stay sharp at any size.
    const lb = lastBubbles.current;
    if (t - lb.at < 0.25 && t >= lb.at) return;
    lb.at = t;
    const max = c.clientWidth < 560 ? 2 : 5;
    const next: Bubble[] = [];
    for (const a of actors) {
      const say = d.speech.get(a.id);
      if (!say) continue;
      const [sx, sy] = r.screenPoint(a);
      const lift = a.layer === 'seated' ? 31 : 36;
      next.push({ ...say, id: a.id, x: sx / n.width, y: (sy - lift * S) / n.height });
    }
    next.sort((a, b) => RANK[a.tone] - RANK[b.tone] || a.y - b.y);
    const shown = next.slice(0, max);
    const key = shown.map((b) => `${b.id}:${b.text}:${Math.round(b.x * 1000)}:${Math.round(b.y * 1000)}`).join('|');
    if (key !== lb.key) {
      lb.key = key;
      setBubbles(shown);
    }
  }, [reduced]);

  // Size the backing store to a whole multiple of the native resolution.
  useEffect(() => {
    const el = wrap.current;
    const c = canvas.current;
    if (!el || !c) return;
    const fit = () => {
      const cssW = el.clientWidth;
      const dpr = window.devicePixelRatio || 1;
      const ratio = (cssW * dpr) / dims.w;
      // Snap to a whole multiple when close; otherwise match the device pixels exactly.
      const k = ratio >= 1 && Math.abs(ratio - Math.round(ratio)) < 0.12 ? Math.round(ratio) : ratio;
      c.width = Math.round(dims.w * k);
      c.height = Math.round(dims.h * k);
      draw(performance.now() / 1000);
    };
    fit();
    const ro = new ResizeObserver(fit);
    ro.observe(el);
    window.addEventListener('resize', fit);
    return () => {
      ro.disconnect();
      window.removeEventListener('resize', fit);
    };
  }, [dims, draw, ready]);

  // The loop: ~12fps, paused when hidden or scrolled away; a single frame under reduced motion.
  useEffect(() => {
    if (!ready) return;
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
  }, [ready, reduced, draw]);

  // Under reduced motion, redraw when the data changes.
  useEffect(() => {
    if (reduced && ready) draw(0);
  }, [reduced, ready, draw, state.tick, hot]);

  const toNative = (e: React.PointerEvent | React.MouseEvent) => {
    const r = canvas.current!.getBoundingClientRect();
    return { x: ((e.clientX - r.left) * dims.w) / r.width, y: ((e.clientY - r.top) * dims.h) / r.height, cx: e.clientX - r.left, cy: e.clientY - r.top };
  };

  const describe = (desk: number) => {
    if (desk === DESK_COUNT + 1) {
      const m = state.mine[0];
      return m ? `${pad2(desk)} · ${m.name} · ${fmtPct(m.resultPct)}` : `${pad2(desk)} · pencilled in`;
    }
    const t = state.traders.find((x) => x.desk === desk);
    return t ? `${pad2(desk)} · ${t.name} · ${fmtPct(t.resultPct)}` : `${pad2(desk)} · being cleaned`;
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
        {bubbles.map((b) => (
          <span
            key={b.id}
            className={`scene-say scene-say--${b.tone}${b.x > 0.72 ? ' scene-say--left' : ''}`}
            style={{ left: `${b.x * 100}%`, top: `${b.y * 100}%` }}
            aria-hidden="true"
          >
            {b.text}
          </span>
        ))}
        {label && (
          <span className="scene-label" style={{ left: label.x, top: label.y }} aria-hidden="true">
            {label.text}
          </span>
        )}
      </div>
      <figcaption className="scene-caption">
        <button hidden={reduced} type="button" onClick={() => director.current.replay(state, performance.now() / 1000)}>
          replay arrival
        </button>
      </figcaption>
    </figure>
  );
}
