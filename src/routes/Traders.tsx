import { Link } from 'react-router-dom';
import { DESK_COUNT, PARTNER_NAME } from '../../firm.config';
import { Headshot } from '../components/Sprite';
import { useFirm } from '../hooks/useFirm';
import { usePanel } from '../hooks/usePanel';
import { fmtPct, numWord, pad2, pctClass } from '../format';
import { ARCHETYPES } from '../sim/archetypes';
import type { Trader } from '../sim/types';

function RosterList({ traders, numbered = true }: { traders: Trader[]; numbered?: boolean }) {
  const { open } = usePanel();
  return (
    <ul className="roster">
      {traders.map((t, i) => (
        <li key={t.id}>
          <button type="button" onClick={() => open(t.id)}>
            <span className="desk-no">{numbered && t.desk ? pad2(t.desk) : pad2(i + 1)}</span>
            <span className="avatar" style={{ width: 44, height: 44 }}>
              <Headshot look={t.look} size={40} />
            </span>
            <span>
              <span className="roster-name">{t.name}</span>
              <span className="roster-arch">{ARCHETYPES[t.archetype].title}</span>
            </span>
            <span className={`roster-res num ${pctClass(t.resultPct)}`}>
              {t.status === 'waiting' ? '' : fmtPct(t.resultPct)}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

export default function Traders() {
  const { state } = useFirm();
  const ranked = [...state.traders].sort((a, b) => b.resultPct - a.resultPct);
  return (
    <div className="wrap">
      <header className="page-head">
        <p className="label">The roster</p>
        <h1 className="hero-title">
          {numWord(DESK_COUNT)} desks.
          <em>one line.</em>
        </h1>
        <p className="prose">
          Ranked by season result. {PARTNER_NAME} reviews the bottom of this list every hour. Three strikes and a
          trader leaves with a box.
        </p>
      </header>
      <section className="section" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="desks-head" style={{ borderBottom: 0 }}>
          <h2 className="label" style={{ color: 'var(--ink)' }}>
            Seated
          </h2>
          <span className="label" style={{ color: 'var(--ink)' }} aria-hidden="true">
            Result
          </span>
        </div>
        <RosterList traders={ranked} />
      </section>
      <div className="two-col">
        <section className="section">
          <h2 className="label" style={{ marginBottom: 14 }}>
            Waiting for a desk
          </h2>
          <RosterList traders={state.waiting} numbered={false} />
        </section>
        <section className="section">
          <h2 className="label" style={{ marginBottom: 14 }}>
            Escorted out
          </h2>
          {state.alumni.length ? (
            <RosterList traders={state.alumni} numbered={false} />
          ) : (
            <p className="prose muted">Nobody yet. The box is still flat.</p>
          )}
          <p style={{ marginTop: 24 }}>
            <Link to="/hire" className="textlink">
              hire a trader <span aria-hidden="true">→</span>
            </Link>
          </p>
        </section>
      </div>
    </div>
  );
}
