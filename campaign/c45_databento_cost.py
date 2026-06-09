"""Cost estimates (NO download) for the #2 and #3 databento pulls, via metadata.get_cost.
Reads the verified key from spx-0dte-pinfly-lab\\databendto_key.txt (value never printed).
#2 curve RV: ZN/ZF/ZB/ES/UB/TN continuous front, a few schemas, full 2023-2026 span.
#3 OZB options: one ~70-min event window (full chain) -> x28 events upper bound (ATM-band is ~10-20x cheaper).
"""
from __future__ import annotations

import re

import databento as db

KEY_FILE = r"D:\workspace\spx-0dte-pinfly-lab\databendto_key.txt"
GLBX = "GLBX.MDP3"
CURVE = ["ZN.c.0", "ZF.c.0", "ZB.c.0", "ES.c.0", "UB.c.0", "TN.c.0"]


def read_key(f):
    m = re.search(r"db-[A-Za-z0-9]+", open(f, encoding="utf-8", errors="ignore").read())
    if not m:
        raise SystemExit("no key parsed")
    return m.group(0)


def main():
    client = db.Historical(read_key(KEY_FILE))

    def cost(label, **kw):
        try:
            c = client.metadata.get_cost(**kw)
            print(f"  {label}: ${c:,.2f}")
            return c
        except Exception as e:
            print(f"  {label}: ERROR {type(e).__name__}: {e}")
            return None

    print("=== #2 curve RV (GLBX, 6 instruments continuous front, 2023-01-01..2026-04-30) ===")
    for sch in ("ohlcv-1m", "ohlcv-1s", "mbp-1"):
        cost(f"{sch:9s} ZN/ZF/ZB/ES/UB/TN", dataset=GLBX, symbols=CURVE, schema=sch,
             stype_in="continuous", start="2023-01-01", end="2026-04-30")

    print("\n=== #3 OZB options (GLBX) -- 1 CPI event ~70-min window, full chain ===")
    for sch in ("bbo-1s", "mbp-1"):
        one = cost(f"OZB.OPT {sch} (2025-09-11 12:25..13:35 UTC, full chain)", dataset=GLBX,
                   symbols=["OZB.OPT"], stype_in="parent", schema=sch,
                   start="2025-09-11T12:25", end="2025-09-11T13:35")
        if one is not None:
            print(f"     -> x28 events full-chain: ${one*28:,.2f}  |  ATM-band ~10-20x cheaper: ~${one*28/15:,.2f}")
    # also the per-event definitions (tiny) needed to find strikes
    cost("OZB.OPT definition (1 day, for strike discovery)", dataset=GLBX, symbols=["OZB.OPT"],
         stype_in="parent", schema="definition", start="2025-09-11", end="2025-09-12")
    print("\n[get_cost = exact historical price, no data pulled. Decide spend, then download.]")


if __name__ == "__main__":
    main()
