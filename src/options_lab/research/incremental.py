"""Nested-model incremental out-of-sample skill (spec section 5): does D add skill over B?

For each walk-forward fold we fit M_B (baseline) and M_BD (baseline + differentiated), collect
out-of-fold predictions, and test whether M_BD lowers prediction loss -- a Diebold-Mariano-style HAC
t-test on the per-observation loss differential -- plus per-fold sign consistency.
"""
from __future__ import annotations

import numpy as np
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import r2_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

from options_lab.research.multiple_testing import min_detectable_effect


def _fit_predict(x_tr, y_tr, x_te, task):
    scaler = StandardScaler().fit(x_tr)
    x_tr_s = scaler.transform(x_tr)
    x_te_s = scaler.transform(x_te)
    if task == "reg":
        return Ridge(alpha=1.0).fit(x_tr_s, y_tr).predict(x_te_s)
    return LogisticRegression(max_iter=1000).fit(x_tr_s, y_tr).predict_proba(x_te_s)[:, 1]


def incremental_skill(X_B, X_D, y, folds, task: str = "reg", maxlags: int = 5) -> dict:
    """Out-of-fold incremental skill of D over B.

    ``X_B``,``X_D`` arrays (n, .); ``y`` array (n,); ``folds`` iterable of (train_pos, test_pos)
    positional index arrays; ``task`` "reg" (Ridge/R2) or "clf" (Logit/AUC). Returns dict with
    ``delta`` (pooled R2/AUC gain), ``mean_d`` (mean loss differential), ``t_stat`` (HAC, + = BD
    better), ``sign_consistency``, ``n_oof``, ``n_folds``, ``mde``.
    """
    X_B = np.asarray(X_B, float)
    X_D = np.asarray(X_D, float)
    y = np.asarray(y, float)
    X_BD = np.hstack([X_B, X_D])

    oof_y, oof_b, oof_bd, fold_deltas = [], [], [], []
    for tr, te in folds:
        tr = np.asarray(tr, int)
        te = np.asarray(te, int)
        ok_tr = np.isfinite(X_BD[tr]).all(1) & np.isfinite(y[tr])
        ok_te = np.isfinite(X_BD[te]).all(1) & np.isfinite(y[te])
        tri, tei = tr[ok_tr], te[ok_te]
        if len(tri) < 30 or len(tei) < 5:
            continue
        if task == "clf" and len(np.unique(y[tri])) < 2:
            continue
        p_b = _fit_predict(X_B[tri], y[tri], X_B[tei], task)
        p_bd = _fit_predict(X_BD[tri], y[tri], X_BD[tei], task)
        yt = y[tei]
        if task == "reg":
            fold_deltas.append(r2_score(yt, p_bd) - r2_score(yt, p_b))
        elif len(np.unique(yt)) == 2:
            fold_deltas.append(roc_auc_score(yt, p_bd) - roc_auc_score(yt, p_b))
        else:
            continue
        oof_y.append(yt)
        oof_b.append(p_b)
        oof_bd.append(p_bd)

    if not fold_deltas:
        return {"delta": np.nan, "mean_d": np.nan, "t_stat": np.nan, "sign_consistency": np.nan,
                "n_oof": 0, "n_folds": 0, "mde": np.nan}

    yt = np.concatenate(oof_y)
    p_b = np.concatenate(oof_b)
    p_bd = np.concatenate(oof_bd)
    if task == "reg":
        delta = r2_score(yt, p_bd) - r2_score(yt, p_b)
        d = (yt - p_b) ** 2 - (yt - p_bd) ** 2          # > 0  => BD better
    else:
        delta = roc_auc_score(yt, p_bd) - roc_auc_score(yt, p_b)
        d = (p_b - yt) ** 2 - (p_bd - yt) ** 2          # brier diff, > 0 => BD better

    res = sm.OLS(d, np.ones(len(d))).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    return {
        "delta": float(delta),
        "mean_d": float(res.params[0]),
        "t_stat": float(res.tvalues[0]),
        "sign_consistency": float(np.mean(np.asarray(fold_deltas) > 0)),
        "n_oof": int(len(d)),
        "n_folds": int(len(fold_deltas)),
        "mde": float(min_detectable_effect(float(res.bse[0]))),
    }
