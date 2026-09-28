import { useEffect, useRef, useState } from 'react';
import { useFirm } from '../hooks/useFirm';
import { usePanel } from '../hooks/usePanel';
import { fmtPct, fmtSol, pad2, pctClass } from '../format';
import { ARCHETYPES } from '../sim/archetypes';
import { Strikes, TradeRow } from './Books';
import { Headshot } from './Sprite';

export function TraderPanel() {
  const { openId, close } = usePanel();
  const { state, now, byId } = useFirm();
  const t = openId ? byId.get(openId) : undefined;
  const ref = useRef<HTMLDivElement>(null);
  const lastFocus = useRef<HTMLElement | null>(null);
  const [following, setFollowing] = useState(false);

  useEffect(() => {
    if (!t) return;
    lastFocus.current = document.activeElement as HTMLElement;
    ref.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close();
      if (e.key === 'Tab' && ref.current) {
        const f = ref.current.querySelectorAll<HTMLElement>('button, a[href]');
        if (!f.length) return;
        const first = f[0];
        const last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
      lastFocus.current?.focus?.();
    };
  }, [t?.id, close]);

  if (!t) return null;
  const a = ARCHETYPES[t.archetype];
  const trades = state.feed.filter((x) => x.traderId === t.id).slice(0, 5);
  const where =
    t.status === 'seated' ? `desk ${pad2(t.desk!)}` : t.status === 'waiting' ? 'waiting for a desk' : 'escorted out';

  return (
    <>
      <div className="scrim" onClick={close} aria-hidden="true" />
      <div
        ref={ref}
        className="panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="panel-name"
        tabIndex={-1}
      >
        <div className="panel-grab" aria-hidden="true" />
        <div className="panel-top">
          <p className="label">Employee file · {where}</p>
          <button type="button" className="panel-close" onClick={close}>
            close
          </button>
        </div>
        <div className="panel-id">
          <div className="portrait">
            <Headshot look={t.look} size={84} label={`Headshot of ${t.name}`} />
          </div>
          <div>
            <h2 id="panel-name" className="panel-name">
              {t.name}
            </h2>
            <p className="panel-arch">{a.title}</p>
          </div>
        </div>
        <p className="prose" style={{ fontSize: 18 }}>
          {a.blurb}
        </p>
        <div className="stats">
          <div className="stat">
            <p className="label">Result</p>
            <div className={`stat-val num ${pctClass(t.resultPct)}`}>{fmtPct(t.resultPct)}</div>
          </div>
          <div className="stat">
            <p className="label">Book</p>
            <div className="stat-val num">
              {fmtSol(t.bookSol, 2)}
              <small>SOL</small>
            </div>
          </div>
          <div className="stat">
            <p className="label">Strikes</p>
            <div className="stat-val">
              <Strikes n={t.strikes} />
            </div>
          </div>
        </div>
        <h3 className="label">Last five trades</h3>
        {trades.length ? (
          <ul className="feed">
            {trades.map((x) => (
              <TradeRow key={x.id} trade={x} trader={t} now={now} />
            ))}
          </ul>
        ) : (
          <p className="prose muted" style={{ fontSize: 17, marginTop: 10 }}>
            Nothing on the books yet.
          </p>
        )}
        <div className="panel-actions">
          <button
            type="button"
            className="btn-black follow-btn"
            aria-pressed={following}
            onClick={() => setFollowing((f) => !f)}
          >
            {following ? 'following' : 'follow'}
          </button>
        </div>
      </div>
    </>
  );
}
