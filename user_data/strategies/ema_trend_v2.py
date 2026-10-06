"""
EMA Trend v2 - the same crossover idea, decided on 4h candles with slower averages.

Idea:
    v1 (1h, EMA 12/50) made +26% before fees but -4% after, over 675 trades:
    1h crossovers whipsaw too often. v2 makes the decision on 4h candles with
    slower averages (21/55), so it only acts on bigger trend changes, and gives
    winners more room (trailing stop starts at +10% instead of +6%).
    It still runs on the 1h engine, so stoploss and trailing stop are checked
    every hour.

Should work when:
    Multi-week trends (most of 2024, late 2024, mid 2025).

Should fail when:
    Long sideways ranges (fewer whipsaws than v1, but each costs more) and
    sharp V-shaped reversals (4h averages react days late).

Entry:  4h EMA fast crosses above 4h EMA slow, while 4h close > 4h EMA200.
Exit:   4h EMA fast crosses below 4h EMA slow; trailing stop; stoploss -10%.
Tunable (hyperopt): 4h fast EMA length, 4h slow EMA length.
Changes vs v1: decisions on 4h instead of 1h; EMAs 21/55 instead of 12/50;
               wider stop (-10%) and trailing stop (+10% trigger, 5% trail).
"""

from pandas import DataFrame
import talib.abstract as ta
from technical import qtpylib

from freqtrade.strategy import CategoricalParameter, informative
from ema_trend_v1 import EmaTrendV1


class EmaTrendV2(EmaTrendV1):
    minimal_roi = {"0": 0.50}
    stoploss = -0.10

    trailing_stop = True
    trailing_stop_positive = 0.05
    trailing_stop_positive_offset = 0.10
    trailing_only_offset_is_reached = True

    startup_candle_count = 600  # 4h EMA200

    fast_period = CategoricalParameter([12, 21, 26], default=21, space="buy")
    slow_period = CategoricalParameter([50, 55, 72], default=55, space="buy")

    plot_config = {
        "main_plot": {"ema_fast_4h": {"color": "orange"}, "ema_slow_4h": {"color": "blue"},
                      "ema_trend_4h": {"color": "grey"}},
    }

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for period in set(self.fast_period.range) | set(self.slow_period.range):
            dataframe[f"ema_{period}"] = ta.EMA(dataframe, timeperiod=period)
        dataframe["ema_trend"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe  # every decision uses the 4h columns

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fast = dataframe[f"ema_{self.fast_period.value}_4h"]
        slow = dataframe[f"ema_{self.slow_period.value}_4h"]
        dataframe["ema_fast_4h"], dataframe["ema_slow_4h"] = fast, slow  # for charts
        dataframe.loc[
            (
                qtpylib.crossed_above(fast, slow)                          # 4h momentum turned up
                & (dataframe["close_4h"] > dataframe["ema_trend_4h"])      # 4h long-term trend is up
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "ema_cross_up_4h")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fast = dataframe[f"ema_{self.fast_period.value}_4h"]
        slow = dataframe[f"ema_{self.slow_period.value}_4h"]
        dataframe.loc[qtpylib.crossed_below(fast, slow), ["exit_long", "exit_tag"]] = (1, "ema_cross_down_4h")
        return dataframe
