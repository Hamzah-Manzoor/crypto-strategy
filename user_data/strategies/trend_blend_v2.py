"""
Trend Blend v2 - TrendBlendV1's rules, with partial sells ("trims") sized correctly
(Round 5, version 2 of max 3; see docs/research/trend-blend-preregistration.md).

Why: the order replay (scripts/round5_position_check.py) showed V1's trims did not follow its own
     rules. Freqtrade sells (requested amount / purchase cost) of a position, i.e. it counts a
     partial sell in purchase cost, while V1 asked in today's market value. A position in profit
     was trimmed too much, and a big winner (e.g. SOL up ~5x in late 2023) could not be trimmed at
     all because the request was larger than the whole position. V2 converts the request so the
     right amount is sold. Same idea, same settings, same rules - this is a bug fix, not a change
     of strategy.
Should work / fail: as TrendBlendV1.
Changes vs TrendBlendV1: trim requests converted from market value to purchase-cost units.
"""

from datetime import datetime

from freqtrade.persistence import Trade
from trend_blend_v1 import TrendBlendV1


class TrendBlendV2(TrendBlendV1):

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
        value = trade.amount * current_rate
        gap = weight * slot - value
        if abs(gap) < self.BAND * slot:
            return None                 # close enough to the target: not worth the fees
        if gap > 0:
            stake = min(gap, max_stake)
            return (stake, "top_up") if stake >= (min_stake or 0) else None
        # Trim back to the target. Freqtrade counts a partial sell in purchase cost, so sell
        # gap/value of the position by asking for that share of what we paid for it.
        return (gap / value * trade.stake_amount, "trim")
