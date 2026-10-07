"""
Momentum Rotation v1b - hold the top 3 instead of the top 2 (Round 2, idea C, version 2 of max 3).

Why: v1 was strong on dev data (+355%, Calmar 1.51) but had a 43% max drawdown and 80% of its
     profit came from 3 trades: holding only 2 coins makes it very dependent on a few bets.
     v1b spreads the wallet over the 3 strongest coins (1/3 each) to lower the drawdown.
Should work / fail: as v1; expect smaller drawdowns and smaller peak gains.
Changes vs v1: TOP_N = 3 (positions sized 1/3 each). Everything else unchanged.
"""

from momentum_rotation_v1 import MomentumRotationV1


class MomentumRotationV1b(MomentumRotationV1):
    TOP_N = 3
