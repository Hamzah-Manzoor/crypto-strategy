"""
Momentum Rotation v3b - top-3 momentum rotation with volatility-scaled positions
(Round 4, version 2 of 2; see docs/research/momentum-exposure-preregistration.md).

Idea:
    Momentum strategies crash when markets turn wild: last month's winners swing
    hardest just as the trend breaks. v3b buys the same coins as v1b, but sizes
    each one by how calm it has been. A coin whose daily moves add up to 50% a year
    or less gets a full 1/3 slot; a wilder coin gets proportionally less (100% a
    year -> half a slot). Money not used waits in cash. Scaling momentum by recent
    volatility is a well-documented fix for momentum crashes (Barroso & Santa-Clara,
    2015).

Should work when:
    Trends that start calm and end in a volatile blow-off or crash: positions are
    already small when the big swings arrive.
Should fail when:
    Calm-looking markets that drop suddenly (volatility was low just before the fall),
    and strong but volatile rallies, where it holds too little to keep up.

Rebalance: Monday 12:00 UTC (5 pm Pakistan time) using Sunday's closed daily candle.
Entry/exit: as v1b (top 3 by 30-day return, return > 0, BTC daily close > 200-day SMA).
Sizing: each new position = 1/3 of the wallet x min(1, TARGET_VOL / volatility), where
        volatility = std of the coin's last VOL_DAYS daily log returns x sqrt(365), from
        closed daily candles only. Positions are not resized while held. If a coin has
        no volatility reading yet, it is not bought.
Tunable: none (no hyperopt). Settings are fixed in the pre-registration.
Changes vs MomentumRotationV1b: rebalance time; volatility-scaled position size.
"""

from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import merge_informative_pair
from momentum_rotation_v1b import MomentumRotationV1b


class MomentumRotationV3b(MomentumRotationV1b):
    REBALANCE_WEEKDAY, REBALANCE_HOUR = 0, 11   # Monday 11:00 UTC candle, trades at 12:00 UTC
    TARGET_VOL = 0.5                            # a coin this calm (annualised) gets a full slot
    VOL_DAYS = 30

    # Robustness check R2: neighbour values, fixed in the pre-registration before any run.
    ROBUSTNESS_GRID = {"TARGET_VOL": [0.4, 0.6], "LOOKBACK_DAYS": [20, 25, 35, 40], "TOP_N": [2, 4]}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_indicators(dataframe, metadata)
        daily = self.dp.get_pair_dataframe(metadata["pair"], "1d")
        vol = np.log(daily["close"]).diff().rolling(self.VOL_DAYS).std() * np.sqrt(365)
        # How wild the coin has been lately, known only once each day has closed.
        dataframe = dataframe.drop(columns=["date_1d"])
        return merge_informative_pair(dataframe, pd.DataFrame({"date": daily["date"], "mom_vol": vol}),
                                      self.timeframe, "1d", ffill=True)

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: float | None, max_stake: float,
                            leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        # The volatility the signal candle saw (the analyzed data ends at the signal candle).
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        vol = dataframe["mom_vol_1d"].iloc[-1] if len(dataframe) else np.nan
        if not vol > 0:
            return 0.0  # no reading yet: don't guess a size
        scale = min(1.0, self.TARGET_VOL / vol)
        return min(max_stake, self.wallets.get_total_stake_amount() / self.TOP_N * scale)
