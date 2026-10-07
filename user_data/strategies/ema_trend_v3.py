"""
EMA Trend v3 - EmaTrendV2 plus a Bitcoin market filter and a losing-streak pause
(Round 2, idea B).

Idea:
    EmaTrendV2 passed Round 1's out-of-sample check but was profitable in only
    3 of 8 quarters: most losing quarters came from trend signals in coins while
    the whole market was weak. Crypto coins move together, so v3 only takes new
    trades while BITCOIN itself is in a long-term uptrend (daily close above its
    200-day average). It also pauses after a losing streak: 2 stoplosses within
    3 days stop all new entries for 24 hours, and every pair waits 4 hours after
    an exit before re-entering.

Should work when:
    Broad crypto bull phases; it should sit out bear markets almost entirely.

Should fail when:
    Sharp V-shaped recoveries (the 200-day filter turns back on late) and long
    sideways markets above the 200-day average (still whipsaws, just fewer).

Entry:  EmaTrendV2's entry (4h EMA 21 crosses above 4h EMA 55, 4h close > 4h EMA200)
        AND BTC daily close > BTC 200-day SMA.
Exit:   unchanged from v2 (4h EMA cross down; trailing stop; stoploss −10%).
Protections (Freqtrade): StoplossGuard 2 stops / 72h -> 24h pause (all pairs);
        CooldownPeriod 4 candles after any exit (per pair).
Tunable: none (Round 2 rule: no hyperopt); EmaTrendV2's default 21/55 are used.
Changes vs v2: BTC 200-day market filter on entries; protections.
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import informative
from ema_trend_v2 import EmaTrendV2


class EmaTrendV3(EmaTrendV2):
    # EmaTrendV2's startup (600) also covers 600 daily BTC candles for the 200-day SMA.
    startup_candle_count = 600

    @property
    def protections(self):
        return [
            {"method": "StoplossGuard", "lookback_period_candles": 72, "trade_limit": 2,
             "stop_duration_candles": 24, "only_per_pair": False},
            {"method": "CooldownPeriod", "stop_duration_candles": 4},
        ]

    @informative("1d", "BTC/{stake}")
    def populate_indicators_btc_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma200"] = ta.SMA(dataframe, timeperiod=200)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        btc_uptrend = dataframe["btc_usdt_close_1d"] > dataframe["btc_usdt_sma200_1d"]
        dataframe.loc[~btc_uptrend, ["enter_long", "enter_tag"]] = (0, None)  # market filter
        return dataframe
