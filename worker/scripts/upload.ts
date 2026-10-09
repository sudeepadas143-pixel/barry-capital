/**
 * Upload your generated Investors to Arweave (permanent storage, via Irys)
 * and write manifest.json, the list the bot mints from.
 *
 * Put your generator's output in ../nft/collection/ as either
 *   images/1.png + json/1.json, …            (HashLips-style folders), or
 *   1.png + 1.json, …                        (one folder)
 * plus collection.png (the collection's picture; Investor #1 is used if missing).
 *
 *   npx tsx scripts/upload.ts          checks the files and shows the price
 *   npx tsx scripts/upload.ts --yes    uploads (safe to re-run: it resumes)
 */
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { createGenericFile } from '@metaplex-foundation/umi';
import { irysUploader } from '@metaplex-foundation/umi-uploader-irys';
import { chain } from '../src/chain.js';

const DIR = new URL('../../nft/collection/', import.meta.url).pathname;
const OUT = new URL('../manifest.json', import.meta.url).pathname;
const PARTIAL = new URL('../manifest.partial.json', import.meta.url).pathname;
const COLLECTION = new URL('../collection.json', import.meta.url).pathname;
const COUNT = Number(process.env.INVESTORS_CAP ?? 1111);

const paths = (n: number) =>
  existsSync(join(DIR, 'images', `${n}.png`)) ? { png: join(DIR, 'images', `${n}.png`), json: join(DIR, 'json', `${n}.json`) } : { png: join(DIR, `${n}.png`), json: join(DIR, `${n}.json`) };

const missing: number[] = [];
let bytes = 0;
for (let n = 1; n <= COUNT; n++) {
  const p = paths(n);
  if (!existsSync(p.png) || !existsSync(p.json)) missing.push(n);
  else bytes += readFileSync(p.png).length + readFileSync(p.json).length;
}
if (missing.length) {
  console.error(`Missing files for ${missing.length} Investors (first: #${missing[0]}). Expected ${COUNT} in ${DIR}`);
  process.exit(1);
}

const umi = chain().use(irysUploader());
const price = await umi.uploader.getUploadPrice([createGenericFile(new Uint8Array(bytes), 'all')]);
console.log(`${COUNT} Investors, ${(bytes / 1e6).toFixed(1)} MB. Upload price about ${(Number(price.basisPoints) / 1e9).toFixed(4)} SOL from ${umi.identity.publicKey}.`);
if (!process.argv.includes('--yes')) {
  console.log('Nothing uploaded. Run again with --yes to upload.');
  process.exit(0);
}

const done: { name: string; uri: string }[] = existsSync(PARTIAL) ? JSON.parse(readFileSync(PARTIAL, 'utf8')) : [];
for (let n = done.length + 1; n <= COUNT; n++) {
  const p = paths(n);
  const [image] = await umi.uploader.upload([createGenericFile(readFileSync(p.png), `${n}.png`, { contentType: 'image/png' })]);
  const meta = JSON.parse(readFileSync(p.json, 'utf8')) as Record<string, unknown>;
  const name = typeof meta.name === 'string' && meta.name ? meta.name : `Investor #${n}`;
  const uri = await umi.uploader.uploadJson({
    ...meta,
    name,
    symbol: 'SI',
    image,
    properties: { files: [{ uri: image, type: 'image/png' }], category: 'image' },
  });
  done.push({ name, uri });
  writeFileSync(PARTIAL, JSON.stringify(done));
  if (n % 25 === 0 || n === COUNT) console.log(`uploaded ${n}/${COUNT}`);
}
writeFileSync(OUT, JSON.stringify(done, null, 1));

const cover = existsSync(join(DIR, 'collection.png')) ? join(DIR, 'collection.png') : paths(1).png;
const [coverUri] = await umi.uploader.upload([createGenericFile(readFileSync(cover), 'collection.png', { contentType: 'image/png' })]);
const collectionUri = await umi.uploader.uploadJson({
  name: 'Investors',
  symbol: 'SI',
  description: 'The Investors of Steve’s Investors. Each one hired a trader on the floor.',
  image: coverUri,
  properties: { files: [{ uri: coverUri, type: 'image/png' }], category: 'image' },
});
writeFileSync(COLLECTION, JSON.stringify({ name: 'Investors', uri: collectionUri }, null, 1));
console.log(`Done. manifest.json has ${done.length} Investors; collection.json is ready for scripts/setup.ts.`);
