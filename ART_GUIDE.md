# Art guide

The building and the traders are drawn in code by default. Hand-drawn art can replace
either one by dropping files into `public/art/`. Nothing else needs to change. The build
detects which files exist, so missing files are never requested.

```
public/art/
  building.png        replaces the procedural building        (needs hotspots.json)
  hotspots.json       desk hit areas, seat points, partner spots
  foreground.png      optional: drawn in front of seated traders
  sprites/
    sprites.json      replaces procedural trader poses in the building
    *.png             the sheets it lists
```

Reference files, generated from the procedural art with `npm run art`:

| File | What it is |
| --- | --- |
| `docs/building.reference.png` | The full procedural building at native size (948×1680), transparent background |
| `docs/building.no-desks.png` | The same without the desks: what `building.png` should contain |
| `docs/foreground.reference.png` | Only the desks: what `foreground.png` should contain |
| `docs/hotspots.example.json` | The procedural building's hotspots, in the exact schema below |

## The building

**`building.png`** is the scene at native resolution, with a transparent background (the
page colour shows through). The procedural building is laid out on a 948×1680 grid,
three units per world unit, and drawn as vector shapes at the screen's resolution. The
reference PNGs in `docs/` come from the same drawing code run through a pixel buffer, so
their edges are hard and their lettering uses a small pixel font; the site itself is
smooth and uses real fonts. Any size works as long as `hotspots.json` gives the same
`width` and `height`. The site stretches the image to the screen's pixels with smooth
resampling, so painted or anti-aliased art is fine.

Keep the look in the site's palette: a glass-and-steel tower with a travertine and walnut
banking-hall lobby, charcoal carpet tiles, black desks, gold trim and LED ticker bands.
Suggested colours are in `src/scene/colors.ts`.

**`foreground.png`** (optional) is the same size, and holds anything that should sit in
front of a seated trader, usually the desks. Traders are drawn after `building.png` and
before `foreground.png`. If the desks are painted into `building.png`, the traders will
sit on top of them.

## hotspots.json

```jsonc
{
  "width": 948,            // must match building.png
  "height": 1680,
  "desks": [
    {
      "desk": 1,           // 1–11, and 12 for the pencilled-in desk
      "polygon": [[126, 885], [198, 849], [330, 915], [330, 1011], [258, 1047], [126, 981]],
                           // hit area in image pixels, any simple polygon
      "seat": [240, 990]   // bottom-centre of the seated trader, image pixels
    }
  ],
  "partner": {             // optional: where the managing partner stands, bottom-centre
    "office": [..], "terminal": [..], "review": [..], "compliance": [..],
    "hr": [..], "lobby": [..], "server": [..]
  }
}
```

Coordinates are in image pixels from the top-left corner (see `docs/hotspots.example.json`
for the real values). Every desk from 1 to 12 should be listed. Desks that are missing
can't be clicked and nobody sits at them.

### What still animates with custom art

- Seated traders (typing, the top performer celebrating, the bottom performer slumped),
  drawn at each `seat`.
- The managing partner, at the `partner` point for the current floor.
- The hover marker and the desk list sync.

The following are procedural-only and switch off with a custom building: the chart
screens, the LED ticker bands and the security-desk ticker, server LEDs, the helicopter, steam, the cat, the revolving door, and the
walking paths. "Replay arrival" then brings traders in one by one at their seats, with
no walk.

## The traders

By default the traders aren't sprite sheets at all. `src/art/figure.ts` draws them from
shaded shapes (face, hair, jacket and lapels, shirt, tie, arms, legs) and adds a thin
selective outline, supersampled so edges stay smooth at any size: about 85 grid units
tall standing in the building (drawn at the screen's own resolution), larger on the hire
page, and as busts for headshots.

Each trader is dressed by `src/art/traits.ts`: build, height, one of 14 haircuts, facial
hair, outfit (suit, pinstripe, fleece vest, shirtsleeves and braces, waistcoat,
turtleneck and blazer, double-breasted), shirt colour, neckwear, eyewear or headset, and
a watch. The eleven founding traders are dressed by hand in the `ROSTER` table; anyone
hired later is dressed from their seed and method, so the same trader always looks the
same. At their desks, traders cycle through habits (typing, on the phone, leaning back,
pointing at a chart, espresso, stretching, rubbing their eyes, thumbing a phone, lunch,
loosening the tie, chatting to the next desk, standing with hands on hips or arms
folded, celebrating, slumped), weighted by method, the time of day and how their day is
going (`mood()` in `src/scene/actors.ts`). The partner's routines (drink, watch,
putting, standing calls) are in `ROUTINES` in the same file. Changing a haircut, an outfit or
a pose means editing `figure.ts`.

### Replacing poses with hand-drawn sheets

**`sprites/sprites.json`**

```json
{
  "frameWidth": 32,
  "frameHeight": 60,
  "poses": {
    "stand":     { "src": "stand.png",     "frames": 1 },
    "walk":      { "src": "walk.png",      "frames": 8 },
    "back":      { "src": "back.png",      "frames": 8 },
    "sit":       { "src": "sit.png",       "frames": 3 },
    "celebrate": { "src": "celebrate.png", "frames": 2 },
    "slump":     { "src": "slump.png",     "frames": 2 },
    "box":       { "src": "box.png",       "frames": 8 },
    "backbox":   { "src": "backbox.png",   "frames": 8 }
  }
}
```

Each sheet is one row of frames, left to right, each `frameWidth × frameHeight`. Any pose
left out keeps its procedural version. Sheets only affect the building. Headshots and the
hire-page figure always use the procedural renderer.

| Pose | Used for | Frames |
| --- | --- | --- |
| `stand` | Standing still, facing the viewer | 1 |
| `walk` | Walking toward the viewer | any; the procedural cycle uses 8 |
| `back` | Walking away, back to the viewer | any |
| `sit` | Seated behind a desk, typing | 3; frame 2 is hands still |
| `celebrate` | Arms up | 2 |
| `slump` | Head down on the desk | 2 |
| `box` / `backbox` | Carrying a cardboard box, toward and away from the viewer | any |

Sprites anchor at the **bottom centre** of the frame. Seated poses are shorter, so leave
the top rows transparent and keep the seat at the bottom row. A standing trader is about
85px tall, a little under two-thirds of a floor's interior height (132px). Hand-drawn
sheets only cover the original eight poses; the habit poses (`phone`, `leanback`,
`point`, `coffee`, `stretch`, `rub`, `mobile`, `eat`, `tie`, `chat`, `hips`, `arms`,
`watch`, `drink`, `putt`, `call`) stay procedural.

### Key colours

Draw sheets using only these exact colours (no anti-aliasing). Each one is swapped at
runtime for the trader's own skin, hair, suit and tie, so one set of sheets serves every
trader. Any other colour is treated as transparent.

| Key | Slot | | Key | Slot |
| --- | --- | --- | --- | --- |
| `#000000` | outline | | `#000055` | trousers |
| `#ff0000` | skin | | `#ffffff` | shirt |
| `#aa0000` | skin shade | | `#cccccc` | shirt shade |
| `#00ff00` | hair | | `#ffff00` | tie |
| `#aaffaa` | hair highlight | | `#aaaa00` | tie shade |
| `#0000ff` | suit | | `#333333` | eyes |
| `#0000aa` | suit shade | | `#ff66ff` | mouth |
| `#6666ff` | lapel highlight | | `#555555` | shoes |
| `#ffaa00` | glasses (the partner) | | `#aa5500` / `#773300` / `#ffddaa` | box / box shade / tape |

The mapping lives in `src/scene/artswap.ts` (`SPRITE_KEYS`) if a different key palette
suits the artist better.

## Where the procedural art lives

| File | Contents |
| --- | --- |
| `src/art/figure.ts` | The character renderer: shapes, poses, shading, outline, busts |
| `src/art/traits.ts` | Who wears what: the hand-dressed roster and the seeded wardrobe |
| `src/art/props.ts` | Plants, the cat, the bronze bull, globe, camera, bell and helicopter, drawn the same way |
| `src/scene/layout.ts` | The building as data: scale, dimensions, floors, desk positions, partner spots |
| `src/scene/building.ts` | Walls, floors, furniture, the tower above, facade and street |
| `src/scene/surface.ts` | Where drawing goes: canvas paths in the browser, a pixel buffer in Node |
| `src/scene/renderer.ts` | Layer order, caching and the per-frame composite |
| `src/scene/sprites.ts` | Sprite cache and the loader for hand-drawn sheets |
| `src/scene/colors.ts` | Scene palette |

One constraint to keep in mind if the building is redrawn: in an isometric cutaway,
anything at depth *y* in a room only shows below height *(interior height − (room depth − y))*,
because the floor above covers the rest. That's why the rooms are shallow (24 units) and
tall (44), and why the traders sit near the back wall.
