import { Link } from 'react-router-dom';
import { PARTNER_NAME } from '../../firm.config';
import { FLOORS } from '../copy';
import { useFirm } from '../hooks/useFirm';
import { fmtInt, fmtSol } from '../format';
import type { FirmState, FloorId } from '../sim/types';
import { ArrowRight } from './Icons';

export function floorStatus(id: FloorId, s: FirmState, now: number): string {
  switch (id) {
    case 'office':
      return s.bonus.poolSol > 0.0005
        ? `treasury ${fmtSol(s.treasurySol, 2)} SOL · bonus pool ${fmtSol(s.bonus.poolSol, 2)}`
        : `treasury ${fmtSol(s.treasurySol, 2)} SOL`;
    case 'terminal':
      return `${s.coins.length} coins on the board`;
    case 'compliance':
      return `${s.underReview} ${s.underReview === 1 ? 'trade' : 'trades'} under review`;
    case 'hr':
      return 'headshots and employee files';
    case 'server':
      return s.feedStale
        ? `${PARTNER_NAME} is down here · feed ${Math.round((now - s.boardReadAt) / 60000)} min old`
        : 'price feed is live';
    case 'lobby':
      return `${fmtInt(s.lobby)} coins waiting · ${fmtInt(s.passedOn)} turned down`;
  }
}

export function Floors() {
  const { state, now } = useFirm();
  return (
    <section aria-labelledby="floors-title">
      <div className="section-head">
        <h2 id="floors-title" className="label">
          The building
        </h2>
        <Link to="/firm" className="textlink">
          floor guide <ArrowRight />
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
