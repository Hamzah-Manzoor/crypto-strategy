"""
ADX Supertrend v1 - ride trends only when they are strong.

Idea:
    Supertrend flips "up" when price closes above a volatility band, which
    marks a possible new uptrend. Many flips are false alarms in quiet markets,
    so only take the flip when ADX (trend strength, 0-100) says a real trend
    is in progress and +DI > -DI (buyers stronger than sellers).

Should work when:
    Strong, sustained moves with expanding volatility - breakouts that keep
    going (e.g. Nov 2024 rally).

Should fail when:
    ADX is high at the END of a trend too, so it can buy late into a blow-off
    top. In slow grinding uptrends ADX stays low and it misses the move.
    Sideways chop gives false flips.

Entry:  Supertrend flips from down to up, ADX > threshold, +DI > -DI.
Exit:   Supertrend flips down; trailing stop locks in big moves; stoploss -10%.
Tunable (hyperopt): ATR length and band multiplier (Supertrend), ADX threshold.
Changes vs previous version: none (first version)
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import CategoricalParameter, IntParameter
from labkit.base import LabBaseStrategy
from labkit.indicators import supertrend_direction


class AdxSupertrendV1(LabBaseStrategy):
    minimal_roi = {"0": 0.30}
    stoploss = -0.10

    trailing_stop = True
    trailing_stop_positive = 0.03
    trailing_stop_positive_offset = 0.06
    trailing_only_offset_is_reached = True

    startup_candle_count = 300

    st_period = CategoricalParameter([7, 10, 14], default=10, space="buy")
    st_multiplier = CategoricalParameter([2.0, 2.5, 3.0, 3.5, 4.0], default=3.0, space="buy")
    adx_min = IntParameter(15, 35, default=25, space="buy")

    plot_config = {
        "main_plot": {},
        "subplots": {
            "Supertrend": {"st_dir": {"color": "green"}},
            "ADX": {"adx": {"color": "black"}, "plus_di": {"color": "green"}, "minus_di": {"color": "red"}},
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for period in self.st_period.range:
            for mult in self.st_multiplier.range:
                dataframe[f"st_dir_{period}_{mult}"] = supertrend_direction(dataframe, period, mult)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe, timeperiod=14)
        return dataframe

    def _direction(self, dataframe: DataFrame):
        return dataframe[f"st_dir_{self.st_period.value}_{self.st_multiplier.value}"]

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        direction = self._direction(dataframe)
        dataframe["st_dir"] = direction  # for charts
        dataframe.loc[
            (
                (direction == 1) & (direction.shift(1) == -1)       # trend just flipped up
                & (dataframe["adx"] > self.adx_min.value)           # and the trend is strong
                & (dataframe["plus_di"] > dataframe["minus_di"])   # buyers in control
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "supertrend_up")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        direction = self._direction(dataframe)
        dataframe.loc[
            (direction == -1) & (direction.shift(1) == 1), ["exit_long", "exit_tag"]
        ] = (1, "supertrend_down")
        return dataframe
