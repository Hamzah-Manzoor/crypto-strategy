"""
Momentum Rotation v2c - both drawdown controls: 15% trailing stop per coin AND the
faster BTC 100-day market filter (Round 3, version 3 of 3; see
docs/research/momentum-drawdown-preregistration.md).

Should work when / fail when: as v2 and v2b combined; expect the smallest drawdowns
and also the most missed upside.

Changes vs MomentumRotationV1b: rebalance Monday 12:00 UTC; 15% trailing stop; BTC filter 100 days.
"""

from momentum_rotation_v2 import MomentumRotationV2


class MomentumRotationV2c(MomentumRotationV2):
    BTC_FILTER_DAYS = 100
