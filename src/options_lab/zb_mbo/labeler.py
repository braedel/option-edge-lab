"""Latency-adjusted taker round-turn P&L (review A5 / B6 / spec sections 7.1-7.2 / 7.8).

`bbo_timeline(events)` -> the EXACT best-bid/ask over time (one row whenever the touch changes), so an
entry/exit at an arbitrary timestamp reads the real touch rather than a trade-snapshot approximation.

`forward_move(timeline, t_signal, side, latency_ns, horizon_ns, ...)` -> net ticks of a single taker
round-turn: cross the FAR touch at `t_decision = t_signal + latency_ns` (so the trigger's own prints at
t_signal are excluded -- the pre-decision move is NOT captured), hold `horizon_ns`, cross back to flatten;
subtract the $4 round-turn in ticks. A long pays the ask on entry and earns the bid on exit (and vice
versa) -- the honest taker spread, charged both ways.
"""
from __future__ import annotations

import numpy as np

from .book import BookState
from .codes import FILL, TRADE

BBO_DTYPE = np.dtype([("ts", "i8"), ("bid", "f8"), ("ask", "f8")])
TICK = 0.03125
COST_TICKS_DEFAULT = 4.0 / 31.25  # $4 round-turn / $31.25 per tick = 0.128 ticks


def bbo_timeline(events) -> np.ndarray:
    """One BBO row per touch change (book mutations only; TRADE/FILL do not move the book)."""
    ev = events["ev"]
    ts = events["exch_ts"]
    px = events["px"]
    qty = events["qty"]
    oid = events["order_id"]
    acts = (np.asarray(ev, dtype=np.uint64) & np.uint64(0xFF)).astype(np.int64)
    book = BookState()
    rows = []
    last_b = last_a = None
    for i in range(ev.shape[0]):
        if acts[i] == TRADE or acts[i] == FILL:
            continue
        book.apply(ev[i], px[i], qty[i], oid[i])
        bb = book.best_bid()
        ba = book.best_ask()
        if bb != last_b or ba != last_a:
            rows.append((int(ts[i]), np.nan if bb is None else bb, np.nan if ba is None else ba))
            last_b, last_a = bb, ba
    return np.array(rows, dtype=BBO_DTYPE) if rows else np.empty(0, dtype=BBO_DTYPE)


def _touch_at(timeline, t):
    """(bid, ask) active at time t = last row with ts <= t; (nan, nan) if none."""
    j = int(np.searchsorted(timeline["ts"], t, side="right")) - 1
    if j < 0:
        return np.nan, np.nan
    return timeline["bid"][j], timeline["ask"][j]


def forward_move(timeline, t_signal, side, latency_ns, horizon_ns,
                 tick: float = TICK, cost_ticks: float = COST_TICKS_DEFAULT) -> float:
    """Net ticks of one latency-adjusted taker round-turn (nan if the book is one-sided at either point)."""
    t_dec = int(t_signal) + int(latency_ns)
    eb, ea = _touch_at(timeline, t_dec)
    xb, xa = _touch_at(timeline, t_dec + int(horizon_ns))
    if not (np.isfinite(eb) and np.isfinite(ea) and np.isfinite(xb) and np.isfinite(xa)):
        return float("nan")
    if side > 0:          # take long: buy at ask now, sell at bid later
        gross = xb - ea
    else:                 # take short: sell at bid now, buy at ask later
        gross = eb - xa
    return float(gross / tick - cost_ticks)
