"""Robustness-check settings for strategies whose files are frozen (they already have logged
results, so we don't edit them). New strategies can instead declare in their own class:

    ROBUSTNESS_GRID = {"SETTING": [neighbour values]}   # R2: each value tried alone
    ROBUSTNESS_SKIP = ("R1",)                           # checks that cannot apply

Written 2026-10-07, before the robustness check was run on any of these strategies
(docs/research/robustness-check-plan.md).
"""

REGISTRY = {
    "MomentumRotationV1b": {
        "grid": {"LOOKBACK_DAYS": [20, 25, 35, 40], "TOP_N": [2, 4]},
    },
    "EmaTrendV2": {
        "grid": {"fast_period": [16, 26], "slow_period": [50, 72]},   # defaults 21 / 55
    },
    "BuyHoldV1": {
        "grid": {},
        "skip": ["R1"],   # no timing decision: it buys once at the start and holds
    },
}
