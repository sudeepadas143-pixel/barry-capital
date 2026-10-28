# Cycle engine CY-1: results (EXPLORATORY)

Review mode `self_audited_exploration_only`; config `reports/CYCLE_CONFIG.md` (frozen); run at `4e1fed5`. All data was examined in earlier studies: nothing here is independent confirmation. Test periods: 1W ≥ 2016, 1D ≥ 2020, 4H/1H ≥ 2022.

## Primary verdicts (Holm over 8 TF × direction lift tests of the shipped model's zone onsets)

| TF · dir | verdict | lift | Holm p | zone precision* | B_ext precision* (matched rate) |
|---|---|---:|---:|---:|---:|
| 4H|top | **NOT SUPPORTED** | 1.17 | 0.2888 | 0.414 | 0.414 |
| 1W|bot | **NOT SUPPORTED** | 1.78 | 0.2940 | 0.432 | 0.439 |
| 1D|bot | **NOT SUPPORTED** | 1.31 | 0.5490 | 0.288 | 0.313 |
| 1D|top | **NOT SUPPORTED** | 1.10 | 1.0000 | 0.252 | 0.256 |
| 1H|top | **NOT SUPPORTED** | 1.01 | 1.0000 | 0.429 | 0.330 |
| 1W|top | **NOT SUPPORTED** | 0.94 | 1.0000 | 0.212 | 0.227 |
| 4H|bot | **NOT SUPPORTED** | 0.96 | 1.0000 | 0.352 | 0.383 |
| 1H|bot | **NOT SUPPORTED** | 0.77 | 1.0000 | 0.304 | 0.303 |

## 1W (86 instruments, 74 with volume)

* selection top|vol: core **L_mom**; val AP {"B_ext": 0.2353, "B_rsi": 0.2289, "B_rng": 0.1999, "L_price": 0.2475, "L_mom": 0.2621, "L_vol": 0.2671, "L_int": 0.2652} (base rate 0.1285); G_ref 0.28716805240632337; context {"htf_rng": {"ap_without": 0.2620707253047102, "ap_with": 0.26193960049060794, "kept": false, "rows": 18001}, "breadth": {"ap_without": 0.26132621433277375, "ap_with": 0.2626427537274659, "kept": false, "rows": 18001}}; θ calibration {"target_onsets_per_asset_year": 0.589, "achieved": 0.591, "events_per_asset_year": 0.295}
* selection top|novol: core **L_mom**; val AP {"B_ext": 0.2141, "B_rsi": 0.2051, "B_rng": 0.1884, "L_price": 0.2236, "L_mom": 0.236} (base rate 0.1166); G_ref None; context {"htf_rng": {"ap_without": 0.2360105002286741, "ap_with": 0.23632200660330713, "kept": false, "rows": 21757}, "breadth": {"ap_without": 0.23498617184924106, "ap_with": 0.2341841849593374, "kept": false, "rows": 21757}}; θ calibration {"target_onsets_per_asset_year": 0.576, "achieved": 0.575, "events_per_asset_year": 0.288}
* selection bot|vol: core **L_mom**; val AP {"B_ext": 0.2583, "B_rsi": 0.252, "B_rng": 0.2314, "L_price": 0.265, "L_mom": 0.2728, "L_vol": 0.2734, "L_int": 0.2757} (base rate 0.1010); G_ref 0.2939621116321493; context {"htf_rng": {"ap_without": 0.2727501346441139, "ap_with": 0.2681403364521796, "kept": false, "rows": 18001}, "breadth": {"ap_without": 0.2726962188627615, "ap_with": 0.26760385400048553, "kept": false, "rows": 18001}}; θ calibration {"target_onsets_per_asset_year": 0.471, "achieved": 0.471, "events_per_asset_year": 0.236}
* selection bot|novol: core **L_price**; val AP {"B_ext": 0.2467, "B_rsi": 0.2407, "B_rng": 0.2238, "L_price": 0.2564, "L_mom": 0.2619} (base rate 0.0983); G_ref None; context {"htf_rng": {"ap_without": 0.25644415561438527, "ap_with": 0.25474834786421274, "kept": false, "rows": 21757}, "breadth": {"ap_without": 0.2563158375525621, "ap_with": 0.25218727999743834, "kept": false, "rows": 21757}}; θ calibration {"target_onsets_per_asset_year": 0.47, "achieved": 0.468, "events_per_asset_year": 0.235}

| dir · model | events | alerts | recall | precision* | FA/asset-yr | lead med | lift | excess [CI] (p, G) |
|---|---:|---:|---|---:|---:|---:|---:|---|
| top · SHIPPED | 245 | 440 | 0.380 | 0.212 | 0.43 | 2 | 0.94 | -0.0138 [-0.0885, +0.0609] (0.6534, 10) |
| top · B_ext | 245 | 401 | 0.367 | 0.227 | 0.38 | 4 | 0.98 | -0.0042 [-0.0880, +0.0797] (0.5468, 10) |
| top · B_rsi | 245 | 397 | 0.416 | 0.260 | 0.36 | 2 | 1.11 | +0.0264 [-0.0459, +0.0987] (0.2365, 10) |
| top · B_rng | 245 | 384 | 0.294 | 0.189 | 0.38 | 4 | 0.88 | -0.0262 [-0.1034, +0.0509] (0.7623, 10) |
| top · L_price | 245 | 442 | 0.367 | 0.205 | 0.43 | 2 | 0.93 | -0.0148 [-0.0883, +0.0587] (0.6619, 10) |
| top · L_mom | 245 | 426 | 0.384 | 0.222 | 0.41 | 2 | 0.99 | -0.0016 [-0.0749, +0.0716] (0.5199, 10) |
| top · L_vol | 217 | 399 | 0.419 | 0.229 | 0.45 | 2 | 0.98 | -0.0037 [-0.0841, +0.0768] (0.5396, 10) |
| top · L_int | 217 | 407 | 0.447 | 0.242 | 0.44 | 2 | 1.07 | +0.0156 [-0.0625, +0.0937] (0.3340, 10) |
| bot · SHIPPED | 253 | 398 | 0.676 | 0.432 | 0.28 | 3 | 1.78 | +0.1899 [+0.0075, +0.3724] (0.0420, 10) |
| bot · B_ext | 253 | 394 | 0.672 | 0.439 | 0.27 | 3 | 1.86 | +0.2077 [+0.0209, +0.3944] (0.0425, 10) |
| bot · B_rsi | 253 | 394 | 0.664 | 0.433 | 0.27 | 2 | 1.86 | +0.2036 [+0.0311, +0.3762] (0.0277, 10) |
| bot · B_rng | 253 | 376 | 0.443 | 0.300 | 0.32 | 2 | 1.29 | +0.0683 [-0.0458, +0.1825] (0.1478, 10) |
| bot · L_price | 253 | 394 | 0.676 | 0.435 | 0.28 | 2 | 1.80 | +0.1945 [+0.0088, +0.3802] (0.0479, 10) |
| bot · L_mom | 253 | 384 | 0.660 | 0.437 | 0.27 | 3 | 1.79 | +0.1936 [+0.0091, +0.3781] (0.0453, 10) |
| bot · L_vol | 225 | 330 | 0.653 | 0.448 | 0.26 | 2 | 1.77 | +0.1961 [-0.0168, +0.4090] (0.0775, 10) |
| bot · L_int | 225 | 326 | 0.644 | 0.446 | 0.26 | 3 | 1.75 | +0.1919 [-0.0269, +0.4107] (0.0843, 10) |

| dir | alert | events | alerts | recall | precision* | FA/asset-yr | lead med (candles) | MFE / MAE med (ATR) | net ret mean / med (2× cost mean) |
|---|---|---:|---:|---|---:|---:|---:|---|---|
| top | zone | 245 | 440 | 0.380 | 0.212 | 0.43 | 2 | 1.48 / 2.08 | -0.0264 / -0.0179 (–) |
| top | developing | 245 | 411 | 0.396 | 0.238 | 0.39 | 0 | – / – | – / – (–) |
| top | confirmed | 245 | 194 | 0.327 | 0.412 | 0.14 | -5 | 1.31 / 2.30 | -0.0483 / -0.0354 (-0.0489) |
| top | confirmed vs matched baselines (precision* / recall) | | | | | | | | htf_flip: 0.425 / 0.065; ema_cross: 0.530 / 0.156; supertrend_flip: 0.511 / 0.314; counter_reversal: 0.485 / 0.284 |
| top | shipped − B_ext near-rate (matched rate) | | | | | | | | {"clusters": 10, "delta": -0.023271367036953094, "ci95": [-0.0656593720035743, 0.019116637929668105], "p_wild": 0.8666} |
| top | by_class (near vs bench) | | | | | | | | bond: 0.164 vs 0.227 (n 55); commodity: 0.277 vs 0.231 (n 47); crypto: 0.400 vs 0.325 (n 25); equity: 0.198 vs 0.234 (n 167); equity_index: 0.187 vs 0.206 (n 123); fx: 0.261 vs 0.187 (n 23) |
| top | by_era (near vs bench) | | | | | | | | early: 0.219 vs 0.228 (n 260); late: 0.206 vs 0.226 (n 180) |
| top | by_vol (near vs bench) | | | | | | | | high: 0.265 vs 0.208 (n 68); low: 0.221 vs 0.230 (n 249); mid: 0.171 vs 0.233 (n 123) |
| bot | zone | 253 | 398 | 0.676 | 0.432 | 0.28 | 3 | 1.99 / 1.23 | +0.0579 / +0.0331 (–) |
| bot | developing | 253 | 389 | 0.672 | 0.440 | 0.27 | -1 | – / – | – / – (–) |
| bot | confirmed | 253 | 267 | 0.526 | 0.498 | 0.17 | -5 | 1.78 / 1.07 | +0.0250 / +0.0163 (+0.0244) |
| bot | confirmed vs matched baselines (precision* / recall) | | | | | | | | htf_flip: 0.433 / 0.219; ema_cross: 0.644 / 0.272; supertrend_flip: 0.575 / 0.458; counter_reversal: 0.514 / 0.268 |
| bot | shipped − B_ext near-rate (matched rate) | | | | | | | | {"clusters": 10, "delta": -0.014565211846032211, "ci95": [-0.07431034696716102, 0.04517992327509659], "p_wild": 0.7069} |
| bot | by_class (near vs bench) | | | | | | | | bond: 0.510 vs 0.332 (n 51); commodity: 0.293 vs 0.214 (n 58); crypto: 0.269 vs 0.214 (n 26); equity: 0.472 vs 0.231 (n 123); equity_index: 0.587 vs 0.286 (n 75); fx: 0.323 vs 0.194 (n 65) |
| bot | by_era (near vs bench) | | | | | | | | early: 0.542 vs 0.244 (n 179); late: 0.347 vs 0.245 (n 219) |
| bot | by_vol (near vs bench) | | | | | | | | high: 0.462 vs 0.236 (n 253); low: 0.452 vs 0.281 (n 62); mid: 0.337 vs 0.245 (n 83) |

## 1D (108 instruments, 96 with volume)

* selection top|vol: core **L_mom**; val AP {"B_ext": 0.1991, "B_rsi": 0.1844, "B_rng": 0.1924, "L_price": 0.2066, "L_mom": 0.2118, "L_vol": 0.2137, "L_int": 0.2143} (base rate 0.1285); G_ref 0.28653020748125246; context {"htf_rng": {"ap_without": 0.21013051178513067, "ap_with": 0.2103502905171751, "kept": false, "rows": 67502}, "breadth": {"ap_without": 0.20944569687922807, "ap_with": 0.20937362869906329, "kept": false, "rows": 68838}}; θ calibration {"target_onsets_per_asset_year": 1.372, "achieved": 1.371, "events_per_asset_year": 0.686}
* selection top|novol: core **L_price**; val AP {"B_ext": 0.1962, "B_rsi": 0.1805, "B_rng": 0.1895, "L_price": 0.2045, "L_mom": 0.2099} (base rate 0.1181); G_ref None; context {"htf_rng": {"ap_without": 0.20377604087855594, "ap_with": 0.20385607999537989, "kept": false, "rows": 79985}, "breadth": {"ap_without": 0.2031463220960273, "ap_with": 0.20268824141677458, "kept": false, "rows": 81285}}; θ calibration {"target_onsets_per_asset_year": 1.304, "achieved": 1.307, "events_per_asset_year": 0.652}
* selection bot|vol: core **L_price**; val AP {"B_ext": 0.3888, "B_rsi": 0.3139, "B_rng": 0.3372, "L_price": 0.4105, "L_mom": 0.4077, "L_vol": 0.4106, "L_int": 0.4125} (base rate 0.1163); G_ref 0.46765671638654044; context {"htf_rng": {"ap_without": 0.41641045053264647, "ap_with": 0.4177756372513201, "kept": false, "rows": 67502}, "breadth": {"ap_without": 0.40631232587354454, "ap_with": 0.40673245052194584, "kept": false, "rows": 68838}}; θ calibration {"target_onsets_per_asset_year": 1.14, "achieved": 1.145, "events_per_asset_year": 0.57}
* selection bot|novol: core **L_price**; val AP {"B_ext": 0.3646, "B_rsi": 0.284, "B_rng": 0.3099, "L_price": 0.3897, "L_mom": 0.3858} (base rate 0.1086); G_ref None; context {"htf_rng": {"ap_without": 0.3979819302829774, "ap_with": 0.3981015807668434, "kept": false, "rows": 79985}, "breadth": {"ap_without": 0.38973918430061116, "ap_with": 0.39010013513995706, "kept": false, "rows": 81285}}; θ calibration {"target_onsets_per_asset_year": 1.112, "achieved": 1.11, "events_per_asset_year": 0.556}

| dir · model | events | alerts | recall | precision* | FA/asset-yr | lead med | lift | excess [CI] (p, G) |
|---|---:|---:|---|---:|---:|---:|---:|---|
| top · SHIPPED | 424 | 701 | 0.413 | 0.252 | 0.78 | 9 | 1.10 | +0.0245 [-0.0438, +0.0929] (0.2346, 25) |
| top · B_ext | 424 | 740 | 0.441 | 0.256 | 0.82 | 10 | 1.14 | +0.0323 [-0.0336, +0.0982] (0.1652, 25) |
| top · B_rsi | 424 | 954 | 0.491 | 0.221 | 1.11 | 10 | 1.19 | +0.0362 [-0.0187, +0.0912] (0.0964, 25) |
| top · B_rng | 424 | 210 | 0.106 | 0.215 | 0.25 | 10 | 0.94 | -0.0131 [-0.0711, +0.0449] (0.6775, 25) |
| top · L_price | 424 | 625 | 0.373 | 0.256 | 0.69 | 9 | 1.07 | +0.0168 [-0.0499, +0.0834] (0.3037, 25) |
| top · L_mom | 424 | 718 | 0.417 | 0.248 | 0.81 | 6 | 1.09 | +0.0209 [-0.0464, +0.0881] (0.2682, 25) |
| top · L_vol | 404 | 678 | 0.423 | 0.254 | 0.85 | 7 | 1.09 | +0.0208 [-0.0496, +0.0912] (0.2737, 25) |
| top · L_int | 404 | 676 | 0.423 | 0.256 | 0.85 | 5 | 1.09 | +0.0226 [-0.0474, +0.0925] (0.2559, 25) |
| bot · SHIPPED | 451 | 931 | 0.588 | 0.288 | 0.99 | 7 | 1.31 | +0.0700 [-0.0275, +0.1675] (0.0915, 26) |
| bot · B_ext | 451 | 865 | 0.583 | 0.313 | 0.87 | 4 | 1.45 | +0.1039 [+0.0007, +0.2071] (0.0371, 26) |
| bot · B_rsi | 451 | 885 | 0.545 | 0.286 | 0.92 | 6 | 1.38 | +0.0838 [-0.0141, +0.1818] (0.0547, 26) |
| bot · B_rng | 451 | 656 | 0.408 | 0.287 | 0.69 | 9 | 1.31 | +0.0722 [-0.0375, +0.1819] (0.1182, 25) |
| bot · L_price | 451 | 889 | 0.572 | 0.293 | 0.94 | 7 | 1.33 | +0.0739 [-0.0283, +0.1761] (0.0896, 26) |
| bot · L_mom | 451 | 912 | 0.605 | 0.301 | 0.95 | 8 | 1.35 | +0.0791 [-0.0114, +0.1695] (0.0510, 26) |
| bot · L_vol | 429 | 865 | 0.611 | 0.305 | 1.01 | 7 | 1.30 | +0.0718 [-0.0164, +0.1599] (0.0639, 26) |
| bot · L_int | 429 | 857 | 0.608 | 0.307 | 1.00 | 7 | 1.30 | +0.0713 [-0.0181, +0.1607] (0.0672, 26) |

| dir | alert | events | alerts | recall | precision* | FA/asset-yr | lead med (candles) | MFE / MAE med (ATR) | net ret mean / med (2× cost mean) |
|---|---|---:|---:|---|---:|---:|---:|---|---|
| top | zone | 424 | 701 | 0.413 | 0.252 | 0.78 | 9 | 2.42 / 3.15 | -0.0338 / -0.0058 (–) |
| top | developing | 424 | 680 | 0.413 | 0.260 | 0.75 | 5 | – / – | – / – (–) |
| top | confirmed | 424 | 587 | 0.328 | 0.237 | 0.67 | -6 | 2.47 / 2.62 | -0.0100 / -0.0012 (-0.0109) |
| top | confirmed vs matched baselines (precision* / recall) | | | | | | | | htf_flip: 0.290 / 0.084; ema_cross: 0.458 / 0.273; supertrend_flip: 0.293 / 0.341; counter_reversal: 0.295 / 0.315 |
| top | shipped − B_ext near-rate (matched rate) | | | | | | | | {"clusters": 25, "delta": -0.008013648455873823, "ci95": [-0.05409372441338588, 0.03806642750163823], "p_wild": 0.6357} |
| top | by_class (near vs bench) | | | | | | | | bond: 0.292 vs 0.263 (n 65); commodity: 0.337 vs 0.326 (n 86); crypto: 0.212 vs 0.135 (n 160); equity: 0.267 vs 0.253 (n 206); equity_index: 0.263 vs 0.275 (n 152); fx: 0.125 vs 0.096 (n 32) |
| top | by_era (near vs bench) | | | | | | | | early: 0.245 vs 0.235 (n 380); late: 0.274 vs 0.232 (n 321) |
| top | by_vol (near vs bench) | | | | | | | | high: 0.249 vs 0.210 (n 169); low: 0.261 vs 0.240 (n 348); mid: 0.261 vs 0.244 (n 184) |
| bot | zone | 451 | 931 | 0.588 | 0.288 | 0.99 | 7 | 2.37 / 1.93 | +0.0254 / +0.0056 (–) |
| bot | developing | 451 | 888 | 0.590 | 0.305 | 0.91 | 7 | – / – | – / – (–) |
| bot | confirmed | 451 | 854 | 0.488 | 0.258 | 0.95 | -7 | 2.47 / 2.35 | +0.0083 / -0.0037 (+0.0072) |
| bot | confirmed vs matched baselines (precision* / recall) | | | | | | | | htf_flip: 0.354 / 0.198; ema_cross: 0.438 / 0.449; supertrend_flip: 0.331 / 0.491; counter_reversal: 0.308 / 0.490 |
| bot | shipped − B_ext near-rate (matched rate) | | | | | | | | {"clusters": 26, "delta": -0.036574508111732684, "ci95": [-0.0771460665030375, 0.003997050279572131], "p_wild": 0.9638} |
| bot | by_class (near vs bench) | | | | | | | | bond: 0.397 vs 0.319 (n 58); commodity: 0.314 vs 0.235 (n 86); crypto: 0.273 vs 0.237 (n 421); equity: 0.323 vs 0.236 (n 192); equity_index: 0.333 vs 0.217 (n 87); fx: 0.241 vs 0.106 (n 87) |
| bot | by_era (near vs bench) | | | | | | | | early: 0.270 vs 0.230 (n 511); late: 0.331 vs 0.225 (n 420) |
| bot | by_vol (near vs bench) | | | | | | | | high: 0.265 vs 0.220 (n 471); low: 0.321 vs 0.236 (n 212); mid: 0.339 vs 0.236 (n 248) |

## 4H (108 instruments, 96 with volume)

* selection top|vol: core **B_ext**; val AP {"B_ext": 0.2295, "B_rsi": 0.2026, "B_rng": 0.2168, "L_price": 0.2292, "L_mom": 0.2352, "L_vol": 0.2341, "L_int": 0.2341} (base rate 0.1430); G_ref 0.2760744773103787; context {}; θ calibration {"target_onsets_per_asset_year": 6.852, "achieved": 6.841, "events_per_asset_year": 3.426}
* selection top|novol: core **B_ext**; val AP {"B_ext": 0.2295, "B_rsi": 0.2026, "B_rng": 0.2168, "L_price": 0.2292, "L_mom": 0.2351} (base rate 0.1430); G_ref None; context {}; θ calibration {"target_onsets_per_asset_year": 6.852, "achieved": 6.841, "events_per_asset_year": 3.426}
* selection bot|vol: core **L_price**; val AP {"B_ext": 0.3026, "B_rsi": 0.2277, "B_rng": 0.3387, "L_price": 0.3615, "L_mom": 0.3625, "L_vol": 0.3608, "L_int": 0.359} (base rate 0.1365); G_ref 0.4382244084966436; context {"htf_rng": {"ap_without": 0.35951764729091157, "ap_with": 0.3709965082267, "kept": true, "rows": 77682}}; θ calibration {"target_onsets_per_asset_year": 7.498, "achieved": 7.38, "events_per_asset_year": 3.749}
* selection bot|novol: core **L_price**; val AP {"B_ext": 0.3026, "B_rsi": 0.2277, "B_rng": 0.3387, "L_price": 0.3618, "L_mom": 0.363} (base rate 0.1365); G_ref None; context {"htf_rng": {"ap_without": 0.35951764729091157, "ap_with": 0.3709965082267, "kept": true, "rows": 77682}}; θ calibration {"target_onsets_per_asset_year": 7.498, "achieved": 7.38, "events_per_asset_year": 3.749}

| dir · model | events | alerts | recall | precision* | FA/asset-yr | lead med | lift | excess [CI] (p, G) |
|---|---:|---:|---|---:|---:|---:|---:|---|
| top · SHIPPED | 864 | 1216 | 0.558 | 0.414 | 2.16 | 13 | 1.17 | +0.0642 [-0.0053, +0.1337] (0.0361, 29) |
| top · B_ext | 864 | 1216 | 0.558 | 0.414 | 2.16 | 13 | 1.17 | +0.0642 [-0.0053, +0.1337] (0.0361, 29) |
| top · B_rsi | 864 | 1044 | 0.446 | 0.378 | 2.01 | 14 | 1.09 | +0.0326 [-0.0325, +0.0978] (0.1549, 29) |
| top · B_rng | 864 | 1274 | 0.532 | 0.374 | 2.45 | 16 | 1.06 | +0.0213 [-0.0460, +0.0885] (0.2620, 29) |
| top · L_price | 864 | 1226 | 0.565 | 0.405 | 2.28 | 13 | 1.12 | +0.0429 [-0.0299, +0.1158] (0.1150, 28) |
| top · L_mom | 864 | 1284 | 0.615 | 0.422 | 2.31 | 10 | 1.17 | +0.0630 [-0.0077, +0.1337] (0.0424, 28) |
| top · L_vol | 767 | 1100 | 0.610 | 0.436 | 2.13 | 10 | 1.22 | +0.0813 [+0.0000, +0.1625] (0.0272, 28) |
| top · L_int | 767 | 1122 | 0.625 | 0.440 | 2.15 | 9 | 1.24 | +0.0880 [+0.0108, +0.1651] (0.0145, 28) |
| bot · SHIPPED | 916 | 1679 | 0.629 | 0.352 | 3.37 | 21 | 0.96 | -0.0147 [-0.0872, +0.0577] (0.6658, 29) |
| bot · B_ext | 916 | 1862 | 0.715 | 0.383 | 3.35 | 17 | 1.12 | +0.0473 [-0.0229, +0.1175] (0.0929, 29) |
| bot · B_rsi | 916 | 1640 | 0.657 | 0.385 | 3.05 | 9 | 1.09 | +0.0332 [-0.0509, +0.1172] (0.2199, 29) |
| bot · B_rng | 916 | 1880 | 0.773 | 0.387 | 3.56 | 15 | 1.05 | +0.0177 [-0.0615, +0.0969] (0.3284, 29) |
| bot · L_price | 916 | 1724 | 0.676 | 0.367 | 3.39 | 20 | 0.99 | -0.0024 [-0.0798, +0.0749] (0.5349, 29) |
| bot · L_mom | 916 | 1751 | 0.736 | 0.390 | 3.34 | 17 | 1.04 | +0.0152 [-0.0636, +0.0939] (0.3507, 29) |
| bot · L_vol | 818 | 1570 | 0.746 | 0.395 | 3.28 | 16 | 1.05 | +0.0202 [-0.0665, +0.1070] (0.3211, 29) |
| bot · L_int | 818 | 1584 | 0.736 | 0.388 | 3.34 | 16 | 1.04 | +0.0160 [-0.0680, +0.1001] (0.3510, 29) |

| dir | alert | events | alerts | recall | precision* | FA/asset-yr | lead med (candles) | MFE / MAE med (ATR) | net ret mean / med (2× cost mean) |
|---|---|---:|---:|---|---:|---:|---:|---|---|
| top | zone | 864 | 1216 | 0.558 | 0.414 | 2.16 | 13 | 3.76 / 4.49 | -0.0225 / -0.0005 (–) |
| top | developing | 864 | 1218 | 0.571 | 0.427 | 2.10 | 11 | – / – | – / – (–) |
| top | confirmed | 864 | 1224 | 0.454 | 0.325 | 2.58 | -8 | 3.00 / 3.52 | -0.0232 / -0.0025 (-0.0246) |
| top | confirmed vs matched baselines (precision* / recall) | | | | | | | | htf_flip: 0.362 / 0.285; ema_cross: 0.357 / 0.417; supertrend_flip: 0.309 / 0.406; counter_reversal: 0.338 / 0.441 |
| top | shipped − B_ext near-rate (matched rate) | | | | | | | | {"clusters": 29, "delta": 0.0, "ci95": [-2.9704199459119846e-17, 2.9704199459119846e-17], "p_wild": 0.5045} |
| top | by_class (near vs bench) | | | | | | | | bond: 0.583 vs 0.615 (n 36); commodity: 0.455 vs 0.506 (n 44); crypto: 0.449 vs 0.346 (n 804); equity: 0.411 vs 0.431 (n 107); equity_index: 0.377 vs 0.398 (n 69); fx: 0.397 vs 0.381 (n 156) |
| top | by_era (near vs bench) | | | | | | | | early: 0.434 vs 0.345 (n 440); late: 0.442 vs 0.392 (n 776) |
| top | by_vol (near vs bench) | | | | | | | | high: 0.396 vs 0.360 (n 482); low: 0.483 vs 0.393 (n 431); mid: 0.446 vs 0.374 (n 303) |
| bot | zone | 916 | 1679 | 0.629 | 0.352 | 3.37 | 21 | 3.11 / 3.52 | -0.0012 / -0.0038 (–) |
| bot | developing | 916 | 1685 | 0.629 | 0.349 | 3.41 | 20 | – / – | – / – (–) |
| bot | confirmed | 916 | 1697 | 0.404 | 0.221 | 4.15 | -7 | 3.03 / 3.15 | -0.0062 / -0.0055 (-0.0078) |
| bot | confirmed vs matched baselines (precision* / recall) | | | | | | | | htf_flip: 0.247 / 0.240; ema_cross: 0.330 / 0.546; supertrend_flip: 0.306 / 0.529; counter_reversal: 0.306 / 0.517 |
| bot | shipped − B_ext near-rate (matched rate) | | | | | | | | {"clusters": 29, "delta": -0.06586576199709687, "ci95": [-0.08873744270521813, -0.042994081288975604], "p_wild": 1.0} |
| bot | by_class (near vs bench) | | | | | | | | bond: 0.259 vs 0.325 (n 27); commodity: 0.641 vs 0.537 (n 39); crypto: 0.358 vs 0.381 (n 1287); equity: 0.341 vs 0.378 (n 91); equity_index: 0.600 vs 0.366 (n 50); fx: 0.346 vs 0.375 (n 185) |
| bot | by_era (near vs bench) | | | | | | | | early: 0.361 vs 0.379 (n 662); late: 0.373 vs 0.386 (n 1017) |
| bot | by_vol (near vs bench) | | | | | | | | high: 0.379 vs 0.378 (n 821); low: 0.352 vs 0.389 (n 497); mid: 0.366 vs 0.384 (n 361) |

## 1H (108 instruments, 96 with volume)

* selection top|vol: core **L_price**; val AP {"B_ext": 0.328, "B_rsi": 0.2451, "B_rng": 0.3295, "L_price": 0.3477, "L_mom": 0.35, "L_vol": 0.3504, "L_int": 0.356} (base rate 0.1924); G_ref 0.4144712498868535; context {"htf_rng": {"ap_without": 0.35418577637672466, "ap_with": 0.3595063624487195, "kept": false, "rows": 311275}}; θ calibration {"target_onsets_per_asset_year": 27.942, "achieved": 25.922, "events_per_asset_year": 13.971}
* selection top|novol: core **L_price**; val AP {"B_ext": 0.3344, "B_rsi": 0.2503, "B_rng": 0.3346, "L_price": 0.3548, "L_mom": 0.3565} (base rate 0.1955); G_ref None; context {"htf_rng": {"ap_without": 0.35418577637672466, "ap_with": 0.3595063624487195, "kept": false, "rows": 311275}}; θ calibration {"target_onsets_per_asset_year": 27.942, "achieved": 25.922, "events_per_asset_year": 13.971}
* selection bot|vol: core **L_price**; val AP {"B_ext": 0.3774, "B_rsi": 0.2523, "B_rng": 0.388, "L_price": 0.4375, "L_mom": 0.4426, "L_vol": 0.4378, "L_int": 0.4353} (base rate 0.1772); G_ref 0.4888717440213418; context {"htf_rng": {"ap_without": 0.43777704722176897, "ap_with": 0.4354575620113348, "kept": false, "rows": 311275}}; θ calibration {"target_onsets_per_asset_year": 26.525, "achieved": 25.362, "events_per_asset_year": 13.263}
* selection bot|novol: core **L_price**; val AP {"B_ext": 0.3765, "B_rsi": 0.2496, "B_rng": 0.3863, "L_price": 0.4362, "L_mom": 0.441} (base rate 0.1742); G_ref None; context {"htf_rng": {"ap_without": 0.43777704722176897, "ap_with": 0.4354575620113348, "kept": false, "rows": 311275}}; θ calibration {"target_onsets_per_asset_year": 26.525, "achieved": 25.362, "events_per_asset_year": 13.263}

| dir · model | events | alerts | recall | precision* | FA/asset-yr | lead med | lift | excess [CI] (p, G) |
|---|---:|---:|---|---:|---:|---:|---:|---|
| top · SHIPPED | 3189 | 5351 | 0.707 | 0.429 | 8.65 | 20 | 1.01 | +0.0045 [-0.0335, +0.0426] (0.4070, 58) |
| top · B_ext | 3189 | 6176 | 0.588 | 0.330 | 10.96 | 13 | 0.89 | -0.0474 [-0.0719, -0.0229] (0.9998, 58) |
| top · B_rsi | 3189 | 6047 | 0.694 | 0.391 | 9.90 | -87 | 1.00 | +0.0018 [-0.0262, +0.0298] (0.4529, 58) |
| top · B_rng | 3189 | 5947 | 0.516 | 0.290 | 11.59 | 24 | 0.75 | -0.1079 [-0.1289, -0.0868] (1.0000, 58) |
| top · L_price | 3189 | 5351 | 0.707 | 0.429 | 8.65 | 20 | 1.01 | +0.0045 [-0.0335, +0.0426] (0.4070, 58) |
| top · L_mom | 3189 | 5539 | 0.724 | 0.424 | 9.01 | 20 | 1.00 | +0.0016 [-0.0342, +0.0373] (0.4651, 58) |
| top · L_vol | 2842 | 4951 | 0.561 | 0.332 | 10.18 | 25 | 0.81 | -0.0801 [-0.1072, -0.0530] (1.0000, 58) |
| top · L_int | 2842 | 5044 | 0.547 | 0.320 | 10.48 | 25 | 0.80 | -0.0862 [-0.1131, -0.0593] (1.0000, 58) |
| bot · SHIPPED | 3134 | 5332 | 0.502 | 0.304 | 10.34 | 30 | 0.77 | -0.0990 [-0.1303, -0.0677] (1.0000, 58) |
| bot · B_ext | 3134 | 5490 | 0.503 | 0.303 | 10.45 | -93 | 0.79 | -0.0877 [-0.1201, -0.0553] (1.0000, 58) |
| bot · B_rsi | 3134 | 6144 | 0.700 | 0.395 | 9.65 | 21 | 1.06 | +0.0263 [-0.0117, +0.0643] (0.0854, 58) |
| bot · B_rng | 3134 | 6352 | 0.820 | 0.421 | 10.18 | 23 | 1.04 | +0.0176 [-0.0216, +0.0567] (0.1854, 58) |
| bot · L_price | 3134 | 5332 | 0.502 | 0.304 | 10.34 | 30 | 0.77 | -0.0990 [-0.1303, -0.0677] (1.0000, 58) |
| bot · L_mom | 3134 | 5574 | 0.517 | 0.300 | 10.86 | 29 | 0.76 | -0.1020 [-0.1325, -0.0715] (1.0000, 58) |
| bot · L_vol | 2778 | 4927 | 0.517 | 0.301 | 10.60 | 29 | 0.77 | -0.0984 [-0.1340, -0.0628] (1.0000, 58) |
| bot · L_int | 2778 | 4885 | 0.501 | 0.294 | 10.60 | 30 | 0.75 | -0.1047 [-0.1387, -0.0707] (1.0000, 58) |

| dir | alert | events | alerts | recall | precision* | FA/asset-yr | lead med (candles) | MFE / MAE med (ATR) | net ret mean / med (2× cost mean) |
|---|---|---:|---:|---|---:|---:|---:|---|---|
| top | zone | 3189 | 5351 | 0.707 | 0.429 | 8.65 | 20 | 4.34 / 4.37 | -0.0062 / +0.0001 (–) |
| top | developing | 3189 | 5352 | 0.714 | 0.432 | 8.60 | 18 | – / – | – / – (–) |
| top | confirmed | 3189 | 5363 | 0.422 | 0.251 | 11.55 | -7 | 3.93 / 3.99 | -0.0032 / +0.0004 (-0.0048) |
| top | confirmed vs matched baselines (precision* / recall) | | | | | | | | htf_flip: 0.290 / 0.397; ema_cross: 0.330 / 0.508; supertrend_flip: 0.299 / 0.478; counter_reversal: 0.310 / 0.492 |
| top | shipped − B_ext near-rate (matched rate) | | | | | | | | {"clusters": 58, "delta": 0.055276942085300984, "ci95": [0.018747914117336284, 0.09180597005326568], "p_wild": 0.0014} |
| top | by_class (near vs bench) | | | | | | | | bond: 0.409 vs 0.456 (n 115); commodity: 0.352 vs 0.462 (n 142); crypto: 0.453 vs 0.423 (n 3886); equity: 0.453 vs 0.513 (n 373); equity_index: 0.324 vs 0.466 (n 219); fx: 0.401 vs 0.431 (n 616) |
| top | by_era (near vs bench) | | | | | | | | early: 0.460 vs 0.425 (n 2252); late: 0.422 vs 0.439 (n 3099) |
| top | by_vol (near vs bench) | | | | | | | | high: 0.416 vs 0.431 (n 2644); low: 0.435 vs 0.440 (n 1231); mid: 0.479 vs 0.432 (n 1476) |
| bot | zone | 3134 | 5332 | 0.502 | 0.304 | 10.34 | 30 | 3.57 / 3.90 | -0.0043 / -0.0023 (–) |
| bot | developing | 3134 | 5333 | 0.505 | 0.305 | 10.37 | 30 | – / – | – / – (–) |
| bot | confirmed | 3134 | 5325 | 0.264 | 0.157 | 12.77 | -10 | 3.66 / 3.90 | -0.0042 / -0.0024 (-0.0058) |
| bot | confirmed vs matched baselines (precision* / recall) | | | | | | | | htf_flip: 0.261 / 0.368; ema_cross: 0.318 / 0.499; supertrend_flip: 0.300 / 0.483; counter_reversal: 0.303 / 0.483 |
| bot | shipped − B_ext near-rate (matched rate) | | | | | | | | {"clusters": 58, "delta": -0.012294876997937965, "ci95": [-0.04697087671344861, 0.022381122717572678], "p_wild": 0.7576} |
| bot | by_class (near vs bench) | | | | | | | | bond: 0.343 vs 0.440 (n 99); commodity: 0.431 vs 0.473 (n 123); crypto: 0.307 vs 0.414 (n 4028); equity: 0.387 vs 0.457 (n 331); equity_index: 0.481 vs 0.501 (n 185); fx: 0.348 vs 0.446 (n 566) |
| bot | by_era (near vs bench) | | | | | | | | early: 0.308 vs 0.417 (n 2229); late: 0.339 vs 0.431 (n 3103) |
| bot | by_vol (near vs bench) | | | | | | | | high: 0.325 vs 0.426 (n 2845); low: 0.325 vs 0.423 (n 1222); mid: 0.329 vs 0.424 (n 1265) |
