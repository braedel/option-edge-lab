"""Candidate #1 - forward-OOS test of the frozen threshold-detector v2.

Apply the frozen walk-forward rules to local ES/NQ volume-roll OHLCV (which extends to 2026-03),
replay executably with micro (MES/MNQ) point values, and measure:
  (A) REPRODUCTION: each rule applied to its OWN test_year vs the published OOS -> validates the
      pipeline + ES-as-proxy-for-MES (price/gap/vol features identical; volume features differ).
  (B) FORWARD: the latest (test_year=2025) ruleset applied to the UNSEEN 2025-07-01 .. 2026-03-20
      window, at $2/$4/$6 round-turn, by month, with drawdown + win rate.

Replay once at cost 0; subtract round-turn cost in the summary (gross is cost-invariant).
"""
from __future__ import annotations

import sys

import pandas as pd

DAT = r"D:\workspace\dat-trading-strategy-research"
sys.path.insert(0, DAT + r"\src")

from dat_strategy_research.features import FeatureSnapshotConfig, pre_entry_feature_snapshots  # noqa: E402
from dat_strategy_research.ohlcv import max_drawdown, read_ohlcv  # noqa: E402
from dat_strategy_research.replay import replay_selected_rows  # noqa: E402

RULES_CSV = DAT + r"\reports\outcome_labels\threshold_detector_walkforward_v2\selected_rules.csv"
VR = DAT + r"\data\processed\databento\es_nq_volume_roll_1m\{}_volume_roll_backadjusted_1m.parquet"
SYM_DATA = {"MES": "ES", "MNQ": "NQ"}  # micro rule symbol -> local data symbol (same index)
HORIZON_END = "15:55"


def parse_ts(s: str) -> tuple[float, float]:
    t, st = str(s).split("/")
    return float(t), float(st)


def build_signals(rules: pd.DataFrame, snaps: dict) -> pd.DataFrame:
    out = []
    for r in rules.itertuples(index=False):
        snap = snaps.get((r.symbol, r.entry_time))
        if snap is None or snap.empty or r.feature not in snap.columns:
            continue
        s = snap.loc[snap["same_instrument_pre_entry"].astype(bool) & snap[r.feature].notna()].copy()
        s = s.loc[s[r.feature] >= r.threshold] if r.operator == ">=" else s.loc[s[r.feature] <= r.threshold]
        if s.empty:
            continue
        tgt, stp = parse_ts(r.target_stop)
        out.append(pd.DataFrame({
            "symbol": r.symbol,
            "entry_ts_label": s["entry_ts"].to_numpy(),
            "entry_price": s["entry_open"].to_numpy(),
            "side": r.side,
            "target_points": tgt,
            "stop_points": stp,
            "horizon_end": HORIZON_END,
            "instrument_id_label": s["instrument_id"].to_numpy(),
            "rule_test_year": r.test_year,
        }))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def replay0(signals: pd.DataFrame, ohlcv: dict) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame()
    obs = {sym: ohlcv[SYM_DATA[sym]] for sym in signals["symbol"].unique()}
    tr = replay_selected_rows(obs, signals, round_turn_cost=0.0)
    if not tr.empty:
        tr["exit_ts"] = pd.to_datetime(tr["exit_ts"], utc=True)
    return tr


def summ(tr: pd.DataFrame, cost: float) -> dict:
    if tr.empty:
        return {"trades": 0, "net": 0.0, "net_per": 0.0, "dd": 0.0, "win": 0.0}
    o = tr.sort_values("exit_ts").reset_index(drop=True)
    net = o["gross_dollars"] - cost
    eq = net.cumsum()
    return {"trades": int(len(o)), "net": round(float(net.sum()), 1),
            "net_per": round(float(net.mean()), 3), "dd": round(max_drawdown(eq), 1),
            "win": round(float((net > 0).mean()), 3)}


def main() -> None:
    rules = pd.read_csv(RULES_CSV)
    print(f"rules: {len(rules)} (test_year dist: {rules.groupby('test_year').size().to_dict()})")
    ohlcv = {ds: read_ohlcv(VR.format(ds)) for ds in ["ES", "NQ"]}
    for ds, df in ohlcv.items():
        print(f"  {ds} ohlcv rows={len(df)} {df['timestamp'].min()} .. {df['timestamp'].max()}")

    snaps = {}
    for k in rules[["symbol", "entry_time"]].drop_duplicates().itertuples(index=False):
        cfg = FeatureSnapshotConfig(symbol=k.symbol, entry_time=k.entry_time)
        snaps[(k.symbol, k.entry_time)] = pre_entry_feature_snapshots(ohlcv[SYM_DATA[k.symbol]], cfg)

    # (A) reproduction
    print("\n=== (A) REPRODUCTION: each rule on its own test_year (ES-proxy validity) ===")
    sig = build_signals(rules, snaps)
    sig["entry_year"] = pd.to_datetime(sig["entry_ts_label"], utc=True).dt.year
    repro = sig.loc[sig["entry_year"] == sig["rule_test_year"]].copy()
    tr = replay0(repro, ohlcv)
    tr["exit_year"] = tr["exit_ts"].dt.year
    print("overall @ $2:", summ(tr, 2.0))
    for y, g in tr.groupby("exit_year"):
        print(f"  {int(y)}: {summ(g, 2.0)}")
    print("PUBLISHED (MES/MNQ): 5239 trades, +12316.5 @ $2 (+2.35/trade); 2023=+4256.75 2024=+1397 2025=+6662.75")

    # (B) forward
    print("\n=== (B) FORWARD: test_year=2025 ruleset on UNSEEN windows ===")
    fwd_rules = rules.loc[rules["test_year"] == 2025]
    fsig = build_signals(fwd_rules, snaps)
    fsig["ets"] = pd.to_datetime(fsig["entry_ts_label"], utc=True)
    for label, lo, hi in [("2025H2..2026Q1", "2025-07-01", "2026-03-21"),
                          ("2026-only", "2026-01-01", "2026-03-21")]:
        win = fsig.loc[(fsig["ets"] >= pd.Timestamp(lo, tz="UTC")) & (fsig["ets"] < pd.Timestamp(hi, tz="UTC"))]
        tr = replay0(win, ohlcv)
        print(f"\n-- {label} ({lo}..{hi}): signals={len(win)} replayed={len(tr)} --")
        for c in (2.0, 4.0, 6.0):
            print(f"   ${c:.0f}/RT: {summ(tr, c)}")
        if not tr.empty:
            m = tr.assign(net=tr["gross_dollars"] - 2.0)
            m["mo"] = m["exit_ts"].dt.tz_convert(None).dt.to_period("M").astype(str)
            print("   by month @ $2:", {k: round(v, 0) for k, v in m.groupby("mo")["net"].sum().items()})


if __name__ == "__main__":
    main()
