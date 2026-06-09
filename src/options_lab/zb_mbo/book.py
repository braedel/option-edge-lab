"""Causal L3 order-book replay with per-order identity (databento ZB MBO).

Rules (databento handling guide section 9.2 + review B1):
  - ADD/CANCEL/MODIFY/DEPTH_CLEAR mutate the book; TRADE(2) and FILL(13) do NOT (the matching
    CANCEL/MODIFY on the resting side performs the removal/reduction).
  - MODIFY qty is a FULL replacement; a MODIFY that changes price moves the order across levels.
  - Drop-safe + counted on anomalies: CANCEL/MODIFY on an unknown order_id; ADD on an existing
    order_id (replace); a decrement that would drive a level negative.
Pure-Python and deterministic; replays events in exch_ts order. Best/depth queries are O(levels)
and intended for snapshot/trigger moments, not every event.
"""
from __future__ import annotations

from .codes import ADD, CANCEL, DEPTH_CLEAR, FILL, MODIFY, TRADE, action, is_buy


class BookState:
    __slots__ = ("orders", "bids", "asks", "counters")

    def __init__(self):
        self.orders: dict[int, tuple[str, float, float]] = {}  # oid -> (side 'B'/'A', px, qty)
        self.bids: dict[float, float] = {}                     # px -> total displayed qty
        self.asks: dict[float, float] = {}
        self.counters = {"unknown_reductions": 0, "dup_adds": 0, "negative_depth": 0}

    def _levels(self, side: str) -> dict:
        return self.bids if side == "B" else self.asks

    def _add_qty(self, side: str, px: float, dq: float) -> None:
        lv = self._levels(side)
        q = lv.get(px, 0.0) + dq
        if q > 0:
            lv[px] = q
        else:
            if q < 0:
                self.counters["negative_depth"] += 1
            lv.pop(px, None)

    def apply(self, ev, px, qty, order_id) -> None:
        a = int(action(ev))
        if a == DEPTH_CLEAR:
            self.orders.clear()
            self.bids.clear()
            self.asks.clear()
            return
        if a == TRADE or a == FILL:
            return  # informational; the resting-side CANCEL/MODIFY mutates the book
        side = "B" if is_buy(ev) else "A"
        oid = int(order_id)
        px = float(px)
        qty = float(qty)
        if a == ADD:
            old = self.orders.get(oid)
            if old is not None:  # re-ADD of a live id: replace deterministically
                self.counters["dup_adds"] += 1
                self._add_qty(old[0], old[1], -old[2])
            self.orders[oid] = (side, px, qty)
            self._add_qty(side, px, qty)
        elif a == CANCEL:
            old = self.orders.pop(oid, None)
            if old is None:
                self.counters["unknown_reductions"] += 1
                return
            self._add_qty(old[0], old[1], -old[2])
        elif a == MODIFY:
            old = self.orders.get(oid)
            if old is None:
                self.counters["unknown_reductions"] += 1
                return
            self._add_qty(old[0], old[1], -old[2])          # remove at old (side, price)
            self.orders[oid] = (old[0], px, qty)            # full replace; price may change
            self._add_qty(old[0], px, qty)

    def best_bid(self):
        return max(self.bids) if self.bids else None

    def best_ask(self):
        return min(self.asks) if self.asks else None

    def depth(self, side: str, levels: int) -> list[tuple[float, float]]:
        lv = self.bids if side == "bid" else self.asks
        prices = sorted(lv, reverse=(side == "bid"))[:levels]
        return [(p, lv[p]) for p in prices]

    def n_orders(self) -> int:
        return len(self.orders)
