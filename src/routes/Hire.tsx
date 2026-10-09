import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { DESK_COUNT, INVESTORS_CAP, accountUrl } from '../../firm.config';
import { shortAddress, traderFromWallet } from '../wallet';
import { HireDesk, HiredCount } from '../components/HireDesk';
import { useHireStatus } from '../hooks/useHireStatus';
import { Figure, Headshot } from '../components/Sprite';
import { TradeRow } from '../components/Books';
import {
  BUILD_NAMES,
  EYES_NAMES,
  FACE_NAMES,
  HAIRS,
  HAIR_NAMES,
  HAIR_STYLE_NAMES,
  NECK_NAMES,
  OUTFIT_NAMES,
  SHIRTS,
  SHIRT_NAMES,
  SKINS,
  SUITS,
  SUIT_NAMES,
  TIES,
  TIE_NAMES,
} from '../art/palette';
import { useFirm } from '../hooks/useFirm';
import { usePanel } from '../hooks/usePanel';
import { dayTime, fmtPct, fmtSol, pad2, pctClass } from '../format';
import { ARCHETYPES, ARCHETYPE_IDS } from '../sim/archetypes';
import type { ArchetypeId, Look } from '../sim/types';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { ArrowUpRight, ArrowRight } from '../components/Icons';

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

function Options({ label, names, value, onChange }: { label: string; names: string[]; value: number; onChange: (i: number) => void }) {
  return (
    <div className="field" role="radiogroup" aria-label={label}>
      <span className="label">{label}</span>
      <div className="options">
        {names.map((n, i) => (
          <button key={n} type="button" role="radio" aria-checked={value === i} className="option" onClick={() => onChange(i)}>
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}

const CUT_NAMES = ['men’s cut', 'women’s cut'];
const HEIGHT_NAMES = ['short', 'average', 'tall'];
const WRIST_NAMES = ['bare wrist', 'gold watch'];


const cleanName = (s: string) =>
  s
    .toLowerCase()
    .replace(/[^a-z' -]/g, '')
    .replace(/\s+/g, ' ')
    .slice(0, 16);

function EmployeeFile() {
  const { state, now, removeHire, msForTick, hires } = useFirm();
  const { open } = usePanel();
  const t = state.mine[0];
  const [confirm, setConfirm] = useState(false);
  const reduced = useReducedMotion();
  if (!t) return null;
  const a = ARCHETYPES[t.archetype];
  const trades = t.recent.filter((x) => x.at <= now);
  const rec = hires.find((h) => h.id === t.id);
  const wallet = rec?.wallet;
  const investor = !!rec?.investor;
  return (
    <div className="two-col">
      <section className="section" style={{ borderTop: '2px solid var(--ink)' }} aria-labelledby="file-title">
        <p className="label">Employee file · desk {pad2(DESK_COUNT + 1)}</p>
        <div className="file-id">
          <div className="portrait portrait-tall">
            <Figure look={t.look} pose={reduced ? 'stand' : 'walk'} animate={!reduced} height={132} label={`${t.name}, standing`} />
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
          <dd>not reviewed: your hire can’t be let go</dd>
          {wallet && (
            <>
              <dt>{investor ? 'Investor held by' : 'built from'}</dt>
              <dd>
                <a className="textlink mono" href={accountUrl(wallet)} target="_blank" rel="noreferrer" title={wallet}>
                  {shortAddress(wallet)} <ArrowUpRight />
                </a>
              </dd>
            </>
          )}
        </dl>
        <p className="prose muted" style={{ fontSize: 17, marginTop: 18 }}>
          {investor
            ? `${t.name} is tied to your Investor: paste the same address on any device to see them. Their trades are illustrative and don’t count toward the firm’s.`
            : `Only this browser can see ${t.name}, and their results don’t count toward the firm’s.`}
        </p>
        <div className="panel-actions">
          <button type="button" className="btn-black follow-btn" onClick={() => open(t.id)}>
            open the file
          </button>
          {investor ? null : !confirm ? (
            <button type="button" className="textlink" onClick={() => setConfirm(true)}>
              let {t.name} go
            </button>
          ) : (
            <span className="confirm">
              <span className="muted">Sure?</span>{' '}
              <button type="button" className="textlink" onClick={() => removeHire(t.id)}>
                yes, let them go
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
            see the desk <ArrowRight />
          </Link>
        </p>
      </section>
    </div>
  );
}

interface Draft {
  name: string;
  archetype: ArchetypeId;
  risk: number;
  patience: number;
  look: Look;
  seed: number;
}

/** Design the trader that comes with an Investor. Starts from the trader the address would make. */
function TraderForm({ address, busy, error, onSave }: { address: string; busy: boolean; error: string | null; onSave: (d: Draft) => void }) {
  const { state } = useFirm();
  const start = useMemo(() => traderFromWallet(address), [address]);
  const [name, setName] = useState(start.name);
  const [arch, setArch] = useState<ArchetypeId>(start.archetype);
  const [risk, setRisk] = useState(Math.round(start.risk * 100));
  const [patience, setPatience] = useState(Math.round(start.patience * 100));
  const [look, setLook] = useState<Look>(start.look);
  const [touched, setTouched] = useState(false);
  const first = useRef(true);
  const set = (k: keyof Look) => (i: number) => setLook((l) => ({ ...l, [k]: i }));
  const setFlag = (k: 'fem' | 'watch') => (i: number) => setLook((l) => ({ ...l, [k]: i === 1, ...(k === 'fem' && i === 1 ? { face: 0 } : {}) }));
  const reduced = useReducedMotion();

  // Default the sliders to the method's temperament, except for the address's own pick.
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    setRisk(Math.round(ARCHETYPES[arch].risk * 100));
    setPatience(Math.round(ARCHETYPES[arch].patience * 100));
  }, [arch]);

  const taken = useMemo(() => new Set([...state.traders, ...state.waiting].map((t) => t.name.toLowerCase())), [state.traders, state.waiting]);
  const clean = cleanName(name).trim();
  const nameError = !clean ? 'A surname, please.' : taken.has(clean.toLowerCase()) ? 'That name is already on a desk.' : null;

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (nameError) return;
    onSave({ name: clean, archetype: arch, look, risk: risk / 100, patience: patience / 100, seed: start.seed });
  };

  const randomise = () => {
    const r = (n: number) => Math.floor(Math.random() * n);
    const fem = Math.random() < 0.35;
    setLook({
      skin: r(SKINS.length),
      hair: r(HAIRS.length),
      hairStyle: r(HAIR_STYLE_NAMES.length),
      suit: r(SUITS.length),
      tie: r(TIES.length),
      fem,
      build: r(BUILD_NAMES.length),
      height: r(HEIGHT_NAMES.length),
      face: fem || Math.random() < 0.4 ? 0 : r(FACE_NAMES.length),
      outfit: r(OUTFIT_NAMES.length),
      shirt: r(SHIRTS.length),
      neck: r(NECK_NAMES.length),
      eyes: Math.random() < 0.4 ? 0 : r(EYES_NAMES.length),
      watch: Math.random() < 0.6,
    });
  };

  return (
    <form className="two-col" onSubmit={submit} noValidate>
      <div className="section" style={{ borderTop: '2px solid var(--ink)' }}>
        <p className="hire-ok">
          Your Investor is in <span className="mono">{shortAddress(address)}</span>. Set up the trader who takes your desk. You can do this once.
        </p>
        <label className="field">
          <span className="label">Surname</span>
          <input
            className="input"
            value={name}
            maxLength={16}
            autoComplete="off"
            spellCheck={false}
            aria-invalid={touched && !!nameError}
            aria-describedby="name-err"
            onChange={(e) => setName(cleanName(e.target.value))}
            placeholder="pemberton"
          />
          <span id="name-err" className="field-err" role="alert">
            {touched && nameError ? nameError : ''}
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
            <Figure look={look} pose={reduced ? 'stand' : 'walk'} animate={!reduced} height={132} label="Preview of your trader" />
          </div>
          <div>
            <p className="panel-name">{clean || 'unnamed'}</p>
            <p className="panel-arch">{ARCHETYPES[arch].title}</p>
            <div style={{ marginTop: 12 }}>
              <Headshot look={look} size={48} />
            </div>
          </div>
        </div>
        <Options label="Cut" names={CUT_NAMES} value={look.fem ? 1 : 0} onChange={setFlag('fem')} />
        <Options label="Build" names={BUILD_NAMES} value={look.build ?? 1} onChange={set('build')} />
        <Options label="Height" names={HEIGHT_NAMES} value={look.height ?? 1} onChange={set('height')} />
        <Swatches label="Skin" colors={SKINS} value={look.skin} onChange={set('skin')} />
        <Swatches label="Hair" colors={HAIRS} names={HAIR_NAMES} value={look.hair} onChange={set('hair')} />
        <Options label="Haircut" names={HAIR_STYLE_NAMES} value={look.hairStyle} onChange={set('hairStyle')} />
        {!look.fem && <Options label="Facial hair" names={FACE_NAMES} value={look.face ?? 0} onChange={set('face')} />}
        <Options label="Outfit" names={OUTFIT_NAMES} value={look.outfit ?? 0} onChange={set('outfit')} />
        <Swatches label="Suit" colors={SUITS} names={SUIT_NAMES} value={look.suit} onChange={set('suit')} />
        <Swatches label="Shirt" colors={SHIRTS} names={SHIRT_NAMES} value={look.shirt ?? 0} onChange={set('shirt')} />
        <Options label="Neck" names={NECK_NAMES} value={look.neck ?? 0} onChange={set('neck')} />
        <Swatches label="Tie" colors={TIES} names={TIE_NAMES} value={look.tie} onChange={set('tie')} />
        <Options label="Eyes and ears" names={EYES_NAMES} value={look.eyes ?? 0} onChange={set('eyes')} />
        <Options label="Wrist" names={WRIST_NAMES} value={look.watch ? 1 : 0} onChange={setFlag('watch')} />
        <div className="panel-actions">
          <button type="submit" className="btn-black" disabled={busy}>
            {busy ? 'signing…' : 'sign the paperwork'} <ArrowUpRight />
          </button>
          <button type="button" className="textlink" onClick={randomise}>
            surprise me
          </button>
        </div>
        <p className={error ? 'field-err' : 'muted'} style={{ fontSize: 14, marginTop: 16 }} role={error ? 'alert' : undefined}>
          {error ?? 'Saved to your Investor and locked once signed. Paste the same address on any device to see them.'}
        </p>
      </div>
    </form>
  );
}

export default function Hire() {
  const { state, addHire } = useFirm();
  const hire = useHireStatus();
  const st = hire.status;
  const mine = state.mine[0];

  // A trader saved with the hiring desk shows up on any device with the same address.
  useEffect(() => {
    if (mine || st?.state !== 'hired' || !st.trader) return;
    const t = st.trader;
    addHire({ name: t.name, archetype: t.archetype, look: t.look, risk: t.risk, patience: t.patience, seed: t.seed, wallet: hire.address, investor: true });
  }, [mine, st, addHire, hire.address]);

  const save = async (d: Draft) => {
    const s = await hire.saveTrader(d);
    if (s.state === 'hired' && s.trader) {
      const t = s.trader;
      addHire({ name: t.name, archetype: t.archetype, look: t.look, risk: t.risk, patience: t.patience, seed: t.seed, wallet: hire.address, investor: true });
      window.scrollTo(0, 0);
    }
  };

  return (
    <div className="wrap">
      <header className="page-head">
        <p className="label">Hiring</p>
        <h1 className="hero-title">
          one spare desk,
          <em>yours to fill.</em>
        </h1>
        <p className="prose">
          {mine
            ? `${mine.name} has your desk.`
            : 'Every trader hired here comes with an Investor, a real NFT sent to your wallet. Get one in four steps, then set up the trader who takes your desk.'}
        </p>
        <HiredCount hired={st?.hired ?? 0} cap={st?.cap ?? INVESTORS_CAP} />
      </header>
      {mine ? <EmployeeFile /> : st?.state === 'minted' ? <TraderForm address={hire.address} busy={hire.busy} error={hire.error} onSave={save} /> : <HireDesk hire={hire} />}
    </div>
  );
}
