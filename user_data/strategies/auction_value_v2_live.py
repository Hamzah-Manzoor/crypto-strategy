"""
Auction Value v2 (live) - AuctionValueV2 for the paper bot on a laptop that sleeps: a missed 5 pm
decision is acted on the first time the bot is awake that evening, instead of a day later.

This is NOT a new version of the strategy. The strategy judged in the Round 6 forward test is
AuctionValueV2 (docs/research/auction-value-preregistration.md), measured by a forward backtest.
This copy only changes WHEN the paper bot may act on each day's decision:

    AuctionValueV2:      only at 12:00 UTC (5 pm Pakistan time). Asleep then -> that day's buy,
                         or its daily sell (value falling / back in value), is missed.
    AuctionValueV2Live:  the first time the bot is awake between 12:00 and 23:59 UTC (5 pm - 4:59 am
                         Pakistan time), on the same session (the one that ended at 12:00 UTC).

Guards that keep it making V2's decisions, just later:
    - a coin is not bought again after a trade in it closed since 12:00 UTC (V2 waits for the next
      day's decision);
    - no buy once the price has already reached the setup's stop or target since 12:00 UTC (the
      trade V2 would have made is already over).
Stops and targets work exactly as in V2 whenever the bot is awake. In a backtest the bot never
sleeps, so this copy must give the same trades as AuctionValueV2.
"""

from datetime import datetime

import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from auction_value_v2 import AuctionValueV2

CARRIED = ["av_decision", "av_low", "av_close", "av_enter", "av_stop", "av_target"]


class AuctionValueV2Live(AuctionValueV2):
    LAST_DECISION_CANDLE = 22       # 22:00 UTC candle (acts by 23:59 UTC = 4:59 am Pakistan time)

    def _value_view(self, dataframe: DataFrame) -> DataFrame:
        view = super()._value_view(dataframe)
        # Keep each decision on every candle of its evening window, so a bot that wakes late still sees it.
        hour = dataframe["date"].dt.hour
        window = (hour >= self.REBALANCE_HOUR) & (hour <= self.LAST_DECISION_CANDLE)
        day = (dataframe["date"] - pd.Timedelta(hours=self.REBALANCE_HOUR)).dt.floor("D")
        carried = view[CARRIED].where(view["av_decision"]).groupby(day).ffill()
        carried["av_decision"] = carried["av_decision"].fillna(False).astype(bool)
        view.loc[window, CARRIED] = carried.loc[window]
        return view

    def _window_start(self, current_time: datetime) -> datetime | None:
        """Today's 12:00 UTC decision time if `current_time` is inside today's decision window."""
        now = current_time.replace(minute=0, second=0, microsecond=0)
        if not self.REBALANCE_HOUR + 1 <= now.hour <= self.LAST_DECISION_CANDLE + 1:
            return None
        return now.replace(hour=self.REBALANCE_HOUR + 1)

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float,
                            time_in_force: str, current_time: datetime, entry_tag: str | None,
                            side: str, **kwargs) -> bool:
        start = self._window_start(current_time)
        if start is None:
            return False
        # Closed a trade in this coin since the decision? V2 would only buy again at the next one.
        if any(t.close_date_utc and t.close_date_utc >= start for t in Trade.get_trades_proxy(pair=pair, is_open=False)):
            return False
        candles, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if not len(candles):
            return False
        last = candles.iloc[-1]
        since = candles.loc[candles["date"] >= start]
        low = min([rate, *since["low"]])
        high = max([rate, *since["high"]])
        # The trade V2 made at 12:00 UTC would already be over: don't start it now.
        return low > last["av_stop"] and (pd.isna(last["av_target"]) or high < last["av_target"])
