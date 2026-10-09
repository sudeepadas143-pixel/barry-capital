# Steve’s Investors

A static website for a fictional Wall Street memecoin desk staffed by eleven traders,
run by a managing partner who reviews everyone on the hour. It has an illustrated
isometric office tower, a leaderboard, a live feed, payroll, bonus days, and a trader
you can hire yourself (or build from a Solana wallet address).

**Everything is simulated.** Balances, trades, prices, fees and bonuses come from a
seeded simulation that runs in the browser. The coin tickers are real Solana memecoins,
but their prices on the site are not. The footer says so in one line. There is no
wallet connection, no signing, no payout code, and no network call that could move
funds. A wallet address typed on the hire page is only used to generate a trader and
is kept in that browser. The only requests the site makes are for its own static files.

## Run it

```sh
npm install
npm run dev          # http://localhost:5173
```

Node 20 or newer. A dev-only sprite contact sheet lives at `/_sprites`.

## Test it

```sh
npm test             # unit tests: determinism, coin lifecycles, firing/hiring, pro-rata, local hires
npm run test:e2e     # Playwright: flows, accessibility (axe), screenshots at 390px and 1280px
npm run shots        # just the screenshots, written to screenshots/
npm run art          # renders the procedural art and hotspots into art-out/ and docs/
npm run typecheck
```

Playwright uses a Chromium it finds on the machine. If yours pins a different browser
path, set `PW_CHROMIUM=/path/to/chromium`.

## Build and deploy

```sh
npm run build        # type-checks, then writes the static site to dist/
npm run preview      # serves dist/ on :4173
```

### Vercel

1. Push the repository to GitHub and choose **Add New → Project** in Vercel.
2. Vercel detects Vite. `vercel.json` already sets the build command (`npm run build`),
   the output directory (`dist`), and a rewrite so `/traders`, `/firm`, `/hire` and
   `/books` load on refresh.
3. Deploy. No environment variables are needed.

**Recommended: rebuild daily.** Each build bakes the firm's state at build time into the
bundle, so a first-time visitor only replays the minutes since the last deploy. With a
week-old build that's under half a second. With a month-old build the page shows a brief
"Reading the books" while it catches up. `.github/workflows/redeploy.yml` calls a Vercel
Deploy Hook once a day. Create the hook under Project → Settings → Git → Deploy Hooks and
save it as the repository secret `VERCEL_DEPLOY_HOOK`.

## Configure it

Every brand and network string is in [`firm.config.ts`](firm.config.ts):

| Key | Default | |
| --- | --- | --- |
| `FIRM_NAME` | `Steve’s Investors` | Also the page title and lobby sign |
| `PARTNER_NAME` | `Steve` | The managing partner |
| `SEASON_LABEL` | `Q1` | |
| `DESK_COUNT` | `11` | The layout has twelve bays; eleven desks plus the pencilled-in one |
| `TOKEN_SYMBOL`, `TOKEN_MINT` | placeholder | Shown in the CA card and header pill |
| `EXPLORER_URL` | `https://solscan.io/token/{address}` | `{address}` is replaced with the mint |
| `ACCOUNT_URL` | `https://solscan.io/account/{address}` | Read-only link to a hire's wallet |
| `X_URL` | `https://x.com/` | |
| `SEASON_START` | `2026-09-21T13:00:00Z` | The simulation's minute zero |
| `TICK_SECONDS` | `60` | One simulation step |

Simulation tuning (costs, firing line, review cadence, bonus share, fee rate) is in
`src/sim/params.ts`. Changing anything there rewrites the season's history, so bump
`VERSION` there too, which clears visitors' cached snapshots.

## How it works

**The simulation** (`src/sim/`) is a pure function of `(SEASON_START, tick)`. Each minute
draws its randomness from a hash of the season seed, the tick and a stream id, and the
maths uses only `+ − × ÷` and `sqrt`, which every JavaScript engine rounds the same way.
A test fails if anyone adds `Math.exp`, `Math.log`, `Math.pow` or `**`. So every visitor on
every device sees the same firm at the same minute, with no server.

- **Coins** are real Solana memecoin tickers (`COINS` in `src/sim/names.ts`, no coins
  named after real people) with made-up prices. Each one comes onto the board, maybe
  pumps, chops, then bleeds out, runs again, or crashes (an 80–95% drop in a minute).
  Returns are fat-tailed, coins leave the board, and others take their place. Prices sit
  behind a `PriceSource` interface, so a read-only live feed can be added later.
- **Traders** paper-trade the board using one of twelve methods, each with its own entry,
  exit, holding time and sizing. They pay 1% a side in costs, plus extra slippage for
  buying in a coin's first two minutes. Every trade records a short note built from the
  numbers that triggered it, and the rule behind it.
- **Reviews** run on the hour. The trader with the worst result since hire is let go,
  everyone else keeps their desk, the empty desk is cleared for four minutes, and the
  next person in line sits down. New hires get three hours before their first review.
- **Money:** creator fees are a share of the firm's own token's simulated volume. The
  treasury moves with the traders. A fifth of profit above the high-water mark goes into
  a bonus pool, which is split pro rata, to the lamport, across a simulated cap table
  once a day.

**The page** reads the state once a second. Each minute's trades are stamped across the
following minute, so the feed fills in gradually rather than all at once.

**The building** (`src/scene/`) is drawn with the 2D canvas API (no WebGL) as vector
shapes at the screen's own resolution, so edges are anti-aliased and signs and tickers
use the site's real fonts. The scene is laid out on a 948×1680 grid (three units per
world unit). The static building is drawn once into three offscreen layers (background,
desks, facade); charts are cached until the data changes; each frame composites the
layers with the moving parts (tickers, lights, people, the helicopter). The same drawing
code can also target a plain pixel buffer (`PixelSurface`), which the Node art scripts
and hotspot generator use.

**The traders** (`src/art/figure.ts`) are drawn from shaded shapes (face, hair, jacket,
lapels, tie, arms, legs), supersampled for smooth edges, with a thin selective outline.
At their desks they cycle through habits (typing, calls, leaning back, stretching,
rubbing their eyes, lunch, checking their phone, chatting to the next desk), weighted by
method, the time of day and how their day is going. Now and then one goes for a coffee
or takes the lift. The partner has a routine on each floor (a drink and some putting in
the office, calls by the terminal, walking the desks at review time). One body is palette-swapped per
trader and dressed with their own build, haircut, outfit, neckwear and accessories
(`src/art/traits.ts`). The same renderer draws the figures in the building, the large hire-page
portrait and the headshots, each at the screen's own pixel density. Plants and the office
cat use it too (`src/art/props.ts`). See [ART_GUIDE.md](ART_GUIDE.md) for dropping in
hand-drawn art.

**Your own hire** runs on the same board with its own random stream. It never touches
the shared state, and it lives only in your browser (`localStorage`), along with follows
and the "since the last visit" snapshot. Pasting a public Solana address builds the
trader from a hash of it (`src/wallet.ts`), so the same wallet always makes the same
trader. Private keys and recovery phrases are recognised, refused and cleared.

## Layout

```
firm.config.ts         brand and network strings
src/sim/               simulation: prng, coins, traders, firm, payout, engine, view, tests
src/scene/             building renderer, sprites, actors, animation, hotspots, art swap
src/components/        page sections
src/routes/            /, /traders, /firm, /hire, /books
src/hooks/             firm state, local storage, panel, clock
tests/e2e/             Playwright flows, accessibility and screenshots
scripts/               art renders (npm run art)
docs/                  reference renders and example hotspots for artists
```

See [NOTES.md](NOTES.md) for decisions and open risks.

## The Investors (real NFTs)

The trading floor is fiction; the Investors NFT, its free airdrop and the hire flow are real. `LAUNCH.md` is the owner's step-by-step guide, `worker/` is the airdrop bot (runs on Railway), `api/` is the hire API (Vercel functions), and `nft/` holds the trait layers.
