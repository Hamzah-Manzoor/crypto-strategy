"""
Momentum Rotation v1b (Monday 12:00 UTC) - DIAGNOSTIC ONLY, not a candidate.

Exactly MomentumRotationV1b with only the rebalance moved to Monday 12:00 UTC, so the
Round 3 pre-registration can report how much the operational time change alone affects
results (docs/research/momentum-drawdown-preregistration.md, section 3).
Never selected, never paper-traded.
"""

from momentum_rotation_v1b import MomentumRotationV1b


class MomentumRotationV1bMonday(MomentumRotationV1b):
    REBALANCE_WEEKDAY, REBALANCE_HOUR = 0, 11
