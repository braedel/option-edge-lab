"""Unit tests for zb_mbo.codes. The TRADE/FILL side conventions encoded here were first
ATTESTED on real data (reports/zb_taker/attestation.json) per review item A2 -- these tests
lock that verified behavior against regression; they are not the primary oracle."""
import numpy as np

from options_lab.zb_mbo.codes import (
    ADD, CANCEL, DEPTH_CLEAR, FILL, MODIFY, TRADE, action, is_buy, is_sell, signed_flow,
)

BUY = 0x20000000
SELL = 0x10000000
EXCH = 0x80000000


def _ev(code, side=0):
    return np.uint64(code | side)


def test_action_reads_low_byte_not_bit0():
    assert int(action(_ev(FILL, EXCH))) == 13          # high flags ignored
    assert int(action(_ev(TRADE))) == 2
    # documents WHY (ev & 1) is the wrong filter: it misses TRADE(2), matches CANCEL(11)/FILL(13)
    assert (TRADE & 1) == 0 and (CANCEL & 1) == 1 and (FILL & 1) == 1 and (DEPTH_CLEAR & 1) == 1


def test_buy_sell_flags():
    assert is_buy(_ev(TRADE, BUY)) and not is_sell(_ev(TRADE, BUY))
    assert is_sell(_ev(FILL, SELL)) and not is_buy(_ev(FILL, SELL))


def test_signed_flow_trade_is_aggressor_side():
    assert signed_flow(_ev(TRADE, BUY), 5.0) == 5.0
    assert signed_flow(_ev(TRADE, SELL), 5.0) == -5.0


def test_signed_flow_fill_is_resting_opposite_side():
    # resting SELL hit => buy aggressor => +qty ; resting BUY hit => -qty
    assert signed_flow(_ev(FILL, SELL), 4.0) == 4.0
    assert signed_flow(_ev(FILL, BUY), 4.0) == -4.0


def test_signed_flow_nonexecution_actions_are_zero():
    for code in (DEPTH_CLEAR, ADD, CANCEL, MODIFY):
        assert signed_flow(_ev(code, BUY), 9.0) == 0.0
        assert signed_flow(_ev(code, SELL), 9.0) == 0.0


def test_signed_flow_vectorized_matches_scalar():
    ev = np.array([_ev(TRADE, BUY), _ev(FILL, SELL), _ev(ADD, BUY), _ev(TRADE, SELL)], dtype=np.uint64)
    qty = np.array([1.0, 2.0, 3.0, 4.0])
    assert list(signed_flow(ev, qty)) == [1.0, 2.0, 0.0, -4.0]
