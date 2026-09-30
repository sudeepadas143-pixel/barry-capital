import { useState } from 'react';
import { Link } from 'react-router-dom';
import { DESK_COUNT, PARTNER_NAME } from '../../firm.config';
import { Standing } from '../components/Standing';
import { Headshot } from '../components/Sprite';
import { useFirm } from '../hooks/useFirm';
import { useFollows } from '../hooks/useLocal';
import { usePanel } from '../hooks/usePanel';
import { fmtPct, numWord, pad2, pctClass } from '../format';
import { ARCHETYPES } from '../sim/archetypes';
import { SIM } from '../sim/params';
import type { Trader } from '../sim/types';
import { ArrowRight } from '../components/Icons';

type Sort = 'result' | 'desk' | 'method';

function RosterList({ traders, lead }: { traders: Trader[]; lead: (t: Trader, i: number) => string }) {
  const { open } = usePanel();
  const { isFollowing } = useFollows();
  return (
    <ul className="roster">
      {traders.map((t, i) => (
        <li key={t.id}>
          <button type="button" onClick={() => open(t.id)}>
            <span className="desk-no">{lead(t, i)}</span>
            <span className="avatar" style={{ width: 44, height: 44 }}>
              <Headshot look={t.look} size={40} />
            </span>
            <span style={{ minWidth: 0 }}>
              <span className="roster-name">
                {t.name}
                {t.local && <span className="chip chip-yours" style={{ marginLeft: 8 }}>YOURS</span>}
                {isFollowing(t.id) && <span className="chip" style={{ marginLeft: 8 }}>FOLLOWED</span>}
              </span>
              <span className="roster-arch">
                {ARCHETYPES[t.archetype].title}
                {t.status === 'seated' && !t.local && (
                  <>
                    {' · '}
                    {t.trades} trades · <Standing t={t} />
                  </>
                )}
              </span>
            </span>
            <span className={`roster-res num ${pctClass(t.resultPct)}`}>{t.status === 'waiting' ? '' : fmtPct(t.resultPct)}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}

export default function Traders() {
  const { state } = useFirm();
  const [sort, setSort] = useState<Sort>('result');
  const seated = [...state.traders, ...state.mine];
  const sorted = [...seated].sort((a, b) =>
    sort === 'result' ? b.resultPct - a.resultPct : sort === 'desk' ? (a.desk ?? DESK_COUNT + 1) - (b.desk ?? DESK_COUNT + 1) : ARCHETYPES[a.archetype].title.localeCompare(ARCHETYPES[b.archetype].title),
  );
  return (
    <div className="wrap">
      <header className="page-head">
        <p className="label">The roster</p>
        <h1 className="hero-title">
          {numWord(DESK_COUNT)} desks.
          <em>one line.</em>
        </h1>
        <p className="prose">
          Every hour {PARTNER_NAME} reviews the desks. The trader with the worst result is let go and the next person in
          line takes the desk. Everyone else keeps their seat. New hires get {numWord(SIM.REVIEW_GRACE / 60)} hours before
          their first review.
        </p>
      </header>
      <section className="section" style={{ borderTop: 0, paddingTop: 0 }} aria-labelledby="seated-title">
        <div className="desks-head" style={{ borderBottom: 0, alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <h2 id="seated-title" className="label" style={{ color: 'var(--ink)' }}>
            Seated
          </h2>
          <div className="options" role="radiogroup" aria-label="Sort by">
            {(['result', 'desk', 'method'] as Sort[]).map((x) => (
              <button key={x} type="button" role="radio" aria-checked={sort === x} className="option option-sm" onClick={() => setSort(x)}>
                {x}
              </button>
            ))}
          </div>
        </div>
        <RosterList traders={sorted} lead={(t, i) => (sort === 'result' ? pad2(i + 1) : t.desk ? pad2(t.desk) : pad2(DESK_COUNT + 1))} />
      </section>
      <div className="two-col">
        <section className="section" aria-labelledby="line-title">
          <h2 id="line-title" className="label" style={{ marginBottom: 14 }}>
            Waiting for a desk
          </h2>
          <RosterList traders={state.waiting} lead={(_, i) => pad2(i + 1)} />
        </section>
        <section className="section" aria-labelledby="out-title">
          <h2 id="out-title" className="label" style={{ marginBottom: 14 }}>
            Let go
          </h2>
          {state.alumni.length ? (
            <RosterList traders={state.alumni} lead={() => '—'} />
          ) : (
            <p className="prose muted">Nobody yet.</p>
          )}
          <p style={{ marginTop: 24 }}>
            <Link to="/hire" className="textlink">
              hire a trader <ArrowRight />
            </Link>
          </p>
        </section>
      </div>
    </div>
  );
}
