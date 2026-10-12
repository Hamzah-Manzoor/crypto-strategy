"""
Auction Value v2 - AuctionValueV1 with failed drops bought only in balanced (sideways) markets
(Round 6, version 2 of max 3; see docs/research/auction-value-preregistration.md).

Why: Auction Market Theory says buying at the edge of value ("responsive" buying) is a trade for
     a market in balance; when value is moving, you go with the move instead. V1 also bought
     failed drops while value was rising, and on dev that part lost: 186 trades, 26% winners,
     -377 USDT, against 94 trades, 51% winners, +125 USDT in sideways markets (order replay of
     E0353, all 437 trades matching the written rules). V2 follows the textbook: failed drops
     only when the state is sideways. Accepted rises, exits, sizing and every setting are
     unchanged.
Should work / fail: as AuctionValueV1, without the failed drops in rising markets.
Changes vs AuctionValueV1: the failed-drop setup needs a sideways state (was: not falling).
"""

import numpy as np
from pandas import DataFrame

from auction_value_v1 import AuctionValueV1


class AuctionValueV2(AuctionValueV1):
    FAILED_DROP_STATES = (0,)       # sideways only (V1: sideways or rising)

    def _value_view(self, dataframe: DataFrame) -> DataFrame:
        view = super()._value_view(dataframe)
        # Responsive buying at value low belongs to a balanced market: drop it while value is moving.
        moving = (view["av_enter"] == "failed_drop") & ~view["av_state"].isin(self.FAILED_DROP_STATES)
        view.loc[moving, "av_enter"] = None
        view.loc[moving, ["av_stop", "av_target"]] = np.nan
        return view
