# Component screening (development data only)

45884 MTF structure breaks on the 30 development symbols, before each timeframe's holdout. 
Fresh symbols were not loaded. diff = mean r_h (ATR, after costs) with minus without; 
90% month-cluster bootstrap intervals. The rule is in `scripts/screen_components.py` and was 
fixed before this ran.

| component | decision | crypto diff [90% CI] | crypto TFs > 0 | non-crypto diff [90% CI] | n with / without (crypto) |
|---|---|---:|---:|---:|---:|
| momentum | **DROP** | +0.034 [-0.143, +0.202] | 1/4 | -0.091 [-0.235, +0.056] | 23552 / 2572 |
| strength | **DROP** | +0.085 [-0.022, +0.193] | 3/4 | +0.012 [-0.083, +0.112] | 14097 / 12027 |
| displacement | **DROP** | +0.054 [-0.106, +0.195] | 4/4 | -0.047 [-0.148, +0.062] | 22064 / 4060 |
| fvg | **DROP** | +0.053 [-0.042, +0.154] | 2/4 | +0.020 [-0.081, +0.122] | 9883 / 16241 |
| volume | **DROP** | +0.028 [-0.085, +0.143] | 3/4 | +0.068 [-0.069, +0.216] | 16294 / 9830 |
| sweep | **DROP** | -0.080 [-0.209, +0.045] | 0/4 | -0.181 [-0.288, -0.079] | 7128 / 18996 |
| ltf_momentum | **DROP** | +0.069 [-0.192, +0.340] | 2/4 | -0.427 [-1.024, +0.151] | 25612 / 512 |
| perp_ok | **DROP** | +0.069 [-0.174, +0.317] | 1/4 | – | 16519 / 2654 |
| basis_ok | **DROP** | +0.103 [-0.098, +0.318] | 1/4 | – | 16713 / 2436 |
| oi_up | **DROP** | +0.105 [-0.039, +0.259] | 1/4 | – | 6713 / 5708 |
| not_range | **DROP** | -0.003 [-0.127, +0.115] | 2/4 | -0.025 [-0.117, +0.072] | 18872 / 7252 |
| not_shock | **DROP** | +0.229 [-0.008, +0.441] | 2/4 | +0.300 [+0.100, +0.507] | 23887 / 2237 |
| not_spike_wick | **DROP** | +0.088 [-0.089, +0.263] | 1/4 | +0.191 [-0.084, +0.473] | 23405 / 2719 |
| not_weekend | **DROP** | +0.307 [+0.130, +0.486] | 1/4 | – | 19025 / 7099 |

Per timeframe (crypto diff):

| component | 1H | 4H | 1D | 1W |
|---|---:|---:|---:|---:|
| momentum | +0.157 | -0.135 | -0.583 | – |
| strength | +0.001 | +0.374 | -0.017 | +2.736 |
| displacement | +0.024 | +0.031 | +0.940 | +1.213 |
| fvg | +0.083 | -0.007 | -0.401 | +0.433 |
| volume | +0.059 | +0.028 | -0.104 | +1.233 |
| sweep | -0.039 | -0.107 | -0.803 | -0.694 |
| ltf_momentum | +0.036 | -0.211 | +1.918 | – |
| perp_ok | +0.199 | -0.090 | -0.044 | -3.451 |
| basis_ok | +0.197 | -0.087 | -0.004 | – |
| oi_up | +0.195 | -0.359 | -0.297 | – |
| not_range | -0.077 | +0.257 | -0.150 | +2.025 |
| not_shock | +0.241 | -0.174 | +0.322 | – |
| not_spike_wick | +0.116 | -0.107 | -0.223 | – |
| not_weekend | +0.416 | -0.148 | -1.268 | – |

Counter-HTF reversal MAJOR path: **CLOSED** (sweep diff among counter-HTF reversals, crypto: +0.098 [-0.042, +0.249])

Mean r_h by break class (n, mean):

| class | crypto | non-crypto |
|---|---:|---:|
| continuation | 10145, +0.151 | 9283, +0.219 |
| realignment | 4054, +0.223 | 3062, +0.289 |
| counter_reversal | 11925, -0.220 | 7415, -0.258 |

Family merges (|phi| > 0.5 across families): none

Correlation (phi) between the core conditions:

```
              momentum  strength  displacement   fvg  volume  sweep
momentum          1.00     -0.06          0.05  0.03    0.11  -0.02
strength         -0.06      1.00          0.06  0.03    0.10  -0.16
displacement      0.05      0.06          1.00 -0.21    0.26   0.02
fvg               0.03      0.03         -0.21  1.00   -0.00   0.04
volume            0.11      0.10          0.26 -0.00    1.00   0.04
sweep            -0.02     -0.16          0.02  0.04    0.04   1.00
```