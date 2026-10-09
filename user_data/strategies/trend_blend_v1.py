"""
Trend Blend v1 - trend at four speeds, with position sizes set by risk
(Round 5; see docs/research/trend-blend-preregistration.md).

Idea:
    The most reliable edge in crypto is trend: coins that have been rising tend to
    keep rising for a while, and long falls are where most money is lost. Instead of
    one trend signal (one moving average, all in or all out), each coin gets a score
    from four moving averages at different speeds - 20, 50, 100 and 200 days. The
    position grows as more of them agree and shrinks as they turn, so it steps in and
    out gradually instead of whipsawing. Each position is also sized by how wild the
    coin has been lately: a calm uptrend gets a full slot, a coin swinging twice as
    hard gets half, so every coin carries roughly the same risk.

Should work when:
    Long trends (bull markets, months-long declines): it holds the uptrends and sits in
    cash through bear markets.
Should fail when:
    Sudden crashes inside uptrends (all four averages still point up when the drop
    starts, and it only reacts at the next daily check); long sideways chop, where the
    fast average keeps flipping and each top-up or trim costs fees.

Decision: once a day, on the 11:00 UTC hourly candle (trades at 12:00 UTC = 5 pm Pakistan
          time), using only daily candles that have closed.
Score:    1 point per daily close above its 20 / 50 / 100 / 200-day simple average (0-4).
Weight:   score / 4 x min(1, TARGET_VOL / 30-day volatility), in slots (1 slot = wallet value /
          max_open_trades, the wallet valued at the latest prices).
Trades:   buy when the weight is >= BAND; top up / trim back to the target when target and
          holding differ by >= BAND of a slot; sell everything when the score is 0.
Risk:     -25% emergency stop from the average buy price (disaster backstop only).
Tunable:  none (no hyperopt). Settings are fixed in the pre-registration.
Changes vs previous version: none (first version of a new idea).
"""

from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import merge_informative_pair
from labkit.base import LabBaseStrategy


class TrendBlendV1(LabBaseStrategy):
    minimal_roi = {"0": 100.0}      # no take-profit: trend strategies earn from a few long runs
    stoploss = -0.25                # disaster backstop only
    trailing_stop = False
    position_adjustment_enable = True

    # Daily candles of history needed: the slowest average of the slowest robustness variant
    # (200 x 1.25 = 250 days) plus the longest acting delay (3 days).
    startup_candle_count = 260

    SPEEDS = (20, 50, 100, 200)     # moving-average lengths in days
    SPEED_SCALE = 1.0               # all four lengths x this (robustness check only)
    VOL_DAYS = 30
    TARGET_VOL = 0.30               # a coin this calm (yearly) or calmer gets a full slot
    BAND = 0.25                     # act only on gaps of at least this share of a slot
    REBALANCE_HOUR = 11             # 11:00 UTC candle, trades at 12:00 UTC
    DELAY_DAYS = 0                  # act on the daily view from this many days ago (robustness check only)

    # Robustness check R2: neighbour values, fixed in the pre-registration before any run.
    ROBUSTNESS_GRID = {"TARGET_VOL": [0.25, 0.35], "SPEED_SCALE": [0.75, 1.25],
                       "VOL_DAYS": [20, 45], "BAND": [0.125, 0.5]}

    def informative_pairs(self):
        return [(pair, "1d") for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        daily = self.dp.get_pair_dataframe(metadata["pair"], "1d")
        close = daily["close"]
        averages = [close.rolling(round(n * self.SPEED_SCALE)).mean() for n in self.SPEEDS]
        # How many of the four trend speeds agree the coin is rising (only once all four exist).
        score = sum((close > avg).astype(float) for avg in averages).where(averages[-1].notna())
        # How hard the coin has been swinging, in yearly terms.
        vol = np.log(close).diff().rolling(self.VOL_DAYS).std() * np.sqrt(365)
        weight = score / 4 * np.minimum(1.0, self.TARGET_VOL / vol)
        view = pd.DataFrame({"date": daily["date"], "score": score, "vol": vol, "weight": weight})
        if self.DELAY_DAYS:
            view[["score", "vol", "weight"]] = view[["score", "vol", "weight"]].shift(self.DELAY_DAYS)
        # Each daily value reaches the hourly data only once its day has closed.
        return merge_informative_pair(dataframe, view, self.timeframe, "1d", ffill=True)

    def _decision(self, dataframe: DataFrame) -> pd.Series:
        return dataframe["date"].dt.hour == self.REBALANCE_HOUR

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            self._decision(dataframe) & (dataframe["weight_1d"] >= self.BAND) & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "trend_up")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[self._decision(dataframe) & (dataframe["score_1d"] == 0),
                      ["exit_long", "exit_tag"]] = (1, "trend_gone")
        return dataframe

    # --- position sizing --------------------------------------------------------------------

    def _slots(self) -> int:
        """Number of coin slots: max_open_trades, or one per coin when trades are unlimited
        (Freqtrade's bias checker runs with max_open_trades = -1)."""
        n = self.config.get("max_open_trades", -1)
        return int(n) if 0 < n < float("inf") else len(self.dp.current_whitelist())

    def _slot(self) -> float:
        """One slot = wallet value (cash + coins at the latest close) / number of coin slots."""
        cash = self.wallets.get_free(self.config["stake_currency"])
        held = 0.0
        for trade in Trade.get_trades_proxy(is_open=True):
            candles, _ = self.dp.get_analyzed_dataframe(trade.pair, self.timeframe)
            held += trade.amount * (candles["close"].iloc[-1] if len(candles) else trade.open_rate)
        return (cash + held) * self.config.get("tradable_balance_ratio", 1.0) / self._slots()

    def _weight(self, pair: str) -> float:
        candles, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        return float(candles["weight_1d"].iloc[-1]) if len(candles) else float("nan")

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: float | None, max_stake: float,
                            leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        weight = self._weight(pair)
        if not weight > 0:
            return 0.0
        return min(max_stake, weight * self._slot())

    def adjust_trade_position(self, trade: Trade, current_time: datetime, current_rate: float,
                              current_profit: float, min_stake: float | None, max_stake: float,
                              current_entry_rate: float, current_exit_rate: float,
                              current_entry_profit: float, current_exit_profit: float, **kwargs):
        # Only at the daily decision (the hour after the decision candle closes), once.
        decision_time = current_time.replace(minute=0, second=0, microsecond=0)
        if decision_time.hour != (self.REBALANCE_HOUR + 1) % 24:
            return None
        if any(o.order_date_utc >= decision_time for o in trade.orders):
            return None
        weight = self._weight(trade.pair)
        if not weight > 0:
            return None                 # score 0: the exit signal sells everything instead
        slot = self._slot()
        gap = weight * slot - trade.amount * current_rate
        if abs(gap) < self.BAND * slot:
            return None                 # close enough to the target: not worth the fees
        if gap > 0:
            stake = min(gap, max_stake)
            return (stake, "top_up") if stake >= (min_stake or 0) else None
        return (gap, "trim")
