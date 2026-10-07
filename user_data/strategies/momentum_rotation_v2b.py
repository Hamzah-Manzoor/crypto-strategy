"""
Momentum Rotation v2b - top-3 momentum rotation with a FASTER market filter
(Round 3, version 2 of 3; see docs/research/momentum-drawdown-preregistration.md).

Idea:
    Step aside earlier when the whole market turns: hold coins only while Bitcoin's
    daily close is above its 100-day average (v1b used 200 days, which reacts late).
    No trailing stop - the fixed −20% emergency stop of v1b stays.

Should work when: market-wide tops (late 2021 style) - it goes to cash sooner.
Should fail when: choppy markets around the 100-day average (filter flips on and off,
                  causing extra buys and sells).

Changes vs MomentumRotationV1b: rebalance Monday 12:00 UTC; BTC filter 100 days instead of 200.
"""

from momentum_rotation_v2 import MomentumRotationV2


class MomentumRotationV2b(MomentumRotationV2):
    BTC_FILTER_DAYS = 100
    stoploss = -0.20          # back to v1b's fixed emergency stop ...
    trailing_stop = False     # ... and no trailing stop
