import { useId, useState, type KeyboardEvent } from 'react';
import { Link } from 'react-router-dom';
import { useFirm } from '../hooks/useFirm';
import { usePanel } from '../hooks/usePanel';
import { ago, fmtPct, fmtSignedSol, pad2, pctClass } from '../format';
import { ARCHETYPES } from '../sim/archetypes';
import type { Trade, Trader } from '../sim/types';
import { Headshot } from './Sprite';

type Tab = 'feed' | 'payroll' | 'waiting';
const TABS: { id: Tab; label: string }[] = [
  { id: 'feed', label: 'the feed' },
  { id: 'payroll', label: 'payroll' },
  { id: 'waiting', label: 'waiting for a desk' },
];

export function Strikes({ n, of = 3 }: { n: number; of?: number }) {
  return (
    <span className="strikes" aria-label={`${n} of ${of} strikes`}>
      {Array.from({ length: of }, (_, i) => (i < n ? '●' : '○')).join('')}
    </span>
  );
}

export function TradeRow({ trade, trader, now }: { trade: Trade; trader?: Trader; now: number }) {
  const [open, setOpen] = useState(false);
  const { open: openPanel } = usePanel();
  const ruleId = useId();
  return (
    <li className="trade">
      <div className="trade-top">
        <span className="avatar" aria-hidden="true">
          {trader && <Headshot look={trader.look} size={30} />}
        </span>
        <div className="trade-mid">
          <button type="button" className="trade-who" onClick={() => trader && openPanel(trader.id)}>
            {trader?.name ?? trade.traderId}
          </button>
          <span className={`chip ${trade.side === 'BUY' ? 'chip-buy' : 'chip-sell'}`}>{trade.side}</span>
          <span className="ticker">${trade.ticker}</span>
          {trade.pnlPct !== undefined && (
            <span className={`ticker num ${pctClass(trade.pnlPct)}`}>{fmtPct(trade.pnlPct)}</span>
          )}
          <button
            type="button"
            className="chip"
            aria-expanded={open}
            aria-controls={ruleId}
            onClick={() => setOpen((o) => !o)}
          >
            RULES
          </button>
        </div>
        <time className="ago num" dateTime={new Date(trade.at).toISOString()}>
          {ago(now - trade.at)}
        </time>
      </div>
      <p className="trade-reason">{trade.reason}</p>
      {open && (
        <div id={ruleId} className="trade-rule">
          <span className="mono">rule {trade.rule.code}</span>
          {trade.rule.text}
        </div>
      )}
    </li>
  );
}

function Feed({ limit }: { limit?: number }) {
  const { state, now, byId } = useFirm();
  const rows = limit ? state.feed.slice(0, limit) : state.feed;
  return (
    <ul className="feed">
      {rows.map((t) => (
        <TradeRow key={t.id} trade={t} trader={byId.get(t.traderId)} now={now} />
      ))}
    </ul>
  );
}

function Payroll() {
  const { state } = useFirm();
  const { open } = usePanel();
  const rows = [...state.traders].sort((a, b) => (a.desk ?? 99) - (b.desk ?? 99));
  return (
    <table className="table">
      <thead>
        <tr>
          <th scope="col">Desk</th>
          <th scope="col">Trader</th>
          <th scope="col" className="r">
            P&amp;L
          </th>
          <th scope="col" className="r">
            Strikes
          </th>
        </tr>
      </thead>
      <tbody>
        {rows.map((t) => (
          <tr key={t.id}>
            <td className="mono muted">{t.desk ? pad2(t.desk) : '—'}</td>
            <td>
              <div className="who">
                <button type="button" onClick={() => open(t.id)}>
                  {t.name}
                  <span className="sub">{ARCHETYPES[t.archetype].title}</span>
                </button>
              </div>
            </td>
            <td className={`r mono num ${pctClass(t.pnlSol, 3)}`}>{fmtSignedSol(t.pnlSol)}</td>
            <td className="r">
              <Strikes n={t.strikes} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Waiting() {
  const { state } = useFirm();
  const { open } = usePanel();
  return (
    <ol className="roster" style={{ borderTop: 0 }}>
      {state.waiting.map((t, i) => (
        <li key={t.id}>
          <button type="button" onClick={() => open(t.id)}>
            <span className="desk-no">{pad2(i + 1)}</span>
            <span className="avatar">
              <Headshot look={t.look} size={30} />
            </span>
            <span>
              <span className="roster-name">{t.name}</span>
              <span className="roster-arch">{ARCHETYPES[t.archetype].title}</span>
            </span>
            <span className="muted" style={{ fontSize: 14 }}>
              {i === 0 ? 'next in' : 'in line'}
            </span>
          </button>
        </li>
      ))}
    </ol>
  );
}

export function Books({ limit, showHead = true }: { limit?: number; showHead?: boolean }) {
  const { state } = useFirm();
  const [tab, setTab] = useState<Tab>('feed');
  const base = useId();
  const counts: Record<Tab, number> = {
    feed: state.feed.length,
    payroll: state.traders.length,
    waiting: state.waiting.length,
  };
  const onKey = (e: KeyboardEvent) => {
    const i = TABS.findIndex((t) => t.id === tab);
    if (e.key === 'ArrowRight') setTab(TABS[(i + 1) % TABS.length].id);
    if (e.key === 'ArrowLeft') setTab(TABS[(i + TABS.length - 1) % TABS.length].id);
  };
  return (
    <section aria-labelledby={`${base}-title`}>
      {showHead && (
        <div className="section-head">
          <h2 id={`${base}-title`} className="label">
            The books
          </h2>
          <Link to="/books" className="textlink">
            notebook <span aria-hidden="true">→</span>
          </Link>
        </div>
      )}
      {!showHead && (
        <h2 id={`${base}-title`} className="sr-only">
          The books
        </h2>
      )}
      <div className="tabs" role="tablist" aria-label="The books" onKeyDown={onKey}>
        {TABS.map((t) => (
          <button
            key={t.id}
            id={`${base}-${t.id}`}
            type="button"
            role="tab"
            className="tab"
            aria-selected={tab === t.id}
            aria-controls={`${base}-${t.id}-panel`}
            tabIndex={tab === t.id ? 0 : -1}
            onClick={() => setTab(t.id)}
          >
            {t.label}
            {t.id !== 'feed' && <span className="tab-count">{counts[t.id]}</span>}
          </button>
        ))}
      </div>
      <div id={`${base}-${tab}-panel`} role="tabpanel" aria-labelledby={`${base}-${tab}`}>
        {tab === 'feed' && <Feed limit={limit} />}
        {tab === 'payroll' && <Payroll />}
        {tab === 'waiting' && <Waiting />}
      </div>
    </section>
  );
}
