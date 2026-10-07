"""
EMA Trend v3b - EmaTrendV2 plus ONLY the Bitcoin market filter (Round 2, idea B, version 2 of max 3).

Why: v3 (BTC filter + losing-streak pause) did worse than v2 on dev data (+14.8% vs +36%).
     v3b drops the pause and keeps only the BTC 200-day filter, to see whether the pause
     (which can block the first trades of a new trend) was the part that hurt.
Should work / fail: as v3.
Changes vs v3: no protections (no losing-streak pause, no cooldown). BTC filter unchanged.
"""

from ema_trend_v3 import EmaTrendV3


class EmaTrendV3b(EmaTrendV3):
    @property
    def protections(self):
        return []
