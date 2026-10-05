"""
Squeeze Breakout v1 - quiet markets are followed by loud ones.

Idea:
    When Bollinger Bands shrink inside the Keltner Channel, volatility is
    unusually low: the market is coiling (the "squeeze"). Low volatility does
    not last; when the squeeze releases, price often moves hard. Trade the
    release only if it breaks upward (close above the upper band with positive
    momentum).

Should work when:
    Consolidations that resolve with a strong move up - common before crypto
    rallies.

Should fail when:
    The release goes down (we just stay out, no loss) or fakes up and reverses
    (loss). In a downtrend most releases break downward, so it trades rarely.

Entry:  a squeeze lasting >= X candles released within the last 3 candles,
        close > upper Bollinger Band, momentum > 0.
Exit:   momentum turns negative OR close < EMA20; trailing stop; stoploss -8%.
Tunable (hyperopt): Keltner width multiplier, minimum squeeze length X.
Changes vs previous version: none (first version)
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import CategoricalParameter, IntParameter
from labkit.base import LabBaseStrategy
from labkit.indicators import keltner, run_length, squeeze_momentum

RELEASE_WINDOW = 3  # candles after the squeeze ends in which a breakout still counts


class SqueezeBreakoutV1(LabBaseStrategy):
    minimal_roi = {"0": 0.25}
    stoploss = -0.08

    trailing_stop = True
    trailing_stop_positive = 0.03
    trailing_stop_positive_offset = 0.06
    trailing_only_offset_is_reached = True

    startup_candle_count = 200

    kc_multiplier = CategoricalParameter([1.0, 1.25, 1.5, 2.0], default=1.5, space="buy")
    min_squeeze = IntParameter(3, 20, default=6, space="buy")

    plot_config = {
        "main_plot": {"bb_upper": {"color": "grey"}, "ema20": {"color": "orange"}},
        "subplots": {"Squeeze": {"squeeze_len": {"color": "red"}, "momentum": {"color": "blue"}}},
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        mid = ta.SMA(dataframe, timeperiod=20)
        stdev = ta.STDDEV(dataframe, timeperiod=20, nbdev=1.0)
        bb_upper, bb_lower = mid + 2 * stdev, mid - 2 * stdev
        dataframe["bb_upper"] = bb_upper
        for mult in self.kc_multiplier.range:
            kc_lower, _, kc_upper = keltner(dataframe, 20, mult)
            squeeze_on = (bb_upper < kc_upper) & (bb_lower > kc_lower)  # bands inside the channel
            dataframe[f"squeeze_len_{mult}"] = run_length(squeeze_on)
        dataframe["momentum"] = squeeze_momentum(dataframe, 20)
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        squeeze_len = dataframe[f"squeeze_len_{self.kc_multiplier.value}"]
        dataframe["squeeze_len"] = squeeze_len  # for charts
        # A long enough squeeze just ended (on this candle) ...
        released = (squeeze_len == 0) & (squeeze_len.shift(1) >= self.min_squeeze.value)
        # ... or within the last few candles.
        recently_released = released.astype(int).rolling(RELEASE_WINDOW, min_periods=1).max() > 0
        dataframe.loc[
            (
                recently_released
                & (dataframe["close"] > dataframe["bb_upper"])  # breaking out upward
                & (dataframe["momentum"] > 0)                   # with upward momentum
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "squeeze_release_up")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["momentum"] < 0) | (dataframe["close"] < dataframe["ema20"]),
            ["exit_long", "exit_tag"],
        ] = (1, "momentum_faded")
        return dataframe
