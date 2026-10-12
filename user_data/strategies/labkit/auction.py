"""Auction Market Theory helpers: the volume profile and its value area (Round 6).

The idea: count how much traded at each price over a window. The busiest price is the
point of control (POC); the busiest 70% of the volume around it is the value area, the
range both buyers and sellers accepted as fair. We only have candles, not every trade,
so each candle's volume is spread evenly over its own low-high range - the standard way
to build a profile from candles.

Everything here works on the candles it is given and nothing else, so a profile built
from past candles can't peek into the future. Tests: tests/container/test_auction_value.py
(compared with a slow, cell-by-cell version).
"""

from __future__ import annotations

import math

import numpy as np


def volume_profile(high: np.ndarray, low: np.ndarray, volume: np.ndarray,
                   step: float = 0.0025) -> tuple[np.ndarray, np.ndarray]:
    """Volume traded in each price step (steps of `step`, e.g. 0.25%, on a log scale).

    Returns the step edges (log prices, from the lowest low upwards, the top edge above
    the highest high) and the volume in each step.
    """
    lo, hi = np.log(low), np.log(high)
    width = math.log1p(step)
    base = lo.min()
    edges = base + width * np.arange(int((hi.max() - base) // width) + 2)
    # Share of each candle's volume below each edge (its volume is spread evenly over its range;
    # a candle without range puts it all at its one price).
    span = hi - lo
    below = np.where(span > 0, np.clip((edges[:, None] - lo) / np.where(span > 0, span, 1.0), 0.0, 1.0),
                     (edges[:, None] > lo).astype(float))
    return edges, np.diff(below @ volume)


def expand_value_area(bins: np.ndarray, share: float = 0.70) -> tuple[int, int, int]:
    """Value area as step indexes (low, POC, high): start at the busiest step and keep adding
    the busier neighbour (above on a tie) until `share` of all volume is inside."""
    poc = int(np.argmax(bins))
    low = high = poc
    inside, target = bins[poc], share * bins.sum()
    while inside < target and (low > 0 or high < len(bins) - 1):
        above = bins[high + 1] if high < len(bins) - 1 else -1.0
        below = bins[low - 1] if low > 0 else -1.0
        if above >= below:
            high += 1
            inside += above
        else:
            low -= 1
            inside += below
    return low, poc, high


def value_area(high: np.ndarray, low: np.ndarray, volume: np.ndarray, step: float = 0.0025,
               share: float = 0.70) -> tuple[float, float, float]:
    """(value low, point of control, value high) as prices; NaN if nothing traded."""
    edges, bins = volume_profile(high, low, volume, step)
    if not bins.sum() > 0:
        return math.nan, math.nan, math.nan
    lo, poc, hi = expand_value_area(bins, share)
    return math.exp(edges[lo]), math.exp((edges[poc] + edges[poc + 1]) / 2), math.exp(edges[hi + 1])
