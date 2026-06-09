"""Latency-adjusted labeler tests: the move is measured from t+latency (review A5/7.1) so a
pre-decision jump is NOT captured, and a taker pays the far touch both ways (7.8)."""
import numpy as np

from options_lab.zb_mbo.codes import ADD
from options_lab.zb_mbo.labeler import BBO_DTYPE, COST_TICKS_DEFAULT, TICK, bbo_timeline, forward_move

BUY = 0x20000000
SELL = 0x10000000
_EV = np.dtype([("ev", "u8"), ("exch_ts", "i8"), ("local_ts", "i8"), ("px", "f8"),
                ("qty", "f8"), ("order_id", "u8"), ("ival", "i8"), ("fval", "f8")])


def mk(rows):
    return np.array([(np.uint64(a | s), ts, 0, px, q, oid, 0, 0.0) for (a, s, px, q, oid, ts) in rows],
                    dtype=_EV)


def tl(rows):
    return np.array(rows, dtype=BBO_DTYPE)


def test_bbo_timeline_records_touch_changes():
    ev = mk([(ADD, BUY, 110.0, 5, 1, 1), (ADD, SELL, 110.0 + TICK, 5, 2, 2),
             (ADD, BUY, 110.0 + 0.5 * TICK, 3, 3, 5)])  # improves the bid -> new touch
    t = bbo_timeline(ev)
    assert t.dtype == BBO_DTYPE
    assert t[-1]["bid"] == 110.0 + 0.5 * TICK and t[-1]["ask"] == 110.0 + TICK


def test_forward_move_long_net_is_move_minus_cost():
    timeline = tl([(0, 110.0, 110.0 + TICK), (5000, 110.0 + 2 * TICK, 110.0 + 3 * TICK)])
    # t_signal=0, latency=1000 -> entry from row@0: ask=110+1T ; horizon=10000 -> exit@11000 row@5000: bid=110+2T
    nm = forward_move(timeline, t_signal=0, side=1, latency_ns=1000, horizon_ns=10000, tick=TICK)
    assert abs(nm - (1.0 - COST_TICKS_DEFAULT)) < 1e-9   # +1 tick gross, minus round-turn cost


def test_forward_move_excludes_pre_decision_jump():
    # price jumps +5 ticks BEFORE the decision; the taker enters after it (pays the jumped ask), so the
    # pre-decision move is not free profit -- this is the whole point of measuring from t+latency.
    timeline = tl([(0, 110.0, 110.0 + TICK),
                   (500, 110.0 + 5 * TICK, 110.0 + 6 * TICK),
                   (5000, 110.0 + 5 * TICK, 110.0 + 6 * TICK)])
    nm = forward_move(timeline, t_signal=0, side=1, latency_ns=1000, horizon_ns=10000, tick=TICK)
    # entry ask = 110+6T (post-jump), exit bid = 110+5T -> gross -1 tick
    assert abs(nm - (-1.0 - COST_TICKS_DEFAULT)) < 1e-9


def test_latency_changes_entry_touch():
    timeline = tl([(0, 110.0, 110.0 + TICK), (2000, 110.0 + 4 * TICK, 110.0 + 5 * TICK),
                   (50000, 110.0 + 4 * TICK, 110.0 + 5 * TICK)])
    short_lat = forward_move(timeline, 0, 1, 1000, 100000, tick=TICK)   # entry before the 2000 move
    long_lat = forward_move(timeline, 0, 1, 3000, 100000, tick=TICK)    # entry after it
    assert short_lat != long_lat


def test_one_sided_book_returns_nan():
    timeline = tl([(0, 110.0, np.nan)])
    assert np.isnan(forward_move(timeline, 0, 1, 1000, 10000, tick=TICK))
