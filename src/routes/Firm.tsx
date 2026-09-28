import { FIRM_NAME, PARTNER_NAME } from '../../firm.config';
import { floorStatus } from '../components/Floors';
import { FLOORS } from '../copy';
import { useFirm } from '../hooks/useFirm';
import { agoWords, fmtInt, fmtPct, fmtSol, pctClass, until } from '../format';
import type { FirmState, FloorId } from '../sim/types';

function details(id: FloorId, s: FirmState, now: number): [string, string, string?][] {
  switch (id) {
    case 'office':
      return [
        ['treasury', `${fmtSol(s.treasurySol)} SOL`],
        ['creator fees in', `${fmtSol(s.feesInSol)} SOL`],
        ['bonus pool', `${fmtSol(s.bonus.poolSol)} SOL`],
        ['next bonus day', `in ${until(s.bonus.nextAt - now)}`],
      ];
    case 'terminal': {
      const top = [...s.coins].sort((a, b) => b.change1h - a.change1h).slice(0, 5);
      return [['coins on the board', String(s.coins.length)], ...top.map((c): [string, string, string] => [`$${c.ticker}`, fmtPct(c.change1h), pctClass(c.change1h)])];
    }
    case 'compliance':
      return [
        ['trades under review', String(s.underReview)],
        ['positions under water', fmtInt(s.underWater)],
        ['next performance review', `in ${until(s.nextReviewAt - now)}`],
      ];
    case 'hr':
      return [
        ['employee files open', String(s.traders.length)],
        ['waiting for a desk', String(s.waiting.length)],
        ['escorted out this season', String(s.alumni.length)],
      ];
    case 'server':
      return [
        ['board last read', agoWords(now - s.boardReadAt)],
        ['feed', s.feedStale ? 'stale' : 'current'],
        ['tick', fmtInt(s.tick)],
      ];
    case 'lobby':
      return [
        ['pitched, waiting', fmtInt(s.lobby)],
        ['passed on', fmtInt(s.passedOn)],
        ['the shredder', fmtInt(s.shredder)],
      ];
  }
}

export default function Firm() {
  const { state, now } = useFirm();
  return (
    <div className="wrap">
      <header className="page-head">
        <p className="label">Inside the firm</p>
        <h1 className="hero-title">
          six floors,
          <em>one elevator.</em>
        </h1>
        <p className="prose">
          A floor-by-floor account of {FIRM_NAME}, as of this minute. {PARTNER_NAME} is somewhere in here.
        </p>
      </header>
      <div className="two-col">
        {FLOORS.map((f) => (
          <section key={f.id} id={f.id} className="floor-block" aria-labelledby={`fl-${f.id}`}>
            <p className="label">{f.floor}</p>
            <h2 id={`fl-${f.id}`} className="display">
              {f.name}
              {state.partnerFloor === f.id && (
                <span className="dot" style={{ display: 'inline-block', marginLeft: 14, verticalAlign: 'middle' }} aria-label={`${PARTNER_NAME} is here`} />
              )}
            </h2>
            <p className="prose">{f.blurb}</p>
            <p className="muted" style={{ margin: '14px 0 0' }}>
              {floorStatus(f.id, state, now)}
            </p>
            <dl className="kv">
              {details(f.id, state, now).map(([k, v, cls]) => (
                <div key={k} style={{ display: 'contents' }}>
                  <dt>{k}</dt>
                  <dd className={cls}>{v}</dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </div>
    </div>
  );
}
