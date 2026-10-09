# Launching the Investors

A plain guide to switching on the real part of the site: the Investors NFT, the free airdrop and the hire flow. You don't need any Solana or NFT background. Each step says what to click or type.

## What's real and what isn't

- **Real:** the Investors collection, the mint, the airdrop to people's wallets, the hire count and the market cap bar at the top of the site. These touch real wallets and cost real SOL.
- **Not real:** the trading floor. The traders, desks, trades, P&L, treasury and bonuses are a story the site tells. No money moves, and nothing there needs to be accurate.

## How it works

1. Someone pastes their wallet address on the hire page. The site puts it on a list.
2. They post **mint me an investor** in your coin's chat on pump.fun, from that same wallet.
3. The **bot** (a small program running on Railway) sees the comment and checks four things:
   - the wallet is on the list
   - it hasn't had an Investor before
   - it holds at least $5 of your token
   - all 1,111 haven't gone yet
4. Just before sending, it checks the balance again, so selling straight after commenting doesn't count.
5. It mints one Investor into their wallet and writes the decision to a log.
6. They come back to the hire page with the same address, set up their trader once, and it's locked.

## Checklist before anything touches real money

- [ ] **Token launched on pump.fun.** You have its contract address (CA).
- [ ] **A brand-new wallet just for airdrops**, holding about **0.3 SOL**. Don't use your main wallet. In Phantom: *Add account → Create new*, send it 0.3 SOL, then *Settings → this account → Show private key*. You'll paste that key in two places only: your `worker/.env` file and Railway. Never share it with anyone, including me.
- [ ] **Upstash** (the small database for the hire list, free tier). In Vercel, open the project `barry-capital-3`, then go to *Storage → Create → Upstash Redis* and connect it to the project. Vercel adds its keys to the site by itself. From the database's page, copy the **REST URL** and **REST token** for the bot.
- [ ] **Helius** (a Solana connection, free tier). Sign up at helius.dev and copy your **mainnet RPC URL**. It looks like `https://mainnet.helius-rpc.com/?api-key=…`.
- [ ] **Railway** (where the bot runs, about $5 a month, or a few cents for a day or two). Sign up at railway.com with GitHub.
- [ ] **Your 1,111 generated Investors**: images plus metadata from your generator.
- [ ] **Node.js 20 or newer** on your computer (nodejs.org), for three one-time commands.

## Costs (SOL ≈ $110 on 9 October 2026)

| What | Paid by | SOL | About |
|---|---|---|---|
| Collection | airdrop wallet | ~0.003 | $0.35 |
| Tree for up to 2,048 Investors | airdrop wallet | 0.0873 | $9.60 |
| Upload 1,111 images + metadata to Arweave | airdrop wallet | ~0.005 | under $1 |
| Each mint | airdrop wallet | ~0.000095 | 1 cent |
| All 1,111 mints | airdrop wallet | ~0.106 | $11.70 |
| **Total** | | **~0.2** | **~$22** |

The scripts print the exact figure before spending anything, and nothing is paid until you add `--yes`. Keep about 0.3 SOL in the wallet so it never runs dry halfway.

## Step 1: put the contract address in

Open `firm.config.ts` and replace the placeholder in `TOKEN_MINT` with your CA (or send me the CA and I'll do it). Push to GitHub and Vercel redeploys in about a minute. The site then shows the live market cap and opens hiring, once Upstash is connected.

## Step 2: get the bot ready on your computer

```
cd worker
npm install
cp .env.example .env
```

Open `worker/.env` in any text editor and fill in `SOLANA_RPC_URL` (Helius), `AIRDROP_SECRET_KEY` (the airdrop wallet's private key), `TOKEN_MINT`, `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`. `.env` is never uploaded to GitHub.

## Step 3: upload your Investors

Copy your generator's output into `nft/collection/` in one of two shapes:
- `images/1.png … images/1111.png` with `json/1.json … json/1111.json` (the usual generator folders), or
- `1.png`, `1.json`, … all in one folder.

Optionally add a `collection.png` for the collection's own picture (otherwise Investor #1 is used).

```
npm run upload            # checks every file is there and shows the price
npm run upload -- --yes   # uploads (if it stops halfway, run it again and it carries on)
```

This writes `worker/manifest.json` (the list the bot mints from, in order) and `worker/collection.json`.

## Step 4: create the collection and the tree

```
npm run setup             # shows what it will create and the exact cost
npm run setup -- --yes    # creates them
```

It prints two lines, `COLLECTION_ADDRESS=…` and `MERKLE_TREE=…`. Keep them for Step 6.

## Step 5: commit the two files the bot needs

Commit and push `worker/manifest.json` and `worker/collection.json` (or tell me and I'll do it). They hold no secrets, only links to the public metadata.

## Step 6: start the bot on Railway

1. Railway → *New project → Deploy from GitHub repo* → pick `barry-capital`.
2. Open the service → *Settings → Root directory* → `worker`.
3. *Variables* → add everything from your `.env`, plus `COLLECTION_ADDRESS` and `MERKLE_TREE` from Step 4.
4. *Settings → Networking → Generate domain*, so you get a link to the bot's health page.
5. Deploy. In *Logs* you should see `chat: connected` and the airdrop wallet's address.

The health page (the domain from step 4) shows whether the bot is connected, how many Investors are sent, and whether minting is paused.

## Day to day

From the `worker` folder on your computer:

| Command | What it does |
|---|---|
| `npm run admin -- count` | How many are hired, e.g. `214/1111 Investors Hired` |
| `npm run admin -- log 30` | The last 30 decisions: who, which comment, their balance, and minted, refused or ignored and why |
| `npm run admin -- check <wallet>` | Whether that wallet would get one right now (doesn't mint) |
| `npm run admin -- pause` | **Kill switch.** Stops all minting at once, and the site says hiring is paused |
| `npm run admin -- resume` | Starts again |
| `npm run admin -- send <wallet>` | Sends one by hand, e.g. to retry a failed one. Still one per wallet and within the cap |

Railway's *Logs* tab shows the same decisions live. Each line in the audit log records:
- the comment and the wallet
- the token balance and price it was judged on
- the result, and the transaction signature

Comments refused for being under $5 can simply be posted again once the wallet holds enough.

**If something looks wrong**, pause first, then look at the log. Setting `PAUSED=1` in Railway's Variables also stops it.

**To shut it down after a day or two:** run `npm run admin -- pause`, then remove the service in Railway. Investors already sent stay in people's wallets for good, and traders already set up stay on the site.

## Optional: a rehearsal on Solana's test network

Free and worth doing once:
1. Get free test SOL at faucet.solana.com (sign in with GitHub).
2. Use a Helius **devnet** URL as `SOLANA_RPC_URL`.
3. Run Steps 3 and 4.
4. Run `npm run admin -- send <your wallet>`. A test Investor shows up in Phantom once you switch Phantom to the test network.

The test network can't see pump.fun's chat, so this rehearses the minting only.

## Things to know

- **pump.fun's chat isn't a documented public API.** The bot reads the same chat server pump.fun's own site uses. It worked when this was built (9 October 2026), but pump.fun could change it. If it does, the bot logs warnings and mints nothing, rather than guessing.
- **Commenters must be logged into pump.fun with the wallet that holds the tokens.** People who signed up with email get a separate pump.fun wallet, and it's that wallet's address that appears on their comment.
- **Anyone who knows an address could set up its trader first**, because there's no signature step by design. The setup locks after the first save, so the worst case is someone else choosing the trader for an Investor they don't hold.
- **Royalties are 0%.** Change `sellerFeeBasisPoints` in `worker/src/chain.ts` before Step 6 if you want them.
