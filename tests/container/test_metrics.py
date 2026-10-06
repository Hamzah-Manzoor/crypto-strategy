"""Tests for scripts/metrics.py. Need pandas, so they run inside the Freqtrade container:
python3 scripts/lab.py test   (runs host tests, then these)"""

import math
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import metrics  # noqa: E402


def hourly(values, start="2024-01-01 01:00"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="1h", tz="UTC"), dtype=float)


class EquityMetricsTest(unittest.TestCase):
    def test_drawdown_is_measured_on_the_wallet_value(self):
        # 1000 -> 1200 -> 900 -> 1100: worst fall from a peak is 1200 -> 900 = 25%.
        equity = hourly([1000, 1100, 1200, 1050, 900, 1000, 1100])
        m = metrics.equity_metrics(equity, start_balance=1000, final_balance=1100, days=365)
        self.assertAlmostEqual(m["max_dd_pct"], 25.0)
        self.assertAlmostEqual(m["profit_pct"], 10.0)
        self.assertAlmostEqual(m["cagr_pct"], 10.0)        # exactly one year
        self.assertAlmostEqual(m["calmar"], 0.10 / 0.25)

    def test_cagr_annualises(self):
        m = metrics.equity_metrics(hourly([1000, 1210]), 1000, 1210, days=730)
        self.assertAlmostEqual(m["cagr_pct"], 10.0, places=6)  # 21% over two years

    def test_flat_wallet_has_zero_risk_numbers(self):
        m = metrics.equity_metrics(hourly([1000] * 100), 1000, 1000, days=4)
        self.assertEqual((m["max_dd_pct"], m["sharpe"], m["sortino"], m["calmar"]), (0.0, 0.0, 0.0, 0.0))

    def test_sharpe_and_sortino_use_daily_returns(self):
        days = pd.date_range("2024-01-01", periods=60, freq="1D", tz="UTC")
        rets = [0.01 if i % 2 else -0.005 for i in range(60)]
        equity = pd.Series(1000 * pd.Series(rets).add(1).cumprod().to_numpy(), index=days)
        m = metrics.equity_metrics(equity, 1000, float(equity.iloc[-1]), days=60)
        daily = pd.concat([pd.Series([1000.0]), pd.Series(equity.to_numpy())]).pct_change().dropna()
        expected = daily.mean() / daily.std(ddof=1) * math.sqrt(365)
        self.assertAlmostEqual(m["sharpe"], expected, places=6)
        self.assertGreater(m["sortino"], m["sharpe"])  # losses are smaller than gains here


class WalletTest(unittest.TestCase):
    def wallet(self):
        rows = []
        for i, date in enumerate(pd.date_range("2024-01-01", periods=4, freq="1h", tz="UTC")):
            if i < 2:  # all cash
                rows.append((date, "USDT", 1.0, 1000.0, 1000.0))
            else:      # all in BTC
                rows += [(date, "USDT", 1.0, 0.0, 0.0), (date, "BTC", 50000.0, 0.02, 1000.0)]
        return pd.DataFrame(rows, columns=["date", "currency", "rate", "balance", "total_quote"])

    def test_equity_curve_sums_cash_and_coins(self):
        curve = metrics.equity_curve(self.wallet())
        self.assertEqual(list(curve), [1000.0] * 4)

    def test_exposure_is_share_of_time_in_coins(self):
        self.assertAlmostEqual(metrics.exposure_pct(self.wallet(), "USDT"), 50.0)

    def test_profit_factor_undefined_without_losses(self):
        stats = {"starting_balance": 1000, "final_balance": 1100, "backtest_start_ts": 0,
                 "backtest_end_ts": 86400 * 1000 * 10, "total_trades": 3, "wins": 3, "losses": 0,
                 "winrate": 1.0, "profit_factor": 0.0, "holding_avg_s": 3600, "timeframe": "1h",
                 "timerange": "x", "backtest_start": "a", "backtest_end": "b"}
        m = metrics.summarize_strategy("X", stats, self.wallet(), b"code")
        self.assertIsNone(m["profit_factor"])
        self.assertEqual(m["trades"], 3)


class AppliedFeeTest(unittest.TestCase):
    """The zip's config copy keeps the file fee even when --fee overrides it, so the fee
    must come from the trades themselves."""

    def report(self, *fees):
        return {"strategy": {"A": {"trades": [{"fee_open": f, "fee_close": f} for f in fees]}, "B": {"trades": []}}}

    def test_fee_comes_from_trades_not_config(self):
        self.assertEqual(metrics.applied_fee(self.report(0.0015, 0.0015), {"fee": 0.001}), 0.0015)

    def test_no_trades_falls_back_to_config(self):
        self.assertEqual(metrics.applied_fee(self.report(), {"fee": 0.001}), 0.001)

    def test_mixed_fees_fail_loudly(self):
        with self.assertRaises(SystemExit):
            metrics.applied_fee(self.report(0.001, 0.0015), {"fee": 0.001})


if __name__ == "__main__":
    unittest.main()
