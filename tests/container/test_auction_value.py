"""Tests for the Round 6 volume profile (labkit.auction) and AuctionValueV1's daily view.
Need numpy/pandas/Freqtrade, so they run inside the container:
python3 scripts/lab.py test   (runs host tests, then these)"""

import math
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "user_data" / "strategies"))

from auction_value_v1 import AuctionValueV1  # noqa: E402
from labkit.auction import expand_value_area, value_area, volume_profile  # noqa: E402


def slow_profile(high, low, volume, edges):
    """The same profile, one candle and one price step at a time (exact overlap of log ranges)."""
    out = np.zeros(len(edges) - 1)
    for h, l, v in zip(np.log(high), np.log(low), volume):
        for i in range(len(edges) - 1):
            a, b = edges[i], edges[i + 1]
            if h > l:
                out[i] += v * max(0.0, min(b, h) - max(a, l)) / (h - l)
            elif a <= l < b:
                out[i] += v
    return out


class VolumeProfileTest(unittest.TestCase):
    def test_matches_the_slow_version(self):
        rng = np.random.default_rng(7)
        mid = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 168)))
        high, low = mid * (1 + rng.uniform(0, 0.02, 168)), mid * (1 - rng.uniform(0, 0.02, 168))
        low[5] = high[5]                                   # one candle without range
        volume = rng.uniform(1, 50, 168)
        edges, bins = volume_profile(high, low, volume, 0.0025)
        self.assertTrue(np.allclose(bins, slow_profile(high, low, volume, edges), rtol=1e-9, atol=1e-9))
        self.assertAlmostEqual(bins.sum(), volume.sum(), places=6)       # no volume lost at the edges
        self.assertAlmostEqual(math.exp(edges[0]), low.min(), places=9)
        self.assertGreater(math.exp(edges[-1]), high.max())
        self.assertTrue(np.allclose(np.diff(edges), math.log1p(0.0025)))

    def test_candle_without_range_at_the_top(self):
        edges, bins = volume_profile(np.array([110.0, 105.0]), np.array([100.0, 105.0]), np.array([1.0, 2.0]), 0.0025)
        self.assertAlmostEqual(bins.sum(), 3.0)
        edges, bins = volume_profile(np.array([100.0]), np.array([100.0]), np.array([4.0]), 0.0025)
        self.assertEqual(list(bins), [4.0])


class ValueAreaTest(unittest.TestCase):
    def test_expansion_by_hand(self):
        self.assertEqual(expand_value_area(np.array([1, 2, 10, 3, 1.0]), 0.70), (2, 2, 3))   # 3 above beats 2 below
        self.assertEqual(expand_value_area(np.array([0, 5, 10, 5, 0.0]), 0.90), (1, 2, 3))   # tie: above first
        self.assertEqual(expand_value_area(np.array([10, 1, 1, 1.0]), 0.80), (0, 0, 1))      # nothing below
        self.assertEqual(expand_value_area(np.array([1, 1, 9.0]), 0.95), (0, 2, 2))          # nothing above
        self.assertEqual(expand_value_area(np.array([2, 7, 1.0]), 0.70), (1, 1, 1))          # POC alone is enough

    def test_prices(self):
        high, low, volume = np.array([110.0, 104.0]), np.array([100.0, 102.0]), np.array([10.0, 30.0])
        val, poc, vah = value_area(high, low, volume, 0.0025, 0.70)
        self.assertTrue(100.0 <= val < poc < vah <= 110.0)
        self.assertTrue(102.0 <= poc <= 104.0)                 # the busy small candle holds the POC
        edges, bins = volume_profile(high, low, volume, 0.0025)
        inside = bins[(edges[:-1] >= math.log(val) - 1e-12) & (edges[1:] <= math.log(vah) + 1e-12)].sum()
        self.assertGreaterEqual(inside, 0.70 * bins.sum() - 1e-9)

    def test_no_volume_gives_no_levels(self):
        self.assertTrue(all(math.isnan(x) for x in value_area(np.array([2.0]), np.array([1.0]), np.array([0.0]))))


def hourly(days: int, start: str = "2024-01-01 00:00", seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    date = pd.date_range(start, periods=days * 24, freq="1h", tz="UTC")
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.006, len(date))))
    open_ = np.r_[100.0, close[:-1]]
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.004, len(date)))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.004, len(date)))
    return pd.DataFrame({"date": date, "open": open_, "high": high, "low": low, "close": close,
                         "volume": rng.uniform(10, 100, len(date))})


class DailyViewTest(unittest.TestCase):
    def view(self, df, **settings):
        strat = AuctionValueV1.__new__(AuctionValueV1)       # no Freqtrade config needed for the maths
        for k, v in settings.items():
            setattr(strat, k, v)
        return strat._value_view(df)

    def test_decisions_only_on_the_last_candle_of_each_session(self):
        df = hourly(40)
        v = self.view(df)
        hours = df.loc[v["av_decision"], "date"].dt.hour
        self.assertTrue((hours == 11).all())
        self.assertEqual(len(hours), 40 - 15)   # first session partial; 14 full sessions needed before a decision

    def test_levels_come_from_the_seven_sessions_before(self):
        df = hourly(40)
        v = self.view(df)
        i = v.index[v["av_decision"]][-1]
        window = df.iloc[i - 23 - 168:i - 23]                      # 168 candles before today's session
        self.assertEqual(window["date"].iloc[0].hour, 12)
        val, poc, vah = value_area(window["high"].to_numpy(), window["low"].to_numpy(), window["volume"].to_numpy())
        self.assertAlmostEqual(v.at[i, "av_val"], val)
        self.assertAlmostEqual(v.at[i, "av_poc"], poc)
        self.assertAlmostEqual(v.at[i, "av_vah"], vah)
        self.assertAlmostEqual(v.at[i, "av_low"], df["low"].iloc[i - 23:i + 1].min())

    def test_setups_follow_the_written_rules(self):
        df = hourly(400, seed=3)
        v = self.view(df)
        d = v[v["av_decision"]].copy()
        close, low = df.loc[d.index, "close"], d["av_low"]
        drop = ((d["av_state"] >= 0) & (low < d["av_val"]) & (close > d["av_val"]) & (close < d["av_vah"])
                & ((d["av_vah"] - close) >= 1.0 * (close - low)))

        def prev_session_above(i):          # the session before closed above its own value high
            j = i - 24
            w = df.iloc[j - 23 - 168:j - 23]
            return df["close"].iat[j] > value_area(w["high"].to_numpy(), w["low"].to_numpy(), w["volume"].to_numpy())[2]

        above_before = pd.Series([prev_session_above(i) for i in d.index], index=d.index)
        rise = (d["av_state"] == 1) & (close > d["av_vah"]) & above_before
        self.assertTrue(drop.any() and rise.any(), "the random walk should produce both setups")
        self.assertTrue(((d["av_enter"] == "failed_drop") == drop).all())
        self.assertTrue(((d["av_enter"] == "accepted_rise") == rise).all())
        self.assertTrue((d.loc[drop, "av_stop"] == low[drop]).all())
        self.assertTrue((d.loc[drop, "av_target"] == d.loc[drop, "av_vah"]).all())
        self.assertTrue((d.loc[rise, "av_stop"] == d.loc[rise, "av_val"]).all())
        self.assertTrue(d.loc[rise, "av_target"].isna().all())

    def test_state_compares_with_the_week_before(self):
        df = hourly(60, seed=5)
        v = self.view(df)
        d = v[v["av_decision"]]
        later = d.index[-1]
        earlier = later - 7 * 24
        up = (d.at[later, "av_vah"] > v.at[earlier, "av_vah"]) and (d.at[later, "av_val"] > v.at[earlier, "av_val"])
        down = (d.at[later, "av_vah"] < v.at[earlier, "av_vah"]) and (d.at[later, "av_val"] < v.at[earlier, "av_val"])
        self.assertEqual(d.at[later, "av_state"], 1 if up else (-1 if down else 0))

    def test_no_peeking_and_no_dependence_on_the_start(self):
        df = hourly(80, seed=9)
        full = self.view(df)
        cut = 60 * 24 + 11                                       # data ends on a decision candle
        self.assertTrue(full.iloc[:cut + 1].equals(self.view(df.iloc[:cut + 1].copy()).iloc[:cut + 1]))
        later = self.view(df.iloc[100:].reset_index(drop=True)).set_index(df.index[100:])
        both = full.index[full["av_decision"] & later.reindex(full.index)["av_decision"].fillna(False).astype(bool)]
        self.assertGreater(len(both), 30)
        cols = ["av_val", "av_poc", "av_vah", "av_state", "av_low", "av_stop", "av_target"]
        pd.testing.assert_frame_equal(full.loc[both, cols], later.loc[both, cols])
        self.assertTrue((full.loc[both, "av_enter"].fillna("") == later.loc[both, "av_enter"].fillna("")).all())

    def test_session_boundary_and_delay_settings(self):
        df = hourly(40)
        v = self.view(df, REBALANCE_HOUR=23)
        self.assertTrue((df.loc[v["av_decision"], "date"].dt.hour == 23).all())
        base, late = self.view(df), self.view(df, DELAY_HOURS=2)
        self.assertTrue(late["av_decision"].to_numpy()[2:].tolist() == base["av_decision"].to_numpy()[:-2].tolist())
        i = base.index[base["av_decision"]][-1]
        self.assertEqual(late.at[i + 2, "av_vah"], base.at[i, "av_vah"])

    def test_v2_drops_only_the_failed_drops_outside_balance(self):
        from auction_value_v2 import AuctionValueV2
        df = hourly(400, seed=3)
        v1 = self.view(df)
        v2 = AuctionValueV2.__new__(AuctionValueV2)._value_view(df)
        removed = (v1["av_enter"] == "failed_drop") & (v1["av_state"] != 0)
        self.assertTrue(removed.any() and ((v1["av_enter"] == "failed_drop") & (v1["av_state"] == 0)).any())
        self.assertTrue(v2.loc[removed, "av_enter"].isna().all() and v2.loc[removed, "av_stop"].isna().all())
        kept = ~removed
        pd.testing.assert_frame_equal(v1[kept], v2[kept])
        late = AuctionValueV2.__new__(AuctionValueV2)
        late.DELAY_HOURS = 3
        self.assertTrue(late._value_view(df)["av_enter"].shift(-3).fillna("").eq(v2["av_enter"].fillna("")).all())

    def test_longer_profiles(self):
        df = hourly(60)
        v = self.view(df, PROFILE_SESSIONS=10)
        i = v.index[v["av_decision"]][-1]
        window = df.iloc[i - 23 - 240:i - 23]
        val, poc, vah = value_area(window["high"].to_numpy(), window["low"].to_numpy(), window["volume"].to_numpy())
        self.assertAlmostEqual(v.at[i, "av_vah"], vah)


if __name__ == "__main__":
    unittest.main()
