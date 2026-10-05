"""
RSI + Bollinger Reversion v1 - buy short-term panic, sell the bounce.

Idea:
    When price closes below the lower Bollinger Band (unusually far below its
    20-candle average) AND RSI is low (sellers exhausted), a snap-back toward
    the average is likely. Take a quick, small profit; don't wait for a trend.

Should work when:
    Sideways or gently rising markets with sharp, short-lived dips.
    Many small wins, high win rate.

Should fail when:
    Real crashes and bear markets: "oversold" keeps getting more oversold,
    and buying every dip means catching a falling knife. Losses are rarer but
    bigger than wins, so the stoploss matters a lot.

Entry:  RSI(14) below a threshold AND close below the lower Bollinger Band.
Exit:   close back above the middle band, OR RSI above an exit level; quick
        ROI table; stoploss -6%; no trailing stop (we want the quick bounce).
Tunable (hyperopt): RSI entry level, RSI exit level, Bollinger Band width.
Changes vs previous version: none (first version)
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import CategoricalParameter, IntParameter
from labkit.base import LabBaseStrategy


class RsiBbReversionV1(LabBaseStrategy):
    # Take 6% any time, 3% after 6h, 1% after a day - a bounce is quick or not at all.
    minimal_roi = {"0": 0.06, "360": 0.03, "1440": 0.01}
    stoploss = -0.06
    trailing_stop = False

    startup_candle_count = 200

    rsi_entry = IntParameter(20, 40, default=30, space="buy")
    bb_std = CategoricalParameter([1.5, 2.0, 2.5, 3.0], default=2.0, space="buy")
    rsi_exit = IntParameter(55, 75, default=65, space="sell")

    plot_config = {
        "main_plot": {"bb_lower": {"color": "grey"}, "bb_mid": {"color": "orange"}},
        "subplots": {"RSI": {"rsi": {"color": "purple"}}},
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["bb_mid"] = ta.SMA(dataframe, timeperiod=20)
        stdev = ta.STDDEV(dataframe, timeperiod=20, nbdev=1.0)
        for std in self.bb_std.range:
            dataframe[f"bb_lower_{std}"] = dataframe["bb_mid"] - std * stdev
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        lower = dataframe[f"bb_lower_{self.bb_std.value}"]
        dataframe["bb_lower"] = lower  # for charts
        dataframe.loc[
            (
                (dataframe["rsi"] < self.rsi_entry.value)  # sellers exhausted
                & (dataframe["close"] < lower)             # price stretched far below average
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "oversold_band")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        back_to_mean = dataframe["close"] > dataframe["bb_mid"]
        rsi_recovered = dataframe["rsi"] > self.rsi_exit.value
        dataframe.loc[back_to_mean, ["exit_long", "exit_tag"]] = (1, "back_to_mean")
        dataframe.loc[rsi_recovered & ~back_to_mean, ["exit_long", "exit_tag"]] = (1, "rsi_recovered")
        return dataframe
