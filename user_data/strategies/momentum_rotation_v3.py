"""
Momentum Rotation v3 - top-3 momentum rotation with only half the wallet invested
(Round 4, version 1 of 2; see docs/research/momentum-exposure-preregistration.md).

Idea:
    MomentumRotationV1b's edge held up on unseen data and passed every robustness
    check, but it fell ~40% from its peaks because it was always fully invested
    in 3 volatile coins. v3 buys the same coins at the same times with half the
    money: each new position gets 1/6 of the wallet instead of 1/3, and the rest
    waits in cash. Same edge, roughly half the swings - and half the return.

Should work when:
    As v1b: trending markets where leadership persists for weeks. The cash cushion
    makes the deep falls (e.g. the 2024 whipsaw) survivable.
Should fail when:
    As v1b: sudden reversals and choppy leadership. Smaller positions shrink the
    damage, not the number of bad weeks.

Rebalance: Monday 12:00 UTC (5 pm Pakistan time) using Sunday's closed daily candle,
           so a paper bot on a Mac that sleeps at night does not miss it.
Entry/exit: as v1b (top 3 by 30-day return, return > 0, BTC daily close > 200-day SMA).
Sizing: each new position = EXPOSURE x 1/3 of the whole wallet (1/6 at 0.5). Positions
        are not resized while held, so winners can grow past 1/6.
Tunable: none (no hyperopt). Settings are fixed in the pre-registration.
Changes vs MomentumRotationV1b: rebalance time; position size x EXPOSURE (0.5).
"""

from datetime import datetime

from momentum_rotation_v1b import MomentumRotationV1b


class MomentumRotationV3(MomentumRotationV1b):
    REBALANCE_WEEKDAY, REBALANCE_HOUR = 0, 11   # Monday 11:00 UTC candle, trades at 12:00 UTC
    EXPOSURE = 0.5                              # share of the wallet invested when all slots are full

    # Robustness check R2: neighbour values, fixed in the pre-registration before any run.
    ROBUSTNESS_GRID = {"EXPOSURE": [0.4, 0.6], "LOOKBACK_DAYS": [20, 25, 35, 40], "TOP_N": [2, 4]}

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: float | None, max_stake: float,
                            leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        # Every slot gets the same slice of the whole wallet; together they never start above EXPOSURE.
        return min(max_stake, self.wallets.get_total_stake_amount() * self.EXPOSURE / self.TOP_N)
