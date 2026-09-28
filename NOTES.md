# Notes

Decisions made along the way, and the things worth a second look.

## Decisions from the brief review

- **No market cap.** Removed entirely at the owner's request. It isn't in the page,
  the simulation or the copy.
- **The token is never real.** Bonus day splits across a *simulated* cap table
  (`capTable()` in `src/sim/payout.ts`). No real wallet or holder is referenced anywhere.
- **Clock skew is accepted.** A device with a wrong clock sees a slightly different
  minute. There's no server to sync against.
- **Placeholders** for `TOKEN_MINT` and `X_URL` stay in `firm.config.ts` until real values exist.

## Simulation

- **Determinism.** State is a pure function of `(SEASON_START, tick)`. The simulation uses
  only `+ − × ÷` and `sqrt` on floats, which IEEE-754 guarantees round identically in every
  engine. `Math.exp/log/pow/sin`, `**` and friends can differ in the last bit between V8
  and JavaScriptCore, and in a chaotic system one bit is enough to diverge within hours.
  `sim.test.ts` fails if any of them appear in `src/sim/`. The Pareto tail uses
  `1 / sqrt(u)` (α = 2) for this reason.
- **Randomness** comes from separate streams per purpose (coins, lobby, fees, each
  trader), so adding a trader never shifts the coin prices.
- **Timing.** The state shown is as of the last *completed* minute. That minute's trades
  are stamped across the following minute and revealed as the clock passes them, so the
  feed trickles in rather than arriving in a batch.
- **Build-time checkpoint.** `vite.config.ts` runs the engine at build time and inlines
  the state (about 140 KB raw, most of the 128 KB gzipped main chunk). Because the maths is
  deterministic this is purely a speed-up: a browser computing from scratch reaches the
  identical state, and a test covers that.
- **Catch-up cost.** About 20 µs a minute on a laptop. Gaps under about 2.8 days replay
  before first paint. Longer gaps replay in chunks behind a "Reading the books" line; 30
  days took 1.3–2 s in headless Chromium. The browser also saves a snapshot to
  `localStorage`, so repeat visits are instant. **Rebuild daily**
  (`.github/workflows/redeploy.yml`) to keep first visits fast.
- **Calibration.** Over a simulated fortnight, `SEASON_START` defaults give about four
  firings a day, a treasury drifting gently up on fee income, a bonus day most days, and
  leaderboard results mostly between −40% and +100%. Most traders are below zero most of
  the time. That's the memecoin premise, not a bug. To make the board greener, lower
  `TRADE_COST` or raise chop drift in `coins.ts`, then bump `VERSION`.
- **Firing rule.** Below −35% since hire, at three consecutive hourly reviews, with a
  three-hour grace period after hiring. The desk sits empty for four minutes, then the
  first name in line is seated. HR prefers methods the floor doesn't already have, so the
  floor doesn't converge on a single strategy (in early tuning it became all snipers).
- **Bonus day** uses a high-water mark: a fifth of profit *above the previous peak*
  moves into the pool at each review, and the pool pays out daily. The split is exact
  integer lamports, with leftover lamports going to the largest remainders, so it always
  sums to the pool. `/firm` shows the last split and its checksum.
- **Visitor hires** run the same code on their own random stream, see the same board,
  and never write to shared state. That includes the "has anyone held this coin" flag
  that feeds the shredder count, and a test checks the shared state is byte-identical
  with and without a hire. One hire per browser. If the saved snapshot is lost, the hire
  is rebuilt exactly by replaying from the hire record.
- **The `PriceSource` interface** (`src/sim/coins.ts`) is the seam for a live price feed.
  A real feed can't be replayed deterministically, so it would change the "same state
  everywhere" guarantee for anything after it's switched on. That's a product decision,
  not a code one. Any such feed must stay read-only.

## Art

- **Isometric visibility constraint.** In a cutaway, content at depth *y* only shows up
  to height *(interior height − (room depth − y))*. The first layout (40 deep, 39 tall)
  hid every back wall and seated trader. Rooms are now 24 deep and 44 tall, traders sit
  at the back facing the viewer, and each trader's chart is on the wall beside them
  rather than behind.
- **Layering** rather than a full depth sort: background, key-coloured animation, seated
  traders, desks, walkers, facade and lot, door, people outside. Animated screens only
  repaint pixels still showing their key colour, so anything standing in front keeps
  covering them.
- **Higher-resolution characters (owner request).** The first version used 13×25
  hand-typed pixel grids, which read as retro. Traders are now drawn from shaded shapes
  (`src/art/figure.ts`) with selective outlines, and the scene rendered at 2× (624×1032; now 3×, see below)
  so the figures have room for faces, lapels and ties. Plants and the cat were redrawn the
  same way. The globe and camera are still upscaled grid props, and
  could be redrawn if they start to look coarse next to the rest.
- **Scaling (deviation from the brief).** The brief asked for nearest-neighbour integer
  upscaling. At 2× native resolution a phone shows fewer than two device pixels per art
  pixel, and nearest-neighbour at ratios like 1.875 makes lines uneven. So the canvas
  matches the device's pixels, stays pixel-exact at whole-number ratios, and otherwise
  resamples with high-quality smoothing. The result looks like finished illustration
  rather than chunky pixels, which is what was asked for.
- **Skyscraper restyle (owner request).** The limestone townhouse became a glass tower on
  Wall Street: a travertine-and-walnut banking-hall lobby with a bronze bull, turnstiles
  and a security desk with its own ticker; LED ticker bands along every slab; black
  trading desks with twin monitors and phone turrets; frosted partitions; a skyline behind
  the glass; the tower continuing above the partner's floor and fading out; a cab, a
  WALL ST sign and a helicopter on a 34-second loop. The scene now renders at three pixels
  per world unit (948×1680, up from 624×1032). In headless Chromium on the build machine
  the page kept animation frames under 30ms while the scene ran at 12 fps; worth a check
  on a low-end phone.
- **Unique traders (owner request).** Every trader gets a build, height, haircut (14),
  facial hair, outfit (7), shirt, neckwear, eyewear and watch (`src/art/traits.ts`). The
  founding eleven are dressed by hand; later hires are dressed from their seed and method
  (quants in turtlenecks, perma-bulls in pinstripes, and so on). This lives in the view
  layer, so the simulation and its checkpoints are untouched. Visitors can choose every
  trait on the hire page.
- **Cocky voice (owner request).** Buy and sell reasons, method blurbs, floor events and
  the partner's lines were rewritten in a Wall Street register ("Printed. Next.", "It's a
  dip."). Traders now cycle through moods at their desks and say things in speech bubbles
  (DOM overlays, so they stay sharp), with fresh trades taking priority. Two bubbles at
  most on phones, five on desktop. `SIM.VERSION` is 12, which clears cached snapshots
  because the stored reason strings changed.
- **Desktop scene size.** The scene used to shrink to fit the viewport height, which made
  traders about 18px tall at 1280×800. It now takes the column's width (up to 640px) and
  scrolls with the page instead of sticking.
- **Custom art** switches off the procedural-only animations (screens, ticker, walking
  paths). See ART_GUIDE.md.
- **Known imperfections:** walkers can overlap a partition edge for a frame or two, and a
  walker crossing the revolving door jumps from behind the facade to in front of it.

## Copy and naming

- All copy is new. The reference's vocabulary is avoided (a search for house, lodger,
  rent, demo and devnet across `src/` comes up empty). The only disclosure is the
  pull-quote under the stats and the footer line.
- **Coin names** are word pairs from invented pools ("Soggy Kettle", "$KETTLE"). Common
  words will inevitably coincide with *some* token somewhere. Well-known memecoin tickers
  are deliberately left out of the pools. Worth a skim by someone who follows the market.
- **Trader names** are common surnames, not references to anyone. The same caveat about
  coincidence applies.
- **Visitor hires** accept a surname of lowercase letters, spaces, hyphens and
  apostrophes (16 characters max), shown only in that browser.

## Accessibility and performance

- axe (WCAG 2.1 AA) passes on every route and on the trader panel, at 390px and 1280px.
- The canvas has a text description. Desks are reachable by keyboard through the desk
  list, which highlights the matching desk in the building. The trader panel traps
  focus, closes on Escape and returns focus afterwards.
- Reduced motion gets one static frame, no pulse, a still hire preview, and the replay
  button is hidden.
- The animation runs at about 12 fps and stops when the tab is hidden or the building is
  scrolled out of view. The clock that drives the page also stops while hidden.
- Secondary routes are code-split. Fonts are self-hosted via `@fontsource` and loaded by
  unicode range.

## Open risks and things not done

- **Not deployed.** This session had no Vercel or Git remote access. `vercel.json` and
  the README steps are ready, but no deploy has been run.
- **Placeholder mint** (`BarryCapXXXX…`): the explorer link goes to a page that doesn't
  exist until a real address is set.
- **Main chunk size** (133 KB gzipped). The checkpoint could move to a parallel chunk,
  loaded behind a skeleton, if first paint on slow networks becomes a concern.
- **Snapshots in `localStorage`** are about 140 KB each. A browser that refuses storage
  just replays from the build checkpoint every visit.
- **Local times.** Times on the page ("hired Mon 2:49 PM") use the viewer's time zone,
  while the season itself is defined in UTC.
