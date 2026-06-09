"""Causal per-trade feature stream from L3 replay.

At each TRADE print we snapshot the book state *as of* that print -- features are computed from events
strictly before it -- plus the trade's signed size. These snapshots are the inputs to the trigger
detectors (Phase 2) and the latency-adjusted labeler (Phase 3). Causal by construction (review B2): a
future event cannot change any earlier snapshot, because the replay processes events in exch_ts order
and a snapshot reads only the book accumulated so far.

Pure-Python (correctness first). For the full-span census this is the hot path; profile one real day and
move the book to an array/numba representation if it exceeds the per-day budget (plan v2 / review F1).
"""
from __future__ import annotations

import numpy as np

from .book import BookState
from .codes import TRADE, signed_flow

TICK = 0.03125

SNAP_DTYPE = np.dtype([
    ("ts", "i8"), ("best_bid", "f8"), ("best_ask", "f8"), ("mid", "f8"), ("spread_ticks", "i4"),
    ("bid1", "f8"), ("ask1", "f8"), ("bid3", "f8"), ("ask3", "f8"),
    ("trade_signed", "f8"), ("trade_px", "f8"),
])


def stream_features(events, tick: float = TICK) -> np.ndarray:
    """Return a SNAP_DTYPE array, one causal snapshot per TRADE that has a two-sided book."""
    ev = events["ev"]
    ts = events["exch_ts"]
    px = events["px"]
    qty = events["qty"]
    oid = events["order_id"]
    acts = (np.asarray(ev, dtype=np.uint64) & np.uint64(0xFF)).astype(np.int64)

    book = BookState()
    rows = []
    for i in range(ev.shape[0]):
        if acts[i] == TRADE:
            bb = book.best_bid()
            ba = book.best_ask()
            if bb is not None and ba is not None:
                d_b = book.depth("bid", 3)
                d_a = book.depth("ask", 3)
                rows.append((
                    int(ts[i]), bb, ba, (bb + ba) / 2.0, int(round((ba - bb) / tick)),
                    d_b[0][1], d_a[0][1], sum(q for _, q in d_b), sum(q for _, q in d_a),
                    signed_flow(ev[i], qty[i]), float(px[i]),
                ))
        else:
            book.apply(ev[i], px[i], qty[i], oid[i])
    return np.array(rows, dtype=SNAP_DTYPE) if rows else np.empty(0, dtype=SNAP_DTYPE)
