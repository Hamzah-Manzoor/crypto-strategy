"""
Trend Pullback v2 - buy only deep dips, only in strong uptrends, hold for a real bounce.

Idea:
    Same as v1 (buy sharp 1-3 candle dips inside an uptrend), but v1 took 1,941
    trades in 2 years: its gross edge (+66% before fees) was eaten by fees
    (-23% after). v2 trades far less and asks more of every trade:
      - the uptrend must hold on 4h candles too (4h price > 4h EMA50 > 4h EMA200),
      - the dip must be deeper (RSI(2) < 5 instead of < 10),
      - it holds for a bigger bounce (exit above EMA10 / RSI(2) > 80, not EMA5 / 70).

Should work when:
    Strong, steady uptrends with sharp pullbacks (2023-24, mid 2025).

Should fail when:
    Trend changes: the 4h filter is slower than a crash. Also trades very little
    in sideways or falling markets (by design - cash is a position).

Entry:  1h close > EMA200, 4h close > 4h EMA50 > 4h EMA200, RSI(2) < entry level.
Exit:   close > EMA10 OR RSI(2) > exit level; ROI table; stoploss -8%.
Tunable (hyperopt): RSI(2) entry level, RSI(2) exit level.
Changes vs v1: 4h uptrend filter; deeper dip (5 vs 10); later exit (EMA10/80 vs EMA5/70);
               larger ROI targets.
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IntParameter, informative
from trend_pullback_v1 import TrendPullbackV1


class TrendPullbackV2(TrendPullbackV1):
    minimal_roi = {"0": 0.08, "720": 0.04, "2880": 0.015}
    stoploss = -0.08

    # EMA200 on 4h candles needs ~600 4h candles to settle; Freqtrade applies the
    # startup count to the informative timeframe too.
    startup_candle_count = 600

    rsi_entry = IntParameter(2, 15, default=5, space="buy")
    rsi_exit = IntParameter(60, 95, default=80, space="sell")

    plot_config = {
        "main_plot": {"ema200": {"color": "grey"}, "ema10": {"color": "orange"}, "ema50_4h": {"color": "blue"}},
        "subplots": {"RSI(2)": {"rsi2": {"color": "purple"}}},
    }

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_indicators(dataframe, metadata)
        dataframe["ema10"] = ta.EMA(dataframe, timeperiod=10)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["close"] > dataframe["ema200"])                  # 1h uptrend
                & (dataframe["close_4h"] > dataframe["ema50_4h"])           # 4h uptrend ...
                & (dataframe["ema50_4h"] > dataframe["ema200_4h"])          # ... and a strong one
                & (dataframe["rsi2"] < self.rsi_entry.value)                # deep short-term dip
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "deep_dip_strong_trend")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] > dataframe["ema10"]) | (dataframe["rsi2"] > self.rsi_exit.value),
            ["exit_long", "exit_tag"],
        ] = (1, "bounced")
        return dataframe
