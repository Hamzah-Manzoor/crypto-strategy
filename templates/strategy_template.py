"""
<Name> v1 - <one-line description of the trading idea>

Idea:
    <What market behaviour are we trying to profit from, in plain words?>

Should work when:
    <Market conditions where the idea has an edge.>

Should fail when:
    <Market conditions where it will lose. Every strategy has some - write them down.>

Entry:  <rule in words>
Exit:   <rule in words> (plus ROI table / stoploss / trailing stop below)
Tunable (hyperopt): <list the parameters and what they control>
Changes vs previous version: none (first version)

HOW TO USE THIS TEMPLATE
    1. cp templates/strategy_template.py user_data/strategies/<idea>_v1.py
    2. Rename the class to <Idea>V1 (the version is part of the class name).
    3. Fill in the docstring above BEFORE writing code.
    4. Never edit a version that already has logged results - copy it to _v2
       and subclass it instead:  class <Idea>V2(<Idea>V1): ...
    5. Hyperopt parameters must NOT be read with `.value` inside populate_indicators.
       Pre-compute every option with `.range` there, then pick one with `.value`
       in populate_entry_trend / populate_exit_trend (see the example below).
    6. Never use future candles: no .shift(-1), no rolling windows that include
       the current candle when comparing the current candle against them, no
       whole-column statistics (df["close"].mean()). `lab.py check-bias` verifies.
    7. startup_candle_count >= what recursive-analysis says your slowest
       indicator needs (EMA-based indicators need roughly 3x their period).
"""

from pandas import DataFrame
import talib.abstract as ta
from technical import qtpylib

from freqtrade.strategy import CategoricalParameter, IntParameter
from labkit.base import LabBaseStrategy


class TemplateV1(LabBaseStrategy):
    # --- Risk settings -------------------------------------------------------
    # ROI table: {minutes since entry: minimum profit to take}. Example: take
    # 10% any time, 5% after 12h, break-even after 2 days.
    minimal_roi = {"0": 0.10, "720": 0.05, "2880": 0.0}
    stoploss = -0.08  # sell if the trade loses 8%

    # Trailing stop: once +6% in profit, sell if price falls 3% from its best.
    # Makes sense for trend ideas; usually off for mean-reversion ideas.
    trailing_stop = False
    trailing_stop_positive = 0.03
    trailing_stop_positive_offset = 0.06
    trailing_only_offset_is_reached = True

    # Candles needed before the first signal is trustworthy (see note 7).
    startup_candle_count = 200

    # --- Tunable settings (hyperopt) -------------------------------------------
    # Indicator lengths: a small set of sensible choices (coarse grids overfit less).
    ema_period = CategoricalParameter([20, 50, 100], default=50, space="buy")
    # Thresholds: plain numbers, safe to use directly in entry/exit.
    rsi_entry = IntParameter(20, 40, default=30, space="buy")
    rsi_exit = IntParameter(60, 80, default=70, space="sell")

    plot_config = {
        "main_plot": {f"ema_{ema_period.value}": {"color": "orange"}},
        "subplots": {"RSI": {"rsi": {"color": "purple"}}},
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Every option of a tunable indicator length, so hyperopt can switch between them.
        for period in self.ema_period.range:
            dataframe[f"ema_{period}"] = ta.EMA(dataframe, timeperiod=period)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema = dataframe[f"ema_{self.ema_period.value}"]
        dataframe.loc[
            (
                (dataframe["close"] > ema)  # only buy in an uptrend
                & qtpylib.crossed_above(dataframe["rsi"], self.rsi_entry.value)  # bounce from oversold
                & (dataframe["volume"] > 0)  # skip empty candles
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "rsi_bounce")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            qtpylib.crossed_above(dataframe["rsi"], self.rsi_exit.value),
            ["exit_long", "exit_tag"],
        ] = (1, "rsi_high")
        return dataframe
