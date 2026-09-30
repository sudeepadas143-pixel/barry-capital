import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { PARTNER_NAME } from '../../firm.config';
import { useFollows } from '../hooks/useLocal';
import { useFirm } from '../hooks/useFirm';
import { usePanel } from '../hooks/usePanel';
import { dayTime, fmtPct, fmtSol, pad2, pctClass } from '../format';
import { rulesFor } from '../sim/traders';
import { ARCHETYPES } from '../sim/archetypes';
import { Strikes, TradeRow } from './Books';
import { Headshot } from './Sprite';

export function TraderPanel() {
  const { openId, close } = usePanel();
  const { now, byId, msForTick } = useFirm();
  const t = openId ? byId.get(openId) : undefined;
  const ref = useRef<HTMLDivElement>(null);
  const lastFocus = useRef<HTMLElement | null>(null);
  const { isFollowing, toggle } = useFollows();

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
  const trades = t.recent.filter((x) => x.at <= now).slice(0, 5);
  const where = t.local
    ? 'desk 12, yours'
    : t.status === 'seated'
      ? `desk ${pad2(t.desk!)}`
      : t.status === 'waiting'
        ? 'waiting for a desk'
        : 'no longer here';

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
        <p className="panel-record muted">
          {t.trades} {t.trades === 1 ? 'trade' : 'trades'} · {t.wins} closed up · {t.losses} closed down
          {t.hiredTick >= 0 && !t.local && ` · hired ${dayTime(msForTick(t.hiredTick))}`}
          {t.leftTick !== undefined && ` · left ${dayTime(msForTick(t.leftTick))}`}
        </p>
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
        <details className="rules">
          <summary className="label">Standing rules</summary>
          <ol>
            {rulesFor(t.archetype).map((r) => (
              <li key={r.code}>
                <span className="mono">{r.code}</span> {r.text}
              </li>
            ))}
          </ol>
        </details>
        <div className="panel-actions">
          {t.local ? (
            <>
              <Link to="/hire" className="btn-black follow-btn" onClick={close}>
                employee file
              </Link>
              <span className="muted" style={{ fontSize: 14 }}>
                Only this browser can see {t.name}.
              </span>
            </>
          ) : (
            <>
              <button
                type="button"
                className="btn-black follow-btn"
                aria-pressed={isFollowing(t.id)}
                onClick={() => toggle(t)}
              >
                {isFollowing(t.id) ? 'following' : 'follow'}
              </button>
              <span className="muted" style={{ fontSize: 14 }}>
                {t.status === 'seated'
                  ? t.strikes
                    ? t.strikes === 1
                      ? `One strike. ${PARTNER_NAME} will be watching the next review.`
                      : `${t.strikes} strikes. One more and they’re out.`
                    : 'No strikes.'
                  : t.status === 'waiting'
                    ? 'In line for the next desk.'
                    : 'No longer with the firm.'}
              </span>
            </>
          )}
        </div>
      </div>
    </>
  );
}
