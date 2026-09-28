import { Link } from 'react-router-dom';
import { DESK_COUNT } from '../../firm.config';
import { useFirm } from '../hooks/useFirm';
import { usePanel } from '../hooks/usePanel';
import { fmtPct, pad2, pctClass } from '../format';

interface Props {
  hot?: number | null;
  onHover?: (desk: number | null) => void;
}

export function DeskBoard({ hot, onHover }: Props) {
  const { state } = useFirm();
  const { open } = usePanel();
  const byDesk = new Map(state.traders.filter((t) => t.desk).map((t) => [t.desk!, t]));
  const desks = Array.from({ length: DESK_COUNT }, (_, i) => i + 1);
  const mine = state.mine[0];

  return (
    <section aria-labelledby="desks-title">
      <div className="desks-head">
        <h2 id="desks-title" className="label" style={{ color: 'var(--ink)' }}>
          The traders’ desks
        </h2>
        <span className="label" style={{ color: 'var(--ink)' }} aria-hidden="true">
          Result
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
                  <span className="desk-name muted">vacant</span>
                  <span className="desk-res zero">being cleaned</span>
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
                aria-label={`Desk ${d}, ${t.name}, ${fmtPct(t.resultPct)}`}
              >
                <span className="desk-no">{pad2(d)}</span>
                <span className="desk-name">{t.name}</span>
                <span className={`desk-res num ${pctClass(t.resultPct)}`}>{fmtPct(t.resultPct)}</span>
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
              <span className="desk-name">pencilled in</span>
              <span className="desk-res">the next trader’s desk</span>
            </Link>
          )}
        </li>
      </ul>
    </section>
  );
}
