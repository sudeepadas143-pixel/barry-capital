import { useState } from 'react';
import { Headshot } from '../components/Sprite';
import { HAIRS, HAIR_STYLE_NAMES, SKINS, SUITS, SUIT_NAMES, TIES, TIE_NAMES } from '../art/palette';
import { ARCHETYPES, ARCHETYPE_IDS } from '../sim/archetypes';
import type { ArchetypeId, Look } from '../sim/types';

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

/** M1: layout only. Saving, the sprite and the private simulation arrive in M4. */
export default function Hire() {
  const [name, setName] = useState('');
  const [arch, setArch] = useState<ArchetypeId>('intern');
  const [risk, setRisk] = useState(50);
  const [patience, setPatience] = useState(50);
  const [look, setLook] = useState<Look>({ skin: 1, hair: 1, hairStyle: 0, suit: 0, tie: 0 });
  const set = (k: keyof Look) => (i: number) => setLook((l) => ({ ...l, [k]: i }));

  return (
    <div className="wrap">
      <header className="page-head">
        <p className="label">Hiring</p>
        <h1 className="hero-title">
          one desk,
          <em>pencilled in.</em>
        </h1>
        <p className="prose">
          Design a trader. They take the spare desk on this browser and trade the same board as everyone else.
        </p>
      </header>
      <div className="two-col">
        <form className="section" style={{ borderTop: '2px solid var(--ink)' }} onSubmit={(e) => e.preventDefault()}>
          <label className="field">
            <span className="label">Surname</span>
            <input className="input" value={name} maxLength={16} onChange={(e) => setName(e.target.value)} placeholder="e.g. pemberton" />
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
            <span className="label">Risk</span>
            <input type="range" min={0} max={100} value={risk} onChange={(e) => setRisk(+e.target.value)} />
            <span className="range-ends">
              <span>careful</span>
              <span>unwell</span>
            </span>
          </label>
          <label className="field">
            <span className="label">Patience</span>
            <input type="range" min={0} max={100} value={patience} onChange={(e) => setPatience(+e.target.value)} />
            <span className="range-ends">
              <span>minutes</span>
              <span>forever</span>
            </span>
          </label>
          <Swatches label="Skin" colors={SKINS} value={look.skin} onChange={set('skin')} />
          <Swatches label="Hair" colors={HAIRS} value={look.hair} onChange={set('hair')} />
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
        </form>
        <aside className="section" aria-label="Employee file preview">
          <p className="label">Employee file</p>
          <div className="panel-id">
            <div className="portrait">
              <Headshot look={look} size={84} />
            </div>
            <div>
              <p className="panel-name">{name || 'unnamed'}</p>
              <p className="panel-arch">{ARCHETYPES[arch].title}</p>
            </div>
          </div>
          <button type="button" className="btn-black" disabled>
            sign the paperwork <span aria-hidden="true">↗</span>
          </button>
        </aside>
      </div>
    </div>
  );
}
