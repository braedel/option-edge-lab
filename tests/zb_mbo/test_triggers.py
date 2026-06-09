"""Trigger-detector tests with review-B3 oracles: boundary battery, an independent hand-traced
median, causality (future trade can't change an earlier episode), and refractory dedupe."""
import numpy as np

from options_lab.zb_mbo.stream import SNAP_DTYPE, TICK
from options_lab.zb_mbo.triggers import detect_event, detect_sweep, detect_vacuum


def snaps(specs):
    rows = []
    for i, sp in enumerate(specs):
        rows.append((
            sp.get("ts", i + 1), 110.0, 110.0 + TICK, 110.0 + TICK / 2, 1,
            sp.get("bid1", 10.0), sp.get("ask1", 10.0),
            sp.get("bid3", 30.0), sp.get("ask3", 30.0),
            sp.get("signed", 0.0), 110.0,
        ))
    return np.array(rows, dtype=SNAP_DTYPE)


def test_vacuum_boundary_battery():
    # window=4 trailing median of bid3 = 30; thresh=0.5 -> fires iff hit < 15.
    base = [{"signed": -1.0, "bid3": 30.0} for _ in range(4)]
    below = base + [{"signed": -1.0, "bid3": 14.0, "ts": 100}]   # 14 < 15 -> fire
    above = base + [{"signed": -1.0, "bid3": 16.0, "ts": 100}]   # 16 > 15 -> no fire
    assert len(detect_vacuum(snaps(below), 0.5, 4, 1)) == 1
    assert len(detect_vacuum(snaps(above), 0.5, 4, 1)) == 0


def test_vacuum_independent_median_trace():
    # trailing window=3 of bid3 [10,20,30] -> median 20; thresh=0.6 -> fire iff hit < 12.
    sp = [{"signed": -1.0, "bid3": 10.0}, {"signed": -1.0, "bid3": 20.0},
          {"signed": -1.0, "bid3": 30.0}, {"signed": -1.0, "bid3": 11.0, "ts": 50}]
    assert len(detect_vacuum(snaps(sp), 0.6, 3, 1)) == 1
    sp[-1]["bid3"] = 13.0
    assert len(detect_vacuum(snaps(sp), 0.6, 3, 1)) == 0


def test_vacuum_side_is_aggression_direction():
    sp = [{"signed": -1.0, "bid3": 30.0} for _ in range(4)] + [{"signed": -1.0, "bid3": 5.0, "ts": 100}]
    ep = detect_vacuum(snaps(sp), 0.5, 4, 1)
    assert ep[0]["side"] == -1 and ep[0]["family"] == "A"   # sell-aggressor -> short-direction take


def test_vacuum_causal_future_does_not_change_episode():
    sp = [{"signed": -1.0, "bid3": 30.0} for _ in range(4)] + \
         [{"signed": -1.0, "bid3": 10.0, "ts": 100}, {"signed": -1.0, "bid3": 10.0, "ts": 200}]
    ep0 = detect_vacuum(snaps(sp), 0.5, 4, 1)
    sp2 = [dict(x) for x in sp]
    sp2[-1]["bid3"] = 0.0          # corrupt the LATER (future) snapshot
    ep1 = detect_vacuum(snaps(sp2), 0.5, 4, 1)
    assert ep0[0]["ts"] == ep1[0]["ts"] == 100


def test_sweep_boundary_battery():
    base = [{"signed": -1.0} for _ in range(5)]   # trailing-median |size| = 1
    assert len(detect_sweep(snaps(base + [{"signed": -5.0, "ts": 100}]), 3.0, 5, 1)) == 1
    assert len(detect_sweep(snaps(base + [{"signed": -2.0, "ts": 100}]), 3.0, 5, 1)) == 0


def test_event_fires_inside_window_only():
    sp = [{"signed": -1.0, "ts": 10}, {"signed": 1.0, "ts": 150}, {"signed": -1.0, "ts": 300}]
    ep = detect_event(snaps(sp), np.array([(100, 200)]), 1)
    assert len(ep) == 1 and ep[0]["ts"] == 150 and ep[0]["family"] == "C"


def test_refractory_dedupes_close_episodes():
    sp = [{"signed": -1.0, "bid3": 30.0} for _ in range(4)] + \
         [{"signed": -1.0, "bid3": 10.0, "ts": 100}, {"signed": -1.0, "bid3": 10.0, "ts": 105}]
    assert len(detect_vacuum(snaps(sp), 0.5, 4, refractory_ns=50)) == 1   # 105 within 50ns of 100
    assert len(detect_vacuum(snaps(sp), 0.5, 4, refractory_ns=1)) == 2
