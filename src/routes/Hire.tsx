import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { DESK_COUNT, PARTNER_NAME } from '../../firm.config';
import { Figure, Headshot } from '../components/Sprite';
import { Strikes, TradeRow } from '../components/Books';
import { HAIRS, HAIR_NAMES, HAIR_STYLE_NAMES, SKINS, SUITS, SUIT_NAMES, TIES, TIE_NAMES } from '../art/palette';
import { useFirm } from '../hooks/useFirm';
import { usePanel } from '../hooks/usePanel';
import { dayTime, fmtPct, fmtSol, pad2, pctClass } from '../format';
import { ARCHETYPES, ARCHETYPE_IDS } from '../sim/archetypes';
import type { ArchetypeId, Look } from '../sim/types';
import { useNow } from '../hooks/useNow';
import { useReducedMotion } from '../hooks/useReducedMotion';

function Swatches({
  label,
  colors,
  names,
  value,
  onChange,
}: {
  label: string;
  colors: string[];
  names?: string[];
  value: number;
  onChange: (i: number) => void;
}) {
  return (
    <div className="field" role="radiogroup" aria-label={label}>
      <span className="label">{label}</span>
      <div className="swatches">
        {colors.map((c, i) => (
          <button
            key={c}
            type="button"
            role="radio"
            aria-checked={value === i}
            aria-label={names?.[i] ?? `${label} ${i + 1}`}
            className="swatch"
            style={{ background: c }}
            onClick={() => onChange(i)}
          />
        ))}
      </div>
    </div>
  );
}

const cleanName = (s: string) =>
  s
    .toLowerCase()
    .replace(/[^a-z' -]/g, '')
    .replace(/\s+/g, ' ')
    .slice(0, 16);

function EmployeeFile() {
  const { state, now, removeHire, msForTick } = useFirm();
  const { open } = usePanel();
  const t = state.mine[0];
  const [confirm, setConfirm] = useState(false);
  const pose = useNow(400);
  const reduced = useReducedMotion();
  if (!t) return null;
  const a = ARCHETYPES[t.archetype];
  const trades = t.recent.filter((x) => x.at <= now);
  return (
    <div className="two-col">
      <section className="section" style={{ borderTop: '2px solid var(--ink)' }} aria-labelledby="file-title">
        <p className="label">Employee file · desk {pad2(DESK_COUNT + 1)}, pencilled in</p>
        <div className="file-id">
          <div className="portrait portrait-tall">
            <Figure look={t.look} pose={reduced ? 'stand' : 'walk'} frame={reduced ? 0 : Math.floor(pose / 400) % 4} scale={5} label={`${t.name}, standing`} />
          </div>
          <div>
            <h2 id="file-title" className="panel-name">
              {t.name}
            </h2>
            <p className="panel-arch">{a.title}</p>
            <p className="muted" style={{ margin: '10px 0 0', fontSize: 14 }}>
              hired {dayTime(msForTick(t.hiredTick))}
            </p>
          </div>
        </div>
        <div className="stats">
          <div className="stat">
            <p className="label">Result</p>
            <div className={`stat-val num ${pctClass(t.resultPct)}`}>{fmtPct(t.resultPct)}</div>
          </div>
          <div className="stat">
            <p className="label">Book</p>
            <div className="stat-val num">
              {fmtSol(t.bookSol, 2)}
              <small>SOL</small>
            </div>
          </div>
          <div className="stat">
            <p className="label">Trades</p>
            <div className="stat-val num">{t.trades}</div>
          </div>
        </div>
        <dl className="kv">
          <dt>risk</dt>
          <dd>{Math.round(t.risk * 100)} / 100</dd>
          <dt>patience</dt>
          <dd>{Math.round(t.patience * 100)} / 100</dd>
          <dt>wins / losses</dt>
          <dd>
            {t.wins} / {t.losses}
          </dd>
          <dt>reviews</dt>
          <dd>
            <Strikes n={0} /> exempt
          </dd>
        </dl>
        <p className="prose muted" style={{ fontSize: 17, marginTop: 18 }}>
          Only this browser can see {t.name}. {PARTNER_NAME} has agreed not to ask.
        </p>
        <div className="panel-actions">
          <button type="button" className="btn-black follow-btn" onClick={() => open(t.id)}>
            open the file
          </button>
          {!confirm ? (
            <button type="button" className="textlink" onClick={() => setConfirm(true)}>
              let {t.name} go
            </button>
          ) : (
            <span className="confirm">
              <span className="muted">Sure?</span>{' '}
              <button type="button" className="textlink" onClick={() => removeHire(t.id)}>
                yes, hand over the box
              </button>{' '}
              <button type="button" className="textlink" onClick={() => setConfirm(false)}>
                no
              </button>
            </span>
          )}
        </div>
      </section>
      <section className="section" aria-labelledby="file-trades">
        <h3 id="file-trades" className="label">
          Recent trades
        </h3>
        {trades.length ? (
          <ul className="feed">
            {trades.map((x) => (
              <TradeRow key={x.id} trade={x} trader={t} now={now} />
            ))}
          </ul>
        ) : (
          <p className="prose muted" style={{ fontSize: 17, marginTop: 12 }}>
            Settling in. The first trade usually comes within a few minutes, depending on the method.
          </p>
        )}
        <p style={{ marginTop: 24 }}>
          <Link to="/" className="textlink">
            see the desk <span aria-hidden="true">→</span>
          </Link>
        </p>
      </section>
    </div>
  );
}

export default function Hire() {
  const { state, addHire } = useFirm();
  const [name, setName] = useState('');
  const [arch, setArch] = useState<ArchetypeId>('intern');
  const [risk, setRisk] = useState(50);
  const [patience, setPatience] = useState(50);
  const [look, setLook] = useState<Look>({ skin: 1, hair: 1, hairStyle: 0, suit: 0, tie: 0 });
  const [touched, setTouched] = useState(false);
  const set = (k: keyof Look) => (i: number) => setLook((l) => ({ ...l, [k]: i }));
  const reduced = useReducedMotion();
  const tickNow = useNow(450);
  const frame = reduced ? 0 : Math.floor(tickNow / 450) % 4;

  // Default the sliders to the method's temperament.
  useEffect(() => {
    setRisk(Math.round(ARCHETYPES[arch].risk * 100));
    setPatience(Math.round(ARCHETYPES[arch].patience * 100));
  }, [arch]);

  const taken = useMemo(() => new Set([...state.traders, ...state.waiting].map((t) => t.name)), [state.traders, state.waiting]);
  const clean = cleanName(name).trim();
  const error = !clean ? 'A surname, please.' : taken.has(clean) ? 'That name is already on a desk.' : null;
  const hired = state.mine[0];

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (error) return;
    addHire({ name: clean, archetype: arch, look, risk: risk / 100, patience: patience / 100 });
    window.scrollTo(0, 0);
  };

  const randomise = () => {
    const r = (n: number) => Math.floor(Math.random() * n);
    setLook({ skin: r(SKINS.length), hair: r(HAIRS.length), hairStyle: r(HAIR_STYLE_NAMES.length), suit: r(SUITS.length), tie: r(TIES.length) });
  };

  return (
    <div className="wrap">
      <header className="page-head">
        <p className="label">Hiring</p>
        <h1 className="hero-title">
          one desk,
          <em>pencilled in.</em>
        </h1>
        <p className="prose">
          {hired
            ? `${hired.name} has the spare desk on this browser. One hire at a time; the budget is what it is.`
            : 'Design a trader. They take the spare desk on this browser and trade the same board as everyone else, with a paper book of their own.'}
        </p>
      </header>
      {hired ? (
        <EmployeeFile />
      ) : (
        <form className="two-col" onSubmit={submit} noValidate>
          <div className="section" style={{ borderTop: '2px solid var(--ink)' }}>
            <label className="field">
              <span className="label">Surname</span>
              <input
                className="input"
                value={name}
                maxLength={16}
                autoComplete="off"
                spellCheck={false}
                aria-invalid={touched && !!error}
                aria-describedby="name-err"
                onChange={(e) => setName(cleanName(e.target.value))}
                placeholder="pemberton"
              />
              <span id="name-err" className="field-err" role="alert">
                {touched && error ? error : ''}
              </span>
            </label>
            <div className="field" role="radiogroup" aria-label="Method">
              <span className="label">Method</span>
              <div className="options">
                {ARCHETYPE_IDS.map((id) => (
                  <button key={id} type="button" role="radio" aria-checked={arch === id} className="option" onClick={() => setArch(id)}>
                    {ARCHETYPES[id].title}
                  </button>
                ))}
              </div>
              <p className="prose muted" style={{ fontSize: 17, marginTop: 12 }}>
                {ARCHETYPES[arch].blurb}
              </p>
            </div>
            <label className="field">
              <span className="label">
                Risk <span className="mono muted">{risk}</span>
              </span>
              <input type="range" min={0} max={100} value={risk} onChange={(e) => setRisk(+e.target.value)} />
              <span className="range-ends">
                <span>careful</span>
                <span>unwell</span>
              </span>
            </label>
            <label className="field">
              <span className="label">
                Patience <span className="mono muted">{patience}</span>
              </span>
              <input type="range" min={0} max={100} value={patience} onChange={(e) => setPatience(+e.target.value)} />
              <span className="range-ends">
                <span>minutes</span>
                <span>forever</span>
              </span>
            </label>
          </div>
          <div className="section">
            <div className="file-id">
              <div className="portrait portrait-tall">
                <Figure look={look} pose={reduced ? 'stand' : 'walk'} frame={frame} scale={5} label="Preview of your trader" />
              </div>
              <div>
                <p className="panel-name">{clean || 'unnamed'}</p>
                <p className="panel-arch">{ARCHETYPES[arch].title}</p>
                <div style={{ marginTop: 12 }}>
                  <Headshot look={look} size={48} />
                </div>
              </div>
            </div>
            <Swatches label="Skin" colors={SKINS} value={look.skin} onChange={set('skin')} />
            <Swatches label="Hair" colors={HAIRS} names={HAIR_NAMES} value={look.hair} onChange={set('hair')} />
            <div className="field" role="radiogroup" aria-label="Haircut">
              <span className="label">Haircut</span>
              <div className="options">
                {HAIR_STYLE_NAMES.map((n, i) => (
                  <button key={n} type="button" role="radio" aria-checked={look.hairStyle === i} className="option" onClick={() => set('hairStyle')(i)}>
                    {n}
                  </button>
                ))}
              </div>
            </div>
            <Swatches label="Suit" colors={SUITS} names={SUIT_NAMES} value={look.suit} onChange={set('suit')} />
            <Swatches label="Tie" colors={TIES} names={TIE_NAMES} value={look.tie} onChange={set('tie')} />
            <div className="panel-actions">
              <button type="submit" className="btn-black">
                sign the paperwork <span aria-hidden="true">↗</span>
              </button>
              <button type="button" className="textlink" onClick={randomise}>
                surprise me
              </button>
            </div>
            <p className="muted" style={{ fontSize: 14, marginTop: 16 }}>
              Saved in this browser only.
            </p>
          </div>
        </form>
      )}
    </div>
  );
}
