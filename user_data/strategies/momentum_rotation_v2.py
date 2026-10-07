"""
Momentum Rotation v2 - top-3 momentum rotation with a 15% trailing stop per coin
(Round 3, version 1 of 3; see docs/research/momentum-drawdown-preregistration.md).

Idea:
    MomentumRotationV1b beat buy & hold on unseen data but fell 41% at market turns,
    because it kept holding last month's winners until the next weekly rebalance.
    v2 sells a coin as soon as it falls 15% below its highest price since it was
    bought - any day of the week - and keeps that money in cash until the next
    rebalance.

Should work when:
    Momentum markets with sharp reversals: it keeps the run-ups and cuts the fall.
Should fail when:
    Volatile uptrends with 15%+ pullbacks: it gets shaken out and only buys back at
    the next weekly rebalance (often higher).

Rebalance: Monday 12:00 UTC (5 pm Pakistan time) using Sunday's closed daily candle,
           so a paper bot on a Mac that sleeps at night does not miss it.
Entry/exit: as v1b (top 3 by 30-day return, return > 0, BTC daily close > 200-day SMA).
Risk: 15% trailing stop from the highest price since entry (also the initial stop).
Changes vs MomentumRotationV1b: rebalance time; 15% trailing stop instead of a fixed −20% stop.
"""

import talib.abstract as ta

from momentum_rotation_v1b import MomentumRotationV1b


class MomentumRotationV2(MomentumRotationV1b):
    REBALANCE_WEEKDAY, REBALANCE_HOUR = 0, 11   # Monday 11:00 UTC candle, trades at 12:00 UTC
    BTC_FILTER_DAYS = 200

    stoploss = -0.15
    trailing_stop = True                  # stop follows 15% below the highest price since entry
    trailing_stop_positive = None
    trailing_stop_positive_offset = 0.0
    trailing_only_offset_is_reached = False

    def _ranks(self):
        returns, ranks, _ = super()._ranks()
        btc = self.dp.get_pair_dataframe("BTC/USDT", "1d").set_index("date")
        btc_ok = (btc["close"] > ta.SMA(btc["close"], timeperiod=self.BTC_FILTER_DAYS)).astype(float)
        return returns, ranks, btc_ok
