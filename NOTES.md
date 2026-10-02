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
- **Calibration.** Under the worst-goes rule a simulated week gives 24 firings a day (one
  per review), top traders who keep their desks for three or four days, and a treasury
  that drifts between about 90 and 115 SOL, because every firing closes the worst book
  at a loss. Leaderboard results run from about −40% to +200%. Most traders are below zero most of
  the time. That's the memecoin premise, not a bug. To make the board greener, lower
  `TRADE_COST` or raise chop drift in `coins.ts`, then bump `VERSION`.
- **Firing rule (owner's concept).** Every hourly review, the trader with the worst result
  since hire is let go and everyone else keeps their desk, so the best performers stay
  as long as they stay ahead of someone. New hires skip reviews for their first three
  hours, so they're judged on more than a handful of trades, and nobody is fired unless
  at least three desks are up for review (`REVIEW_MIN`). The worst performer goes even
  if they're up; it's a ranking, not a threshold. Ties go against the smaller book. This
  replaced the earlier "−35% at three reviews in a row" rule and its strikes. The desk
  sits empty for four minutes, then the first name in line is seated. The desk list,
  payroll and trader files show who's top, who's next out and when the next review is.
  `SIM.VERSION` is 14. HR prefers methods the floor doesn't already have, so the
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
- **Layering** rather than a full depth sort: background, screens and tickers, seated
  traders, desks, desk monitors, walkers, facade and street, door, people outside,
  helicopter. Each animated screen is drawn clipped to its own glass. That works because
  nothing static sits in front of a screen (the lobby palm was moved to keep it that way);
  if new furniture ever covers one, it will need a mask.
- **Higher-resolution characters (owner request).** The first version used 13×25
  hand-typed pixel grids, which read as retro. Traders are now drawn from shaded shapes
  (`src/art/figure.ts`) with selective outlines, and the scene rendered at 2× (624×1032; now 3×, see below)
  so the figures have room for faces, lapels and ties. Plants and the cat were redrawn the
  same way. The globe and camera are still upscaled grid props, and
  could be redrawn if they start to look coarse next to the rest.
- **Vector renderer (owner request: "too retro").** The scene used to be rasterised into
  a pixel buffer and scaled up, which kept stair-stepped edges and a 3×5 pixel font on
  the signs. It is now drawn with canvas paths at the screen's own resolution:
  anti-aliased shapes, real fonts (EB Garamond on the lobby sign, JetBrains Mono on the
  tickers and desk plates, Inter Tight on the street sign), soft contact shadows under
  people and a little shading where floors meet walls. Characters and painted props
  (plants, the bull, globe, camera, bell, cat, helicopter) are supersampled 2–3× and
  box-filtered, with an outline one final pixel wide. This departs from the brief's
  "pixel art, nearest-neighbour" instruction; it's what was asked for since.
  Measured in headless Chromium: the static layers build in about 220–330 ms, a normal
  frame takes 1–2 ms of script time, and poses are pre-rendered in idle time so a new
  pose doesn't stutter. Still worth a check on a low-end phone.
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
- **No dialogue (owner request).** The speech bubbles were removed, along with the
  first-person trade quips. Trade notes are now short third-person desk notes built from
  the numbers that triggered them ("Biggest gainer this hour, +42%.", "Stop-loss hit.").
- **Mannerisms (owner request).** Twelve new poses: stretching, rubbing eyes, thumbing a
  phone, lunch at the desk, loosening the tie, chatting to the next desk, hands on hips,
  arms folded, checking a watch, a whisky, putting, a standing phone call. Desk habits are
  weighted by method, local time of day (lunch around noon, more stretching after five)
  and how the day is going; a fresh trade puts the trader on the phone. Every 14 seconds
  or so someone may go for a coffee (second floor) or take the lift and come back. The
  partner has a looping routine on each floor instead of pacing.
- **Desktop scene size.** The scene used to shrink to fit the viewport height, which made
  traders about 18px tall at 1280×800. It now takes the column's width (up to 640px) and
  scrolls with the page instead of sticking.
- **Custom art** switches off the procedural-only animations (screens, ticker, walking
  paths). See ART_GUIDE.md.
- **Known imperfections:** walkers can overlap a partition edge for a frame or two, and a
  walker crossing the revolving door jumps from behind the facade to in front of it.

## Copy and naming

- **Renamed to Steve’s Investors (owner request).** The partner is Steve. Trader names
  and coin tickers are lists the owner supplied (`TRADER_NAMES`, `COINS` in
  `src/sim/names.ts`). Founders, hires and replacements are drawn from the names at
  random, never two at once, and recently fired names are avoided while others are free.
  Six tickers from the owner's list were left out as slurs or hateful references
  ($NIGINU, $retard, $Nazcat, $GAYOL, $hiv, $KDiddy). Many trader names look like real
  crypto accounts, so the site shows invented trades and firings under real handles;
  the footer line saying trades aren't real matters more now. `SIM.VERSION` is 17.

- All copy is new. The reference's vocabulary is avoided (a search for house, lodger,
  rent, demo and devnet across `src/` comes up empty).
- **Plain voice (owner request).** Copy was rewritten to read like a person wrote it:
  plain sentences, fewer quips, no clever rule-of-three lines. "AI traders" became "SI
  traders" throughout.
- **Disclosures (flagged).** The owner asked for all the simulation text to go. The
  pull-quote under the stats and the "simulated" wording are gone. One plain line stays
  in the footer: "Prices, balances and trades on this site aren’t real. Not financial
  advice." Once the tickers became real coins, the site shows made-up prices for real
  tokens next to a contract-address card and a treasury figure, and without that line a
  visitor could reasonably read them as real. It's one string (`FOOTER_NOTE` in
  `src/copy.ts`) if the owner wants to change it.
- **Coin tickers are real (owner request).** About thirty well-known Solana memecoins
  (BONK, WIF, PENGU, POPCAT, FARTCOIN and others; list in `src/sim/names.ts`, taken from
  public market-cap rankings in September 2026). Coins named after real people (TRUMP,
  MELANIA, BODEN) are left out, in line with the brief's no-jokes-about-real-people rule.
  Their prices, charts and crashes on the site are invented; the "crash" event says the
  coin dropped, not that anyone rugged it. The list will date; refresh it now and then.
  `SIM.VERSION` is 13 because the coins and trade notes changed, which clears cached
  snapshots.
- **Trader names** are common surnames, not references to anyone. The same caveat about
  coincidence applies.
- **Visitor hires** accept a surname of lowercase letters, spaces, hyphens and
  apostrophes (16 characters max), shown only in that browser.
- **Wallet address on the hire page (owner request).** Optional. A public Solana address
  is checked (base58, decodes to 32 bytes) and hashed into a trader: look, method, risk,
  patience and a suggested name. The same wallet always makes the same trader. The
  address is saved with the hire in `localStorage` and shown on the employee file with a
  read-only explorer link. Nothing connects to a wallet, signs, or sends the address
  anywhere. Recovery phrases (12+ words), 64-byte keys and JSON key arrays are
  recognised, refused and cleared from the field with a warning.

## Accessibility and performance

- axe (WCAG 2.1 AA) passes on every route and on the trader panel, at 390px and 1280px.
- The canvas has a text description. Desks are reachable by keyboard through the desk
  list, which highlights the matching desk in the building. The trader panel traps
  focus, closes on Escape and returns focus afterwards.
- Reduced motion gets one static frame, no pulse, a still hire preview, and the replay
  button is hidden.
- The animation runs at about 15 fps and stops when the tab is hidden or the building is
  scrolled out of view. The clock that drives the page also stops while hidden.
- Secondary routes are code-split. Fonts are self-hosted via `@fontsource` and loaded by
  unicode range.

## Open risks and things not done

- **Deploys.** The GitHub repository is linked to the Vercel project `barry-capital-3`
  (barry-capital-3.vercel.app). Every push to `main` builds and publishes the site.
- **Placeholder mint** (`StevesInvXXXX…`): the explorer link goes to a page that doesn't
  exist until a real address is set.
- **Main chunk size** (133 KB gzipped). The checkpoint could move to a parallel chunk,
  loaded behind a skeleton, if first paint on slow networks becomes a concern.
- **Snapshots in `localStorage`** are about 140 KB each. A browser that refuses storage
  just replays from the build checkpoint every visit.
- **Local times.** Times on the page ("hired Mon 2:49 PM") use the viewer's time zone,
  while the season itself is defined in UTC.
