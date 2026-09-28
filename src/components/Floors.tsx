import { Link } from 'react-router-dom';
import { PARTNER_NAME } from '../../firm.config';
import { FLOORS } from '../copy';
import { useFirm } from '../hooks/useFirm';
import { fmtInt, fmtSol } from '../format';
import type { FirmState, FloorId } from '../sim/types';

export function floorStatus(id: FloorId, s: FirmState, now: number): string {
  switch (id) {
    case 'office':
      return s.bonus.poolSol > 0.0005
        ? `treasury ${fmtSol(s.treasurySol)} SOL · bonus pool ${fmtSol(s.bonus.poolSol)}`
        : `treasury ${fmtSol(s.treasurySol)} SOL`;
    case 'terminal':
      return `${s.coins.length} coins on the board`;
    case 'compliance':
      return `${s.underReview} ${s.underReview === 1 ? 'trade' : 'trades'} under review`;
    case 'hr':
      return 'headshots and employee files';
    case 'server':
      return s.feedStale
        ? `${PARTNER_NAME} is down here now · feed ${Math.round((now - s.boardReadAt) / 60000)} min old`
        : `where ${PARTNER_NAME} waits out a stale feed`;
    case 'lobby':
      return `${fmtInt(s.lobby)} waiting · ${fmtInt(s.passedOn)} passed on`;
  }
}

export function Floors() {
  const { state, now } = useFirm();
  return (
    <section aria-labelledby="floors-title">
      <div className="section-head">
        <h2 id="floors-title" className="label">
          {PARTNER_NAME}’s floors
        </h2>
        <Link to="/firm" className="textlink">
          inside the firm <span aria-hidden="true">→</span>
        </Link>
      </div>
      <ul className="rows">
        {FLOORS.map((f) => (
          <li key={f.id} className="row">
            <Link to={`/firm#${f.id}`}>
              <span className="row-title">{f.name}</span>
              <span className="row-sub">{floorStatus(f.id, state, now)}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
