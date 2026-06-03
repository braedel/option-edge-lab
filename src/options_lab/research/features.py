"""As-of-*t* features: crowded baseline ``B`` and differentiated ``D`` (spec section 3).

Every feature at row *t* uses only information available at *t*'s close. Differentiated GEX/DIX are
lagged one day (conservative: avoids any same-day end-of-day-measurement timing leak).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

BASELINE_RV_WINDOWS = (5, 10, 21)


def baseline_features(panel: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Crowded baseline ``B``: trailing realized vol (5/10/21d), 5d return, day-of-week one-hots."""
    p = panel.reset_index(drop=True)
    feats = pd.DataFrame(index=p.index)
    for w in BASELINE_RV_WINDOWS:
        feats[f"rv_{w}"] = p["ret"].rolling(w).std(ddof=0) * np.sqrt(252)
    feats["ret_5d"] = p["spx_close"].pct_change(5)
    dow = p["date"].dt.dayofweek
    for d in range(5):
        feats[f"dow_{d}"] = (dow == d).astype(float)
    return feats, list(feats.columns)


def differentiated_features(panel: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Differentiated ``D``: lagged GEX, lagged DIX, and a trailing-252 z-score of lagged GEX."""
    p = panel.reset_index(drop=True)
    feats = pd.DataFrame(index=p.index)
    gl = p["gex"].shift(1)
    dl = p["dix"].shift(1)
    feats["gex_lag1"] = gl
    feats["dix_lag1"] = dl
    mu = gl.rolling(252, min_periods=60).mean()
    sd = gl.rolling(252, min_periods=60).std(ddof=0)
    feats["gex_z"] = (gl - mu) / sd
    return feats, list(feats.columns)
