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


class Round3RulesTest(unittest.TestCase):
    def m(self, name, **over):
        base = {"strategy": name, "trades": 60, "profit_pct": 150.0, "profit_factor": 2.0,
                "max_dd_pct": 25.0, "calmar": 1.5}
        base.update(over)
        return base

    def test_picks_best_calmar_among_eligible(self):
        dev = {"MomentumRotationV2": self.m("MomentumRotationV2", calmar=1.2),
               "MomentumRotationV2b": self.m("MomentumRotationV2b", calmar=2.0, max_dd_pct=35.0),  # DD too big
               "MomentumRotationV2c": self.m("MomentumRotationV2c", calmar=1.4)}
        pick, lines = rules.select_round3(dev, {n: True for n in dev})
        self.assertEqual(pick, "MomentumRotationV2c")
        self.assertTrue(any("V2b`: not eligible (max drawdown 35.0% > 30%" in line for line in lines))

    def test_none_eligible_drops_the_idea(self):
        dev = {n: self.m(n, max_dd_pct=40.0) for n in rules.ROUND3_CANDIDATES}
        self.assertIsNone(rules.select_round3(dev, {n: True for n in dev})[0])

    def test_preregistration_states_the_same_numbers(self):
        doc = (REPO / "docs" / "research" / "momentum-drawdown-preregistration.md").read_text()
        s, f = rules.ROUND3_SELECT, rules.FORWARD
        for text in (f"dev max drawdown **≤ {s['max_dd_pct']:g}%**", f"profit factor **≥ {s['min_profit_factor']:g}**",
                     f"at least **{s['min_trades']}** trades", f"≥ {f['min_trades']} |",
                     f"max drawdown **≤ {f['max_dd_pct']:g}%**",
                     f"≥ {f['min_profitable_quarters']} of the {f['quarters']} quarters profitable",
                     f"worse than −{abs(f['worst_quarter_pct']):g}%"):
            self.assertIn(text, doc)


class Round4RulesTest(unittest.TestCase):
    def test_exam_is_round3_forward_rules_over_8_quarters(self):
        e, f = rules.ROUND4_EXAM, rules.FORWARD
        self.assertEqual({k: v for k, v in e.items() if k not in ("quarters", "min_profitable_quarters")},
                         {k: v for k, v in f.items() if k not in ("quarters", "min_profitable_quarters")})
        self.assertEqual((e["min_profitable_quarters"], e["quarters"]), (4, 8))
        self.assertEqual(rules.ROUND4_SELECT["robustness"], "ROBUST")

    def m(self, name, **over):
        base = {"strategy": name, "trades": 65, "profit_pct": 95.0, "profit_factor": 2.1, "max_dd_pct": 29.0,
                "calmar": 0.9, "quarters_profitable": 4, "quarters_total": 8, "worst_quarter_pct": -8.0}
        base.update(over)
        return base

    def test_selection_needs_robust(self):
        dev = {"MomentumRotationV3": self.m("MomentumRotationV3", calmar=0.8),
               "MomentumRotationV3b": self.m("MomentumRotationV3b", calmar=1.0)}
        bias = {n: True for n in dev}
        pick, lines = rules.select_round4(dev, bias, {"MomentumRotationV3": "ROBUST", "MomentumRotationV3b": "FRAGILE"})
        self.assertEqual(pick, "MomentumRotationV3")
        self.assertTrue(any("V3b`: not eligible (robustness check FRAGILE (need ROBUST)" in line for line in lines))
        pick, lines = rules.select_round4(dev, bias, {"MomentumRotationV3": "ROBUST"})
        self.assertTrue(any("robustness check not run" in line for line in lines))
        for m in dev.values():
            m["max_dd_pct"] = 30.5                                           # none eligible: idea dropped
        self.assertIsNone(rules.select_round4(dev, bias, {n: "ROBUST" for n in dev})[0])

    def test_exam_uses_round4_numbers_and_labels(self):
        bh = {"strategy": "BuyHoldV1", "max_dd_pct": 60.0, "calmar": 0.5}
        ok = self.m("MomentumRotationV3_R3_noSOL", trades=20)          # 20 trades: enough here, not in Round 2
        status, checks = rules.exam(ok, self.m("x"), bh, True, rules.ROUND4_EXAM, "H")
        self.assertEqual(status, "PASS", checks)
        self.assertTrue(all(text.startswith(f"H{i}") for i, (_, text) in enumerate(checks, 1)))
        self.assertEqual(rules.exam(ok, self.m("x"), bh, True)[0], "FAIL")   # Round 2 numbers: 30 trades, 11 quarters
        for over in (dict(trades=19), dict(quarters_profitable=3), dict(max_dd_pct=30.1), dict(worst_quarter_pct=-10.5),
                     dict(calmar=0.5), dict(quarters_total=7)):
            with self.subTest(**over):
                self.assertEqual(rules.exam(self.m("v", **over), self.m("x"), bh, True, rules.ROUND4_EXAM, "H")[0], "FAIL")

    def test_preregistration_states_the_same_numbers(self):
        doc = (REPO / "docs" / "research" / "momentum-exposure-preregistration.md").read_text()
        s, e = rules.ROUND4_SELECT, rules.ROUND4_EXAM
        for text in (f"dev max drawdown **≤ {s['max_dd_pct']:g}%**", f"profit factor **≥ {s['min_profit_factor']:g}**",
                     f"at least **{s['min_trades']}** trades", f"**{s['robustness']}** in `lab.py robustness`",
                     f"| ≥ {e['min_trades']} |", f"profit factor ≥ {e['min_profit_factor']:g}",
                     f"max drawdown ≤ {e['max_dd_pct']:g}%",
                     f"≥ {e['min_profitable_quarters']} of the {e['quarters']} quarters profitable",
                     f"worse than −{abs(e['worst_quarter_pct']):g}%", "2019-01-01 → 2021-01-01",
                     *(f"`{c}`" for c in rules.ROUND4_CANDIDATES)):
            self.assertIn(text, doc)


class Round5RulesTest(unittest.TestCase):
    def m(self, name, quarters=None, **over):
        base = {"strategy": name, "trades": 60, "profit_pct": 80.0, "profit_factor": 1.8, "max_dd_pct": 22.0,
                "calmar": 0.9}
        base.update(over)
        base["quarters"] = quarters if quarters is not None else (
            [{"quarter": f"q{i}", "ret_pct": r, "partial": False} for i, r in enumerate([5.0] * 8 + [0.0] * 6 + [-4.0] * 5)])
        return base

    BH = {"strategy": "BuyHoldV1", "max_dd_pct": 85.0, "calmar": 0.3}

    def test_exam_pass_and_each_failure(self):
        ok = self.m("TrendBlendV1")
        status, checks = rules.exam_round5(ok, self.m("x"), self.BH, True)
        self.assertEqual(status, "PASS", checks)
        self.assertTrue(all(text.startswith(f"E{i}") for i, (_, text) in enumerate(checks, 1)))
        self.assertIn("8 quarters up vs 5 down, 6 in cash", checks[5][1])
        fails = {"E1": dict(trades=29), "E2": dict(profit_factor=1.1), "E4": dict(max_dd_pct=30.5),
                 "E5": dict(calmar=0.3)}
        for rule, over in fails.items():
            with self.subTest(rule):
                status, checks = rules.exam_round5(self.m("v", **over), self.m("x"), self.BH, True)
                self.assertEqual(status, "FAIL")
                self.assertTrue(any(t.startswith(rule) for ok_, t in checks if not ok_), checks)
        q = lambda rets: [{"quarter": f"q{i}", "ret_pct": r, "partial": False} for i, r in enumerate(rets)]
        more_down = q([5.0] * 6 + [-1.0] * 7 + [0.0] * 6)                  # 6 up < 7 down
        too_deep = q([5.0] * 10 + [-15.5] + [0.0] * 8)                    # one quarter below -15%
        short = q([5.0] * 18)                                            # only 18 full quarters
        for quarters in (more_down, too_deep, short):
            self.assertEqual(rules.exam_round5(self.m("v", quarters=quarters), self.m("x"), self.BH, True)[0], "FAIL")
        partial = q([5.0] * 19) + [{"quarter": "p", "ret_pct": -40.0, "partial": True}]   # partial quarters ignored
        self.assertEqual(rules.exam_round5(self.m("v", quarters=partial), self.m("x"), self.BH, True)[0], "PASS")
        self.assertEqual(rules.exam_round5(ok, self.m("x", profit_pct=-0.1), self.BH, True)[0], "FAIL")   # E3
        self.assertEqual(rules.exam_round5(ok, self.m("x"), self.BH, None)[0], "FAIL")                    # E7

    def test_selection(self):
        dev = {"BuyHoldV1": {"strategy": "BuyHoldV1", "calmar": 0.76, "max_dd_pct": 65.0, "profit_pct": 230.0,
                             "profit_factor": None, "trades": 5},
               "TrendBlendV1": self.m("TrendBlendV1", calmar=0.70),          # below buy & hold
               "TrendBlendV2": self.m("TrendBlendV2", calmar=1.10)}
        bias, robust = {n: True for n in dev}, {"TrendBlendV1": "ROBUST", "TrendBlendV2": "ROBUST"}
        pick, lines = rules.select_round5(dev, bias, robust)
        self.assertEqual(pick, "TrendBlendV2")
        self.assertTrue(any("V1`: not eligible (Calmar 0.70 not above buy & hold's 0.76" in line for line in lines))
        for extra in ("TrendBlendV3", "TrendBlendV4"):
            dev[extra] = self.m(extra)
        with self.assertRaises(SystemExit):
            rules.select_round5(dev, bias, robust)

    def test_preregistration_states_the_same_numbers(self):
        doc = (REPO / "docs" / "research" / "trend-blend-preregistration.md").read_text()
        s, e = rules.ROUND5_SELECT, rules.ROUND5_EXAM
        coins = ", ".join(c.split("/")[0] for c in rules.ROUND5_EXAM_COINS)
        for text in (f"max drawdown **≤ {s['max_dd_pct']:g}%**", f"profit factor **≥ {s['min_profit_factor']:g}**",
                     f"at least **{s['min_trades']}** trades", f"**{s['robustness']}** in `lab.py robustness`",
                     "Calmar **above buy & hold's**", f"| ≥ {e['min_trades']} |", f"profit factor ≥ {e['min_profit_factor']:g}",
                     f"max drawdown ≤ {e['max_dd_pct']:g}%", f"worse than −{abs(e['worst_quarter_pct']):g}%",
                     f"**{coins}.**", f"at most {rules.ROUND5_MAX_VERSIONS - 1} more versions** ({rules.ROUND5_MAX_VERSIONS} in total)",
                     "2019-01-01 → 2023-10-01"):
            self.assertIn(text, doc)


class Round6RulesTest(unittest.TestCase):
    m = Round5RulesTest.m
    BH = {"strategy": "BuyHoldV1", "max_dd_pct": 92.1, "calmar": 0.86}

    def q(self, rets):
        return [{"quarter": f"q{i}", "ret_pct": r, "partial": False} for i, r in enumerate(rets)]

    def test_exam_uses_the_holdout_quarters(self):
        ok = self.m("AuctionValueV1", calmar=1.2, quarters=self.q([4.0] * 5 + [0.0] * 2 + [-3.0] * 4))
        status, checks = rules.exam_round6(ok, self.m("x"), self.BH, True)
        self.assertEqual(status, "PASS", checks)
        self.assertIn("5 quarters up vs 4 down, 2 in cash (of 11", checks[5][1])
        nineteen = self.m("v", calmar=1.2)                                   # Round 5's 19 quarters: wrong length
        self.assertEqual(rules.exam_round6(nineteen, self.m("x"), self.BH, True)[0], "FAIL")
        self.assertEqual(rules.exam_round6(self.m("v", calmar=0.86, quarters=ok["quarters"]),
                                           self.m("x"), self.BH, True)[0], "FAIL")      # E5: must beat 0.86
        self.assertEqual(rules.ROUND6_FORWARD["min_trades"], 20)
        self.assertEqual(rules.ROUND6_FORWARD["quarters"], 4)

    def test_selection(self):
        dev = {"BuyHoldV1": {"strategy": "BuyHoldV1", "calmar": 0.76, "max_dd_pct": 65.0, "profit_pct": 230.0,
                             "profit_factor": None, "trades": 5},
               "AuctionValueV1": self.m("AuctionValueV1", calmar=1.0),
               "TrendBlendV2": self.m("TrendBlendV2", calmar=2.0)}            # another round: never a candidate
        bias = {n: True for n in dev}
        pick, lines = rules.select_round6(dev, bias, {"AuctionValueV1": "FRAGILE"})
        self.assertIsNone(pick)
        self.assertTrue(any("robustness check FRAGILE" in line for line in lines), lines)
        pick, _ = rules.select_round6(dev, bias, {"AuctionValueV1": "ROBUST"})
        self.assertEqual(pick, "AuctionValueV1")
        for extra in ("AuctionValueV2", "AuctionValueV3", "AuctionValueV4"):
            dev[extra] = self.m(extra)
        with self.assertRaises(SystemExit):
            rules.select_round6(dev, bias, {})

    def test_preregistration_states_the_same_numbers(self):
        doc = (REPO / "docs" / "research" / "auction-value-preregistration.md").read_text()
        s, e = rules.ROUND6_SELECT, rules.ROUND6_EXAM
        for text in (f"max drawdown **≤ {s['max_dd_pct']:g}%**", f"profit factor **≥ {s['min_profit_factor']:g}**",
                     f"at least **{s['min_trades']}** trades", f"**{s['robustness']}** in `lab.py robustness`",
                     "Calmar **above buy & hold's**", f"| ≥ {e['min_trades']} |", f"profit factor ≥ {e['min_profit_factor']:g}",
                     f"max drawdown ≤ {e['max_dd_pct']:g}%", f"worse than −{abs(e['worst_quarter_pct']):g}%",
                     f"over the {e['quarters']} quarters", f"≥ {rules.ROUND6_FORWARD['min_trades']} trades over "
                     f"{rules.ROUND6_FORWARD['quarters']} quarters",
                     f"at most {rules.ROUND6_MAX_VERSIONS - 1} more versions** ({rules.ROUND6_MAX_VERSIONS} in total)",
                     "2021-01-01 → 2023-10-01", "`AuctionValueV1`"):
            self.assertIn(text, doc)


class RobustnessRulesTest(unittest.TestCase):
    ORIG = {"profit_pct": 100.0, "calmar": 2.0}

    def v(self, profit, calmar):
        return {"profit_pct": profit, "calmar": calmar}

    def test_share_and_median_rules(self):
        good = [self.v(50, 1.5)] * 9 + [self.v(-5, -0.1)]          # 90% profitable, median 1.5 = 75%
        self.assertEqual(rules.variants_verdict(self.ORIG, good)[0], "PASS")
        spread = [self.v(10, 0.5)] * 10                              # all profitable but median 25%
        self.assertEqual(rules.variants_verdict(self.ORIG, spread)[0], "FAIL")
        losers = [self.v(50, 1.5)] * 7 + [self.v(-5, -0.1)] * 3     # 70% profitable
        self.assertEqual(rules.variants_verdict(self.ORIG, losers)[0], "FAIL")

    def test_leave_one_out_needs_all_profitable(self):
        four_of_five = [self.v(50, 1.5)] * 4 + [self.v(-1, -0.05)]
        self.assertEqual(rules.variants_verdict(self.ORIG, four_of_five, all_profitable=True)[0], "FAIL")
        self.assertEqual(rules.variants_verdict(self.ORIG, [self.v(50, 1.5)] * 5, all_profitable=True)[0], "PASS")

    def test_skipped_and_not_applicable(self):
        self.assertEqual(rules.variants_verdict(self.ORIG, [])[0], "SKIPPED")
        self.assertEqual(rules.variants_verdict({"profit_pct": -3.0, "calmar": -0.1}, [self.v(1, 0.1)])[0], "N/A")

    def test_concentration(self):
        self.assertEqual(rules.concentration_verdict(1070, [500, 300, 200])[0], "PASS")   # 70 left
        self.assertEqual(rules.concentration_verdict(930, [900, 50, 40])[0], "FAIL")      # -60 left
        self.assertEqual(rules.concentration_verdict(0, [])[0], "SKIPPED")
        self.assertEqual(rules.concentration_verdict(-50, [10, 5, 1])[0], "N/A")


class RobustnessVariantsTest(unittest.TestCase):
    WEEKLY = {"strategy": "MomentumRotationV1b", "module": "momentum_rotation_v1b", "weekly": True,
              "rebalance": [6, 23], "universe": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"],
              "settings": {"LOOKBACK_DAYS": {"kind": "const", "default": 30, "values": [20, 25, 35, 40]},
                           "TOP_N": {"kind": "const", "default": 3, "values": [2, 4]}}, "skip": []}
    SIGNAL = {"strategy": "EmaTrendV2", "module": "ema_trend_v2", "weekly": False, "rebalance": None,
              "universe": None, "skip": [],
              "settings": {"fast_period": {"kind": "param", "space": "buy", "default": 21, "values": [16, 26]}}}

    def test_weekly_timing_slots(self):
        import robustness
        slots = robustness.timing_slots((6, 23), 6)
        self.assertEqual(len(slots), 28)
        self.assertIn((6, 23), slots)                     # the original slot is one of them
        self.assertEqual({h for _, h in slots}, {5, 11, 17, 23})
        variants = robustness.timing_variants(self.WEEKLY)
        self.assertEqual(len(variants), 28)
        for src in variants.values():
            ast.parse(src)

    def test_daily_timing_variants(self):
        import robustness
        info = {"strategy": "TrendBlendV1", "module": "trend_blend_v1", "weekly": False, "daily": True,
                "delay_days": True, "rebalance": [11], "universe": None, "settings": {}, "skip": []}
        out = robustness.timing_variants(info)
        self.assertEqual(sorted(out), sorted(["TrendBlendV1_R1_h05", "TrendBlendV1_R1_h11", "TrendBlendV1_R1_h17",
                                              "TrendBlendV1_R1_h23", "TrendBlendV1_R1_delay1",
                                              "TrendBlendV1_R1_delay2", "TrendBlendV1_R1_delay3"]))
        self.assertIn("REBALANCE_HOUR = 5", out["TrendBlendV1_R1_h05"])
        self.assertIn("DELAY_DAYS = 3", out["TrendBlendV1_R1_delay3"])
        for src in out.values():
            ast.parse(src)
        no_delay = robustness.timing_variants({**info, "delay_days": False})
        self.assertEqual(len(no_delay), 4)
        # Round 6: a daily decision about the day's own session is delayed by hours, not days.
        hours = robustness.timing_variants({**info, "strategy": "AuctionValueV1", "module": "auction_value_v1",
                                            "delay_days": False, "delay_hours": True})
        self.assertEqual(sorted(hours), sorted(["AuctionValueV1_R1_h05", "AuctionValueV1_R1_h11",
                                                "AuctionValueV1_R1_h17", "AuctionValueV1_R1_h23",
                                                "AuctionValueV1_R1_delay1h", "AuctionValueV1_R1_delay2h",
                                                "AuctionValueV1_R1_delay3h"]))
        self.assertIn("DELAY_HOURS = 2", hours["AuctionValueV1_R1_delay2h"])
        for src in hours.values():
            ast.parse(src)

    def test_signal_delay_variants_shift_only_into_the_past(self):
        import robustness
        variants = robustness.timing_variants(self.SIGNAL)
        self.assertEqual(sorted(variants), ["EmaTrendV2_R1_late1", "EmaTrendV2_R1_late2", "EmaTrendV2_R1_late3"])
        src = variants["EmaTrendV2_R1_late2"]
        ast.parse(src)
        self.assertIn(".shift(2)", src)
        self.assertNotIn("shift(-", src)                  # never pulls future signals

    def test_setting_variants(self):
        import robustness
        weekly = robustness.setting_variants(self.WEEKLY)
        self.assertEqual(len(weekly), 6)
        self.assertIn("LOOKBACK_DAYS = 20", weekly["MomentumRotationV1b_R2_LOOKBACK_DAYS_20"])
        sig = robustness.setting_variants(self.SIGNAL)
        self.assertIn("buy_params = {'fast_period': 16}", sig["EmaTrendV2_R2_fast_period_16"])
        for src in [*weekly.values(), *sig.values()]:
            ast.parse(src)

    def test_leave_one_coin_out(self):
        import robustness
        pairs = self.WEEKLY["universe"]
        runs = robustness.coin_variants(self.WEEKLY, pairs)
        self.assertEqual([r["left_out"] for r in runs], pairs)
        sol = next(r for r in runs if r["left_out"] == "SOL/USDT")
        self.assertNotIn("SOL/USDT", sol["pairs"])
        self.assertNotIn("SOL/USDT", sol["source"].split("UNIVERSE = ")[1].split("\n")[0])
        self.assertIn("if metadata['pair'] not in self.UNIVERSE", sol["source"])   # left-out coin never trades
        ast.parse(sol["source"])
        no_universe = robustness.coin_variants(self.SIGNAL, pairs)
        self.assertIsNone(no_universe[0]["class"])        # uses --pairs with the original class

    def test_overall(self):
        self.assertEqual(rules.robustness_overall({"R1": "PASS", "R2": "SKIPPED", "R3": "PASS", "R4": "PASS"}), "ROBUST")
        self.assertEqual(rules.robustness_overall({"R1": "FAIL", "R3": "PASS"}), "FRAGILE")
        self.assertEqual(rules.robustness_overall({"R1": "N/A", "R2": "SKIPPED"}), "N/A")

    def test_methodology_and_plan_state_the_same_numbers(self):
        r = rules.ROBUSTNESS
        for doc_name in ("TESTING_METHODOLOGY.md", "research/robustness-check-plan.md"):
            doc = (REPO / "docs" / doc_name).read_text().replace("**", "")   # ignore bold markers
            for text in (f"≥ {r['min_profitable_share']:.0%} of", f"≥ {r['min_median_calmar_ratio']:.0%} of the original",
                         f"every {r['timing_step_hours']} hours", "1, 2", f"{r['drop_top_trades']} best trades"):
                self.assertIn(text, doc, f"{doc_name} is missing: {text}")
