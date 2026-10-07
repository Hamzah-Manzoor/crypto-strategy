"""
Trend Pullback v3b - v3, but only buy dips while the market is healthy (Round 2, idea A, version 2 of max 3).

Why: v3 cut trades 10x vs v1 (271 vs 2,714) but still lost on dev data (−7.7%, profit factor 0.91):
     too many dips kept falling. v3b only buys a dip when the coin's 4h trend is clearly up
     (4h EMA50 above 4h EMA200, as in v2) AND Bitcoin is in a long-term uptrend (daily close
     above its 200-day average - the same market filter as idea B).
Should work / fail: as v3, with fewer trades in weak markets.
Changes vs v3: two extra entry filters (4h EMA50 > EMA200; BTC daily > 200-day SMA). Exits unchanged.
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import informative
from trend_pullback_v3 import TrendPullbackV3


class TrendPullbackV3b(TrendPullbackV3):
    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Same 4h indicators as v3, plus EMA50 for the "clear uptrend" filter.
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi2"] = ta.RSI(dataframe, timeperiod=2)
        return dataframe

    @informative("1d", "BTC/{stake}")
    def populate_indicators_btc_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma200"] = ta.SMA(dataframe, timeperiod=200)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        healthy = (dataframe["ema50_4h"] > dataframe["ema200_4h"]) & \
                  (dataframe["btc_usdt_close_1d"] > dataframe["btc_usdt_sma200_1d"])
        dataframe.loc[~healthy, ["enter_long", "enter_tag"]] = (0, None)
        return dataframe
