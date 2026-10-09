# Investors: trait layers

Layers for the Investors collection, drawn by the same renderer as the traders on the site and finished with a retro filter. Each bust is drawn on an 80×80 pixel grid and scaled to 1024×1024 with nearest-neighbour, ready for a 1024 canvas.

Every file is a **1024×1024 transparent PNG** on the same frame, so the layers stack with no offsets. If you resize them, use nearest-neighbour scaling (in Photoshop: "Nearest Neighbor (hard edges)"), otherwise the pixels blur.

## Stack order

Stack one file from each folder, lowest number at the bottom:

| # | Folder | Required | Options |
|---|---|---|---|
| 1 | `01-background` | yes | 15 (8 colours, 7 rooms of the building) |
| 2 | `02-chart` | optional | 7 price charts behind the Investor |
| 3 | `03-shadow` | yes | 1 (the cast shadow that gives depth) |
| 4 | `04-hair-back` | when it exists | matches the hair |
| 5 | `05-neck` | yes | 6 skins |
| 6 | `06-outfit` | yes | 16 |
| 7 | `07-head` | yes | 6 skins |
| 8 | `08-facial-hair` | optional | 4 styles × 7 colours |
| 9 | `09-expression` | yes | 8 |
| 10 | `10-hair` | yes | 14 styles × 7 colours |
| 11 | `11-eyewear` | optional | 5 |
| 12 | `12-accessory` | optional | cigar |
| 13 | `13-frame` | optional | 5: two ticker strips, a breaking banner, an ink border, a gold stock-certificate edge |
| 14 | `14-finish` | optional | 3: dithered vignette, CRT scanlines, film grain |

## Rules that keep it looking right

- **Charts go on plain colour backgrounds only.** The rooms are already busy.

- **Hair back and hair share a file name.** If you pick `08-hair/long-auburn.png`, also use `02-hair-back/long-auburn.png`. Bald has no back file, so skip that layer for it.
- **Neck and head use the same skin.** For example `03-neck/skin-4.png` goes with `05-head/skin-4.png`.
- **Facial hair should match the hair colour.** `short-beard-grey` goes with grey hair, and so on.
- **No cigar with `shouting`** (the mouth is wide open) **or with `headset`** (the mouthpiece is in the way).
- `stubble-*` and some `07-expression` pixels are semi-transparent on purpose, so one file works on every skin. Your tool needs to blend alpha (any normal PNG compositing does).

Suggested rarity weights are in `RARITY.md`. `preview.png` shows twelve random stacks and `catalog.png` shows every option.

## Remaking the layers

All of this comes from code, so it can be regenerated or extended:

```
npm run art -- nft-layers
```

This rewrites `nft/layers/`, `preview.png`, `catalog.png` and `layers/counts.json`. To add or change options, edit the lists at the top of `scripts/nft-layers.art.ts`: backgrounds, outfits, expressions and eyewear. Hairstyles, hair colours and skins come from `src/art/palette.ts`, the same lists the site uses.
