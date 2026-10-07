"""Tests for scripts/tuning.py and rules.stage2. Run: python3 scripts/lab.py test"""

import ast
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import rules  # noqa: E402
import tuning  # noqa: E402


class WalkForwardWindowsTest(unittest.TestCase):
    def test_project_windows(self):
        w = tuning.walkforward_windows("20231001", "20261001", 12, 3, 3)
        self.assertEqual(len(w), 8)
        self.assertEqual(w[0], {"k": 0, "train": "20231001-20241001", "test": "20241001-20250101"})
        self.assertEqual(w[-1]["test"], "20260701-20261001")

    def test_test_windows_follow_training_and_never_overlap(self):
        w = tuning.walkforward_windows("20231001", "20261001", 12, 3, 3)
        for a in w:
            self.assertEqual(a["train"].split("-")[1], a["test"].split("-")[0])  # test starts where train ends
        for a, b in zip(w, w[1:]):
            self.assertEqual(a["test"].split("-")[1], b["test"].split("-")[0])  # back to back, no overlap

    def test_month_arithmetic_wraps_years(self):
        from datetime import date
        self.assertEqual(tuning.add_months(date(2024, 11, 1), 3), date(2025, 2, 1))


class WalkForwardSummaryTest(unittest.TestCase):
    def row(self, test, train=20.0, dd=10.0, bh=5.0):
        return {"train_profit_pct": train, "train_days": 365, "test_profit_pct": test, "test_days": 91.25,
                "test_max_dd_pct": dd, "test_trades": 10, "bh_test_profit_pct": bh}

    def test_stitching_compounds_windows(self):
        s = tuning.walkforward_summary([self.row(10.0), self.row(-10.0)])
        self.assertAlmostEqual(s["stitched_profit_pct"], -1.0)  # 1.1 * 0.9 = 0.99
        self.assertEqual(s["profitable_windows_pct"], 50.0)

    def test_efficiency(self):
        # four quarters of +4.66% = +20% a year, same as training -> efficiency ~1
        s = tuning.walkforward_summary([self.row(4.66)] * 4)
        self.assertAlmostEqual(s["wf_efficiency"], 1.0, places=2)

    def test_efficiency_undefined_when_training_lost(self):
        self.assertIsNone(tuning.walkforward_summary([self.row(5.0, train=-10.0)])["wf_efficiency"])


class TunedStrategyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_best_epoch_is_lowest_loss(self):
        f = self.tmp / "x.fthypt"
        epochs = [
            {"current_epoch": 1, "loss": -1.0, "params_details": {"buy": {"a": 1}}, "results_metrics": {"total_trades": 60}},
            {"current_epoch": 2, "loss": -3.0, "params_details": {"buy": {"a": 2}}, "results_metrics": {"total_trades": 80}},
            {"current_epoch": 3, "loss": 100000, "params_details": {"buy": {"a": 3}}, "results_metrics": {"total_trades": 2}},
        ]
        f.write_text("\n".join(json.dumps(e) for e in epochs))
        best = tuning.best_epoch(f)
        self.assertEqual((best["epoch"], best["params"], best["epochs_run"], best["last_epoch"]),
                         (2, {"buy": {"a": 2}}, 3, 3))

    def test_rendered_tuned_class_is_valid_python_with_settings(self):
        params = {"buy": {"macd_set": "8_17_9", "volume_min": 2.1}, "sell": {}, "stoploss": {"stoploss": -0.065}}
        src = tuning.render_tuned("MacdVolumeV1", "macd_volume_v1", "MacdVolumeV1T", params, {"Tuned on": "x"})
        tree = ast.parse(src)
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        self.assertEqual((cls.name, cls.bases[0].id), ("MacdVolumeV1T", "MacdVolumeV1"))
        assigned = {t.id: ast.literal_eval(n.value) for n in cls.body if isinstance(n, ast.Assign) for t in n.targets}
        self.assertEqual(assigned, {"buy_params": {"macd_set": "8_17_9", "volume_min": 2.1}, "stoploss": -0.065})

    def test_tuned_names(self):
        self.assertEqual(tuning.tuned_names("EmaTrendV2", Path("ema_trend_v2.py")), ("EmaTrendV2T", "ema_trend_v2t.py"))

    def test_find_strategy_file(self):
        self.assertEqual(tuning.find_strategy_file("EmaTrendV1").name, "ema_trend_v1.py")
        with self.assertRaises(SystemExit):
            tuning.find_strategy_file("NoSuchStrategyV9")


class Stage2RulesTest(unittest.TestCase):
    WF = {"windows": 8, "profitable_windows_pct": 62.5, "wf_efficiency": 0.7}
    REGIMES = {w: 12.0 for w in ("bull-is", "bear-is", "sideways-is", "bull-oos", "bear-oos", "sideways-oos")}

    def test_pass(self):
        self.assertEqual(rules.stage2(self.WF, self.REGIMES)[0], "PASS")

    def test_failures(self):
        cases = {
            "walk-forward not run": (None, self.REGIMES),
            "test windows profitable": ({**self.WF, "profitable_windows_pct": 50.0}, self.REGIMES),
            "efficiency 0.40": ({**self.WF, "wf_efficiency": 0.4}, self.REGIMES),
            "efficiency n/a": ({**self.WF, "wf_efficiency": None}, self.REGIMES),
            "bear-oos": (self.WF, {**self.REGIMES, "bear-oos": 35.0}),
            "only 5 of 6": (self.WF, {k: v for k, v in list(self.REGIMES.items())[:5]}),
        }
        for text, (wf, reg) in cases.items():
            with self.subTest(text):
                status, checks = rules.stage2(wf, reg)
                self.assertEqual(status, "FAIL")
                self.assertTrue(any(text in t for ok, t in checks if not ok), checks)


if __name__ == "__main__":
    unittest.main()


class Round2RulesTest(unittest.TestCase):
    def m(self, name, **over):
        base = {"strategy": name, "trades": 80, "profit_pct": 30.0, "profit_factor": 1.4, "max_dd_pct": 15.0,
                "calmar": 1.5, "quarters_profitable": 7, "quarters_total": 11, "worst_quarter_pct": -6.0}
        base.update(over)
        return base

    BH = {"strategy": "BuyHoldV1", "max_dd_pct": 80.0, "calmar": 1.0}

    def test_exam_pass_and_each_failure(self):
        ok = self.m("EmaTrendV3")
        self.assertEqual(rules.exam(ok, self.m("x", profit_pct=20.0), self.BH, True)[0], "PASS")
        cases = {
            "X1": dict(trades=20), "X2": dict(profit_factor=1.1), "X4": dict(max_dd_pct=31.0),
            "X5": dict(calmar=0.9), "X6": dict(quarters_profitable=5),
        }
        for rule, over in cases.items():
            with self.subTest(rule):
                status, checks = rules.exam(self.m("EmaTrendV3", **over), self.m("x"), self.BH, True)
                self.assertEqual(status, "FAIL")
                self.assertTrue(any(t.startswith(rule) for ok_, t in checks if not ok_), checks)
        self.assertEqual(rules.exam(self.m("E", worst_quarter_pct=-12.0), self.m("x"), self.BH, True)[0], "FAIL")
        self.assertEqual(rules.exam(ok, self.m("x", profit_pct=-1.0), self.BH, True)[0], "FAIL")   # X3
        self.assertEqual(rules.exam(ok, self.m("x"), self.BH, None)[0], "FAIL")                    # X7

    def test_dev_selection_takes_best_two_eligible_per_idea(self):
        dev = {n: self.m(n, calmar=c) for n, c in
               (("EmaTrendV3", 1.0), ("EmaTrendV3b", 2.0), ("EmaTrendV3c", 1.5), ("MomentumRotationV1", 0.8))}
        dev["MomentumRotationV1"]["profit_factor"] = 1.05      # not eligible
        bias = {n: True for n in dev}
        selected, lines = rules.select_for_exam(dev, bias)
        self.assertEqual(selected, ["EmaTrendV3b", "EmaTrendV3c"])
        self.assertTrue(any("MomentumRotationV1` not eligible" in line for line in lines))

    def test_more_than_three_versions_is_refused(self):
        dev = {f"TrendPullbackV3{s}": self.m(f"TrendPullbackV3{s}") for s in ("", "b", "c", "d")}
        with self.assertRaises(SystemExit):
            rules.select_for_exam(dev, {n: True for n in dev})

    def test_preregistration_states_the_same_numbers(self):
        doc = (REPO / "docs" / "research" / "round2-preregistration.md").read_text()
        e, d = rules.EXAM, rules.DEV_SELECT
        for text in (f"≥ {e['min_trades']}", f"profit factor ≥ {e['min_profit_factor']:g}",
                     f"max drawdown ≤ {e['max_dd_pct']:g}%", f"≥ {e['min_profitable_quarters']} of the {e['quarters']} quarters",
                     f"worse than **−{abs(e['worst_quarter_pct']):g}%**", f"dev profit factor ≥ {d['min_profit_factor']:g}",
                     f"at least {d['min_trades']} dev trades", f"best {d['per_idea']} per idea",
                     f"At most {d['max_versions_per_idea']} versions per idea"):
            self.assertIn(text, doc)
