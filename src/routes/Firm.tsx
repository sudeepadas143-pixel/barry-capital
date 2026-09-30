import { useMemo, type ReactNode } from 'react';
import { FIRM_NAME, PARTNER_NAME } from '../../firm.config';
import { Headshot } from '../components/Sprite';
import { floorStatus } from '../components/Floors';
import { FLOORS } from '../copy';
import { useFirm } from '../hooks/useFirm';
import { usePanel } from '../hooks/usePanel';
import { agoWords, dayTime, fmtInt, fmtPct, fmtSol, pad2, pctClass, until } from '../format';
import { capTable, splitProRata, toLamports, toSol } from '../sim/payout';
import type { CoinPhase, FirmState, FloorId, Trade } from '../sim/types';

const PHASE_WORDS: Record<CoinPhase, string> = {
  launch: 'new on the board',
  pump: 'going up',
  chop: 'going sideways',
  bleed: 'slowly falling',
  run: 'going up again',
  rug: 'crashed',
  delisted: 'gone',
};

function KV({ rows }: { rows: [string, ReactNode, string?][] }) {
  return (
    <dl className="kv">
      {rows.map(([k, v, cls]) => (
        <div key={k} style={{ display: 'contents' }}>
          <dt>{k}</dt>
          <dd className={cls}>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

function Office({ s, now }: { s: FirmState; now: number }) {
  const b = s.bonus;
  // Recreate the last bonus day's split across the simulated cap table.
  const split = useMemo(() => {
    if (!b.lastAt || b.lastPaidSol <= 0) return null;
    const day = b.days;
    const balances = capTable(s.season.seed, day, b.lastHolders || b.holders);
    const shares = splitProRata(toLamports(b.lastPaidSol), balances);
    const total = balances.reduce((x, y) => x + y, 0);
    return { rows: balances.slice(0, 6).map((bal, i) => ({ bal, pct: (bal / total) * 100, sol: toSol(shares[i]) })), rest: balances.length - 6, check: toSol(shares.reduce((x, y) => x + y, 0)) };
  }, [s.season.seed, b.days, b.holders, b.lastHolders, b.lastAt, b.lastPaidSol]);
  return (
    <>
      <KV
        rows={[
          ['treasury', `${fmtSol(s.treasurySol)} SOL`],
          ['creator fees in', `${fmtSol(s.feesInSol)} SOL`],
          ['bonus pool', `${fmtSol(s.bonus.poolSol)} SOL`],
          ['last bonus day', b.lastAt ? `${dayTime(b.lastAt)} · ${fmtSol(b.lastPaidSol)} SOL` : 'not yet'],
          ['paid out this season', `${fmtSol(b.totalPaidSol)} SOL over ${b.days} ${b.days === 1 ? 'day' : 'days'}`],
          ['next bonus day', `in ${until(b.nextAt - now)}`],
          ['holders on the books', fmtInt(b.holders)],
        ]}
      />
      <p className="prose muted small-prose">
        Once a day, a fifth of any profit above the previous high goes into the bonus pool and is split between
        holders in proportion to their balance, down to the lamport.
      </p>
      {split && (
        <table className="table" style={{ marginTop: 12 }}>
          <caption className="label" style={{ textAlign: 'left', padding: '14px 0 4px' }}>
            The last split, largest holders
          </caption>
          <thead>
            <tr>
              <th scope="col">Holder</th>
              <th scope="col" className="r">
                Share
              </th>
              <th scope="col" className="r">
                Paid
              </th>
            </tr>
          </thead>
          <tbody>
            {split.rows.map((r, i) => (
              <tr key={i}>
                <td className="mono muted">holder {pad2(i + 1)}</td>
                <td className="r mono">{r.pct.toFixed(3)}%</td>
                <td className="r mono">{r.sol.toFixed(6)}</td>
              </tr>
            ))}
            <tr>
              <td className="muted">and {fmtInt(split.rest)} others</td>
              <td className="r mono muted">—</td>
              <td className="r mono">Σ {split.check.toFixed(9)}</td>
            </tr>
          </tbody>
        </table>
      )}
    </>
  );
}

function Terminal({ s }: { s: FirmState }) {
  const coins = [...s.coins].sort((a, b) => b.change1h - a.change1h);
  return (
    <>
      <KV rows={[['coins on the board', String(s.coins.length)], ["today's theme", s.theme]]} />
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Coin</th>
            <th scope="col">State</th>
            <th scope="col" className="r">
              1h
            </th>
            <th scope="col" className="r">
              Desks
            </th>
          </tr>
        </thead>
        <tbody>
          {coins.map((c) => (
            <tr key={c.id}>
              <td>
                <span className="ticker">${c.ticker}</span>
                <span className="sub">{c.name}</span>
              </td>
              <td className="muted" style={{ fontFamily: 'var(--serif)', fontStyle: 'italic' }}>
                {PHASE_WORDS[c.phase]}
              </td>
              <td className={`r mono num ${pctClass(c.change1h)}`}>{fmtPct(c.change1h)}</td>
              <td className="r mono">{c.holders || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function underReview(s: FirmState): Trade[] {
  const out: Trade[] = [];
  for (const f of s.feed) {
    if (f.type !== 'trade' || f.local) continue;
    if ((f.side === 'SELL' && (f.pnlPct ?? 0) < -20) || f.sizeSol > 1.25) out.push(f);
    if (out.length >= 6) break;
  }
  return out;
}

function Compliance({ s, now }: { s: FirmState; now: number }) {
  const { byId } = useFirm();
  const { open } = usePanel();
  const rows = underReview(s);
  return (
    <>
      <KV
        rows={[
          ['trades under review', String(s.underReview)],
          ['positions under water', fmtInt(s.underWater)],
          ['last performance review', s.lastReviewAt ? agoWords(now - s.lastReviewAt) : 'not yet'],
          ['next performance review', `in ${until(s.nextReviewAt - now)}`],
        ]}
      />
      {rows.length > 0 && (
        <ul className="mini-list">
          {rows.map((t) => {
            const tr = byId.get(t.traderId);
            return (
              <li key={t.id}>
                <button type="button" className="mini" onClick={() => tr && open(tr.id)}>
                  <span className="avatar">{tr && <Headshot look={tr.look} size={30} />}</span>
                  <span className="mini-main">
                    <span className="mini-name">
                      {tr?.name} <span className="ticker">{t.side === 'BUY' ? 'bought' : 'sold'} ${t.ticker}</span>
                    </span>
                    <span className="mini-sub">{t.reason}</span>
                  </span>
                  <span className={`mini-res num mono ${t.pnlPct !== undefined ? pctClass(t.pnlPct) : ''}`}>
                    {t.pnlPct !== undefined ? fmtPct(t.pnlPct) : `${fmtSol(t.sizeSol, 2)}`}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </>
  );
}

function HR({ s }: { s: FirmState }) {
  const { open } = usePanel();
  const people = [...s.traders.map((t) => ({ t, note: `desk ${pad2(t.desk!)}` })), ...s.waiting.map((t) => ({ t, note: 'in line' })), ...s.alumni.slice(0, 6).map((t) => ({ t, note: 'left' }))];
  return (
    <>
      <KV
        rows={[
          ['employee files open', String(s.traders.length)],
          ['waiting for a desk', String(s.waiting.length)],
          ['let go this season', String(s.counts.fired)],
          ['hired this season', String(s.counts.hired)],
        ]}
      />
      <ul className="headshots" aria-label="Headshots">
        {people.map(({ t, note }) => (
          <li key={t.id}>
            <button type="button" onClick={() => open(t.id)} className={t.status === 'escorted' ? 'gone' : ''}>
              <span className="portrait">
                <Headshot look={t.look} size={56} />
              </span>
              <span className="hs-name">{t.name}</span>
              <span className="hs-note">{note}</span>
            </button>
          </li>
        ))}
      </ul>
    </>
  );
}

function Server({ s, now }: { s: FirmState; now: number }) {
  return (
    <KV
      rows={[
        ['feed', s.feedStale ? 'stale' : 'current', s.feedStale ? 'neg' : ''],
        ['board last read', agoWords(now - s.boardReadAt)],
        ['feed outages this season', String(s.counts.outages)],
        ['last outage', s.counts.lastOutageAt ? agoWords(now - s.counts.lastOutageAt) : 'none yet'],
        ['minutes into the season', fmtInt(Math.max(0, s.tick))],
      ]}
    />
  );
}

function Lobby({ s }: { s: FirmState }) {
  return (
    <KV
      rows={[
        ['coins pitched this season', fmtInt(s.counts.pitched)],
        ['waiting in the lobby', fmtInt(s.lobby)],
        ['added to the board', fmtInt(s.counts.listed)],
        ['turned down', fmtInt(s.passedOn)],
        ['pitches shredded', fmtInt(s.shredder)],
      ]}
    />
  );
}

function Detail({ id, s, now }: { id: FloorId; s: FirmState; now: number }) {
  switch (id) {
    case 'office':
      return <Office s={s} now={now} />;
    case 'terminal':
      return <Terminal s={s} />;
    case 'compliance':
      return <Compliance s={s} now={now} />;
    case 'hr':
      return <HR s={s} />;
    case 'server':
      return <Server s={s} now={now} />;
    case 'lobby':
      return <Lobby s={s} />;
  }
}

export default function Firm() {
  const { state, now } = useFirm();
  const here = state.partnerFloor === 'review' ? 'terminal' : state.partnerFloor;
  return (
    <div className="wrap">
      <header className="page-head">
        <p className="label">Inside the firm</p>
        <h1 className="hero-title">
          six floors,
          <em>one lift.</em>
        </h1>
        <p className="prose">
          What’s going on at {FIRM_NAME} right now, floor by floor. {PARTNER_NAME} is on one of them.
        </p>
      </header>
      <div className="floors-grid">
        {FLOORS.map((f) => (
          <section key={f.id} id={f.id} className="floor-block" aria-labelledby={`fl-${f.id}`}>
            <p className="label">{f.floor}</p>
            <h2 id={`fl-${f.id}`} className="display">
              {f.name}
              {here === f.id && (
                <span className="here" title={`${PARTNER_NAME} is here`}>
                  <span className="dot" aria-hidden="true" /> {PARTNER_NAME} is here
                </span>
              )}
            </h2>
            <p className="prose">{f.blurb}</p>
            <p className="muted" style={{ margin: '14px 0 0' }}>
              {floorStatus(f.id, state, now)}
            </p>
            <Detail id={f.id} s={state} now={now} />
          </section>
        ))}
      </div>
    </div>
  );
}
