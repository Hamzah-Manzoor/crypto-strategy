"""Tests for rules.py, report.py, experiments.py and lab.py period handling.
Run: python3 scripts/lab.py test"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import experiments  # noqa: E402
import lab  # noqa: E402
import report  # noqa: E402
import rules  # noqa: E402


def metrics(name="EmaTrendV1", **over):
    m = {
        "strategy": name, "timeframe": "1h", "timeframe_detail": None, "timerange": "20231001-20251001",
        "start": "2023-10-01", "end": "2025-10-01", "days": 731.0, "trades": 120, "win_rate_pct": 45.0,
        "profit_factor": 1.5, "avg_hold_hours": 20.0, "market_change_pct": 150.0, "final_balance": 1400.0,
        "profit_pct": 40.0, "cagr_pct": 18.3, "max_dd_pct": 12.0, "sharpe": 1.4, "sortino": 2.0, "calmar": 1.5,
        "exposure_pct": 35.0, "code_sha": "abc", "stoploss": -0.08, "minimal_roi": {"0": 0.3}, "trailing_stop": True,
    }
    m.update(over)
    return m


def run(run_id, period, strategies, timeframe="1h", fee=0.001):
    return {"run_id": run_id, "period": period, "timerange": "20231001-20251001", "timeframe": timeframe,
            "timeframe_detail": None, "fee": fee, "notes": "", "zip": "x.zip",
            "strategies": {s["strategy"]: s for s in strategies}}


BH_OOS = metrics("BuyHoldV1", profit_pct=-30.0, max_dd_pct=45.0, calmar=-0.7, sharpe=-0.5, trades=5)


class SuspiciousFlagsTest(unittest.TestCase):
    def test_normal_result_has_no_flags(self):
        self.assertEqual(rules.suspicious_flags(metrics()), [])

    def test_baseline_is_never_flagged(self):
        self.assertEqual(rules.suspicious_flags(metrics("BuyHoldV1", trades=5, sharpe=9)), [])

    def test_short_periods_are_not_flagged(self):
        self.assertEqual(rules.suspicious_flags(metrics(days=90, trades=4, sharpe=5)), [])

    def test_each_flag(self):
        cases = {"Sharpe": dict(sharpe=3.5), "win rate": dict(win_rate_pct=85.0),
                 "profit factor": dict(profit_factor=4.0), "only 12 trades": dict(trades=12),
                 "drawdown": dict(max_dd_pct=2.0)}
        for text, over in cases.items():
            with self.subTest(text):
                flags = rules.suspicious_flags(metrics(**over))
                self.assertTrue(any(text in f for f in flags), flags)


class Stage1RulesTest(unittest.TestCase):
    def verdict(self, is_over=None, oos_over=None, stress=metrics(profit_pct=5.0), bias=True, bh=BH_OOS):
        is_m = metrics(**(is_over or {}))
        oos_m = metrics(**{"timerange": "20251001-20261001", "days": 365.0, "trades": 40, "profit_pct": 10.0,
                           "sharpe": 1.0, "max_dd_pct": 15.0, "calmar": 0.7, **(oos_over or {})})
        return rules.stage1(is_m, oos_m, stress, bh, bias)

    def test_good_strategy_passes(self):
        status, checks = self.verdict()
        self.assertEqual(status, "PASS", checks)

    def assert_fails(self, text, **kw):
        status, checks = self.verdict(**kw)
        self.assertEqual(status, "FAIL")
        failed = [t for ok, t in checks if not ok]
        self.assertTrue(any(text in t for t in failed), failed)

    def test_too_few_trades(self):
        self.assert_fails("trades IS", is_over=dict(trades=30))
        self.assert_fails("trades IS", oos_over=dict(trades=10))

    def test_drawdown_too_big(self):
        self.assert_fails("OOS max drawdown", oos_over=dict(max_dd_pct=26.0))

    def test_drawdown_not_better_than_buy_and_hold(self):
        self.assert_fails("OOS max drawdown", bh=metrics("BuyHoldV1", max_dd_pct=14.0, calmar=-1.0))

    def test_losing_out_of_sample(self):
        self.assert_fails("OOS profit", oos_over=dict(profit_pct=-1.0))

    def test_weak_profit_factor_or_none(self):
        self.assert_fails("profit factor", oos_over=dict(profit_factor=1.1))
        self.assert_fails("profit factor", oos_over=dict(profit_factor=None))

    def test_stress_fee(self):
        self.assert_fails("0.15% fee not run", stress=None)
        self.assert_fails("0.15% fee", stress=metrics(profit_pct=-0.5))

    def test_calmar_not_better_than_buy_and_hold(self):
        self.assert_fails("OOS Calmar", bh=metrics("BuyHoldV1", max_dd_pct=40.0, calmar=0.9))

    def test_sharpe_decay(self):
        self.assert_fails("Sharpe IS", oos_over=dict(sharpe=0.6))  # keeps 43% of 1.4
        self.assert_fails("Sharpe IS", is_over=dict(sharpe=-0.2))

    def test_bias(self):
        self.assert_fails("bias checks FAILED", bias=False)
        self.assert_fails("bias checks not run", bias=None)

    def test_too_good_goes_to_review(self):
        status, checks = self.verdict(oos_over=dict(sharpe=3.5, calmar=5.0))
        self.assertEqual(status, "REVIEW")
        self.assertIn("too good", checks[-1][1])


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._boards, self._doc = report.BOARDS, report.RESULTS_DOC
        report.BOARDS, report.RESULTS_DOC = self.tmp / "boards", self.tmp / "RESULTS.md"

    def tearDown(self):
        report.BOARDS, report.RESULTS_DOC = self._boards, self._doc
        shutil.rmtree(self.tmp)

    def sample_run(self, run_id="20261006-000000_is_1h", period="is"):
        return run(run_id, period, [
            metrics("BuyHoldV1", calmar=1.0, trades=5, profit_factor=None),
            metrics("EmaTrendV1", calmar=1.5),
            metrics("RsiBbReversionV1", calmar=0.4),
        ])

    def test_leaderboard_sorted_by_calmar_with_baseline_comparison(self):
        rows = report.leaderboard(self.sample_run())
        self.assertEqual([r["strategy"] for r in rows], ["EmaTrendV1", "BuyHoldV1", "RsiBbReversionV1"])
        self.assertEqual([r["beats_bh"] for r in rows], ["yes", "baseline", "no"])
        self.assertEqual([r["rank"] for r in rows], [1, 2, 3])

    def test_write_run_creates_markdown_and_csv(self):
        md = report.write_run(self.sample_run())
        text = md.read_text()
        self.assertIn("`EmaTrendV1`", text)
        self.assertIn("Calmar", text)
        self.assertIn("n/a", text)  # buy & hold profit factor
        csv_text = (report.BOARDS / "20261006-000000_is_1h.csv").read_text()
        self.assertTrue(csv_text.startswith("rank,strategy,profit_pct"))

    def test_results_doc_only_changes_between_markers(self):
        report.RESULTS_DOC.write_text("# Results\nintro\n<!-- AUTO:START -->\nSTALE-CONTENT\n<!-- AUTO:END -->\nmy notes\n")
        report.update_results_doc([self.sample_run()])
        text = report.RESULTS_DOC.read_text()
        self.assertIn("intro", text)
        self.assertIn("my notes", text)
        self.assertNotIn("STALE-CONTENT", text)
        self.assertIn("In-sample · 1h", text)

    def test_results_doc_without_markers_fails_loudly(self):
        report.RESULTS_DOC.write_text("# Results\n")
        with self.assertRaises(SystemExit):
            report.update_results_doc([self.sample_run()])

    def test_latest_picks_newest_standard_run(self):
        runs = [self.sample_run("20261006-000000_is_1h"), self.sample_run("20261007-000000_is_1h"),
                run("20261008-000000_is_1h_fee0.15pct", "is", [metrics("BuyHoldV1")], fee=0.0015)]
        self.assertEqual(report.latest(runs, "is", "1h")["run_id"], "20261007-000000_is_1h")

    def test_latest_treats_empty_detail_as_none(self):
        r = self.sample_run()
        r["timeframe_detail"] = ""  # what Freqtrade writes when there is no detail timeframe
        self.assertIs(report.latest([r], "is", "1h"), r)

    def test_stage1_table(self):
        is_run = self.sample_run()
        oos_run = run("20261006-000001_oos_1h", "oos", [
            BH_OOS, metrics("EmaTrendV1", trades=40, profit_pct=10.0, sharpe=1.0, max_dd_pct=15.0, calmar=0.7),
            metrics("RsiBbReversionV1", trades=40, profit_pct=-5.0, sharpe=-0.3, max_dd_pct=20.0, calmar=-0.2)])
        stress = run("20261006-000002_oos_1h_fee0.15pct", "oos", [
            metrics("EmaTrendV1", profit_pct=6.0), metrics("RsiBbReversionV1", profit_pct=-9.0)], fee=0.0015)
        rows = report.stage1(is_run, oos_run, stress, {"EmaTrendV1": True, "RsiBbReversionV1": True})
        self.assertEqual({r["strategy"]: r["status"] for r in rows}, {"EmaTrendV1": "PASS", "RsiBbReversionV1": "FAIL"})
        md = report.stage1_md(is_run, oos_run, stress, rows)
        self.assertIn("✅", md)
        self.assertIn("❌", md)


class ExperimentsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.log, self.doc = self.tmp / "exp.jsonl", self.tmp / "LOG.md"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_log_decide_render(self):
        r = run("20261006-000000_is_1h", "is", [metrics("BuyHoldV1"), metrics("EmaTrendV1")])
        ids = experiments.log_run(r, log=self.log)
        self.assertEqual(ids, ["E0001", "E0002"])
        entries = experiments.load(self.log)
        self.assertEqual(entries[0]["decision"], "baseline")
        self.assertEqual(entries[1]["decision"], "pending")
        self.assertEqual(experiments.log_run(r, oos_look=True, log=self.log), ["E0003", "E0004"])

        experiments.decide("E0002", "tweak", "whipsaws in chop", log=self.log)
        self.assertEqual(experiments.load(self.log)[1]["decision_note"], "whipsaws in chop")

        experiments.render(log=self.log, doc=self.doc)
        text = self.doc.read_text()
        self.assertIn("**4 entries**, 2 of them out-of-sample looks", text)
        self.assertIn("tweak: whipsaws in chop", text)
        self.assertIn("👁", text)

    def test_refresh_updates_measurements_but_keeps_decisions(self):
        r = run("r1", "is", [metrics("EmaTrendV1", profit_pct=5.0)], fee=0.001)
        experiments.log_run(r, log=self.log)
        experiments.decide("E0001", "keep", "looks fine", log=self.log)
        fixed = run("r1", "is", [metrics("EmaTrendV1", profit_pct=7.5)], fee=0.0)
        self.assertEqual(experiments.refresh([fixed], log=self.log), 1)
        e = experiments.load(self.log)[0]
        self.assertEqual((e["fee"], e["metrics"]["profit_pct"]), (0.0, 7.5))
        self.assertEqual((e["id"], e["decision"], e["decision_note"]), ("E0001", "keep", "looks fine"))
        self.assertEqual(experiments.refresh([fixed], log=self.log), 0)  # nothing left to change

    def test_bad_decisions_are_rejected(self):
        experiments.log_run(run("r", "is", [metrics()]), log=self.log)
        with self.assertRaises(SystemExit):
            experiments.decide("E0001", "maybe", "", log=self.log)
        with self.assertRaises(SystemExit):
            experiments.decide("E9999", "keep", "", log=self.log)


class DocsMatchRulesTest(unittest.TestCase):
    """docs/TESTING_METHODOLOGY.md must state the thresholds that scripts/rules.py enforces."""

    def test_thresholds_are_documented(self):
        doc = (REPO / "docs" / "TESTING_METHODOLOGY.md").read_text()
        s1, s2, sus = rules.STAGE1, rules.STAGE2, rules.SUSPICIOUS
        expected = [
            f"≥ {s1['min_trades_is']} in-sample", f"≥ {s1['min_trades_oos']} out-of-sample",
            f"OOS max DD ≤ {s1['max_dd_oos_pct']:g}%", f"profit factor ≥ {s1['min_profit_factor_oos']:g}",
            f"OOS Sharpe ≥ {s1['min_oos_is_sharpe_ratio']:.0%} of IS Sharpe",
            f"≥ {s2['min_profitable_windows_pct']:g}% of walk-forward", f"≥ {s2['min_wf_efficiency']:g} |",
            f"Max DD ≤ {s2['max_dd_regime_pct']:g}% in every regime",
            f"Sharpe above {sus['sharpe_above']:g}", f"win rate above {sus['win_rate_above_pct']:g}%",
            f"profit factor above {sus['profit_factor_above']:g}", f"under {sus['trades_below']}",
            f"drawdown below {sus['max_dd_below_pct']:g}%",
        ]
        missing = [e for e in expected if e not in doc]
        self.assertEqual(missing, [], "TESTING_METHODOLOGY.md is out of sync with scripts/rules.py")


class PeriodTest(unittest.TestCase):
    def test_protected_holdout_detection(self):
        self.assertEqual(lab.touches_protected("20231001-20261001"), [])        # dev data
        self.assertEqual(lab.touches_protected("20251001-20261001"), [])        # retired Round 1 OOS year
        self.assertEqual(lab.touches_protected("20210101-20231001"), ["holdout"])
        self.assertEqual(lab.touches_protected("20200801-20210102"), ["holdout"])  # one day in
        self.assertEqual(lab.touches_protected("20200801-20210101"), [])        # end date is exclusive
        self.assertEqual(lab.touches_protected("20231001-"), [])
        self.assertEqual(lab.touches_protected("20220101-"), ["holdout"])

    def test_resolve_period(self):
        self.assertEqual(lab.resolve_period("is"), ("is", "20231001-20251001"))
        self.assertEqual(lab.resolve_period("dev"), ("dev", "20231001-20261001"))
        self.assertEqual(lab.resolve_period("holdout"), ("holdout", "20210101-20231001"))
        self.assertEqual(lab.resolve_period("full"), ("full", "20231001-20261001"))
        self.assertEqual(lab.resolve_period("20240101-20240201"), ("custom", "20240101-20240201"))
        regimes = json.loads((REPO / "results" / "regimes.json").read_text())["windows"]
        self.assertEqual(lab.resolve_period("bull-is"), ("bull-is", regimes["bull-is"]["timerange"]))
        with self.assertRaises(SystemExit):
            lab.resolve_period("someday")


if __name__ == "__main__":
    unittest.main()
