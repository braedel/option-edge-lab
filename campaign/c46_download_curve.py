"""#2 data pull: download ZN/ZF/ZB/ES/UB/TN continuous-front 1-min bars (GLBX, 2023-01..2026-04) for the
cross-instrument curve-RV / lead-lag study. ~$19 (get_cost confirmed). Saves to the local data tree.
Key read from the verified file (value never printed). Run once.
"""
from __future__ import annotations

import re
from pathlib import Path

import databento as db

KEY_FILE = r"D:\workspace\spx-0dte-pinfly-lab\databendto_key.txt"
GLBX = "GLBX.MDP3"
CURVE = ["ZN.c.0", "ZF.c.0", "ZB.c.0", "ES.c.0", "UB.c.0", "TN.c.0"]
OUT = Path(r"D:\TradingData\databento\curve")


def read_key(f):
    m = re.search(r"db-[A-Za-z0-9]+", open(f, encoding="utf-8", errors="ignore").read())
    if not m:
        raise SystemExit("no key parsed")
    return m.group(0)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    client = db.Historical(read_key(KEY_FILE))
    print(f"downloading {len(CURVE)} continuous-front 1-min series 2023-01-01..2026-04-30 ...", flush=True)
    data = client.timeseries.get_range(dataset=GLBX, symbols=CURVE, schema="ohlcv-1m",
                                       stype_in="continuous", start="2023-01-01", end="2026-04-30")
    df = data.to_df()
    p = OUT / "curve_ohlcv1m.parquet"
    df.to_parquet(p)
    print(f"-> wrote {p}: {len(df):,} rows, cols={list(df.columns)}")
    if "symbol" in df.columns:
        print(df.groupby("symbol").size().to_string())


if __name__ == "__main__":
    main()
