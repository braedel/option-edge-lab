"""Maker TAIL-GUARD test -- the experiment I should have run before calling the maker NULL.

The maker proxy (c26) wins 64-69% with +0.87t median but mean ~-0.8t: the loss tail is the FORCED
cross-exit (passive exit never fills -> dump at the touch H_EXIT later, after the price has already run
-16..-28t). That tail is exactly what a STOP cuts. This re-runs the round-trip with, per pre-registered
cell, the earliest of {passive-exit fill (+spread), HARD STOP at -S ticks, TIME STOP at T s, forced exit},
and separately an EVENT-BLACKOUT (suppress quotes around NFP/FOMC/CPI, the worst adverse-selection windows).

Causal: the exit path is scanned forward trade-by-trade; a stop/time trigger uses the touch AS IT UNFOLDS
(no look-ahead). Pooled over 9 OOS months (post-train, non-sealed) for a stable tail. Coarse offline proxy
(optimistic on fills, same conventions as c26) -- but the QUESTION (does capping the tail flip the mean
positive, robustly across months?) is robust to small proxy error. Run on local mirror (ZB_DATA_ROOT).

Reports per cell: n, mean/median net, %positive, 5th-pctile & worst (tail), exit-reason mix, and the
per-month mean (leave-one-out: is any improvement carried by one month?). Honest verdict, not a foregone one.
"""
from __future__ import annotations

import csv
import datetime as dt
import multiprocessing as mp
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c22_zb_discovery import build_features  # noqa: E402
from c24_zb_multivariate import extract  # noqa: E402

from options_lab.zb_mbo.loader import load_events, month_path  # noqa: E402
from options_lab.zb_mbo.stream import TICK, stream_features  # noqa: E402

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
SEC = 1_000_000_000
TRAIN = ["2024-05", "2024-06", "2024-07"]
VAL_MONTHS = ["2024-08", "2024-09", "2024-10", "2024-11", "2024-12", "2025-06", "2025-07", "2025-08", "2025-09"]
MAXEV = 6_000_000
H_FILL = 600          # snaps to get the entry fill
H_EXIT = 1200         # snaps before a forced cross-exit
QUOTE_Q = 0.75
FEE_T = 4.0 / 31.25
EVENT_PRE, EVENT_POST = 120 * SEC, 900 * SEC   # blackout window around a scheduled event
STOPS = (2, 3, 4, 6)
TIMES = (60, 120, 300)
# pre-registered cells: (name, hard_stop_ticks|None, time_stop_seconds|None)
CELLS = [
    ("base", None, None),
    ("stop6", 6, None), ("stop4", 4, None), ("stop3", 3, None), ("stop2", 2, None),
    ("time300", None, 300), ("time120", None, 120), ("time60", None, 60),
    ("stop4_time120", 4, 120), ("stop3_time60", 3, 60),
]
_MODEL = None
_EVENTS = None


def _utc_ns(date_str, time_et):
    d = dt.date.fromisoformat(date_str)
    hh, mm = map(int, time_et.split(":"))
    return int(dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(UTC).timestamp() * 1e9)


def load_event_ts():
    out = []
    p = Path("data/zb_macro_events.csv")
    for r in csv.DictReader(open(p)):
        if r["pinning"] == "NOT_FOUND" or len(r["date"]) != 10:
            continue
        out.append(_utc_ns(r["date"], r["time_et"]))
    return np.array(sorted(out), np.int64)


def fit_signal():
    Xtr, ytr = [], []
    for m in TRAIN:
        X, y = extract(m); Xtr.append(X); ytr.append(y)
    g = HistGradientBoostingRegressor(max_depth=3, max_iter=250, learning_rate=0.05)
    g.fit(np.vstack(Xtr), np.concatenate(ytr)); return g


def _init(model, events):
    global _MODEL, _EVENTS
    _MODEL, _EVENTS = model, events


def _entry_fill(start, P, need, buy_side_aggressor, tsign, tpx, tqty, N):
    """Forward-scan for the entry passive fill: aggressor vol at the touch clears `need`. Return snap or -1."""
    cum = 0.0
    end = min(N, start + H_FILL + 1)
    j = start + 1
    while j < end:
        if buy_side_aggressor and tsign[j] < 0 and tpx[j] <= P + 1e-9:      # long entry: sell-aggressors hit our bid
            cum += tqty[j]
        elif (not buy_side_aggressor) and tsign[j] > 0 and tpx[j] >= P - 1e-9:  # short entry: buy-aggressors lift our ask
            cum += tqty[j]
        if cum >= need:
            return j
        j += 1
    return -1


def process_month(mk):
    a = load_events(month_path(mk))[:MAXEV]
    snaps = stream_features(a)
    feats = build_features(snaps)
    ok = feats.notna().all(axis=1).to_numpy()
    snaps, feats = snaps[ok], feats[ok].to_numpy()
    ts = snaps["ts"].astype(np.int64)
    sig = _MODEL.predict(feats)
    side = np.sign(sig).astype(int)
    quote = np.abs(sig) >= np.quantile(np.abs(sig), QUOTE_Q)
    bb, ba = snaps["best_bid"].astype(float), snaps["best_ask"].astype(float)
    bid1, ask1 = snaps["bid1"], snaps["ask1"]
    tpx, tqty, tsign = snaps["trade_px"], np.abs(snaps["trade_signed"]), np.sign(snaps["trade_signed"])
    N = len(ts)
    ev = _EVENTS
    # per cell -> list of net ticks ; plus reason tallies for the headline cells
    out = {c[0]: [] for c in CELLS}
    out_be = {c[0]: [] for c in CELLS}   # blackout-filtered (events suppressed)
    reasons = {c[0]: {"pass": 0, "stop": 0, "time": 0, "forced": 0} for c in CELLS}

    for i in np.flatnonzero(quote):
        s = side[i]
        if s == 0:
            continue
        long = s > 0
        if long:
            ej = _entry_fill(i, bb[i], bid1[i], True, tsign, tpx, tqty, N)
        else:
            ej = _entry_fill(i, ba[i], ask1[i], False, tsign, tpx, tqty, N)
        if ej < 0:
            continue
        entry_px = bb[i] if long else ba[i]
        exit_target = ba[i] if long else bb[i]        # passive exit price (capture the spread)
        need_exit = ask1[i] if long else bid1[i]
        end = min(N, ej + H_EXIT + 1)
        # ONE forward scan: passive-exit fill snap, and first-hit snap for each stop level
        pass_j, cum = -1, 0.0
        hit = {S: -1 for S in STOPS}
        j = ej + 1
        while j < end:
            if pass_j < 0:
                if long and tsign[j] > 0 and tpx[j] >= exit_target - 1e-9:      # buy-aggressor lifts our ask
                    cum += tqty[j]
                elif (not long) and tsign[j] < 0 and tpx[j] <= exit_target + 1e-9:  # sell-aggressor hits our bid
                    cum += tqty[j]
                if cum >= need_exit:
                    pass_j = j
            adv = (bb[j] - entry_px) / TICK if long else (entry_px - ba[j]) / TICK   # signed P&L if we cross-exit now
            for S in STOPS:
                if hit[S] < 0 and adv <= -S:
                    hit[S] = j
            j += 1
        k = min(ej + H_EXIT, N - 1)                                            # forced exit snap
        in_event = bool(ev.size and np.min(np.abs(ev - ts[i])) <= max(EVENT_PRE, EVENT_POST)
                        and (-EVENT_PRE <= (ts[i] - ev[np.argmin(np.abs(ev - ts[i]))]) <= EVENT_POST))

        def cross_net(jj):
            px = bb[jj] if long else ba[jj]
            return (px - entry_px) / TICK * s - FEE_T

        pass_net = (exit_target - entry_px) / TICK * s - FEE_T                  # = +spread - fee
        for name, S, T in CELLS:
            cands = [(ts[k], "forced", cross_net(k))]
            if pass_j >= 0:
                cands.append((ts[pass_j], "pass", pass_net))
            if S is not None and hit[S] >= 0:
                cands.append((ts[hit[S]], "stop", cross_net(hit[S])))
            if T is not None:
                tj = int(np.searchsorted(ts, ts[ej] + T * SEC, "left"))
                if ej < tj < end:
                    cands.append((ts[tj], "time", cross_net(tj)))
            _, reason, net = min(cands, key=lambda c: c[0])                     # earliest in time wins
            out[name].append(net)
            reasons[name][reason] += 1
            if not in_event:
                out_be[name].append(net)
    days = max(int(np.unique(ts // (86_400 * SEC)).size), 1)
    return mk, days, {k: np.array(v) for k, v in out.items()}, {k: np.array(v) for k, v in out_be.items()}, reasons


def stat(v):
    if len(v) < 5:
        return f"n={len(v)} (few)"
    return (f"n={len(v):4d} mean={v.mean():+6.3f}t med={np.median(v):+6.3f}t %pos={np.mean(v > 0):.3f} "
            f"p05={np.percentile(v, 5):+6.2f}t worst={v.min():+6.1f}t")


def main():
    model = fit_signal()
    events = load_event_ts()
    nproc = min(9, len(VAL_MONTHS))
    print(f"train={TRAIN} -> {len(VAL_MONTHS)} OOS months across {nproc} workers (events={events.size})", flush=True)
    pooled = {c[0]: [] for c in CELLS}
    pooled_be = {c[0]: [] for c in CELLS}
    permonth = {c[0]: {} for c in CELLS}
    reasons_tot = {c[0]: {"pass": 0, "stop": 0, "time": 0, "forced": 0} for c in CELLS}
    with mp.Pool(nproc, initializer=_init, initargs=(model, events)) as pool:
        for mk, days, out, out_be, reasons in pool.imap_unordered(process_month, VAL_MONTHS):
            for name in pooled:
                pooled[name].append(out[name]); pooled_be[name].append(out_be[name])
                permonth[name][mk] = float(out[name].mean()) if len(out[name]) else float("nan")
                for r in reasons_tot[name]:
                    reasons_tot[name][r] += reasons[name][r]
            print(f"  done {mk} ({days}d, {len(out['base'])} round-trips)", flush=True)

    print("\n=== maker tail-guard, pooled over OOS months (coarse proxy, optimistic on fills) ===")
    base_mean = np.concatenate(pooled["base"]).mean()
    for name, S, T in CELLS:
        v = np.concatenate(pooled[name])
        rm = reasons_tot[name]; tot = max(sum(rm.values()), 1)
        mix = f"pass={rm['pass']/tot:.2f} stop={rm['stop']/tot:.2f} time={rm['time']/tot:.2f} forced={rm['forced']/tot:.2f}"
        print(f"{name:14s} {stat(v)}  d_mean={v.mean()-base_mean:+.3f}t [{mix}]")

    print("\n-- event-blackout (quotes near NFP/FOMC/CPI suppressed) --")
    for name in ("base", "stop3", "stop3_time60"):
        v = np.concatenate(pooled_be[name])
        print(f"{name:14s} {stat(v)}")

    # leave-one-month-out on the best-mean cell
    best = max(CELLS, key=lambda c: np.concatenate(pooled[c[0]]).mean())[0]
    pm = permonth[best]
    print(f"\nbest cell by pooled mean = '{best}'. per-month means:")
    for mk in VAL_MONTHS:
        print(f"   {mk}: {pm.get(mk, float('nan')):+.3f}t")
    vals = np.array([pm[m] for m in VAL_MONTHS if np.isfinite(pm.get(m, np.nan))])
    print(f"   -> months positive: {int((vals > 0).sum())}/{len(vals)}; min month={vals.min():+.3f}t  "
          f"sign-stable={'YES' if (vals > 0).all() else 'NO'}")
    print("\n[Does capping the tail flip the mean positive AND hold across months? That is the test. "
          "If yes -> build the real hftbacktest harness; if no -> the tail is not a stop-able artifact.]")


if __name__ == "__main__":
    main()
