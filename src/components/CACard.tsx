import { EXPLORER_LABEL, TOKEN_MINT, explorerUrl } from '../../firm.config';
import { useCopy } from '../hooks/useCopy';
import { ArrowUpRight, CheckIcon } from './Icons';

export function CACard() {
  const { copied, copy } = useCopy(TOKEN_MINT);
  return (
    <div className="ca-card">
      <div className="ca-top">
        <p className="label">Contract address</p>
        <button type="button" className="pill" data-copied={copied} onClick={copy} aria-live="polite">
          {copied ? (
            <>
              copied <CheckIcon />
            </>
          ) : (
            'copy'
          )}
        </button>
        <a className="textlink" href={explorerUrl()} target="_blank" rel="noreferrer">
          {EXPLORER_LABEL} <ArrowUpRight />
        </a>
      </div>
      <p className="ca-addr">{TOKEN_MINT}</p>
    </div>
  );
}
