"""
Momentum Rotation v1 - each week, hold the strongest coins (Round 2, idea C).

Idea:
    "Winners keep winning for a while" (momentum) is one of the best-documented
    effects in crypto. Every week, rank the 5 coins by their 30-day return and
    hold the top 2 (50/50) - but only coins that actually rose over those 30
    days, and only while Bitcoin is in a long-term uptrend (daily close above its
    200-day average). Otherwise: cash. It changes positions at most once a week,
    so fees barely matter - the opposite of Round 1's busy strategies.

Should work when:
    Trending markets where leadership persists for weeks (e.g. one coin running
    for a month); bull markets in general.

Should fail when:
    Sudden reversals: last month's leader can be next week's biggest loser, and it
    only re-checks once a week. Choppy markets where leadership changes every week
    (buys high, sells low). The −20% emergency stop caps a single disaster.

Rebalance: weekly, on the 1h candle Sunday 23:00-24:00 UTC, using the daily candle
           that just closed (Freqtrade only merges a daily candle once it has closed).
Entry:  at rebalance, the coin is in the top 2 by 30-day return, that return is > 0,
        and BTC daily close > BTC 200-day SMA.
Exit:   at rebalance, any of those stops being true; emergency stoploss −20%.
Sizing: each position gets 1/2 of the wallet (custom_stake_amount).
Tunable: none (Round 2 rule: no hyperopt). Settings are class constants.
Changes vs previous version: none (first version of a new idea).
"""

from datetime import datetime

import pandas as pd
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import merge_informative_pair
from labkit.base import LabBaseStrategy


class MomentumRotationV1(LabBaseStrategy):
    minimal_roi = {"0": 100.0}  # no take-profit: exits only at the weekly rebalance
    stoploss = -0.20            # emergency stop only
    trailing_stop = False

    startup_candle_count = 210  # 200-day BTC average (+ margin), in daily candles

    # The coins being ranked are part of the strategy, not "whatever pairlist is loaded":
    # Freqtrade's lookahead check re-runs with a one-pair whitelist, and ranking against the
    # current whitelist then gives different ranks (a false "lookahead" alarm). Same 5 coins as base.json.
    UNIVERSE = ("BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT")
    TOP_N = 2
    LOOKBACK_DAYS = 30
    REBALANCE_WEEKDAY, REBALANCE_HOUR = 6, 23   # Sunday 23:00 UTC candle (closes Monday 00:00)

    plot_config = {"subplots": {"Momentum": {"mom_ret_1d": {"color": "blue"}, "mom_rank_1d": {"color": "red"}}}}

    def informative_pairs(self):
        return [(pair, "1d") for pair in self.UNIVERSE]

    def _ranks(self) -> DataFrame:
        """Daily table: 30-day return and rank (1 = strongest) of every whitelist coin, and the BTC filter."""
        closes = {}
        for pair in self.UNIVERSE:
            daily = self.dp.get_pair_dataframe(pair, "1d")
            closes[pair] = daily.set_index("date")["close"]
        closes = pd.DataFrame(closes).sort_index()
        returns = closes / closes.shift(self.LOOKBACK_DAYS) - 1
        ranks = returns.rank(axis=1, ascending=False, method="first")
        btc = self.dp.get_pair_dataframe("BTC/USDT", "1d").set_index("date")
        btc_ok = (btc["close"] > ta.SMA(btc["close"], timeperiod=200)).astype(float)
        return returns, ranks, btc_ok

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        returns, ranks, btc_ok = self._ranks()
        pair = metadata["pair"]
        daily = pd.DataFrame({
            "date": returns.index,
            "mom_ret": returns[pair].to_numpy(),
            "mom_rank": ranks[pair].to_numpy(),
            "btc_ok": btc_ok.reindex(returns.index).to_numpy(),
        })
        # Shifts each daily value to the hour its candle closes: no peeking at an unfinished day.
        return merge_informative_pair(dataframe, daily, self.timeframe, "1d", ffill=True)

    def _rebalance(self, dataframe: DataFrame) -> pd.Series:
        return (dataframe["date"].dt.weekday == self.REBALANCE_WEEKDAY) & (dataframe["date"].dt.hour == self.REBALANCE_HOUR)

    def _selected(self, dataframe: DataFrame) -> pd.Series:
        return ((dataframe["mom_rank_1d"] <= self.TOP_N) & (dataframe["mom_ret_1d"] > 0)
                & (dataframe["btc_ok_1d"] == 1))

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            self._rebalance(dataframe) & self._selected(dataframe) & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "top_momentum")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            self._rebalance(dataframe) & ~self._selected(dataframe),
            ["exit_long", "exit_tag"],
        ] = (1, "rotated_out")
        return dataframe

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: float | None, max_stake: float,
                            leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        # Each of the TOP_N positions gets an equal share of the whole wallet.
        return min(max_stake, self.wallets.get_total_stake_amount() / self.TOP_N)
