"""
Trend Pullback v1 - buy short dips inside an uptrend (Connors RSI-2 style).

Idea:
    In an uptrend (price above its 200-candle average), sharp 1-3 candle dips
    are usually bought by other traders. RSI(2) - an RSI over just 2 candles -
    drops below 10 on such dips. Buy the dip, sell as soon as price pops back
    above its 5-candle average. A mix of trend following (only in uptrends)
    and mean reversion (buy weakness, sell strength).

Should work when:
    Steady uptrends with normal noise. High win rate, short holding time.

Should fail when:
    The "dip" is actually the start of a trend change: the uptrend filter is
    slow to react, so the first leg of a crash gets bought. Also suffers in
    fast markets where 1h dips keep going (fees eat small wins).

Entry:  close > EMA200 AND RSI(2) < entry level.
Exit:   close > EMA5 OR RSI(2) > exit level; ROI table; stoploss -8%.
Tunable (hyperopt): RSI(2) entry level, RSI(2) exit level.
Changes vs previous version: none (first version)
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IntParameter
from labkit.base import LabBaseStrategy


class TrendPullbackV1(LabBaseStrategy):
    minimal_roi = {"0": 0.05, "720": 0.025, "2880": 0.0}
    stoploss = -0.08
    trailing_stop = False

    startup_candle_count = 600  # EMA200 needs ~3x its length to settle

    rsi_entry = IntParameter(3, 20, default=10, space="buy")
    rsi_exit = IntParameter(50, 90, default=70, space="sell")

    plot_config = {
        "main_plot": {"ema200": {"color": "grey"}, "ema5": {"color": "orange"}},
        "subplots": {"RSI(2)": {"rsi2": {"color": "purple"}}},
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["ema5"] = ta.EMA(dataframe, timeperiod=5)
        dataframe["rsi2"] = ta.RSI(dataframe, timeperiod=2)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["close"] > dataframe["ema200"])     # uptrend
                & (dataframe["rsi2"] < self.rsi_entry.value)   # sharp short-term dip
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "dip_in_uptrend")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] > dataframe["ema5"]) | (dataframe["rsi2"] > self.rsi_exit.value),
            ["exit_long", "exit_tag"],
        ] = (1, "bounced")
        return dataframe
