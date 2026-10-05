"""LabBaseStrategy: settings shared by every lab strategy.

Strategies inherit from it so they all trade the same way (spot, long only,
1h, market orders) and differ only in their trading idea.
"""

from __future__ import annotations

from freqtrade.optimize.space import Categorical, SKDecimal
from freqtrade.strategy import IStrategy


class LabBaseStrategy(IStrategy):
    INTERFACE_VERSION = 3

    # Spot only: we can buy and later sell, never short.
    can_short = False
    timeframe = "1h"

    # Decide once per finished candle, never on a half-formed one.
    process_only_new_candles = True

    # Exits come from the strategy's exit signal, the ROI table, the stoploss
    # or the trailing stop - whichever hits first.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Market orders: closest match to the backtest assumption of "fill at candle open".
    # (base.json sets the same; repeated here so a strategy file is self-describing.)
    order_types = {
        "entry": "market",
        "exit": "market",
        "emergency_exit": "market",
        "force_entry": "market",
        "force_exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    class HyperOpt:
        # Keep the tuner inside sensible risk limits: no 35% stoplosses,
        # no trailing stop that gives back half the move.
        def stoploss_space():
            return [SKDecimal(-0.15, -0.03, decimals=3, name="stoploss")]

        def trailing_space():
            return [
                Categorical([True], name="trailing_stop"),
                SKDecimal(0.01, 0.08, decimals=3, name="trailing_stop_positive"),
                SKDecimal(0.005, 0.08, decimals=3, name="trailing_stop_positive_offset_p1"),
                Categorical([True], name="trailing_only_offset_is_reached"),
            ]
