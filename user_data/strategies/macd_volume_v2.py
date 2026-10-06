"""
MACD Volume v2 - v1's momentum signal, only with the 4h trend and a bigger volume burst.

Idea:
    v1 was the only strategy profitable after fees in-sample (+18%, 695 trades),
    but fees still took 36 percentage points of its +54% gross. v2 keeps the
    same signal and removes the weakest trades:
      - only trade when the 4h trend is up (4h close > 4h EMA50 > 4h EMA200),
      - require a bigger volume burst (2.0x average by default, was 1.5x).

Should work when:
    Momentum bursts that go with the bigger trend.

Should fail when:
    Sideways markets where the 4h trend filter flips on and off; sharp
    V-reversals (MACD is late at both ends).

Entry:  1h MACD crosses above signal, volume > k x average, close > EMA100,
        4h close > 4h EMA50 > 4h EMA200.
Exit:   MACD crosses below signal; ROI table; stoploss -8%.
Tunable (hyperopt): MACD speed set, volume multiplier k.
Changes vs v1: 4h uptrend filter; default volume multiplier 2.0 (range 1.5-3.5).
"""

from pandas import DataFrame
import talib.abstract as ta
from technical import qtpylib

from freqtrade.strategy import DecimalParameter, informative
from macd_volume_v1 import MacdVolumeV1


class MacdVolumeV2(MacdVolumeV1):
    startup_candle_count = 600  # 4h EMA200

    volume_min = DecimalParameter(1.5, 3.5, decimals=1, default=2.0, space="buy")

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        name = self.macd_set.value
        dataframe["macd"], dataframe["macd_signal"] = dataframe[f"macd_{name}"], dataframe[f"macd_signal_{name}"]
        dataframe.loc[
            (
                qtpylib.crossed_above(dataframe["macd"], dataframe["macd_signal"])  # momentum turns up
                & (dataframe["vol_ratio"] > self.volume_min.value)                  # with a big volume burst
                & (dataframe["close"] > dataframe["ema_trend"])                     # 1h trend agrees
                & (dataframe["close_4h"] > dataframe["ema50_4h"])                   # 4h trend agrees ...
                & (dataframe["ema50_4h"] > dataframe["ema200_4h"])                  # ... and is strong
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "macd_cross_volume_4h_trend")
        return dataframe
