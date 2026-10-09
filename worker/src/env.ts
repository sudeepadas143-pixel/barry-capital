/**
 * Settings, all from environment variables (set them in Railway, or in a
 * local .env file that never gets committed). See LAUNCH.md.
 */
import { readFileSync } from 'node:fs';

function need(name: string): string {
  const v = process.env[name]?.trim();
  if (!v) throw new Error(`Missing ${name}. See LAUNCH.md for what to set.`);
  return v;
}

const num = (name: string, fallback: number) => {
  const v = process.env[name];
  return v ? Number(v) : fallback;
};

// Load ./.env if present (simple KEY=value lines), without overriding real env vars.
try {
  for (const line of readFileSync(new URL('../.env', import.meta.url), 'utf8').split('\n')) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
    if (m && process.env[m[1]] === undefined) process.env[m[1]] = m[2].replace(/^["']|["']$/g, '');
  }
} catch {
  /* no .env */
}

export const env = {
  /** A Solana RPC that also answers DAS queries (Helius works; the public RPC doesn't do DAS). */
  rpc: () => need('SOLANA_RPC_URL'),
  /** The airdrop wallet's secret key: a JSON array (solana-keygen) or a base58 string (Phantom export). */
  secret: () => need('AIRDROP_SECRET_KEY'),
  tokenMint: () => need('TOKEN_MINT'),
  collection: () => need('COLLECTION_ADDRESS'),
  tree: () => need('MERKLE_TREE'),
  redisUrl: () => process.env.UPSTASH_REDIS_REST_URL ?? need('KV_REST_API_URL'),
  redisToken: () => process.env.UPSTASH_REDIS_REST_TOKEN ?? need('KV_REST_API_TOKEN'),
  phrase: () => (process.env.MINT_PHRASE ?? 'mint me an investor').toLowerCase(),
  minUsd: () => num('MIN_HOLDING_USD', 5),
  cap: () => num('INVESTORS_CAP', 1111),
  /** Set PAUSED=1 to stop minting without touching the store. */
  pausedByEnv: () => process.env.PAUSED === '1',
  /** Where the uploaded metadata list lives (written by scripts/upload.ts). */
  manifest: () => process.env.MANIFEST_PATH ?? new URL('../manifest.json', import.meta.url).pathname,
  /** The chat server pump.fun's site uses. */
  chatUrl: () => process.env.PUMP_CHAT_URL ?? 'wss://livechat.pump.fun',
};
