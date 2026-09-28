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
    sprites.json      replaces the procedural character sprites
    *.png             the sheets it lists
```

Reference files, generated from the procedural art with `npm run art`:

| File | What it is |
| --- | --- |
| `docs/building.reference.png` | The full procedural building at native size (312×516), transparent background |
| `docs/building.no-desks.png` | The same without the desks: what `building.png` should contain |
| `docs/foreground.reference.png` | Only the desks: what `foreground.png` should contain |
| `docs/hotspots.example.json` | The procedural building's hotspots, in the exact schema below |

## The building

**`building.png`** is the scene at native resolution: one image pixel per art pixel,
with a transparent background (the page colour shows through). The procedural building
is 312×516. Any size works as long as `hotspots.json` gives the same `width` and `height`.
The site upscales by whole numbers with nearest-neighbour sampling, so draw at 1×. Don't
pre-scale or anti-alias.

Keep the look in the site's palette: warm limestone, navy carpet, walnut, brass, slate.
Suggested colours are in `src/scene/colors.ts`.

**`foreground.png`** (optional) is the same size, and holds anything that should sit in
front of a seated trader, usually the desks. Traders are drawn after `building.png` and
before `foreground.png`. If the desks are painted into `building.png`, the traders will
sit on top of them.

## hotspots.json

```jsonc
{
  "width": 312,            // must match building.png
  "height": 516,
  "desks": [
    {
      "desk": 1,           // 1–11, and 12 for the pencilled-in desk
      "polygon": [[42, 249], [66, 237], [110, 259], [110, 291], [86, 303], [42, 281]],
                           // hit area in image pixels, any simple polygon
      "seat": [56, 264]    // bottom-centre of the seated trader, image pixels
    }
  ],
  "partner": {             // optional: where the managing partner stands, bottom-centre
    "office": [..], "terminal": [..], "review": [..], "compliance": [..],
    "hr": [..], "lobby": [..], "server": [..]
  }
}
```

Coordinates are in image pixels from the top-left corner. Every desk from 1 to 12 should
be listed. Desks that are missing can't be clicked and nobody sits at them.

### What still animates with custom art

- Seated traders (typing, the top performer celebrating, the bottom performer slumped),
  drawn at each `seat`.
- The managing partner, at the `partner` point for the current floor.
- The hover marker and the desk list sync.

The following are procedural-only and switch off with a custom building: the chart
screens, the lobby ticker, server LEDs, steam, the cat, the revolving door, and the
walking paths. "Replay arrival" then brings traders in one by one at their seats, with
no walk.

## Sprites

**`sprites/sprites.json`**

```json
{
  "frameWidth": 15,
  "frameHeight": 25,
  "poses": {
    "stand":     { "src": "stand.png",     "frames": 1 },
    "walk":      { "src": "walk.png",      "frames": 4 },
    "back":      { "src": "back.png",      "frames": 4 },
    "sit":       { "src": "sit.png",       "frames": 3 },
    "celebrate": { "src": "celebrate.png", "frames": 2 },
    "slump":     { "src": "slump.png",     "frames": 2 },
    "box":       { "src": "box.png",       "frames": 4 },
    "backbox":   { "src": "backbox.png",   "frames": 4 }
  }
}
```

Each sheet is one row of frames, left to right, each `frameWidth × frameHeight`. Any pose
left out keeps its procedural version.

| Pose | Used for | Frames |
| --- | --- | --- |
| `stand` | Standing still, facing the viewer | 1 |
| `walk` | Walking toward the viewer | 4: contact, pass, contact, pass |
| `back` | Walking away, back to the viewer | 4 |
| `sit` | Seated behind a desk, typing | 3; frame 2 is hands still |
| `celebrate` | Arms up | 2 |
| `slump` | Head down on the desk | 2 |
| `box` / `backbox` | Carrying a cardboard box, toward and away from the viewer | 4 each |

Sprites anchor at the **bottom centre** of the frame. Seated poses are shorter, so leave
the top rows transparent and keep the seat at the bottom row. At 25px, a character is a
little over half a floor's interior height.

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
| `src/scene/layout.ts` | The building as data: dimensions, floors, desk positions, partner spots |
| `src/scene/building.ts` | Walls, floors, furniture, roof, facade and lot |
| `src/scene/props.ts` | Small pixel props: plants, cat, globe, water tower, portrait |
| `src/scene/sprites.ts` | Character grids and poses |
| `src/scene/colors.ts` | Scene palette |
| `src/art/headshot.ts` | 16×16 headshots used around the site |

One constraint to keep in mind if the building is redrawn: in an isometric cutaway,
anything at depth *y* in a room only shows below height *(interior height − (room depth − y))*,
because the floor above covers the rest. That's why the rooms are shallow (24) and tall
(44), and why the traders sit near the back wall.
