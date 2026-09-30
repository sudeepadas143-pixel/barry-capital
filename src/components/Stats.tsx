import { DESK_COUNT, SEASON_START } from '../../firm.config';
import { useLiveValue } from '../hooks/useLiveValue';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { useFirm } from '../hooks/useFirm';
import { agoWords, fmtSol } from '../format';

export function Stats() {
  const { state, now } = useFirm();
  const seated = state.traders.filter((t) => t.status === 'seated').length;
  const reduced = useReducedMotion();
  // Fees come in at roughly the season's average rate; the treasury grows with them.
  const perMs = state.feesInSol / Math.max(60_000, state.at - Date.parse(SEASON_START));
  const fees = useLiveValue(state.feesInSol, perMs, reduced);
  const treasury = useLiveValue(state.treasurySol, perMs, reduced);
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
            {fmtSol(treasury, 5)}
            <small>SOL</small>
          </div>
        </div>
        <div className="stat">
          <p className="label">Creator fees in</p>
          <div className="stat-val num">
            {fmtSol(fees, 5)}
            <small>SOL</small>
          </div>
        </div>
      </div>
      <p className="read-at">board read {agoWords(now - state.boardReadAt)}</p>
    </>
  );
}
