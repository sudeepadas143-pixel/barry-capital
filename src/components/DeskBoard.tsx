import { Link } from 'react-router-dom';
import { DESK_COUNT } from '../../firm.config';
import { useFirm } from '../hooks/useFirm';
import { usePanel } from '../hooks/usePanel';
import { fmtPct, pad2, pctClass, until } from '../format';
import { PARTNER_NAME } from '../../firm.config';

interface Props {
  hot?: number | null;
  onHover?: (desk: number | null) => void;
}

export function DeskBoard({ hot, onHover }: Props) {
  const { state } = useFirm();
  const { open } = usePanel();
  const byDesk = new Map(state.traders.filter((t) => t.desk).map((t) => [t.desk!, t]));
  // Ranked by result, best first; empty desks at the bottom.
  const desks = Array.from({ length: DESK_COUNT }, (_, i) => i + 1).sort((a, b) => {
    const ta = byDesk.get(a);
    const tb = byDesk.get(b);
    if (!ta || !tb) return ta ? -1 : tb ? 1 : a - b;
    return tb.resultPct - ta.resultPct;
  });
  const mine = state.mine[0];

  return (
    <section aria-labelledby="desks-title">
      <div className="desks-head">
        <h2 id="desks-title" className="label" style={{ color: 'var(--ink)' }}>
          The leaderboard
        </h2>
        <span className="label" style={{ color: 'var(--ink)' }} aria-hidden="true">
          Since hire
        </span>
      </div>
      <ul className="desks">
        {desks.map((d) => {
          const t = byDesk.get(d);
          if (!t)
            return (
              <li key={d} className="desk">
                <div className="desk-btn">
                  <span className="desk-no">{pad2(d)}</span>
                  <span className="desk-name muted">empty</span>
                  <span className="desk-res zero">being cleared</span>
                </div>
              </li>
            );
          return (
            <li key={d} className="desk">
              <button
                type="button"
                className="desk-btn"
                data-hot={hot === d}
                onClick={() => open(t.id)}
                onMouseEnter={() => onHover?.(d)}
                onMouseLeave={() => onHover?.(null)}
                onFocus={() => onHover?.(d)}
                onBlur={() => onHover?.(null)}
                aria-label={`Desk ${d}, ${t.name}, ${fmtPct(t.resultPct)}${t.rank === 1 ? ', top of the board' : t.nextOut ? ', next out' : t.firstReviewTick !== undefined ? ', new' : ''}`}
              >
                <span className="desk-no">{pad2(d)}</span>
                <span className="desk-name">{t.name}</span>
                <span className={`desk-res num ${pctClass(t.resultPct)}`}>
                  {fmtPct(t.resultPct)}
                  {t.rank === 1 && <span className="chip chip-top">TOP</span>}
                  {t.nextOut && <span className="chip chip-out">NEXT OUT</span>}
                  {t.firstReviewTick !== undefined && <span className="chip">NEW</span>}
                </span>
              </button>
            </li>
          );
        })}
        <li className="desk desk-pencil">
          {mine ? (
            <button
              type="button"
              className="desk-btn"
              data-hot={hot === DESK_COUNT + 1}
              onClick={() => open(mine.id)}
              onMouseEnter={() => onHover?.(DESK_COUNT + 1)}
              onMouseLeave={() => onHover?.(null)}
              aria-label={`Desk ${DESK_COUNT + 1}, ${mine.name}, yours, ${fmtPct(mine.resultPct)}`}
            >
              <span className="desk-no">{pad2(DESK_COUNT + 1)}</span>
              <span className="desk-name">
                {mine.name} <span className="chip chip-yours">YOURS</span>
              </span>
              <span className={`desk-res num ${pctClass(mine.resultPct)}`}>{fmtPct(mine.resultPct)}</span>
            </button>
          ) : (
            <Link to="/hire" className="desk-btn" style={{ textDecoration: 'none' }}>
              <span className="desk-no">{pad2(DESK_COUNT + 1)}</span>
              <span className="desk-name">spare desk</span>
              <span className="desk-res">hire someone for it</span>
            </Link>
          )}
        </li>
      </ul>
      <ReviewNote />
    </section>
  );
}

/** The rule, in one line, with who it applies to right now. */
function ReviewNote() {
  const { state, now } = useFirm();
  const out = state.traders.find((t) => t.id === state.nextOutId);
  const top = state.traders.find((t) => t.id === state.topId);
  return (
    <p className="review-note" aria-live="polite">
      Every hour {PARTNER_NAME} lets the worst performer go and keeps the rest. New hires get three hours before
      their first review. Next review in{' '}
      <b className="num">{until(state.nextReviewAt - now)}</b>.
      {out && top && (
        <>
          {' '}
          Right now <b>{out.name}</b> would go ({fmtPct(out.resultPct)}) and <b>{top.name}</b> is top ({fmtPct(top.resultPct)}).
        </>
      )}
    </p>
  );
}
