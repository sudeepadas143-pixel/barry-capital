import { Link } from 'react-router-dom';
import { PARTNER_AT } from '../copy';
import { useFirm } from '../hooks/useFirm';
import { fmtInt } from '../format';

export function StatusLine() {
  const { state } = useFirm();
  const lines = PARTNER_AT[state.partnerFloor];
  const line = lines[state.tick % lines.length];
  return (
    <div className="status">
      <p className="status-line" aria-live="polite">
        <span className="dot" aria-hidden="true" />
        <span>{line}</span>
      </p>
      <p className="status-stats">
        <Link to="/firm#lobby" className="u">
          <b className="num">{fmtInt(state.shredder)}</b> pitches shredded
        </Link>
        {' · '}
        <Link to="/firm#lobby" className="u">
          <b className="num">{fmtInt(state.lobby)}</b> waiting in the lobby
        </Link>
        {' · '}
        <b className="num">{fmtInt(state.underWater)}</b> positions under water
      </p>
    </div>
  );
}
