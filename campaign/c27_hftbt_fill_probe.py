"""REAL hftbacktest fill verification -- no proxy, no subagent hearsay. Does the installed engine signal
fills correctly? Build a tiny synthetic L3 book via correct_event_order, then:
  (A) submit a MARKETABLE limit buy (crosses the ask) -> expect FILLED, exec_qty>0, position>0;
  (B) submit a PASSIVE resting buy at the bid, then feed a sell-aggressor TRADE through that level ->
      observe whether the resting order fills.
Print exactly what the engine reports at each step. Run: .venv-mbo python campaign/c27_hftbt_fill_probe.py
"""
import numpy as np
from hftbacktest import (
    BacktestAsset, HashMapMarketDepthBacktest, GTC, LIMIT,
    BUY_EVENT, SELL_EVENT, DEPTH_CLEAR_EVENT, ADD_ORDER_EVENT, TRADE_EVENT,
)
from hftbacktest.data.validation import correct_event_order, correct_local_timestamp
from hftbacktest.types import event_dtype

TICK = 0.03125
ST = {0: "NONE", 1: "NEW", 2: "EXPIRED", 3: "FILLED", 4: "CANCELED", 5: "PARTIAL", 6: "REJECTED"}


def E(action, sideflag, ts, px, qty, oid):
    # raw event: action|side in ev (EXCH/LOCAL flags are added by correct_event_order); exch_ts==local_ts
    return (np.uint64(int(action) | int(sideflag)), ts, ts, float(px), float(qty), np.uint64(oid), 0, 0.0)


raw = np.array([
    E(DEPTH_CLEAR_EVENT, 0,          1_000_000, 0.0,            0, 0),
    E(ADD_ORDER_EVENT, BUY_EVENT,    2_000_000, 110.00,         5, 101),  # bid 5 @110.00
    E(ADD_ORDER_EVENT, SELL_EVENT,   3_000_000, 110.00 + TICK,  5, 102),  # ask 5 @110.03125
    E(ADD_ORDER_EVENT, BUY_EVENT,    4_000_000, 110.00 - TICK,  7, 103),
    E(ADD_ORDER_EVENT, SELL_EVENT,   5_000_000, 110.00 + 2*TICK, 7, 104),
    E(TRADE_EVENT, SELL_EVENT,      30_000_000, 110.00,        10, 0),    # sell-aggressor through the bid (qty 10 > queue 5)
    E(ADD_ORDER_EVENT, BUY_EVENT,   50_000_000, 110.00,         5, 105),
    E(ADD_ORDER_EVENT, SELL_EVENT,  60_000_000, 110.00 + TICK,  5, 106),
    E(ADD_ORDER_EVENT, BUY_EVENT,   90_000_000, 110.00,         5, 107),
    E(ADD_ORDER_EVENT, SELL_EVENT, 100_000_000, 110.00 + TICK,  5, 108),
], dtype=event_dtype)

data = correct_local_timestamp(raw, base_latency=0)
data = correct_event_order(data,
                           np.argsort(data['exch_ts'], kind='mergesort'),
                           np.argsort(data['local_ts'], kind='mergesort'))
print(f"events: raw={len(raw)} processed={len(data)} (correct_event_order split EXCH/LOCAL)")

asset = (BacktestAsset().data(data).tick_size(TICK).lot_size(1.0)
         .no_partial_fill_exchange().l3_fifo_queue_model()
         .constant_order_latency(1_000, 1_000).last_trades_capacity(100))
hbt = HashMapMarketDepthBacktest([asset])


def show(tag, oid):
    o = hbt.orders(0).get(oid)
    if o is None:
        print(f"  {tag}: order {oid} not found")
        return
    print(f"  {tag}: status={ST.get(int(o.status), o.status)} exec_qty={o.exec_qty} "
          f"exec_px={o.exec_price if int(o.status) in (3, 5) else '-'} maker={bool(o.arr[0]['maker'])} pos={hbt.position(0)}")


try:
    rc = hbt.elapse(6_000_000)
    d = hbt.depth(0)
    print(f"book after build: best_bid={d.best_bid} best_ask={d.best_ask} rc={rc}")

    print("TEST A -- marketable LIMIT buy @ ask (should fill, taker):")
    hbt.submit_buy_order(0, 1, 110.00 + TICK, 1.0, GTC, LIMIT, False)
    hbt.elapse(2_000_000)
    show("A", 1)

    print("TEST B -- passive LIMIT buy @ bid (rest, then a sell-aggressor trades 10 through the 5-deep bid):")
    hbt.submit_buy_order(0, 2, 110.00, 1.0, GTC, LIMIT, False)
    hbt.elapse(2_000_000)
    show("B pre-trade", 2)
    hbt.elapse(40_000_000)  # advance past the 30ms sell-aggressor trade of qty 10 at 110.00
    show("B post-trade", 2)

    sv = hbt.state_values(0)
    print(f"final: pos={hbt.position(0)} balance={sv.balance} fee={sv.fee} num_trades={sv.num_trades}")
finally:
    hbt.close()
