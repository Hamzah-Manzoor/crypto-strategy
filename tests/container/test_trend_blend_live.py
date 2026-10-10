"""Tests for TrendBlendV2Live's catch-up window. Need Freqtrade, so they run inside the container:
python3 scripts/lab.py test   (runs host tests, then these)"""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "user_data" / "strategies"))

from trend_blend_v2_live import TrendBlendV2Live  # noqa: E402

SETTINGS = SimpleNamespace(REBALANCE_HOUR=11, LAST_DECISION_CANDLE=22)


class CatchUpWindowTest(unittest.TestCase):
    def start(self, hour, minute=0):
        return TrendBlendV2Live._window_start(SETTINGS, datetime(2026, 10, 11, hour, minute, tzinfo=timezone.utc))

    def test_open_from_noon_to_midnight_utc(self):
        noon = datetime(2026, 10, 11, 12, tzinfo=timezone.utc)
        for hour in (12, 13, 17, 23):              # 5 pm ... 4:59 am Pakistan time
            self.assertEqual(self.start(hour, 59), noon)

    def test_closed_before_noon_and_after_the_daily_close(self):
        for hour in (0, 5, 11):                     # the next daily candle closes at 00:00 UTC
            self.assertIsNone(self.start(hour, 59))

    def test_signal_rows_stop_before_the_candle_that_carries_the_new_day(self):
        frame = pd.DataFrame({"date": pd.date_range("2026-10-11", periods=24, freq="1h", tz="UTC")})
        hours = frame["date"][TrendBlendV2Live._decision(SETTINGS, frame)].dt.hour.tolist()
        self.assertEqual(hours, list(range(11, 23)))   # 11:00 ... 22:00 candles; never 23:00


if __name__ == "__main__":
    unittest.main()
