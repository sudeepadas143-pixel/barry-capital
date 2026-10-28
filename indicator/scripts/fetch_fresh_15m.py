"""15-minute spot bars for the fresh crypto symbols (LTF of the 1H profile)."""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from hcmtf import derivs  # noqa: E402
from hcmtf.universe import FRESH  # noqa: E402


def go(s):
    try:
        return f"{s} {len(derivs.spot_15m(s))}"
    except Exception as e:
        return f"{s} FAILED {e}"


with ThreadPoolExecutor(4) as ex:
    for r in ex.map(go, [a.symbol for a in FRESH if a.cls == "crypto"]):
        print(r, flush=True)
