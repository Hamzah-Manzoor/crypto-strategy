"""
Auction Value v1 - Auction Market Theory: trade where value is going
(Round 6; see docs/research/auction-value-preregistration.md).

Idea:
    A market is an auction. The price range where most coins changed hands last week is
    "value" - the price both buyers and sellers accepted as fair. Watch what price does at
    the edges of value:
      - it pokes below value, finds no sellers and closes back inside: the drop FAILED, and
        price tends to travel to the other side of value (buy, aim for the value high);
      - it closes above value two days running: the higher price is ACCEPTED, value will
        follow it up (buy, ride it until price is back inside value).
    And watch where value itself moves: if this week's value sits lower than last week's,
    sellers are in control - hold cash.

Should work when:
    Sideways markets with clear ranges (failed drops pay the trip across value) and steady
    uptrends that pause and continue (accepted rises).
Should fail when:
    Drops that keep going a day later (the failed drop's stop is hit), and sharp reversals
    right after a breakout (the accepted rise gives back the trip to its stop).

Session:  24 hourly candles ending with the 11:00 UTC candle; the decision is made when it
          closes (12:00 UTC = 5 pm Pakistan time) and trades at the 12:00 UTC open.
Value:    volume profile of the 7 sessions before today (hourly candles, 0.25% price steps):
          point of control (busiest price) and the 70% value area (value low / value high).
State:    rising if this week's value high and low are both above last week's, falling if both
          below, sideways otherwise.
Buy:      failed_drop   - not falling; today's low < value low < today's close < value high, and
                          value high is at least as far above the close as today's low is below.
          accepted_rise - rising; today and the session before both closed above their value high.
Sell:     failed_drop   - target value high, stop today's low (both checked within every hour).
          accepted_rise - stop value low; sell when a session closes below the point of control.
          both          - sell when the state turns falling. Emergency stop -30%.
Size:     one full slot per trade (wallet value / max_open_trades); no top-ups or partial sells.
Tunable:  none (no hyperopt). Settings are fixed in the pre-registration.
Changes vs previous version: none (first version of a new idea).
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import stoploss_from_absolute
from labkit.auction import value_area
from labkit.base import LabBaseStrategy

EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
LEVELS = ["av_val", "av_poc", "av_vah", "av_state"]                   # kept on every candle (charts)
DECISION = ["av_decision", "av_low", "av_close", "av_enter", "av_stop", "av_target"]   # decision candle only


class AuctionValueV1(LabBaseStrategy):
    minimal_roi = {"0": 100.0}      # no fixed take-profit: failed drops get their own target (custom_roi)
    use_custom_roi = True
    stoploss = -0.30                # disaster backstop only; the structural stops come first
    use_custom_stoploss = True
    trailing_stop = False

    # Hourly candles of history: two weeks of the longest profile variant (2 x 10 sessions), today's
    # session, a partial first session that is skipped, and the longest acting delay (3 hours).
    startup_candle_count = 576

    PROFILE_SESSIONS = 7            # sessions in one "week" of value
    VALUE_AREA = 0.70               # share of the volume inside the value area
    ACCEPT_CLOSES = 2               # closes above value needed to call a rise "accepted"
    MIN_REWARD_RISK = 1.0           # failed drop: target at least this many times as far as the stop
    PRICE_STEP = 0.0025             # 0.25% price steps for the volume profile
    REBALANCE_HOUR = 11             # sessions end with this candle (UTC); trades the hour after
    DELAY_HOURS = 0                 # act this many hours late (robustness check only)

    # Robustness check R2: neighbour values, fixed in the pre-registration before any run.
    ROBUSTNESS_GRID = {"PROFILE_SESSIONS": [5, 10], "VALUE_AREA": [0.60, 0.80],
                       "ACCEPT_CLOSES": [1, 3], "MIN_REWARD_RISK": [0.75, 1.5]}

    plot_config = {"main_plot": {"av_val": {"color": "green"}, "av_poc": {"color": "orange"},
                                 "av_vah": {"color": "red"}}}

    # --- the daily view -----------------------------------------------------------------------

    def _value_view(self, dataframe: DataFrame) -> DataFrame:
        """Value levels, market state and setups, filled in on each session's last candle."""
        n, week = len(dataframe), self.PROFILE_SESSIONS
        out = {c: np.full(n, np.nan) for c in ("av_val", "av_poc", "av_vah", "av_state", "av_low", "av_close",
                                                "av_stop", "av_target")}
        out["av_decision"], out["av_enter"] = np.zeros(n, dtype=bool), np.full(n, None, dtype=object)
        if n == 0:
            return pd.DataFrame(out, index=dataframe.index)
        date = dataframe["date"]
        # Session number of every candle: sessions start the hour after the decision candle.
        sid = ((date - pd.Timedelta(hours=self.REBALANCE_HOUR + 1) - EPOCH) // pd.Timedelta(days=1)).to_numpy()
        # A session that started before the data did is incomplete: never use it.
        first = sid[0] if date.iloc[0].hour == (self.REBALANCE_HOUR + 1) % 24 else sid[0] + 1
        high, low, close, volume = (dataframe[c].to_numpy(dtype=float) for c in ("high", "low", "close", "volume"))
        profiles = {}

        def value(last: int) -> tuple[float, float, float]:
            """Value of the `week` sessions ending with session `last` (NaN if it reaches before the data)."""
            if last not in profiles:
                a, b = np.searchsorted(sid, last - week + 1, "left"), np.searchsorted(sid, last, "right")
                profiles[last] = (value_area(high[a:b], low[a:b], volume[a:b], self.PRICE_STEP, self.VALUE_AREA)
                                  if last - week + 1 >= first and b > a else (np.nan, np.nan, np.nan))
            return profiles[last]

        # Each complete session's last candle, and whether that session closed above its own value high.
        last_rows = [i for i in np.flatnonzero((date.dt.hour == self.REBALANCE_HOUR).to_numpy()) if sid[i] >= first]
        closed_above = {sid[i]: bool(close[i] > value(sid[i] - 1)[2]) for i in last_rows}

        for i in last_rows:
            k = sid[i]
            val, poc, vah = value(k - 1)                    # this week: the sessions before today
            prev_val, _, prev_vah = value(k - 1 - week)      # last week: the sessions before those
            if np.isnan([val, vah, prev_val, prev_vah]).any():
                continue
            state = 1 if vah > prev_vah and val > prev_val else (-1 if vah < prev_vah and val < prev_val else 0)
            day_low, c = low[np.searchsorted(sid, k, "left"):i + 1].min(), close[i]
            out["av_val"][i], out["av_poc"][i], out["av_vah"][i], out["av_state"][i] = val, poc, vah, state
            out["av_low"][i], out["av_close"][i], out["av_decision"][i] = day_low, c, True
            # Failed drop: price auctioned below value, found no sellers and closed back inside it.
            if state >= 0 and day_low < val < c < vah and vah - c >= self.MIN_REWARD_RISK * (c - day_low):
                out["av_enter"][i], out["av_stop"][i], out["av_target"][i] = "failed_drop", day_low, vah
            # Accepted rise: value is moving up and price stayed above value for ACCEPT_CLOSES sessions
            # in a row (a session missing from the data can't count as accepted).
            elif state == 1 and all(closed_above.get(k - j, False) for j in range(self.ACCEPT_CLOSES)):
                out["av_enter"][i], out["av_stop"][i] = "accepted_rise", val

        view = pd.DataFrame(out, index=dataframe.index)
        view[LEVELS] = view[LEVELS].ffill()
        if self.DELAY_HOURS:
            view = view.shift(self.DELAY_HOURS)
            view["av_decision"] = view["av_decision"].fillna(False).astype(bool)
        return view

    # --- signals ------------------------------------------------------------------------------

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        view = self._value_view(dataframe)
        for col in LEVELS + DECISION:
            dataframe[col] = view[col]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        setup = dataframe["av_enter"].notna() & (dataframe["volume"] > 0)
        dataframe.loc[setup, "enter_long"] = 1
        dataframe.loc[setup, "enter_tag"] = dataframe.loc[setup, "av_enter"]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Value is migrating lower: sellers are in control, so every trade goes to cash.
        dataframe.loc[dataframe["av_decision"] & (dataframe["av_state"] == -1),
                      ["exit_long", "exit_tag"]] = (1, "value_falling")
        return dataframe

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs):
        # An accepted rise ends when price is accepted back inside value (a close below the POC).
        if trade.enter_tag != "accepted_rise":
            return None
        candles, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if not len(candles):
            return None
        last = candles.iloc[-1]
        if last["av_decision"] and last["av_close"] < last["av_poc"]:
            return "back_in_value"
        return None

    # --- stops and targets fixed at entry ---------------------------------------------------------

    def _levels(self, trade: Trade) -> tuple[float | None, float | None]:
        """(stop, target) from the trade's entry candle, remembered with the trade."""
        stop = trade.get_custom_data("stop")
        if stop is None:
            candles, _ = self.dp.get_analyzed_dataframe(trade.pair, self.timeframe)
            signal = trade.open_date_utc.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            row = candles.loc[candles["date"] == signal] if len(candles) else candles
            if row.empty or pd.isna(row["av_stop"].iloc[0]):
                return None, None
            stop, target = float(row["av_stop"].iloc[0]), row["av_target"].iloc[0]
            trade.set_custom_data("stop", stop)
            trade.set_custom_data("target", None if pd.isna(target) else float(target))
        return stop, trade.get_custom_data("target")

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime, current_rate: float,
                        current_profit: float, after_fill: bool, **kwargs) -> float | None:
        stop, _ = self._levels(trade)
        if stop is None:
            return None
        return stoploss_from_absolute(stop, current_rate, is_short=False, leverage=trade.leverage)

    def custom_roi(self, pair: str, trade: Trade, current_time: datetime, trade_duration: int,
                   entry_tag: str | None, side: str, **kwargs) -> float | None:
        # A failed drop aims for the other side of value: sell as soon as price reaches value high.
        if entry_tag != "failed_drop":
            return None
        _, target = self._levels(trade)
        return None if target is None else trade.calc_profit_ratio(target)

    # --- position size -------------------------------------------------------------------------

    def _slots(self) -> int:
        """Number of coin slots: max_open_trades, or one per coin when trades are unlimited
        (Freqtrade's bias checker runs with max_open_trades = -1)."""
        n = self.config.get("max_open_trades", -1)
        return int(n) if 0 < n < float("inf") else len(self.dp.current_whitelist())

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: float | None, max_stake: float,
                            leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        # One full slot: the wallet's value (cash + coins at the latest close) split evenly.
        cash = self.wallets.get_free(self.config["stake_currency"])
        held = 0.0
        for trade in Trade.get_trades_proxy(is_open=True):
            candles, _ = self.dp.get_analyzed_dataframe(trade.pair, self.timeframe)
            held += trade.amount * (candles["close"].iloc[-1] if len(candles) else trade.open_rate)
        slot = (cash + held) * self.config.get("tradable_balance_ratio", 1.0) / self._slots()
        return min(max_stake, slot)
