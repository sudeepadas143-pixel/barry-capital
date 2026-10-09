/**
 * One-time setup: create the Investors collection and the tree that holds the
 * compressed NFTs. Run once, after scripts/upload.ts.
 *
 *   npx tsx scripts/setup.ts          shows what it will do and what it costs
 *   npx tsx scripts/setup.ts --yes    does it
 *
 * Prints COLLECTION_ADDRESS and MERKLE_TREE for Railway's settings.
 */
import { readFileSync } from 'node:fs';
import { generateSigner, sol } from '@metaplex-foundation/umi';
import { base58 } from '@metaplex-foundation/umi/serializers';
import { createTreeV2 } from '@metaplex-foundation/mpl-bubblegum';
import { createCollection } from '@metaplex-foundation/mpl-core';
import { getMerkleTreeSize } from '@metaplex-foundation/mpl-account-compression';
import { chain } from '../src/chain.js';

// 2^11 = 2,048 slots for 1,111 Investors. Canopy 6 keeps transfers cheap on marketplaces.
const DEPTH = 11;
const BUFFER = 32;
const CANOPY = 6;

const umi = chain();
const meta = JSON.parse(readFileSync(new URL('../collection.json', import.meta.url), 'utf8')) as { name: string; uri: string };
const size = getMerkleTreeSize(DEPTH, BUFFER, CANOPY);
const treeRent = await umi.rpc.getRent(size);
const collectionRent = await umi.rpc.getRent(300);
const balance = await umi.rpc.getBalance(umi.identity.publicKey);
const fmt = (l: { basisPoints: bigint }) => (Number(l.basisPoints) / 1e9).toFixed(4);

console.log(`Airdrop wallet: ${umi.identity.publicKey}  balance ${fmt(balance)} SOL`);
console.log(`Collection "${meta.name}" (${meta.uri}): about ${fmt(collectionRent)} SOL plus Metaplex's fee`);
console.log(`Tree for ${2 ** DEPTH} Investors (${size} bytes): ${fmt(treeRent)} SOL`);
console.log(`Each mint after that: about 0.000095 SOL (0.00009 Metaplex fee + network fee)`);

if (!process.argv.includes('--yes')) {
  console.log('\nNothing done. Run again with --yes to create them.');
  process.exit(0);
}
if (balance.basisPoints < treeRent.basisPoints + sol(0.02).basisPoints) {
  console.error('Not enough SOL in the airdrop wallet. Top it up and run again.');
  process.exit(1);
}

const collection = generateSigner(umi);
await createCollection(umi, { collection, name: meta.name, uri: meta.uri, plugins: [{ type: 'BubblegumV2' }] }).sendAndConfirm(umi);
console.log(`\nCOLLECTION_ADDRESS=${collection.publicKey}`);

const tree = generateSigner(umi);
const builder = await createTreeV2(umi, { merkleTree: tree, maxDepth: DEPTH, maxBufferSize: BUFFER, canopyDepth: CANOPY });
const { signature } = await builder.sendAndConfirm(umi);
console.log(`MERKLE_TREE=${tree.publicKey}`);
console.log(`(tree signature ${base58.deserialize(signature)[0]})`);
console.log('\nCopy both lines into Railway → Variables.');
