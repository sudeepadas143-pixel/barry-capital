"""Turn reports/screening.json decisions into reports/active_config.json, mechanically.

KEEP -> condition/filter on for every market; KEEP_CRYPTO -> on for crypto charts only;
DROP -> off. Counter-HTF reversal MAJOR path: CLOSED -> counter_major 2.0 (unreachable);
OPEN_WITH_SWEEP -> 1.0 (all available evidence AND a prior sweep). Family merges, if the
screening found any, are written out for the record and must be reflected in
engine.FAMILIES by hand (the script refuses to continue silently).
"""
import json
from pathlib import Path

R = Path(__file__).resolve().parent.parent / "reports"
dec = json.loads((R / "screening.json").read_text())["decisions"]
EVIDENCE = ["momentum", "strength", "displacement", "fvg", "volume", "sweep", "ltf_momentum",
            "perp_ok", "basis_ok", "oi_up"]
FILTERS = ["not_range", "not_shock", "not_spike_wick", "not_weekend"]
if dec.get("merges"):
    raise SystemExit(f"screening found correlated families to merge: {dec['merges']}")
cfg = {
    "evidence": [c for c in EVIDENCE if dec[c] != "DROP"],
    "filters": [c for c in FILTERS if dec[c] != "DROP"],
    "crypto_only": [c for c in EVIDENCE + FILTERS if dec[c] == "KEEP_CRYPTO"],
    "counter_major": 2.0 if dec["counter_major_path"] == "CLOSED" else 1.0,
    "source": "reports/screening.json (scripts/screen_components.py rule)",
}
if len(cfg["evidence"]) < 3:
    cfg["note"] = "fewer than three evidence families survived screening"
(R / "active_config.json").write_text(json.dumps(cfg, indent=1))
print(json.dumps(cfg, indent=1))
