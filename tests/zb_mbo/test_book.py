"""L3 BookState replay correctness, including review item B1 edge cases (price-changing MODIFY
cross-level move, ADD-on-existing-id, MODIFY/CANCEL-on-unknown-id) and the guide rule that
TRADE/FILL do not mutate the book (the matching CANCEL/MODIFY on the resting side does)."""
import numpy as np

from options_lab.zb_mbo.book import BookState
from options_lab.zb_mbo.codes import ADD, CANCEL, DEPTH_CLEAR, FILL, MODIFY, TRADE

BUY = 0x20000000
SELL = 0x10000000
TICK = 0.03125


def ev(a, side=BUY):
    return np.uint64(a | side)


def test_add_best_and_depth_aggregates():
    b = BookState()
    b.apply(ev(ADD, BUY), 110.00, 7, 1)
    b.apply(ev(ADD, BUY), 110.00, 3, 2)
    b.apply(ev(ADD, SELL), 110.00 + TICK, 4, 3)
    assert b.best_bid() == 110.00 and b.best_ask() == 110.00 + TICK
    assert b.depth("bid", 1) == [(110.00, 10.0)]
    assert b.n_orders() == 3


def test_modify_qty_is_full_replacement_same_price():
    b = BookState()
    b.apply(ev(ADD, BUY), 110.0, 7, 1)
    b.apply(ev(ADD, BUY), 110.0, 3, 2)
    b.apply(ev(MODIFY, BUY), 110.0, 2, 1)  # oid1 7 -> 2
    assert b.depth("bid", 1) == [(110.0, 5.0)]


def test_modify_price_change_moves_across_levels():
    b = BookState()
    b.apply(ev(ADD, BUY), 110.0, 5, 1)
    b.apply(ev(MODIFY, BUY), 110.0 - TICK, 5, 1)  # reprice down one tick
    assert b.best_bid() == 110.0 - TICK
    assert 110.0 not in dict(b.depth("bid", 5))


def test_cancel_removes_order_and_qty():
    b = BookState()
    b.apply(ev(ADD, BUY), 110.0, 7, 1)
    b.apply(ev(ADD, BUY), 110.0, 3, 2)
    b.apply(ev(CANCEL, BUY), 110.0, 3, 2)
    assert b.depth("bid", 1) == [(110.0, 7.0)] and b.n_orders() == 1


def test_trade_and_fill_do_not_mutate_book():
    b = BookState()
    b.apply(ev(ADD, BUY), 110.0, 7, 1)
    n = b.n_orders()
    b.apply(ev(TRADE, SELL), 110.0, 1, 0)  # trade print -> no-op
    b.apply(ev(FILL, BUY), 110.0, 1, 1)    # fill leg -> no-op (matching cancel/modify handles removal)
    assert b.n_orders() == n and b.depth("bid", 1) == [(110.0, 7.0)]


def test_depth_clear_resets_everything():
    b = BookState()
    b.apply(ev(ADD, BUY), 110.0, 5, 1)
    b.apply(ev(ADD, SELL), 110.0 + TICK, 5, 2)
    b.apply(ev(DEPTH_CLEAR), 0.0, 0, 0)
    assert b.best_bid() is None and b.best_ask() is None and b.n_orders() == 0


def test_unknown_cancel_is_drop_safe_and_counted():
    b = BookState()
    b.apply(ev(ADD, BUY), 110.0, 5, 1)
    b.apply(ev(CANCEL, BUY), 109.0, 3, 999)  # unknown oid
    assert b.n_orders() == 1 and b.counters["unknown_reductions"] == 1


def test_modify_unknown_is_drop_safe_and_counted():
    b = BookState()
    b.apply(ev(MODIFY, BUY), 110.0, 5, 777)
    assert b.n_orders() == 0 and b.counters["unknown_reductions"] == 1


def test_dup_add_replaces_old_and_counted():
    b = BookState()
    b.apply(ev(ADD, BUY), 110.0, 5, 1)
    b.apply(ev(ADD, BUY), 109.0, 2, 1)  # same oid re-added at a new price
    assert b.n_orders() == 1 and b.best_bid() == 109.0 and b.counters["dup_adds"] == 1
