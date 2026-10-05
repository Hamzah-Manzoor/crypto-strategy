"""
EMA Trend v1 - classic moving-average crossover with a long-term trend filter.

Idea:
    When a fast moving average crosses above a slow one, short-term momentum
    has turned up. Only act on it while price is above the 200-candle average
    (the long-term trend is up), so we buy strength in uptrends and stay out
    of bear markets.

Should work when:
    Long, smooth trends (2023-24 style rallies). One good trend pays for many
    small losses.

Should fail when:
    Choppy sideways markets: the averages cross back and forth, every cross is
    a small loss plus fees ("whipsaw"). Also gives back part of every move,
    because averages react late at tops.

Entry:  fast EMA crosses above slow EMA, while close > EMA200.
Exit:   fast EMA crosses below slow EMA; a trailing stop locks in big moves;
        stoploss -8%.
Tunable (hyperopt): fast EMA length, slow EMA length.
Changes vs previous version: none (first version)
"""

from pandas import DataFrame
import talib.abstract as ta
from technical import qtpylib

from freqtrade.strategy import CategoricalParameter
from labkit.base import LabBaseStrategy


class EmaTrendV1(LabBaseStrategy):
    minimal_roi = {"0": 0.30}  # let trends run; only take a very large win early
    stoploss = -0.08

    # Once 6% up, sell if price drops 3% from the best price since entry.
    trailing_stop = True
    trailing_stop_positive = 0.03
    trailing_stop_positive_offset = 0.06
    trailing_only_offset_is_reached = True

    # EMA200 needs ~3x its length to settle (verified by recursive-analysis).
    startup_candle_count = 600

    fast_period = CategoricalParameter([8, 12, 16, 21, 26], default=12, space="buy")
    slow_period = CategoricalParameter([34, 50, 72, 100], default=50, space="buy")

    plot_config = {
        "main_plot": {
            "ema_fast": {"color": "orange"},
            "ema_slow": {"color": "blue"},
            "ema_trend": {"color": "grey"},
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for period in set(self.fast_period.range) | set(self.slow_period.range):
            dataframe[f"ema_{period}"] = ta.EMA(dataframe, timeperiod=period)
        dataframe["ema_trend"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fast = dataframe[f"ema_{self.fast_period.value}"]
        slow = dataframe[f"ema_{self.slow_period.value}"]
        dataframe["ema_fast"], dataframe["ema_slow"] = fast, slow  # for charts
        dataframe.loc[
            (
                qtpylib.crossed_above(fast, slow)            # momentum turned up
                & (dataframe["close"] > dataframe["ema_trend"])  # long-term trend is up
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "ema_cross_up")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fast = dataframe[f"ema_{self.fast_period.value}"]
        slow = dataframe[f"ema_{self.slow_period.value}"]
        dataframe.loc[qtpylib.crossed_below(fast, slow), ["exit_long", "exit_tag"]] = (1, "ema_cross_down")
        return dataframe
