"""Indicator helpers that TA-Lib doesn't provide.

Every helper uses only the current candle and older candles, never newer ones,
so a backtest can't peek into the future through these functions.
`lab.py check-bias` (lookahead + recursive analysis) verifies this.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import talib.abstract as ta
from pandas import DataFrame, Series


def supertrend_direction(df: DataFrame, period: int, multiplier: float) -> Series:
    """Supertrend: +1 while the trend is up, -1 while it is down.

    Idea: draw a band `multiplier` x ATR above and below the candle's middle.
    The lower band can only rise during an uptrend (it trails price like a
    stop); the trend flips down when price closes below it, and vice versa.
    Recursive (each band depends on the previous one), so it needs warm-up
    candles - checked by recursive-analysis.
    """
    atr = ta.ATR(df, timeperiod=period).to_numpy()
    high, low, close = (df[c].to_numpy() for c in ("high", "low", "close"))
    mid = (high + low) / 2
    upper_basic, lower_basic = mid + multiplier * atr, mid - multiplier * atr

    n = len(df)
    direction = np.full(n, np.nan)
    upper, lower = np.full(n, np.nan), np.full(n, np.nan)
    valid = np.where(~np.isnan(atr))[0]
    if len(valid) == 0:
        return pd.Series(direction, index=df.index)
    start = valid[0]
    upper[start], lower[start], direction[start] = upper_basic[start], lower_basic[start], 1

    for i in range(start + 1, n):
        # Bands only tighten in the trend's favour, unless price closed beyond them.
        upper[i] = upper_basic[i] if (upper_basic[i] < upper[i - 1] or close[i - 1] > upper[i - 1]) else upper[i - 1]
        lower[i] = lower_basic[i] if (lower_basic[i] > lower[i - 1] or close[i - 1] < lower[i - 1]) else lower[i - 1]
        if close[i] > upper[i - 1]:
            direction[i] = 1
        elif close[i] < lower[i - 1]:
            direction[i] = -1
        else:
            direction[i] = direction[i - 1]
    return pd.Series(direction, index=df.index)


def keltner(df: DataFrame, period: int, multiplier: float) -> tuple[Series, Series, Series]:
    """Keltner Channel: EMA middle line +/- multiplier x ATR (lower, middle, upper)."""
    mid = ta.EMA(df, timeperiod=period)
    atr = ta.ATR(df, timeperiod=period)
    return mid - multiplier * atr, mid, mid + multiplier * atr


def donchian_high(df: DataFrame, period: int) -> Series:
    """Highest high of the PREVIOUS `period` candles (the current candle is excluded,
    otherwise "close above the channel" could never happen and would hide lookahead)."""
    return df["high"].rolling(period).max().shift(1)


def donchian_low(df: DataFrame, period: int) -> Series:
    """Lowest low of the PREVIOUS `period` candles."""
    return df["low"].rolling(period).min().shift(1)


def run_length(flag: Series) -> Series:
    """How many candles in a row `flag` has been True, ending at each candle (0 if False)."""
    flag = flag.fillna(False).astype(bool)
    blocks = (~flag).cumsum()
    return flag.astype(int).groupby(blocks).cumsum()


def squeeze_momentum(df: DataFrame, period: int) -> Series:
    """LazyBear-style squeeze momentum: how far price sits from the middle of its
    recent range, smoothed with a linear regression. Positive = pushing up."""
    middle = (
        (df["high"].rolling(period).max() + df["low"].rolling(period).min()) / 2
        + df["close"].rolling(period).mean()
    ) / 2
    return ta.LINEARREG(df["close"] - middle, timeperiod=period)


def volume_ratio(df: DataFrame, period: int = 20) -> Series:
    """This candle's volume divided by the average of the previous `period` candles."""
    return df["volume"] / df["volume"].rolling(period).mean().shift(1)
