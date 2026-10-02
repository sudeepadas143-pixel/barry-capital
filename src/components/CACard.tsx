import { EXPLORER_LABEL, TOKEN_MINT, explorerUrl } from '../../firm.config';
import { useCopy } from '../hooks/useCopy';
import { ArrowUpRight, CopyIcon } from './Icons';

/** The token address as a dark strip: tag, address, copy and explorer. */
export function CACard() {
  const { copied, copy } = useCopy(TOKEN_MINT);
  return (
    <div className="ca-card">
      <span className="ca-tag">CA</span>
      <p className="ca-addr" aria-label="Contract address">
        {TOKEN_MINT}
      </p>
      <div className="ca-actions">
        <button type="button" className="ca-btn" onClick={copy} aria-live="polite">
          {copied ? 'copied' : 'copy'} <CopyIcon />
        </button>
        <a className="ca-btn" href={explorerUrl()} target="_blank" rel="noreferrer">
          {EXPLORER_LABEL} <ArrowUpRight />
        </a>
      </div>
    </div>
  );
}
