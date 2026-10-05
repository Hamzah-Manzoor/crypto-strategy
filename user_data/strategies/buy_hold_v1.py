"""
Buy & Hold v1 - the baseline every strategy must beat.

Idea:
    Do nothing clever. Buy all 5 coins on the first candle with an equal share
    (20% each) and hold them to the end of the test period.

Should work when:
    Prices mostly go up (bull markets). Hard to beat on raw profit in a rally,
    because it is always fully invested and pays fees only twice.

Should fail when:
    Prices fall for a long time (bear markets): it rides every crash all the
    way down, so its drawdown is the market's drawdown.

Why it matters:
    A strategy that makes +40% while buy & hold made +120% did not "work".
    Strategies are judged against this baseline on a RISK-ADJUSTED basis
    (Calmar / Sharpe), because beating a bull market on raw profit is rare,
    but cutting the drawdown in half for a similar return is valuable.

Entry:  every candle signals "buy"; with 5 slots and 5 pairs all fill at once.
Exit:   never (open trades are closed at the end of the backtest).
Tunable (hyperopt): nothing.
Changes vs previous version: none (first version)
"""

from pandas import DataFrame

from labkit.base import LabBaseStrategy


class BuyHoldV1(LabBaseStrategy):
    minimal_roi = {"0": 1000.0}  # never take profit
    stoploss = -0.99             # never stop out
    trailing_stop = False
    use_exit_signal = False
    startup_candle_count = 0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["volume"] > 0, ["enter_long", "enter_tag"]] = (1, "hold")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
