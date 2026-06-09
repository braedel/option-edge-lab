"""Causal feature-stream tests, incl. the review B2 leak proof: corrupting FUTURE events must not
change any earlier snapshot."""
import numpy as np

from options_lab.zb_mbo.codes import ADD, TRADE
from options_lab.zb_mbo.stream import SNAP_DTYPE, TICK, stream_features

BUY = 0x20000000
SELL = 0x10000000

_EV = np.dtype([("ev", "u8"), ("exch_ts", "i8"), ("local_ts", "i8"), ("px", "f8"),
                ("qty", "f8"), ("order_id", "u8"), ("ival", "i8"), ("fval", "f8")])


def mk(rows):
    """rows: list of (action, side, px, qty, oid, ts)."""
    return np.array([(np.uint64(a | s), ts, 0, px, q, oid, 0, 0.0) for (a, s, px, q, oid, ts) in rows],
                    dtype=_EV)


def test_snapshot_at_trade_is_causal_book_state():
    ev = mk([
        (ADD, BUY, 110.0, 5, 1, 1),
        (ADD, BUY, 110.0 - TICK, 7, 2, 2),
        (ADD, SELL, 110.0 + TICK, 4, 3, 3),
        (ADD, SELL, 110.0 + 2 * TICK, 9, 4, 4),
        (TRADE, SELL, 110.0, 2, 0, 5),   # sell-aggressor trade
    ])
    s = stream_features(ev)
    assert s.dtype == SNAP_DTYPE and len(s) == 1
    r = s[0]
    assert r["best_bid"] == 110.0 and r["best_ask"] == 110.0 + TICK and r["spread_ticks"] == 1
    assert r["bid1"] == 5 and r["ask1"] == 4
    assert r["bid3"] == 5 + 7 and r["ask3"] == 4 + 9      # only 2 levels exist per side
    assert r["trade_signed"] == -2.0                      # sell aggressor -> negative


def test_future_events_do_not_change_past_snapshots():
    base = mk([
        (ADD, BUY, 110.0, 5, 1, 1),
        (ADD, SELL, 110.0 + TICK, 5, 2, 2),
        (TRADE, SELL, 110.0, 1, 0, 3),     # snapshot #0 (ts=3) -- BEFORE the corruption window
        (ADD, BUY, 109.0, 5, 3, 4),
        (TRADE, SELL, 109.0, 1, 0, 5),     # snapshot #1 (ts=5)
    ])
    s0 = stream_features(base)
    pert = base.copy()
    pert["px"][3:] *= 2.0          # corrupt FUTURE prices (index >= 3)
    pert["qty"][3:] += 100.0       # and future sizes
    s1 = stream_features(pert)
    assert len(s0) == 2 and len(s1) >= 1
    assert s0[0].tolist() == s1[0].tolist()   # the pre-corruption snapshot is bit-identical
