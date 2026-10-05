"""
Donchian Breakout v1 - the "Turtle" idea: buy new highs, sell new lows.

Idea:
    When price closes above the highest high of the last N candles, it has
    broken out of its recent range - often the start of a new leg up.
    Require above-average volume so the breakout has real buying behind it.
    Exit when price closes below the lowest low of the last M candles
    (M < N, so we get out faster than we got in).

Should work when:
    Markets that break out of ranges and keep going (crypto does this often).
    Few trades, low win rate, but winners much bigger than losers.

Should fail when:
    Fake-outs in sideways markets: price pokes above the range, then falls
    back in. Several small losses in a row are normal for this style.

Entry:  close > highest high of previous N candles AND volume > k x average.
Exit:   close < lowest low of previous M candles; trailing stop locks in
        big moves; stoploss -10%.
Tunable (hyperopt): N (entry channel), M (exit channel), volume multiplier k.
Changes vs previous version: none (first version)
"""

from pandas import DataFrame

from freqtrade.strategy import CategoricalParameter, DecimalParameter
from labkit.base import LabBaseStrategy
from labkit.indicators import donchian_high, donchian_low, volume_ratio


class DonchianBreakoutV1(LabBaseStrategy):
    minimal_roi = {"0": 0.30}
    stoploss = -0.10

    trailing_stop = True
    trailing_stop_positive = 0.03
    trailing_stop_positive_offset = 0.06
    trailing_only_offset_is_reached = True

    startup_candle_count = 120  # longest channel (55) + volume average (20), not recursive

    entry_period = CategoricalParameter([20, 30, 40, 55], default=20, space="buy")
    volume_min = DecimalParameter(0.8, 2.0, decimals=1, default=1.0, space="buy")
    exit_period = CategoricalParameter([10, 15, 20], default=10, space="sell")

    plot_config = {
        "main_plot": {"dc_high": {"color": "green"}, "dc_low": {"color": "red"}},
        "subplots": {"Volume ratio": {"vol_ratio": {"color": "blue"}}},
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for period in self.entry_period.range:
            dataframe[f"dc_high_{period}"] = donchian_high(dataframe, period)
        for period in self.exit_period.range:
            dataframe[f"dc_low_{period}"] = donchian_low(dataframe, period)
        dataframe["vol_ratio"] = volume_ratio(dataframe, 20)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        channel_high = dataframe[f"dc_high_{self.entry_period.value}"]
        dataframe["dc_high"] = channel_high  # for charts
        dataframe.loc[
            (
                (dataframe["close"] > channel_high)                     # new N-candle high
                & (dataframe["vol_ratio"] > self.volume_min.value)      # with real buying
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        channel_low = dataframe[f"dc_low_{self.exit_period.value}"]
        dataframe["dc_low"] = channel_low  # for charts
        dataframe.loc[dataframe["close"] < channel_low, ["exit_long", "exit_tag"]] = (1, "breakdown")
        return dataframe
