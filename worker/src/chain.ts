/**
 * Everything that touches Solana. Reads are plain RPC calls; the one write is
 * minting an Investor (a compressed NFT, Bubblegum V2) straight to a wallet.
 */
import { readFileSync } from 'node:fs';
import { createUmi } from '@metaplex-foundation/umi-bundle-defaults';
import { keypairIdentity, publicKey, type Umi } from '@metaplex-foundation/umi';
import { base58 } from '@metaplex-foundation/umi/serializers';
import { mintV2, mplBubblegum, parseLeafFromMintV2Transaction } from '@metaplex-foundation/mpl-bubblegum';
import { mplCore } from '@metaplex-foundation/mpl-core';
import { env } from './env.js';

let umi: Umi | null = null;

/** Umi signed by the airdrop wallet. */
export function chain(): Umi {
  if (umi) return umi;
  umi = createUmi(env.rpc()).use(mplBubblegum()).use(mplCore());
  const raw = env.secret();
  const bytes = raw.startsWith('[') ? Uint8Array.from(JSON.parse(raw) as number[]) : base58.serialize(raw);
  umi.use(keypairIdentity(umi.eddsa.createKeypairFromSecretKey(bytes)));
  return umi;
}

async function rpc<T>(method: string, params: unknown): Promise<T> {
  const res = await fetch(env.rpc(), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }) });
  const data = (await res.json()) as { result?: T; error?: { message: string } };
  if (data.error) throw new Error(`${method}: ${data.error.message}`);
  return data.result as T;
}

/** How many of our tokens a wallet holds right now (any token program). */
export async function tokenBalance(owner: string): Promise<number> {
  const res = await rpc<{ value: { account: { data: { parsed: { info: { tokenAmount: { uiAmount: number | null } } } } } }[] }>('getTokenAccountsByOwner', [
    owner,
    { mint: env.tokenMint() },
    { encoding: 'jsonParsed', commitment: 'confirmed' },
  ]);
  return res.value.reduce((n, a) => n + (a.account.data.parsed.info.tokenAmount.uiAmount ?? 0), 0);
}

/** The token's USD price: Jupiter first, pump.fun's own market cap as a fallback. */
export async function tokenPrice(): Promise<number> {
  const mint = env.tokenMint();
  try {
    const r = await fetch(`https://lite-api.jup.ag/price/v3?ids=${mint}`);
    const p = ((await r.json()) as Record<string, { usdPrice?: number }>)[mint]?.usdPrice;
    if (typeof p === 'number' && p > 0) return p;
  } catch {
    /* fall through */
  }
  const r = await fetch(`https://frontend-api-v3.pump.fun/coins-v2/${mint}`, { headers: { Origin: 'https://pump.fun', Accept: 'application/json' } });
  const c = (await r.json()) as { usd_market_cap?: number; total_supply?: number; base_decimals?: number };
  if (!c.usd_market_cap || !c.total_supply) throw new Error('no price from Jupiter or pump.fun');
  return c.usd_market_cap / (c.total_supply / 10 ** (c.base_decimals ?? 6));
}

/** Does this wallet already hold an Investor? Uses the DAS API (Helius). */
export async function holdsInvestor(owner: string): Promise<boolean> {
  const res = await rpc<{ total: number }>('searchAssets', { ownerAddress: owner, grouping: ['collection', env.collection()], page: 1, limit: 1 });
  return res.total > 0;
}

export interface Item {
  name: string;
  uri: string;
}

let items: Item[] | null = null;
/** The uploaded metadata, in order. Investor #n is items[n - 1]. */
export function item(n: number): Item {
  items ??= JSON.parse(readFileSync(env.manifest(), 'utf8')) as Item[];
  const it = items[n - 1];
  if (!it) throw new Error(`manifest has no item ${n} (it has ${items.length})`);
  return it;
}

/** Mint Investor #n to `owner`. Returns the signature and the new asset id. */
export async function mintInvestor(owner: string, n: number): Promise<{ sig: string; asset?: string }> {
  const u = chain();
  const it = item(n);
  const tx = mintV2(u, {
    leafOwner: publicKey(owner),
    merkleTree: publicKey(env.tree()),
    coreCollection: publicKey(env.collection()),
    metadata: { name: it.name, uri: it.uri, sellerFeeBasisPoints: 0, collection: publicKey(env.collection()), creators: [] },
  });
  const { signature } = await tx.sendAndConfirm(u, { confirm: { commitment: 'confirmed' } });
  const sig = base58.deserialize(signature)[0];
  let asset: string | undefined;
  try {
    asset = (await parseLeafFromMintV2Transaction(u, signature)).id.toString();
  } catch {
    /* the asset id is a nice-to-have; the signature is the record */
  }
  return { sig, asset };
}
