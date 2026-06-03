"""Stage-1a orchestrator: run the (target x horizon) incremental grid and apply the spec-section-6
pre-registered decision rule (PASS / KILL / INCONCLUSIVE).

For each (target, horizon) we build a no-lookahead target, fit nested models inside purged
walk-forward folds (embargo = h, OOS sealed), and measure whether the differentiated features add
out-of-fold skill over the baseline. p-values are one-sided ("does D help?"), BH-corrected across the
whole grid; a cell PASSES only with sign-consistency, BH-corrected |t| > 3, and effect above the MDE.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from options_lab.research.features import baseline_features, differentiated_features
from options_lab.research.incremental import incremental_skill
from options_lab.research.multiple_testing import bh_adjust, t_to_p
from options_lab.research.targets import forward_max_drawdown, forward_realized_vol
from options_lab.research.validation import walk_forward_folds

HORIZONS = (1, 3, 5)
TARGETS = ("fwd_rv", "fwd_dd")


def _target_series(panel: pd.DataFrame, name: str, h: int) -> pd.Series:
    if name == "fwd_rv":
        return forward_realized_vol(panel["ret"], h)
    return forward_max_drawdown(panel["spx_close"], h)


def _p_to_t(p: float) -> float:
    p = float(min(max(p, 1e-300), 1 - 1e-16))
    return float(stats.norm.isf(p))  # one-sided


def run_stage1a(panel: pd.DataFrame, horizons=HORIZONS, targets=TARGETS, n_splits: int = 5,
                oos_start: str | None = "2025-09-01", t_pass: float = 3.0,
                sign_pass: float = 2.0 / 3.0) -> tuple[pd.DataFrame, str]:
    panel = panel.reset_index(drop=True)
    dates = panel["date"]
    Xb, _ = baseline_features(panel)
    Xd, _ = differentiated_features(panel)
    Xb_v, Xd_v = Xb.to_numpy(float), Xd.to_numpy(float)

    has_oos = oos_start is not None and bool((dates >= pd.to_datetime(oos_start)).any())
    first_oos = int(np.argmax((dates >= pd.to_datetime(oos_start)).to_numpy())) if has_oos else len(dates)
    pre_dates = dates.iloc[:first_oos]
    date_to_pos = {d: i for i, d in enumerate(dates)}

    rows = []
    for name in targets:
        for h in horizons:
            y = _target_series(panel, name, h).to_numpy(float).copy()
            if first_oos < len(y):  # purge labels whose forward window crosses the OOS boundary
                y[max(0, first_oos - h):first_oos] = np.nan
            fd = list(walk_forward_folds(pre_dates, n_splits=n_splits, embargo=h, oos_start=oos_start))
            folds = [(np.array([date_to_pos[d] for d in tr], int),
                      np.array([date_to_pos[d] for d in te], int)) for tr, te in fd]
            r = incremental_skill(Xb_v, Xd_v, y, folds, task="reg", maxlags=h)
            rows.append({"target": name, "h": h, **r})

    table = pd.DataFrame(rows)
    table["p"] = table["t_stat"].apply(lambda t: t_to_p(t, two_sided=False) if np.isfinite(t) else np.nan)
    table["p_bh"] = np.nan
    finite = table["p"].notna()
    if finite.any():
        table.loc[finite, "p_bh"] = bh_adjust(table.loc[finite, "p"].to_numpy())
    table["t_corrected"] = table["p_bh"].apply(lambda p: _p_to_t(p) if pd.notna(p) else np.nan)

    def cell(row):
        if not np.isfinite(row["t_stat"]):
            return "skip"
        favorable = (row["t_stat"] > 0) and (row["sign_consistency"] >= sign_pass)
        strong = (favorable and np.isfinite(row["t_corrected"])
                  and abs(row["t_corrected"]) >= t_pass and row["mean_d"] > row["mde"])
        if strong:
            return "PASS"
        if favorable and row["mean_d"] <= row["mde"]:
            return "INCONCLUSIVE"
        return "null"

    table["verdict"] = table.apply(cell, axis=1)
    if (table["verdict"] == "PASS").any():
        overall = "PASS"
    elif (table["verdict"] == "INCONCLUSIVE").any():
        overall = "INCONCLUSIVE"
    else:
        overall = "KILL"
    return table, overall
