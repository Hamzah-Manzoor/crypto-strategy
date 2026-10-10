"""
Trend Blend v2 (live) - TrendBlendV2 for the paper bot on a laptop that sleeps: catches up on a
missed daily decision instead of skipping the day.

This is NOT a new version of the strategy. The strategy judged in the Round 5 forward test is
TrendBlendV2 (docs/research/trend-blend-preregistration.md), measured by a forward backtest. This
copy only changes WHEN the paper bot may make each day's decision:

    TrendBlendV2:      only at 12:00 UTC (5 pm Pakistan time). Asleep then -> the day is skipped.
    TrendBlendV2Live:  the first time the bot is awake between 12:00 and 22:59 UTC (5 pm - 4 am
                       Pakistan time), once per day per coin, using the same closed daily candle
                       V2 would have used. The window ends before the next daily candle closes
                       (00:00 UTC), so a late decision never uses newer information than V2's.

Guards that keep it making V2's decisions, just later:
    - each open position is reviewed once per day (remembered per trade), not every few seconds;
    - nothing is decided on stale prices straight after waking (waits for fresh candles);
    - no re-buying a coin the same day after the emergency stop sold it (V2 waits for tomorrow).
In a backtest the bot never sleeps, so this copy must give the same results as TrendBlendV2.
"""

from datetime import datetime, timedelta

import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from trend_blend_v2 import TrendBlendV2


class TrendBlendV2Live(TrendBlendV2):
    LAST_DECISION_CANDLE = 22       # 22:00 UTC candle (trades by 23:59 UTC = 4:59 am Pakistan time)

    def _decision(self, dataframe: DataFrame) -> pd.Series:
        # Any candle from the normal decision candle to the last one before the next daily close.
        hour = dataframe["date"].dt.hour
        return (hour >= self.REBALANCE_HOUR) & (hour <= self.LAST_DECISION_CANDLE)

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
        # Sold today already (emergency stop)? V2 would only buy back at tomorrow's decision.
        return not any(t.close_date_utc and t.close_date_utc >= start
                       for t in Trade.get_trades_proxy(pair=pair, is_open=False))

    def adjust_trade_position(self, trade: Trade, current_time: datetime, current_rate: float,
                              current_profit: float, min_stake: float | None, max_stake: float,
                              current_entry_rate: float, current_exit_rate: float,
                              current_entry_profit: float, current_exit_profit: float, **kwargs):
        start = self._window_start(current_time)
        if start is None:
            return None
        day = start.date().isoformat()
        if trade.get_custom_data("reviewed_day") == day:
            return None                 # already reviewed today
        candles, _ = self.dp.get_analyzed_dataframe(trade.pair, self.timeframe)
        latest_closed = current_time.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
        if not len(candles) or candles["date"].iloc[-1] != latest_closed:
            return None                 # prices not fresh yet (e.g. just woke up): try again shortly
        # Review exactly as V2 does at 12:00 UTC, with today's prices.
        result = super().adjust_trade_position(trade, start, current_rate, current_profit, min_stake,
                                               max_stake, current_entry_rate, current_exit_rate,
                                               current_entry_profit, current_exit_profit, **kwargs)
        trade.set_custom_data("reviewed_day", day)
        return result
