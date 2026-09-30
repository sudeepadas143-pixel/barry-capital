import { Link } from 'react-router-dom';
import { DESK_COUNT } from '../../firm.config';
import { CORNER, SINCE } from '../copy';
import { useFirm } from '../hooks/useFirm';
import { useFollows, useVisit, type VisitSnap } from '../hooks/useLocal';
import { usePanel } from '../hooks/usePanel';
import { agoWords, fmtPct, fmtSignedSol, pad2, pctClass } from '../format';
import { ARCHETYPES } from '../sim/archetypes';
import type { Trader } from '../sim/types';
import { Headshot } from './Sprite';

function MiniRow({ t, sub, onClick }: { t: Trader; sub: React.ReactNode; onClick: () => void }) {
  return (
    <li>
      <button type="button" className="mini" onClick={onClick}>
        <span className="avatar">
          <Headshot look={t.look} size={30} />
        </span>
        <span className="mini-main">
          <span className="mini-name">{t.name}</span>
          <span className="mini-sub">{sub}</span>
        </span>
        <span className={`mini-res num ${pctClass(t.resultPct)}`}>{fmtPct(t.resultPct)}</span>
      </button>
    </li>
  );
}

export function YourCorner() {
  const { state, byId } = useFirm();
  const { open } = usePanel();
  const { list } = useFollows();
  const mine = state.mine[0];
  const followed = list.map((f) => byId.get(f.id)).filter((t): t is Trader => !!t);
  const empty = !mine && !followed.length;
  return (
    <section className="section corner" aria-labelledby="corner-title">
      <p className="label">{CORNER.label}</p>
      <h2 id="corner-title" className="display">
        {CORNER.title}
      </h2>
      <Link to="/hire" className="textlink">
        {mine ? `${mine.name}'s file` : CORNER.link} <span aria-hidden="true">→</span>
      </Link>
      {empty ? (
        <p className="prose">{CORNER.body}</p>
      ) : (
        <ul className="mini-list">
          {mine && (
            <MiniRow
              t={mine}
              onClick={() => open(mine.id)}
              sub={
                <>
                  desk {pad2(DESK_COUNT + 1)} · yours · {ARCHETYPES[mine.archetype].title}
                </>
              }
            />
          )}
          {followed.map((t) => (
            <MiniRow
              key={t.id}
              t={t}
              onClick={() => open(t.id)}
              sub={t.status === 'escorted' ? 'let go' : t.status === 'waiting' ? 'waiting for a desk' : `desk ${pad2(t.desk ?? 0)} · followed`}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

function summary(prev: VisitSnap, fired: number, hired: number, treasury: number, bonusPaid: number): string[] {
  const out: string[] = [];
  const f = fired - prev.fired;
  const h = hired - prev.hired;
  if (f > 0) out.push(`${f} let go`);
  if (h > 0) out.push(`${h} hired`);
  const dt = treasury - prev.treasury;
  if (Math.abs(dt) >= 0.001) out.push(`treasury ${fmtSignedSol(dt)} SOL`);
  const b = bonusPaid - prev.bonusPaid;
  if (b > 0.0005) out.push(`${fmtSignedSol(b).replace('+', '')} SOL paid on bonus day`);
  return out;
}

export function SinceLastVisit() {
  const { state, byId, now } = useFirm();
  const { open } = usePanel();
  const { list } = useFollows();
  const prev = useVisit(state, list.map((f) => f.id));
  const followed = list.map((f) => ({ f, t: byId.get(f.id) }));
  const away = prev ? now - prev.at : 0;
  const worth = prev && away > 90_000;
  const lines = worth ? summary(prev!, state.counts.fired, state.counts.hired, state.treasurySol, state.bonus.totalPaidSol) : [];

  return (
    <section className="section since" aria-labelledby="since-title">
      <div className="since-head">
        <h2 id="since-title" className="label">
          {SINCE.label}
        </h2>
        <Link to="/traders" className="textlink">
          {list.length} followed
        </Link>
      </div>
      {worth && (
        <p className="prose since-summary">
          Last here {agoWords(away)}.{' '}
          {lines.length ? `Since then: ${lines.join(', ')}.` : 'Not much has changed.'}
        </p>
      )}
      {followed.length ? (
        <ul className="mini-list">
          {followed.map(({ f, t }) => {
            if (!t)
              return (
                <li key={f.id}>
                  <div className="mini">
                    <span className="avatar" />
                    <span className="mini-main">
                      <span className="mini-name">{f.name}</span>
                      <span className="mini-sub">no longer with the firm</span>
                    </span>
                  </div>
                </li>
              );
            const was = prev?.traders[t.id];
            let sub: string;
            if (t.status === 'escorted') sub = was && was.status !== 'escorted' ? 'let go since your last visit' : 'let go';
            else if (was && worth) {
              const d = t.resultPct - was.resultPct;
              const n = t.trades - was.trades;
              sub = `${d >= 0 ? 'up' : 'down'} ${Math.abs(d).toFixed(1)} pts · ${n} ${n === 1 ? 'trade' : 'trades'} since`;
              if (t.nextOut) sub += ' · bottom of the board';
            } else {
              const d = t.resultPct - f.startPct;
              sub = `${d >= 0 ? 'up' : 'down'} ${Math.abs(d).toFixed(1)} pts since you followed`;
            }
            return <MiniRow key={f.id} t={t} sub={sub} onClick={() => open(t.id)} />;
          })}
        </ul>
      ) : (
        !worth && <p className="prose">{SINCE.empty}</p>
      )}
    </section>
  );
}
