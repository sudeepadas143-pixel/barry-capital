# Barry Capital

A static website for a fictional memecoin desk staffed by eleven AI traders in suits,
run by a managing partner who reviews everyone on the hour. It has an isometric
pixel-art office building, a leaderboard, a live-feeling feed, payroll, bonus days,
and a trader you can hire yourself.

**Everything is simulated.** Balances, trades, prices, fees and bonuses come from a
seeded simulation that runs in the browser. There is no wallet connection, no signing,
no payout code, and no network call that could move funds. The only requests the site
makes are for its own static files.

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
| `FIRM_NAME` | `Barry Capital` | Also the page title and lobby sign |
| `PARTNER_NAME` | `Barry` | The managing partner |
| `SEASON_LABEL` | `Q1` | |
| `DESK_COUNT` | `11` | The layout has twelve bays; eleven desks plus the pencilled-in one |
| `TOKEN_SYMBOL`, `TOKEN_MINT` | placeholder | Shown in the CA card and header pill |
| `EXPLORER_URL` | `https://solscan.io/token/{address}` | `{address}` is replaced with the mint |
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

- **Coins** launch, maybe pump, chop, then bleed out, run again, or rug (an 80–95% drop in
  a minute). Returns are fat-tailed, coins leave the board, and new ones arrive from the
  lobby. Prices sit behind a `PriceSource` interface, so a read-only live feed can be
  added later.
- **Traders** paper-trade the board using one of twelve methods, each with its own entry,
  exit, holding time and sizing. They pay 1% a side in costs, plus extra slippage for
  buying in a coin's first two minutes. Every trade records a deadpan reason and the rule
  that triggered it.
- **Reviews** run on the hour. Three reviews in a row below −35% and the trader is
  escorted out with a box, the desk is cleaned for four minutes, and the next name in
  line sits down.
- **Money:** creator fees are a share of the firm's own token's simulated volume. The
  treasury moves with the traders. A fifth of profit above the high-water mark goes into
  a bonus pool, which is split pro rata, to the lamport, across a simulated cap table
  once a day.

**The page** reads the state once a second. Each minute's trades are stamped across the
following minute, so the feed fills in gradually rather than all at once.

**The building** (`src/scene/`) is drawn into a 948×1680 pixel buffer (three pixels per world unit) with a small
isometric rasterizer (no WebGL). The canvas matches the device's pixels: exact
whole-number scales stay pixel-exact, and anything else is resampled smoothly.

**The traders** (`src/art/figure.ts`) are drawn from shaded shapes (face, hair, jacket,
lapels, tie, arms, legs) with a thin selective outline. One body is palette-swapped per
trader and dressed with their own build, haircut, outfit, neckwear and accessories
(`src/art/traits.ts`). The same renderer draws the figures in the building, the large hire-page
portrait and the headshots, each at the screen's own pixel density. Plants and the office
cat use it too (`src/art/props.ts`). See [ART_GUIDE.md](ART_GUIDE.md) for dropping in
hand-drawn art.

**Your own hire** runs on the same board with its own random stream. It never touches
the shared state, and it lives only in your browser (`localStorage`), along with follows
and the "since the last visit" snapshot.

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
