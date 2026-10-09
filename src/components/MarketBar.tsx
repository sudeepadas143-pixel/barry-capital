import { TOKEN_LAUNCHED, TOKEN_MINT, TOKEN_SYMBOL } from '../../firm.config';
import { useCopy } from '../hooks/useCopy';
import { fmtUsdShort, useMarketCap } from '../hooks/useMarketCap';
import { CheckIcon, CopyIcon } from './Icons';

/** Live market cap and the contract address. Real data, unlike the trading floor below. */
export function MarketBar() {
  const cap = useMarketCap();
  const { copied, copy } = useCopy(TOKEN_MINT);
  return (
    <div className="market-bar">
      <div className="wrap market-in">
        <p className="market-cap">
          <span className="live-dot" aria-hidden="true" />
          <span className="label">${TOKEN_SYMBOL} market cap</span>
          <b className="num">{!TOKEN_LAUNCHED ? 'at launch' : cap === null ? '…' : fmtUsdShort(cap)}</b>
        </p>
        <button type="button" className="market-ca" onClick={copy} aria-label={copied ? 'Contract address copied' : 'Copy contract address'}>
          <span className="label">CA</span>
          <span className="mono market-addr">{TOKEN_MINT}</span>
          {copied ? <CheckIcon /> : <CopyIcon />}
        </button>
      </div>
    </div>
  );
}
