"""
Donchian Breakout v2 - multi-day breakouts on 4h candles, only in uptrends.

Idea:
    v1 bought every new 20-hour high: 1,329 trades in 2 years, +19% before fees
    and -27% after. Most 1h breakouts are noise. v2 waits for a breakout above
    the highest high of the last N *4h* candles (default 30 = 5 days), with
    strong volume, while the 4h trend is up (EMA50 > EMA200). It exits on a
    close below the lowest low of the last M 4h candles (default 10 = ~2 days).
    The classic Turtle "system 2" idea: fewer, bigger breakouts.

Should work when:
    Range breakouts that turn into multi-week moves.

Should fail when:
    Choppy markets with failed breakouts; exits are slower than v1, so each
    failed breakout costs more.

Entry:  first 1h candle after a 4h close above the previous N 4h-candle high,
        with 4h volume > k x its average and 4h EMA50 > EMA200.
Exit:   4h close below the previous M 4h-candle low; trailing stop; stoploss -10%.
Tunable (hyperopt): N, M (in 4h candles), volume multiplier k.
Changes vs v1: channels on 4h candles (days, not hours); uptrend filter;
               default volume filter 1.2x (was 1.0x); wider trailing stop.
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import CategoricalParameter, DecimalParameter, informative
from donchian_breakout_v1 import DonchianBreakoutV1
from labkit.indicators import donchian_high, donchian_low, volume_ratio


class DonchianBreakoutV2(DonchianBreakoutV1):
    minimal_roi = {"0": 0.50}
    stoploss = -0.10

    trailing_stop = True
    trailing_stop_positive = 0.05
    trailing_stop_positive_offset = 0.10
    trailing_only_offset_is_reached = True

    startup_candle_count = 600  # 4h EMA200

    entry_period = CategoricalParameter([20, 30, 42, 55], default=30, space="buy")
    volume_min = DecimalParameter(1.0, 2.5, decimals=1, default=1.2, space="buy")
    exit_period = CategoricalParameter([6, 10, 15], default=10, space="sell")

    plot_config = {
        "main_plot": {"dc_high_4h": {"color": "green"}, "dc_low_4h": {"color": "red"}},
        "subplots": {"Volume ratio (4h)": {"vol_ratio_4h": {"color": "blue"}}},
    }

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for period in self.entry_period.range:
            dataframe[f"dc_high_{period}"] = donchian_high(dataframe, period)
        for period in self.exit_period.range:
            dataframe[f"dc_low_{period}"] = donchian_low(dataframe, period)
        dataframe["vol_ratio"] = volume_ratio(dataframe, 20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe  # every decision uses the 4h columns

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        channel_high = dataframe[f"dc_high_{self.entry_period.value}_4h"]
        dataframe["dc_high_4h"] = channel_high  # for charts
        above = dataframe["close_4h"] > channel_high
        dataframe.loc[
            (
                above & ~above.shift(1, fill_value=False)                     # first hour after the 4h breakout
                & (dataframe["vol_ratio_4h"] > self.volume_min.value)       # with strong volume
                & (dataframe["ema50_4h"] > dataframe["ema200_4h"])          # in a 4h uptrend
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "breakout_4h")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        channel_low = dataframe[f"dc_low_{self.exit_period.value}_4h"]
        dataframe["dc_low_4h"] = channel_low  # for charts
        dataframe.loc[dataframe["close_4h"] < channel_low, ["exit_long", "exit_tag"]] = (1, "breakdown_4h")
        return dataframe
