"""
MACD Volume v1 - momentum turns, confirmed by a burst of volume.

Idea:
    MACD crossing above its signal line means short-term momentum is turning
    up. Crosses happen constantly, so only trust one that comes with a volume
    spike (participants are piling in) and while price is above its 100-candle
    average (the bigger trend agrees).

Should work when:
    Markets with clear momentum swings - impulsive moves after pauses.

Should fail when:
    Low-volatility drifts (few volume spikes, so it barely trades) and sharp
    V-shaped reversals, where MACD reacts too late at both ends.

Entry:  MACD crosses above signal, volume > k x average, close > EMA100.
Exit:   MACD crosses below signal; ROI table; stoploss -8%.
Tunable (hyperopt): MACD speed set, volume multiplier k.
Changes vs previous version: none (first version)
"""

from pandas import DataFrame
import talib.abstract as ta
from technical import qtpylib

from freqtrade.strategy import CategoricalParameter, DecimalParameter
from labkit.base import LabBaseStrategy
from labkit.indicators import volume_ratio

# fast-slow-signal EMA lengths: classic, quicker, and a slow/smooth variant.
MACD_SETS = {"12_26_9": (12, 26, 9), "8_17_9": (8, 17, 9), "5_35_5": (5, 35, 5)}


class MacdVolumeV1(LabBaseStrategy):
    minimal_roi = {"0": 0.15, "720": 0.06, "2880": 0.02}
    stoploss = -0.08
    trailing_stop = False

    startup_candle_count = 400  # EMA100 trend filter is the slowest part

    macd_set = CategoricalParameter(list(MACD_SETS), default="12_26_9", space="buy")
    volume_min = DecimalParameter(1.0, 3.0, decimals=1, default=1.5, space="buy")

    plot_config = {
        "main_plot": {"ema_trend": {"color": "grey"}},
        "subplots": {
            "MACD": {"macd": {"color": "blue"}, "macd_signal": {"color": "orange"}},
            "Volume ratio": {"vol_ratio": {"color": "green"}},
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for name in self.macd_set.range:
            fast, slow, signal = MACD_SETS[name]
            macd = ta.MACD(dataframe, fastperiod=fast, slowperiod=slow, signalperiod=signal)
            dataframe[f"macd_{name}"] = macd["macd"]
            dataframe[f"macd_signal_{name}"] = macd["macdsignal"]
        dataframe["vol_ratio"] = volume_ratio(dataframe, 20)
        dataframe["ema_trend"] = ta.EMA(dataframe, timeperiod=100)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        name = self.macd_set.value
        dataframe["macd"], dataframe["macd_signal"] = dataframe[f"macd_{name}"], dataframe[f"macd_signal_{name}"]
        dataframe.loc[
            (
                qtpylib.crossed_above(dataframe["macd"], dataframe["macd_signal"])  # momentum turns up
                & (dataframe["vol_ratio"] > self.volume_min.value)                  # with a volume burst
                & (dataframe["close"] > dataframe["ema_trend"])                     # bigger trend agrees
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "macd_cross_volume")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        name = self.macd_set.value
        dataframe.loc[
            qtpylib.crossed_below(dataframe[f"macd_{name}"], dataframe[f"macd_signal_{name}"]),
            ["exit_long", "exit_tag"],
        ] = (1, "macd_cross_down")
        return dataframe
