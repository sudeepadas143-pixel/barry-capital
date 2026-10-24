# Build prompt: Steve's Investors

A single brief that describes everything in this project, so it can be rebuilt from scratch or handed to another developer or agent. Build it in the order of the steps, and stop after each one with a short report and screenshots.

---

## What this is

**Steve's Investors (SI)** is a website for a fictional Wall Street-style memecoin trading firm. Steve, the managing partner, runs a floor of eleven traders who "trade" memecoins with the firm's creator fees. Every hour Steve reviews the desks: the worst performer is fired and replaced, and everyone else keeps their seat.

The project has two halves. Keep the line between them unmistakable in the code, the docs and the site:

| Concept only (moves nothing) | Real (on-chain, real wallets, real SOL) |
|---|---|
| The trading floor: traders, desks, trades, P&L, treasury, creator fees, bonuses, firings | **Investors**: a collection of 1,111 NFTs |
| Everything a hired trader "does" | The free mint and airdrop of an Investor to a holder's wallet |
| | The hire list and the counter `xyz/1111 Investors Hired` |
| | The live market cap bar |

The token is **$SI**, launched on pump.fun. Until it launches, the contract address in config is a placeholder and every live feature stays quiet ("at launch", "Hiring opens when the token launches").

## Hard rules

- **No wallet connection and no signing in the browser, ever.** Visitors only paste a public address. All signing happens in a separate server-side bot (Step 6), which holds its own airdrop wallet's key.
- Any price feed is read-only.
- Don't use the words "demo", "simulation" or "devnet" anywhere in the UI, page titles or metadata. The only disclaimer is one 10px line in the footer corner: "Illustrative figures. Not financial advice."
- No jokes about real people or real companies. Trader names come from the owner's list.
- Take inspiration from the reference site ("Phil's house"); don't copy it.
- All brand strings and network values live in `firm.config.ts`: firm name, partner name, token symbol, mint, cap, phrase, minimum holding, URLs.
- Write copy like a person: short, plain, specific. No AI-sounding filler.

## Stack and deploy

- Vite + React + TypeScript, deployed on Vercel.
- The GitHub repo is linked to the Vercel project, so every push to `main` deploys.
- Serverless functions live in `/api` (Node runtime). Relative imports there need `.js` extensions, because Vercel loads them as ES modules.
- The `vercel.json` rewrite must exclude `api/`.
- Tests:
  - Vitest for unit tests: the simulation, wallet parsing and the API against a fake store.
  - Playwright for end-to-end and accessibility checks at 390px and 1280px.
  - Separate "art" scripts render PNGs for review.

---

## Step 1: The site and the look

- **Layout:**
  - A paper-and-ink editorial look: off-white paper, near-black ink, serif headlines (EB Garamond), a sans body font (Inter Tight), mono numbers (JetBrains Mono) and tabular figures.
  - Black pill buttons with clean SVG arrows. Never emoji arrows.
- **Top bar (real data):**
  - Sits above the header on every page: "$SI market cap" with a live dot, and the contract address with a copy button.
  - Market cap = Jupiter price API v3 (`lite-api.jup.ag/price/v3?ids=<mint>`, no key, works from the browser) × the fixed pump.fun supply of 1,000,000,000. It refreshes every 30 seconds.
- **Header:**
  - Steve's headshot, the firm name, a CA copy pill, an X link and a menu.
  - Menu pages: the building, the traders, the floors, the books, hire a trader.
- **Hero:**
  - Headline "eleven traders, / one gets fired." (second line in italic serif).
  - Short bio: "Steve runs a floor of traders, and every one of them thinks they're the smartest person in the building. Every hour Steve checks the numbers. Whoever's last clears their desk."
  - Buttons: "hire your own trader" and "see the leaderboard".
  - Then a contract-address card, a status line (what Steve is doing right now) and a stats row: traders, treasury, creator fees in.
- **Treasury and fees:**
  - Shown in SOL to 2 decimals, small (about 1.2 SOL or less).
  - They tick up by small amounts on their own.
- **The traders' desks:**
  - A two-column list in desk order: desk number, name, result.
  - Chips for TOP, NEXT OUT and NEW, plus a spare desk 12 for the visitor's hire.
  - A one-line review note: "Every hour Steve lets the worst performer go…", with a countdown and who's top and who's next out.
- **Other sections:**
  - **The building:** a floor guide.
  - **Your watchlist:** follow traders; the list is saved in this browser.
  - **The tape:** tabs for trades, payroll and the bench.
  - **Footer:** the one-line disclaimer.
- **Trader panel:** opens from any desk with a headshot, method, result, book, standing, follow button, last five trades and standing rules.

## Step 2: The trading floor (concept, deterministic)

- **Determinism:** the floor is a pure function of `(SEASON_START, minute tick)`, so every visitor sees the same floor.
  - Use only + − × ÷ and sqrt in the sim; no `Math.exp`, `pow` or `sin`, which can differ between browser engines.
  - Bump `SIM.VERSION` whenever sim output changes.
  - A build-time checkpoint is inlined so first paint is fast.
  - Long gaps since the last deploy replay in chunks behind "Reading the books."
- **The floor:** eleven traders, each with a method (perma-bull, trend follower, dip buyer, sniper, quant, contrarian…), risk, patience and a book in SOL.
- **Coins:** they trade a fixed list of current memecoin tickers (the owner's list, minus anything offensive), each with a theme.
- **Firing rule:**
  - Every hour, the worst result since hire is fired, as long as at least 3 desks are eligible.
  - New hires get 3 hours of grace.
  - The desk sits empty for 4 minutes, then the next name in line is seated.
- **Names:** hires and fires draw at random from the owner's list of 63 trader names, avoiding names already seated and recent alumni.
- **Treasury and bonuses:**
  - Treasury = starting balance + creator fees in, and it only ever goes up.
  - Desk P&L feeds a bonus pool with a high-water mark.
- **Mannerisms:** natural trader habits for the traders and Steve, shown as status lines and actions, never dialogue.
- **Visitor hires:** a visitor's hire runs on its own random stream and never changes the shared floor.

## Step 3: Art

- **Characters:**
  - Drawn in code on Canvas2D: full-length chibi figures for the isometric building, and head-and-shoulders headshots from the same renderer.
  - Flat shading with a highlight and a shade, and a one-pixel ink outline.
- **Look options:** skin (6), hair colour (7), 15 hairstyles (including curtains), build, height, facial hair (stubble, short beard, moustache, goatee), outfits (suit, pinstripe, vest, braces, waistcoat, turtleneck, double-breasted), shirt, neckwear, eyewear (sunglasses, glasses, headset, earpiece) and watch.
  - Heads must sit on the collar at every height and build.
- **The building:**
  - A 2D isometric building drawn on canvas: lobby with a bronze bull and a "STEVE'S INVESTORS" sign, trading floors with numbered desks and monitors, Steve's corner office with a putting green, globe and safe, a screen wall, compliance, HR, server room and street level.
  - Traders animate at their desks.
- **Steve:** silver slicked-back hair, gold glasses, a cigar, a navy double-breasted suit and a brass tie.
  - Export a 1024×1024 profile picture of him.

## Step 4: Hiring through an Investor (the real loop)

The hire page shows "xyz/1111 Investors Hired", where xyz is the number of Investors minted. It then walks the visitor through four numbered steps:

1. **Paste the wallet you want your Investor sent to.** A plain text field (base58, decodes to 32 bytes). Refuse anything that looks like a private key or recovery phrase, and clear it. Submitting registers the address.
2. **Copy this line:** `mint me an investor`, with a copy button.
3. **Post it as a comment on our pump.fun page, from that same wallet.** Link straight to the page, and note that the wallet needs at least $5 of $SI when posting and again when we send.
4. **Your Investor lands in your wallet.** Then come back with the same address to set up your trader.

Show the address's status:

| State | What the page shows |
|---|---|
| closed | Before launch, paused, or all 1,111 gone, with the reason |
| pending | "We're watching the chat…", checked again every 15 seconds |
| minted | The existing trader designer opens (name, method, risk, patience, every look option) |
| hired | The trader appears on desk 12 |

- **Saving:** the trader is saved to the address, not just the browser, so any device with the same address shows it. Once saved it is **locked**: no edits and no "let go".
- **Real vs concept note:** a short line saying the Investor is real and free, and the floor is a story whose trades move no money.

## Step 5: The hiring desk API

- **Store:** Vercel functions over Upstash Redis REST, with no client library. Accept `UPSTASH_REDIS_REST_*` or Vercel's `KV_REST_API_*` variables.
- **Routes:**
  - `GET /api/status?address=` returns state, hired count, cap, reason, and the trader if saved.
  - `POST /api/register {address}` puts the address on the watch list.
  - `POST /api/trader {address, trader}` saves the trader once, only for an address that was minted, validated against the site's real option ranges.
- **Keys** (prefix `si:`):

| Key | Holds |
|---|---|
| `reg:<addr>` | a registered address |
| `minted:<addr>` | `{at, n, sig, asset}` |
| `trader:<addr>` | the saved trader |
| `hired` | integer count |
| `paused` | `"1"` when paused (the kill switch) |
| `log` | audit list |
| `seen:<commentId>` | comments already handled |
| `review:<addr>` | mints that need a manual check |

- **Protection:** a loose per-IP rate limit on register and trader.
- **Tests:** cover the whole API against a fake store.

## Step 6: The airdrop bot (`worker/`, runs on Railway)

- **Packages:** a separate package, so none of it ships with the site: umi, umi-bundle-defaults, mpl-bubblegum (V2), mpl-core, mpl-account-compression, umi-uploader-irys, socket.io-client and tsx.
- **Reading pump.fun comments:**
  - The old REST endpoint `frontend-api…/replies/{mint}` is gone.
  - Coin chat runs on socket.io at `wss://livechat.pump.fun`: `joinRoom {roomId: mint}`, `getMessageHistory {roomId, before, limit}`, and live `newMessage` events.
  - Each message has `id`, `userAddress`, `message` and `timestamp`. Reading needs no login.
  - On every (re)connect, backfill the last 50 messages.
  - It isn't a documented API, so log loudly if the chat goes quiet.
- **Rules**, one comment at a time:
  1. The message contains the phrase (case-insensitive).
  2. The comment hasn't been handled before.
  3. The wallet is registered.
  4. Minting isn't paused.
  5. The wallet hasn't been sent one before, by the store or on-chain via DAS `searchAssets` by owner and collection.
  6. The wallet holds at least $5: `getTokenAccountsByOwner` (any token program) × the Jupiter price, falling back to pump.fun's own market cap read server-side.
  7. Take a number with `INCR hired`; give it back if it's over the cap.
  8. **Re-check the balance right before minting.**
  9. Mint one compressed Investor (Bubblegum V2 `mintV2` into a Core collection with the BubblegumV2 plugin) straight to the wallet.
  10. Record the mint. If the mint is unconfirmed, keep the number and flag `review:` rather than risk sending two.
- **Audit log:** every decision is written with the comment, the wallet, the balance and price, the result and the signature.
- **Health:** a health endpoint shows connection, count, paused state and the wallet, plus a heartbeat log line.
- **Scripts** (each prints the exact cost and does nothing until `--yes`):
  - `upload`: generator output (`images/n.png` + `json/n.json`, or a flat folder) goes to Arweave via Irys and writes `manifest.json` plus `collection.json`. It can resume.
  - `setup`: creates the Core collection and a tree (depth 11, buffer 32, canopy 6; 2,048 slots; 17,048 bytes; about 0.0873 SOL rent).
  - `admin`: `pause`, `resume`, `log [n]`, `count`, `check <wallet>`, `send <wallet>` (a manual retry that still respects one-per-wallet and the cap).
- **Tests:** the rules, with a fake store and fake chain.
- **Costs** (at about $110/SOL):
  - collection about 0.003 SOL
  - tree 0.0873 SOL
  - upload about 0.005 SOL
  - each mint about 0.000095 SOL
  - about 0.2 SOL for all 1,111
  - fund the airdrop wallet with about 0.3 SOL

## Step 7: Investors NFT trait layers

- **Format:**
  - The owner generates the 1,111 images themselves, so deliver **layers only**, on a 1024×1024 canvas.
  - Each layer is drawn by the site's own figure renderer, one part at a time (a part gate in the painter), on an **80×80 hard-pixel grid** (the retro filter), then nearest-neighbour scaled to 1024.
  - Every file uses the same frame and stacks exactly.
- **Folders, in stack order:**

| # | Folder | Contents |
|---|---|---|
| 1 | `01-background` | 8 flat colours with a dithered shadow, plus 7 front-on rooms of the building drawn in the same style (trading floor, corner office with Steve's portrait, lobby with the bull and sign, server room, screen wall, putting green, Wall Street with a cab) |
| 2 | `02-chart` | moon, steady climb, chop, rug pull, dead-cat bounce, V-recovery, candles, each with chart paper and a last-price marker |
| 3 | `03-shadow` | a dithered cast shadow, always on |
| 4 | `04-hair-back` | matches the hair |
| 5 | `05-neck` | 6 skins |
| 6 | `06-outfit` | 16 presets, with no open collars |
| 7 | `07-head` | 6 skins |
| 8 | `08-facial-hair` | stubble (semi-transparent), short beard, moustache, goatee, each × 7 colours |
| 9 | `09-expression` | 8, with semi-transparent lips so one file suits every skin |
| 10 | `10-hair` | 14 styles × 7 colours; the afro is left out |
| 11 | `11-eyewear` | sunglasses, glasses, gold glasses, headset, earpiece |
| 12 | `12-accessory` | cigar |
| 13 | `13-frame` | `MKT $SI +4.20%` green ticker, `MKT $SI -6.90%` red ticker, `LIVE · INVESTOR HIRED` banner, ink border, gold stock certificate |
| 14 | `14-finish` | dithered vignette, scanlines, film grain |

- **Rules:**
  - Charts only on plain colour backgrounds.
  - Hair-back and hair share a file name.
  - Neck and head use the same skin.
  - Facial hair matches the hair colour.
  - No cigar with "shouting" or the headset.
- **Rarity:** the weights in `RARITY.md`. Rares: moon chart, gold glasses, cigar, gold certificate, after-hours background.
- **Docs and previews:**
  - A README with the order and rules.
  - A catalogue of every option.
  - A sample of 24 Investors rolled by the `RARITY.md` weights and the rules, exactly as a generator would make them.

## Step 8: Docs

- **`LAUNCH.md`:** a plain, no-jargon guide for the owner:
  - the real vs concept split
  - a checklist (token CA, a fresh airdrop wallet with about 0.3 SOL, Upstash via Vercel Storage, Helius RPC, Railway, the generated files, Node 20)
  - costs
  - the order: put the CA in config → `npm install` and `.env` → upload → setup → commit `manifest.json` and `collection.json` → Railway with root `worker`
  - day-to-day commands and the kill switch
  - a test-network rehearsal
  - known risks: the undocumented chat API; comments come from the wallet logged into pump.fun; trader setup needs no signature, so it locks after the first save; 0% royalties
- **`NOTES.md`:** the decisions, the real vs concept table and open risks.
- **`README.md`:** what each folder is.
