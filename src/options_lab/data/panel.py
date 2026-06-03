"""Daily SPX panel from in-hand vendor CSVs.

v1 source: SqueezeMetrics ``squeezemetrics_gex.csv`` (``date, price, dix, gex``), daily, 2011 ->.
One responsibility: tidy CSV -> clean daily frame the research layer builds features/targets on.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PANEL_COLUMNS = ["date", "spx_close", "ret", "gex", "dix"]


def load_daily_panel(path: str | Path) -> pd.DataFrame:
    """Load a daily SPX panel from a SqueezeMetrics-style CSV.

    Expects columns ``date, price, dix, gex``. Returns a frame with columns
    ``date`` (datetime64), ``spx_close``, ``ret``, ``gex``, ``dix`` -- sorted ascending by date,
    de-duplicated (keep last per date), with ``ret = spx_close.pct_change()`` (first row NaN).
    Raises ``ValueError`` if a ``source`` column is present and any row is not ``"real"``
    (integrity rule 1: real data only).
    """
    df = pd.read_csv(path)
    if "source" in df.columns and not (df["source"].astype(str) == "real").all():
        raise ValueError("panel contains non-real rows (integrity rule 1)")
    df = df.rename(columns={"price": "spx_close"})
    missing = {"date", "spx_close", "gex", "dix"} - set(df.columns)
    if missing:
        raise ValueError(f"panel CSV missing columns: {sorted(missing)}")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    df["ret"] = df["spx_close"].pct_change()
    if df.empty:
        raise ValueError("panel is empty")
    return df[PANEL_COLUMNS]
