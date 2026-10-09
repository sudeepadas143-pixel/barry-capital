/**
 * Every brand string and network-specific value lives here.
 * Nothing else in the codebase should hardcode these.
 */
export const FIRM_NAME = 'Steve’s Investors';
export const PARTNER_NAME = 'Steve';
export const SEASON_LABEL = 'Q1';
export const DESK_COUNT = 11;

export const TOKEN_SYMBOL = 'SI';
/** Placeholder. Swap for the real mint when there is one. */
export const TOKEN_MINT = 'StevesInvXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX';
/** `{address}` is replaced with TOKEN_MINT. */
export const EXPLORER_URL = 'https://solscan.io/token/{address}';
export const EXPLORER_LABEL = 'solscan';
/** Read-only explorer page for a wallet address. */
export const ACCOUNT_URL = 'https://solscan.io/account/{address}';
export const X_URL = 'https://x.com/';

/** True until TOKEN_MINT is the real address. Live features stay quiet until then. */
export const TOKEN_LAUNCHED = !TOKEN_MINT.includes('XXXX');
/** pump.fun tokens have a fixed supply of one billion. */
export const TOKEN_SUPPLY = 1_000_000_000;
/** Read-only price feed (no key needed). `{mint}` is replaced with TOKEN_MINT. */
export const PRICE_URL = 'https://lite-api.jup.ag/price/v3?ids={mint}';
/** The token's pump.fun page, where the mint phrase is posted. */
export const PUMP_URL = 'https://pump.fun/coin/{mint}';
export const pumpUrl = () => PUMP_URL.replace('{mint}', TOKEN_MINT);

/** The Investors NFT: how many exist, what to post, and the minimum holding. */
export const INVESTORS_CAP = 1111;
export const MINT_PHRASE = 'mint me an investor';
export const MIN_HOLDING_USD = 5;

/** The simulation is a pure function of (SEASON_START, tick index). */
export const SEASON_START = '2026-09-21T13:00:00Z';
export const TICK_SECONDS = 60;

export const SITE_DESCRIPTION =
  'A Wall Street trading floor for memecoins, with eleven traders and one very demanding boss.';

export const explorerUrl = (address: string = TOKEN_MINT) =>
  EXPLORER_URL.replace('{address}', address);

export const accountUrl = (address: string) => ACCOUNT_URL.replace('{address}', address);
