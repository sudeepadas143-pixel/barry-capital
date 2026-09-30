import { useEffect, useId, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { FIRM_NAME, TOKEN_MINT, X_URL } from '../../firm.config';
import { PARTNER_LOOK } from '../art/partner';
import { useCopy } from '../hooks/useCopy';
import { CopyIcon, XIcon } from './Icons';
import { Headshot } from './Sprite';

const LINKS = [
  { to: '/', label: 'the building', sub: 'front page' },
  { to: '/traders', label: 'the traders', sub: 'roster and results' },
  { to: '/firm', label: 'the floors', sub: 'inside the firm' },
  { to: '/books', label: 'the books', sub: 'every trade and hire' },
  { to: '/hire', label: 'hire a trader', sub: 'design your own' },
];

export function Header() {
  const [open, setOpen] = useState(false);
  const { copied, copy } = useCopy(TOKEN_MINT);
  const loc = useLocation();
  const menuId = useId();

  useEffect(() => setOpen(false), [loc.pathname]);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  return (
    <header className="header">
      <div className="wrap header-in">
        <Link to="/" className="brand" aria-label={`${FIRM_NAME}, front page`}>
          <Headshot look={PARTNER_LOOK} glasses size={34} />
          <span className="brand-name">{FIRM_NAME}</span>
        </Link>
        <button
          type="button"
          className="pill pill-ca"
          onClick={copy}
          aria-label={copied ? 'Contract address copied' : 'Copy contract address'}
        >
          {copied ? 'copied' : 'CA'}
          {!copied && <CopyIcon />}
        </button>
        <a className="icon-x" href={X_URL} target="_blank" rel="noreferrer" aria-label="X">
          <XIcon />
        </a>
        <button
          type="button"
          className="pill"
          aria-expanded={open}
          aria-controls={menuId}
          onClick={() => setOpen((o) => !o)}
        >
          {open ? 'close' : 'menu'} <span className="burger" aria-hidden="true" />
        </button>
      </div>
      <span className="sr-only" aria-live="polite">
        {copied ? 'Contract address copied' : ''}
      </span>
      {open && (
        <nav id={menuId} className="menu" aria-label="Site">
          <ul className="wrap">
            {LINKS.map((l) => (
              <li key={l.to}>
                <NavLink to={l.to} end>
                  <span>{l.label}</span>
                  <span>{l.sub}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </header>
  );
}
