"""
Trend Pullback v3 - fee-aware dip buying on 4h candles (Round 2, idea A).

Idea:
    v1 had the biggest edge before fees of any Round 1 strategy (+66% in-sample)
    but fees ate it: 1,941 trades, each expecting only a tiny bounce. v3 only
    takes a dip when the EXPECTED bounce is large compared with the 0.2%
    round-trip fee: the 4h close must be at least 2% below its 4h EMA20 (the
    level we expect price to snap back to) - ten times the cost of the trade.
    Decisions use 4h candles, so there are far fewer, bigger trades.

Should work when:
    Uptrends with sharp but short pullbacks (crypto does this a lot).

Should fail when:
    The "dip" is the start of a trend change: the 4h EMA200 filter reacts late,
    so the first leg of a crash can be bought. The −8% stop limits that damage.

Entry:  first 1h candle after a 4h candle that closed above the 4h EMA200, with
        4h RSI(2) < 10, and at least 2% below the 4h EMA20.
Exit:   1h close back at/above the 4h EMA20 (the bounce happened), or 4h RSI(2) > 70;
        ROI 10% any time / 3% after 1 day / break-even after 3 days; stoploss −8%.
Tunable: none (Round 2 rule: no hyperopt). Settings are class constants.
Changes vs v2: decisions entirely on 4h; requires the expected bounce (gap to
               EMA20) to be >= 2%; exits at the EMA20 target instead of EMA10/RSI(2) 80.
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import informative
from labkit.base import LabBaseStrategy


class TrendPullbackV3(LabBaseStrategy):
    minimal_roi = {"0": 0.10, "1440": 0.03, "4320": 0.0}
    stoploss = -0.08
    trailing_stop = False

    startup_candle_count = 600  # 4h EMA200

    RSI_ENTRY = 10      # 4h RSI(2) below this = sharp dip
    RSI_EXIT = 70
    MIN_BOUNCE = 0.02   # expected move to the 4h EMA20 must be >= 2% (10x the round-trip fee)

    plot_config = {
        "main_plot": {"ema20_4h": {"color": "orange"}, "ema200_4h": {"color": "grey"}},
        "subplots": {"RSI(2) 4h": {"rsi2_4h": {"color": "purple"}}},
    }

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi2"] = ta.RSI(dataframe, timeperiod=2)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe  # every decision uses the 4h columns

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        expected_bounce = (dataframe["ema20_4h"] - dataframe["close_4h"]) / dataframe["close_4h"]
        new_4h_candle = dataframe["date_4h"] != dataframe["date_4h"].shift(1)
        dataframe.loc[
            (
                new_4h_candle                                            # act once per 4h candle
                & (dataframe["close_4h"] > dataframe["ema200_4h"])     # uptrend
                & (dataframe["rsi2_4h"] < self.RSI_ENTRY)              # sharp dip
                & (expected_bounce >= self.MIN_BOUNCE)                 # bounce worth far more than fees
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "deep_dip_4h")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] >= dataframe["ema20_4h"]) | (dataframe["rsi2_4h"] > self.RSI_EXIT),
            ["exit_long", "exit_tag"],
        ] = (1, "bounced_to_mean")
        return dataframe
