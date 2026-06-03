"""No-lookahead forward targets for the favorable-state labels (spec section 4).

Every target at decision time *t* uses ONLY the window (t, t+h] -- strictly future, never *t* or
earlier. The last ``h`` rows are NaN (insufficient future). Horizons ``h`` are in trading days (rows).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

TRADING_DAYS = 252


def forward_realized_vol(ret: pd.Series, h: int) -> pd.Series:
    """Annualized realized vol of returns over (t, t+h].

    At index *t*: ``sqrt(mean(ret[t+1 .. t+h]^2)) * sqrt(252)`` -- the zero-mean realized-vol
    estimator (sum of squared returns), which is well-defined even at ``h == 1``. NaN in the last
    ``h`` rows.
    """
    r = pd.Series(ret)
    vals = r.to_numpy(dtype=float)
    n = len(vals)
    out = np.full(n, np.nan)
    future = vals[1:]
    if len(future) >= h >= 1:
        w = sliding_window_view(future, h)  # (n-h, h): w[t] = vals[t+1 : t+1+h]
        rv = np.sqrt(np.mean(w ** 2, axis=1)) * np.sqrt(TRADING_DAYS)
        out[: len(rv)] = rv
    return pd.Series(out, index=r.index, name=f"fwd_rv_{h}")


def forward_max_drawdown(close: pd.Series, h: int) -> pd.Series:
    """Worst forward return over (t, t+h]: ``min_k close[k]/close[t] - 1`` for k in (t, t+h].

    Negative = a drawdown. NaN in the last ``h`` rows.
    """
    c = pd.Series(close)
    vals = c.to_numpy(dtype=float)
    n = len(vals)
    out = np.full(n, np.nan)
    future = vals[1:]
    if len(future) >= h >= 1:
        w = sliding_window_view(future, h)  # (n-h, h): w[t] = close[t+1 : t+1+h]
        mins = w.min(axis=1)
        base = vals[: len(mins)]
        out[: len(mins)] = mins / base - 1.0
    return pd.Series(out, index=c.index, name=f"fwd_dd_{h}")


def low_vol_label(fwd_rv: pd.Series, q: float = 1 / 3) -> pd.Series:
    """Binary favorable-state label: 1 if forward vol is in the low ``q`` tail, else 0; NaN preserved.

    Threshold is the global ``q``-quantile of the available targets. This is fine for the *increment*
    test (M_B and M_BD see the identical label, so the threshold cannot bias the delta).
    """
    thr = fwd_rv.quantile(q)
    lab = (fwd_rv <= thr).astype(float)
    return lab.where(fwd_rv.notna())


def no_down_label(fwd_dd: pd.Series, thr: float = -0.02) -> pd.Series:
    """Binary favorable-state label: 1 if forward drawdown is shallower than ``thr``, else 0."""
    lab = (fwd_dd > thr).astype(float)
    return lab.where(fwd_dd.notna())
