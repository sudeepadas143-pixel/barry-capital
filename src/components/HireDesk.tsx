import { useState } from 'react';
import { MINT_PHRASE, MIN_HOLDING_USD, TOKEN_SYMBOL, pumpUrl } from '../../firm.config';
import { useCopy } from '../hooks/useCopy';
import type { useHireStatus } from '../hooks/useHireStatus';
import { checkWallet, shortAddress } from '../wallet';
import { ArrowUpRight, CheckIcon, CopyIcon } from './Icons';

type Hire = ReturnType<typeof useHireStatus>;

export function HiredCount({ hired, cap }: { hired: number; cap: number }) {
  return (
    <p className="hired-count">
      <b className="num">{hired}</b>/{cap} Investors Hired
    </p>
  );
}

/** The four steps: address, phrase, comment, airdrop. */
export function HireDesk({ hire }: { hire: Hire }) {
  const { status, address, busy, error, register, forget } = hire;
  const [input, setInput] = useState(address);
  const [note, setNote] = useState<string | null>(null);
  const phrase = useCopy(MINT_PHRASE);
  const state = status?.state ?? 'closed';
  const closed = state === 'closed';
  const pending = state === 'pending';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const c = checkWallet(input);
    if (c.kind === 'secret') {
      setInput('');
      setNote(c.message);
      return;
    }
    if (c.kind !== 'ok') {
      setNote(c.kind === 'empty' ? 'Paste the address first.' : c.message);
      return;
    }
    setNote(null);
    await register(c.address);
  };

  return (
    <section className="hire-desk section" aria-labelledby="hire-steps">
      <h2 id="hire-steps" className="label">
        Four steps
      </h2>
      <div className={`hire-status hire-${state}`} role="status" aria-live="polite">
        {closed && <p>{status?.reason ?? 'Hiring opens when the token launches.'}</p>}
        {pending && (
          <>
            <p>
              <b className="mono">{shortAddress(address)}</b> is registered. We’re watching the chat for your comment, and this page checks again every
              15 seconds.
            </p>
            <button type="button" className="textlink" onClick={() => { setInput(''); forget(); }}>
              use a different address
            </button>
          </>
        )}
      </div>
      <ol className="steps">
        <li>
          <p className="step-title">Paste the wallet you want your Investor sent to.</p>
          <form className="step-row" onSubmit={submit} noValidate>
            <input
              id="investor-address"
              className="input mono"
              value={input}
              autoComplete="off"
              autoCapitalize="off"
              spellCheck={false}
              placeholder="your public Solana address"
              aria-label="Your public Solana address"
              aria-describedby="address-note"
              aria-invalid={!!note}
              disabled={closed || pending || busy}
              onChange={(e) => setInput(e.target.value.trim())}
            />
            <button type="submit" className="btn-black" disabled={closed || pending || busy}>
              {busy ? 'checking…' : pending ? 'registered' : 'register'}
            </button>
          </form>
          <p id="address-note" className={note || error ? 'field-err' : 'field-help'} role={note || error ? 'alert' : undefined}>
            {note ?? error ?? 'Just the public address. Nothing to connect or sign, and never a private key or recovery phrase.'}
          </p>
        </li>
        <li>
          <p className="step-title">Copy this line.</p>
          <div className="phrase">
            <span className="mono">{MINT_PHRASE}</span>
            <button type="button" className="pill" data-copied={phrase.copied} onClick={phrase.copy} aria-live="polite">
              {phrase.copied ? (
                <>
                  copied <CheckIcon />
                </>
              ) : (
                <>
                  copy <CopyIcon />
                </>
              )}
            </button>
          </div>
        </li>
        <li>
          <p className="step-title">Post it as a comment on our pump.fun page, from that same wallet.</p>
          <p className="field-help">
            The wallet needs at least ${MIN_HOLDING_USD} of ${TOKEN_SYMBOL} when you post, and still when we send.
          </p>
          <a className="textlink" href={pumpUrl()} target="_blank" rel="noreferrer">
            open the pump.fun page <ArrowUpRight />
          </a>
        </li>
        <li>
          <p className="step-title">Your Investor lands in your wallet.</p>
          <p className="field-help">Then come back here with the same address to set up the trader who takes your desk.</p>
        </li>
      </ol>
      <p className="real-note">
        The Investor is a real NFT, sent to your wallet for free. The trading floor is a story: the trades your trader makes here are illustrative and
        move no money.
      </p>
    </section>
  );
}
