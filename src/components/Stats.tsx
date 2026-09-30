import { DESK_COUNT } from '../../firm.config';
import { useFirm } from '../hooks/useFirm';
import { agoWords, fmtSol } from '../format';

export function Stats() {
  const { state, now } = useFirm();
  const seated = state.traders.filter((t) => t.status === 'seated').length;
  return (
    <>
      <div className="stats">
        <div className="stat">
          <p className="label">Traders</p>
          <div className="stat-val num">
            {seated}
            <span className="of">/ {DESK_COUNT} desks</span>
          </div>
        </div>
        <div className="stat">
          <p className="label">Treasury</p>
          <div className="stat-val num">
            {fmtSol(state.treasurySol, state.treasurySol >= 100 ? 1 : 3)}
            <small>SOL</small>
          </div>
        </div>
        <div className="stat">
          <p className="label">Creator fees in</p>
          <div className="stat-val num">
            {fmtSol(state.feesInSol)}
            <small>SOL</small>
          </div>
        </div>
      </div>
      <p className="read-at">board read {agoWords(now - state.boardReadAt)}</p>
    </>
  );
}
