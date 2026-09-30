import { useId, useState, type KeyboardEvent } from 'react';
import { Link } from 'react-router-dom';
import { PARTNER_LOOK } from '../art/partner';
import { useFirm } from '../hooks/useFirm';
import { usePanel } from '../hooks/usePanel';
import { ago, fmtPct, fmtSignedSol, fmtSol, pad2, pctClass } from '../format';
import { ARCHETYPES } from '../sim/archetypes';
import { SIM } from '../sim/params';
import type { EventKind, FeedItem, FirmEvent, Trade, Trader } from '../sim/types';
import { Headshot } from './Sprite';

type Tab = 'feed' | 'payroll' | 'waiting';
const TABS: { id: Tab; label: string }[] = [
  { id: 'feed', label: 'the feed' },
  { id: 'payroll', label: 'payroll' },
  { id: 'waiting', label: 'waiting for a desk' },
];

const EVENT_CHIP: Record<EventKind, string> = {
  escorted: 'HR',
  hired: 'HR',
  bonus: 'BONUS',
  review: 'REVIEW',
  stale: 'FEED',
  rug: 'DROP',
};

export function Strikes({ n, of = SIM.STRIKES_TO_FIRE }: { n: number; of?: number }) {
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
          {trade.local && <span className="chip chip-yours">YOURS</span>}
          <span className={`chip ${trade.side === 'BUY' ? 'chip-buy' : 'chip-sell'}`}>{trade.side}</span>
          <span className="ticker">${trade.ticker}</span>
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
      <p className="trade-reason">
        {trade.reason}{' '}
        <span className="trade-meta num">
          {fmtSol(trade.sizeSol, 2)} SOL
          {trade.pnlPct !== undefined && (
            <>
              {' · '}
              <span className={pctClass(trade.pnlPct)}>{fmtPct(trade.pnlPct)}</span>
            </>
          )}
        </span>
      </p>
      {open && (
        <div id={ruleId} className="trade-rule">
          <span className="mono">rule {trade.rule.code}</span>
          {trade.rule.text}
        </div>
      )}
    </li>
  );
}

export function EventRow({ ev, trader, now }: { ev: FirmEvent; trader?: Trader; now: number }) {
  const { open } = usePanel();
  const look = trader && (ev.kind === 'hired' || ev.kind === 'escorted') ? trader.look : PARTNER_LOOK;
  return (
    <li className="trade trade-event">
      <div className="trade-top">
        <span className="avatar" aria-hidden="true">
          <Headshot look={look} size={30} glasses={look === PARTNER_LOOK} />
        </span>
        <div className="trade-mid">
          <span className={`chip chip-ev chip-${ev.kind}`}>{EVENT_CHIP[ev.kind]}</span>
          {trader && (
            <button type="button" className="trade-who" onClick={() => open(trader.id)}>
              {trader.name}
            </button>
          )}
        </div>
        <time className="ago num" dateTime={new Date(ev.at).toISOString()}>
          {ago(now - ev.at)}
        </time>
      </div>
      <p className="trade-reason">{ev.text}</p>
    </li>
  );
}

export function FeedRow({ item, now, byId }: { item: FeedItem; now: number; byId: Map<string, Trader> }) {
  return item.type === 'trade' ? (
    <TradeRow trade={item} trader={byId.get(item.traderId)} now={now} />
  ) : (
    <EventRow ev={item} trader={item.traderId ? byId.get(item.traderId) : undefined} now={now} />
  );
}

type Filter = 'all' | 'trades' | 'events' | 'mine';

function Feed({ limit, filters }: { limit?: number; filters?: boolean }) {
  const { state, now, byId } = useFirm();
  const [f, setF] = useState<Filter>('all');
  let rows = state.feed;
  if (f === 'trades') rows = rows.filter((x) => x.type === 'trade');
  if (f === 'events') rows = rows.filter((x) => x.type === 'event');
  if (f === 'mine') rows = rows.filter((x) => x.type === 'trade' && x.local);
  if (limit) rows = rows.slice(0, limit);
  return (
    <>
      {filters && (
        <div className="options feed-filters" role="radiogroup" aria-label="Show">
          {(['all', 'trades', 'events', ...(state.mine.length ? ['mine' as const] : [])] as Filter[]).map((x) => (
            <button key={x} type="button" role="radio" aria-checked={f === x} className="option" onClick={() => setF(x)}>
              {x === 'mine' ? 'yours' : x}
            </button>
          ))}
        </div>
      )}
      {rows.length ? (
        <ul className="feed">
          {rows.map((t) => (
            <FeedRow key={t.id} item={t} now={now} byId={byId} />
          ))}
        </ul>
      ) : (
        <p className="prose muted" style={{ fontSize: 17, padding: '18px 0' }}>
          Nothing on the books yet. Check back in a minute.
        </p>
      )}
    </>
  );
}

function Payroll() {
  const { state } = useFirm();
  const { open } = usePanel();
  const rows = [...state.traders, ...state.mine].sort((a, b) => (a.desk ?? 99) - (b.desk ?? 99));
  return (
    <table className="table">
      <thead>
        <tr>
          <th scope="col">Desk</th>
          <th scope="col">Trader</th>
          <th scope="col" className="r">
            P&amp;L SOL
          </th>
          <th scope="col" className="r">
            Strikes
          </th>
        </tr>
      </thead>
      <tbody>
        {rows.map((t) => (
          <tr key={t.id}>
            <td className="mono muted">{t.desk ? pad2(t.desk) : t.local ? '12' : '—'}</td>
            <td>
              <div className="who">
                <span className="avatar" aria-hidden="true">
                  <Headshot look={t.look} size={30} />
                </span>
                <button type="button" onClick={() => open(t.id)}>
                  {t.name}
                  {t.local && <span className="chip chip-yours" style={{ marginLeft: 8 }}>YOURS</span>}
                  <span className="sub">{ARCHETYPES[t.archetype].title}</span>
                </button>
              </div>
            </td>
            <td className={`r mono num ${pctClass(t.pnlSol, 3)}`}>{fmtSignedSol(t.pnlSol)}</td>
            <td className="r">{t.local ? <span className="muted">—</span> : <Strikes n={t.strikes} />}</td>
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

export function Books({ limit, showHead = true, filters = false }: { limit?: number; showHead?: boolean; filters?: boolean }) {
  const { state } = useFirm();
  const [tab, setTab] = useState<Tab>('feed');
  const base = useId();
  const counts: Record<Tab, number> = {
    feed: state.feed.length,
    payroll: state.traders.length + state.mine.length,
    waiting: state.waiting.length,
  };
  const onKey = (e: KeyboardEvent) => {
    const i = TABS.findIndex((t) => t.id === tab);
    let n = -1;
    if (e.key === 'ArrowRight') n = (i + 1) % TABS.length;
    if (e.key === 'ArrowLeft') n = (i + TABS.length - 1) % TABS.length;
    if (n >= 0) {
      setTab(TABS[n].id);
      document.getElementById(`${base}-${TABS[n].id}`)?.focus();
    }
  };
  return (
    <section aria-labelledby={`${base}-title`}>
      {showHead ? (
        <div className="section-head">
          <h2 id={`${base}-title`} className="label">
            The books
          </h2>
          <Link to="/books" className="textlink">
            everything <span aria-hidden="true">→</span>
          </Link>
        </div>
      ) : (
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
        {tab === 'feed' && <Feed limit={limit} filters={filters} />}
        {tab === 'payroll' && <Payroll />}
        {tab === 'waiting' && <Waiting />}
      </div>
    </section>
  );
}
