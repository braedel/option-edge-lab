"""Action/flag decode + signed order-flow for ZB databento MBO npz records.

Empirically ATTESTED on real data 2026-06-08 (reports/zb_taker/attestation.json,
zb_2024-12.npz): the RAW npz action space is exactly
    {2 TRADE, 3 DEPTH_CLEAR, 10 ADD, 11 CANCEL, 12 MODIFY, 13 FILL}
with clear == 3 (NOT the hftbacktest engine's DEPTH == 1 enum -- never conflate the
two code spaces). TRADE flag = aggressor side; FILL flag = resting side (OPPOSITE).
Verified on a real session: per-day Sum(TRADE qty) == Sum(FILL qty) to 0.3% (ratio
1.0028), and signed flow computed via the TRADE-aggressor and FILL-resting conventions
AGREE in sign and track the day's price drift.

NEVER use the bit-0 (ev & 1) trap: bit 0 is set on CLEAR(3)/CANCEL(11)/FILL(13) and
NOT on the real TRADE(2), so it both misses trades and matches a flood of cancels/fills.
"""
from __future__ import annotations

import numpy as np

# Raw npz action codes (databento packing). Attested; distinct from the hftbacktest engine enum.
TRADE, DEPTH_CLEAR, ADD, CANCEL, MODIFY, FILL = 2, 3, 10, 11, 12, 13
RAW_ACTIONS = frozenset({TRADE, DEPTH_CLEAR, ADD, CANCEL, MODIFY, FILL})

_BUY = np.uint64(0x20000000)
_SELL = np.uint64(0x10000000)
_LOWBYTE = np.uint64(0xFF)


def action(ev):
    """Action code = low byte of ev (`ev & 0xFF`). Scalars or uint64 arrays. NEVER `ev & 1`."""
    return np.asarray(ev, dtype=np.uint64) & _LOWBYTE


def is_buy(ev):
    return (np.asarray(ev, dtype=np.uint64) & _BUY) != 0


def is_sell(ev):
    return (np.asarray(ev, dtype=np.uint64) & _SELL) != 0


def signed_flow(ev, qty):
    """Signed aggressor volume (+ = buy pressure), branching on action code.

    TRADE(2): flag = aggressor  -> +qty if buy-aggressor  else -qty.
    FILL(13): flag = resting (OPPOSITE of aggressor) -> +qty if resting-sell else -qty.
    All other actions contribute 0. Vectorized over uint64 / float arrays; returns a
    float for scalar input.
    """
    ev = np.asarray(ev, dtype=np.uint64)
    qty = np.asarray(qty, dtype=np.float64)
    a = ev & _LOWBYTE
    buy = (ev & _BUY) != 0
    sell = (ev & _SELL) != 0
    out = np.zeros(np.broadcast(ev, qty).shape, dtype=np.float64)
    out = np.where(a == TRADE, np.where(buy, qty, -qty), out)
    out = np.where(a == FILL, np.where(sell, qty, -qty), out)
    return float(out) if out.ndim == 0 else out
