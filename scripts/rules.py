"""Promotion rules: the single source of truth for the report and the docs.

A strategy goes to paper trading only after passing BOTH stages:

  Stage 1 (lab.py validate): in-sample vs out-of-sample on 1h, plus a fee stress test.
  Stage 2 (Phase 6): walk-forward windows and market regimes.

Thresholds were written down BEFORE any out-of-sample result was looked at
(2026-10-06). Changing them later needs a dated entry in docs/DECISIONS.md.
Standard library only.
"""

from __future__ import annotations

BASELINE = "BuyHoldV1"

# "Too good to be true": investigate before trusting. Only judged on periods of
# at least FLAG_MIN_DAYS; short windows (e.g. a 90-day bull run) can
# legitimately look extreme.
FLAG_MIN_DAYS = 180
SUSPICIOUS = {
    "sharpe_above": 3.0,
    "win_rate_above_pct": 80.0,
    "profit_factor_above": 3.0,
    "trades_below": 30,
    "max_dd_below_pct": 3.0,
}

STAGE1 = {
    "min_trades_is": 50,              # enough trades to mean something
    "min_trades_oos": 20,
    "max_dd_oos_pct": 25.0,           # worst wallet fall allowed out-of-sample
    "min_profit_factor_oos": 1.2,     # gross wins at least 1.2x gross losses
    "min_oos_is_sharpe_ratio": 0.5,   # OOS Sharpe keeps at least half of IS Sharpe
}

STAGE2 = {
    "min_profitable_windows_pct": 60.0,  # walk-forward test windows that made money
    "min_wf_efficiency": 0.5,            # walk-forward return / in-sample return (annualised)
    "max_dd_regime_pct": 30.0,           # worst drawdown in any bull/bear/sideways window
}


def suspicious_flags(m: dict) -> list[str]:
    """Reasons a result looks too good (or too thin) to trust as-is."""
    if m["strategy"] == BASELINE or m.get("days", 0) < FLAG_MIN_DAYS:
        return []
    s, flags = SUSPICIOUS, []
    if m["sharpe"] > s["sharpe_above"]:
        flags.append(f"Sharpe {m['sharpe']:.1f} > {s['sharpe_above']:g}")
    if m["trades"] and m["win_rate_pct"] > s["win_rate_above_pct"]:
        flags.append(f"win rate {m['win_rate_pct']:.0f}% > {s['win_rate_above_pct']:g}%")
    if m.get("profit_factor") is not None and m["profit_factor"] > s["profit_factor_above"]:
        flags.append(f"profit factor {m['profit_factor']:.1f} > {s['profit_factor_above']:g}")
    if m["trades"] < s["trades_below"]:
        flags.append(f"only {m['trades']} trades")
    if m["trades"] and m["max_dd_pct"] < s["max_dd_below_pct"]:
        flags.append(f"drawdown {m['max_dd_pct']:.1f}% < {s['max_dd_below_pct']:g}%")
    return flags


def sharpe_ratio_kept(is_m: dict, oos_m: dict) -> float | None:
    """OOS Sharpe / IS Sharpe (1.0 = no decay). None if IS Sharpe is not positive."""
    return oos_m["sharpe"] / is_m["sharpe"] if is_m["sharpe"] > 0 else None


def stage1(is_m: dict, oos_m: dict, stress_m: dict | None, bh_oos: dict, bias_ok: bool | None) -> tuple[str, list[tuple[bool, str]]]:
    """Stage-1 verdict for one strategy.

    Returns (status, checks): status is PASS, FAIL or REVIEW (all rules pass but a
    "too good to be true" flag needs a human look). checks = [(passed, text), ...].
    """
    r = STAGE1
    kept = sharpe_ratio_kept(is_m, oos_m)
    pf = oos_m.get("profit_factor")
    checks = [
        (is_m["trades"] >= r["min_trades_is"] and oos_m["trades"] >= r["min_trades_oos"],
         f"trades IS {is_m['trades']} (>= {r['min_trades_is']}), OOS {oos_m['trades']} (>= {r['min_trades_oos']})"),
        (oos_m["max_dd_pct"] <= r["max_dd_oos_pct"] and oos_m["max_dd_pct"] < bh_oos["max_dd_pct"],
         f"OOS max drawdown {oos_m['max_dd_pct']:.1f}% (<= {r['max_dd_oos_pct']:g}% and < buy & hold {bh_oos['max_dd_pct']:.1f}%)"),
        (oos_m["profit_pct"] > 0 and pf is not None and pf >= r["min_profit_factor_oos"],
         f"OOS profit {oos_m['profit_pct']:+.1f}% (> 0), profit factor {pf if pf is None else round(pf, 2)} (>= {r['min_profit_factor_oos']:g})"),
        (stress_m is not None and stress_m["profit_pct"] > 0,
         "OOS profit at 0.15% fee " + ("not run" if stress_m is None else f"{stress_m['profit_pct']:+.1f}% (> 0)")),
        (oos_m["calmar"] > bh_oos["calmar"],
         f"OOS Calmar {oos_m['calmar']:.2f} > buy & hold {bh_oos['calmar']:.2f}"),
        (kept is not None and kept >= r["min_oos_is_sharpe_ratio"],
         f"Sharpe IS {is_m['sharpe']:.2f} -> OOS {oos_m['sharpe']:.2f} "
         f"(keeps {'n/a' if kept is None else f'{kept:.0%}'}, need >= {r['min_oos_is_sharpe_ratio']:.0%})"),
        (bias_ok is True,
         "bias checks " + {True: "passed", False: "FAILED", None: "not run"}[bias_ok]),
    ]
    if not all(ok for ok, _ in checks):
        return "FAIL", checks
    flags = suspicious_flags(oos_m) + suspicious_flags(is_m)
    if flags:
        return "REVIEW", checks + [(False, "too good to be true? " + "; ".join(flags))]
    return "PASS", checks


def stage2(wf: dict | None, regime_dd: dict[str, float]) -> tuple[str, list[tuple[bool, str]]]:
    """Stage-2 verdict. wf = walk-forward summary (tuning.walkforward_summary);
    regime_dd = {window name: max drawdown %} over all six regime windows."""
    r = STAGE2
    if wf is None:
        checks = [(False, "walk-forward not run")]
    else:
        eff = wf["wf_efficiency"]
        checks = [
            (wf["profitable_windows_pct"] >= r["min_profitable_windows_pct"],
             f"{wf['profitable_windows_pct']:.0f}% of {wf['windows']} walk-forward test windows profitable "
             f"(>= {r['min_profitable_windows_pct']:g}%)"),
            (eff is not None and eff >= r["min_wf_efficiency"],
             "walk-forward efficiency " + ("n/a (training was not profitable)" if eff is None else f"{eff:.2f}")
             + f" (>= {r['min_wf_efficiency']:g})"),
        ]
    if len(regime_dd) < 6:
        checks.append((False, f"only {len(regime_dd)} of 6 regime windows tested"))
    worst = max(regime_dd.items(), key=lambda kv: kv[1]) if regime_dd else ("none", 0.0)
    checks.append((bool(regime_dd) and worst[1] <= r["max_dd_regime_pct"],
                   f"worst regime drawdown {worst[1]:.1f}% in {worst[0]} (<= {r['max_dd_regime_pct']:g}%)"))
    return ("PASS" if all(ok for ok, _ in checks) else "FAIL"), checks


# --------------------------------------------------------------------------- Round 2
# Pre-registered in docs/research/round2-preregistration.md (2026-10-07). A test keeps
# that document and these numbers in sync.

ROUND2_IDEAS = {  # class-name prefix -> idea
    "TrendPullbackV3": "A: fee-aware pullback",
    "EmaTrendV3": "B: EmaTrendV2 + market filter",
    "MomentumRotation": "C: momentum rotation",
}

DEV_SELECT = {
    "min_profit_factor": 1.1,
    "min_trades": 30,
    "per_idea": 2,              # best N per idea by dev Calmar go to the exam
    "max_versions_per_idea": 3,
}

EXAM = {
    "min_trades": 30,
    "min_profit_factor": 1.2,
    "max_dd_pct": 30.0,
    "min_profitable_quarters": 6,
    "quarters": 11,
    "worst_quarter_pct": -10.0,
}


def round2_idea(strategy: str) -> str | None:
    return next((idea for prefix, idea in ROUND2_IDEAS.items() if strategy.startswith(prefix)), None)


def select_for_exam(dev_strategies: dict[str, dict], bias: dict[str, bool]) -> tuple[list[str], list[str]]:
    """Apply the pre-registered dev rule. Returns (selected, explanation lines)."""
    r, lines, selected = DEV_SELECT, [], []
    by_idea: dict[str, list[dict]] = {}
    for name, m in dev_strategies.items():
        idea = round2_idea(name)
        if idea:
            by_idea.setdefault(idea, []).append(m)
    for idea, versions in sorted(by_idea.items()):
        if len(versions) > r["max_versions_per_idea"]:
            raise SystemExit(f"{idea}: {len(versions)} versions tried, the limit is {r['max_versions_per_idea']}")
        eligible = []
        for m in sorted(versions, key=lambda m: m["calmar"], reverse=True):
            pf = m.get("profit_factor")
            reasons = []
            if m["profit_pct"] <= 0:
                reasons.append(f"profit {m['profit_pct']:+.1f}% <= 0")
            if pf is None or pf < r["min_profit_factor"]:
                reasons.append(f"profit factor {pf if pf is None else round(pf, 2)} < {r['min_profit_factor']}")
            if m["trades"] < r["min_trades"]:
                reasons.append(f"{m['trades']} trades < {r['min_trades']}")
            if bias.get(m["strategy"]) is not True:
                reasons.append("bias checks not passed")
            if reasons:
                lines.append(f"- {idea}: `{m['strategy']}` not eligible ({'; '.join(reasons)})")
            else:
                eligible.append(m)
        for i, m in enumerate(eligible):
            if i < r["per_idea"]:
                selected.append(m["strategy"])
                lines.append(f"- {idea}: `{m['strategy']}` **selected** (dev Calmar {m['calmar']:.2f}, "
                             f"profit {m['profit_pct']:+.1f}%, PF {m['profit_factor']:.2f}, {m['trades']} trades)")
            else:
                lines.append(f"- {idea}: `{m['strategy']}` eligible but not in the best {r['per_idea']} by dev Calmar")
    return selected, lines


def exam(m: dict, stress_m: dict | None, bh: dict, bias_ok: bool | None,
         r: dict = EXAM, prefix: str = "X") -> tuple[str, list[tuple[bool, str]]]:
    """Exam verdict on protected data: PASS only if every rule holds (Round 2: EXAM/X, Round 4: ROUND4_EXAM/H)."""
    pf = m.get("profit_factor")
    q_ok, q_total, worst = m.get("quarters_profitable", 0), m.get("quarters_total", 0), m.get("worst_quarter_pct")
    checks = [
        (m["trades"] >= r["min_trades"], f"{prefix}1 trades {m['trades']} (>= {r['min_trades']})"),
        (m["profit_pct"] > 0 and pf is not None and pf >= r["min_profit_factor"],
         f"{prefix}2 profit {m['profit_pct']:+.1f}% (> 0), profit factor {pf if pf is None else round(pf, 2)} "
         f"(>= {r['min_profit_factor']:g})"),
        (stress_m is not None and stress_m["profit_pct"] > 0,
         f"{prefix}3 profit at 0.15% fee " + ("not run" if stress_m is None else f"{stress_m['profit_pct']:+.1f}% (> 0)")),
        (m["max_dd_pct"] <= r["max_dd_pct"] and m["max_dd_pct"] < bh["max_dd_pct"],
         f"{prefix}4 max drawdown {m['max_dd_pct']:.1f}% (<= {r['max_dd_pct']:g}% and < buy & hold {bh['max_dd_pct']:.1f}%)"),
        (m["calmar"] > bh["calmar"], f"{prefix}5 Calmar {m['calmar']:.2f} > buy & hold {bh['calmar']:.2f}"),
        (q_total == r["quarters"] and q_ok >= r["min_profitable_quarters"]
         and worst is not None and worst >= r["worst_quarter_pct"],
         f"{prefix}6 profitable in {q_ok} of {q_total} quarters (>= {r['min_profitable_quarters']} of {r['quarters']}), "
         f"worst quarter {'n/a' if worst is None else f'{worst:+.1f}%'} (>= {r['worst_quarter_pct']:g}%)"),
        (bias_ok is True, f"{prefix}7 bias checks " + {True: "passed", False: "FAILED", None: "not run"}[bias_ok]),
    ]
    return ("PASS" if all(ok for ok, _ in checks) else "FAIL"), checks


# --------------------------------------------------------------------------- Round 3
# Pre-registered in docs/research/momentum-drawdown-preregistration.md (2026-10-07).

ROUND3_CANDIDATES = ("MomentumRotationV2", "MomentumRotationV2b", "MomentumRotationV2c")
ROUND3_SELECT = {"max_dd_pct": 30.0, "min_profit_factor": 1.2, "min_trades": 30}
FORWARD = {  # forward exam, 12 months
    "min_trades": 20, "min_profit_factor": 1.2, "max_dd_pct": 30.0,
    "min_profitable_quarters": 2, "quarters": 4, "worst_quarter_pct": -10.0,
}


def select_round3(dev_strategies: dict[str, dict], bias: dict[str, bool]) -> tuple[str | None, list[str]]:
    """The single eligible Round 3 version with the highest dev Calmar (None = idea dropped)."""
    return select_one(ROUND3_CANDIDATES, ROUND3_SELECT, dev_strategies, bias)


def select_one(candidates: tuple[str, ...], r: dict, dev_strategies: dict[str, dict], bias: dict[str, bool],
               robust: dict[str, str | None] | None = None) -> tuple[str | None, list[str]]:
    """Single-pick dev rule (Rounds 3 and 4): every candidate is checked; the best eligible dev Calmar wins."""
    lines, eligible = [], []
    for name in candidates:
        m = dev_strategies.get(name)
        if m is None:
            lines.append(f"- `{name}`: not in the dev run")
            continue
        pf, reasons = m.get("profit_factor"), []
        if m["max_dd_pct"] > r["max_dd_pct"]:
            reasons.append(f"max drawdown {m['max_dd_pct']:.1f}% > {r['max_dd_pct']:g}%")
        if m["profit_pct"] <= 0:
            reasons.append(f"profit {m['profit_pct']:+.1f}% <= 0")
        if pf is None or pf < r["min_profit_factor"]:
            reasons.append(f"profit factor {pf if pf is None else round(pf, 2)} < {r['min_profit_factor']:g}")
        if m["trades"] < r["min_trades"]:
            reasons.append(f"{m['trades']} trades < {r['min_trades']}")
        if bias.get(name) is not True:
            reasons.append("bias checks not passed")
        if "robustness" in r and (robust or {}).get(name) != r["robustness"]:
            reasons.append(f"robustness check {(robust or {}).get(name) or 'not run'} (need {r['robustness']})")
        bh = dev_strategies.get(BASELINE)
        if r.get("beat_bh") and (bh is None or m["calmar"] <= bh["calmar"]):
            reasons.append(f"Calmar {m['calmar']:.2f} not above buy & hold's "
                           + ("(not in the run)" if bh is None else f"{bh['calmar']:.2f}"))
        status = "eligible" if not reasons else "not eligible (" + "; ".join(reasons) + ")"
        lines.append(f"- `{name}`: {status} - dev profit {m['profit_pct']:+.1f}%, max DD {m['max_dd_pct']:.1f}%, "
                     f"Calmar {m['calmar']:.2f}, PF {pf if pf is None else round(pf, 2)}, {m['trades']} trades")
        if not reasons:
            eligible.append(m)
    pick = max(eligible, key=lambda m: m["calmar"])["strategy"] if eligible else None
    return pick, lines


# --------------------------------------------------------------------------- Round 4
# Pre-registered in docs/research/momentum-exposure-preregistration.md (2026-10-08), before any
# version was built. Dev selection = Round 3's rule + the robustness gate. The exam runs once on
# 2019-2020 (lab.py period "exam2019", 4 coins) with Round 3's forward rules over 8 quarters.

ROUND4_CANDIDATES = ("MomentumRotationV3", "MomentumRotationV3b")
ROUND4_SELECT = {**ROUND3_SELECT, "robustness": "ROBUST"}
ROUND4_EXAM = {**FORWARD, "min_profitable_quarters": 4, "quarters": 8}


def select_round4(dev_strategies: dict[str, dict], bias: dict[str, bool],
                  robust: dict[str, str | None]) -> tuple[str | None, list[str]]:
    """The single eligible Round 4 version (Round 3's rule + ROBUST) with the highest dev Calmar."""
    return select_one(ROUND4_CANDIDATES, ROUND4_SELECT, dev_strategies, bias, robust)


# --------------------------------------------------------------------------- Round 5
# Pre-registered in docs/research/trend-blend-preregistration.md (2026-10-09), before any version
# was built. Dev selection = Round 4's rule + Calmar above buy & hold. The exam runs once on 9 coins
# no strategy in this lab has traded, 2019-01 -> 2023-10.

ROUND5_PREFIX = "TrendBlend"     # every version of the idea
ROUND5_MAX_VERSIONS = 3
ROUND5_SELECT = {**ROUND3_SELECT, "robustness": "ROBUST", "beat_bh": True}
# Rule: still listed on Binance (2026-10-09), USDT daily data before 2018-06-15, not ours, not a stablecoin.
ROUND5_EXAM_COINS = ("NEO/USDT", "LTC/USDT", "QTUM/USDT", "ADA/USDT", "IOTA/USDT", "XLM/USDT",
                     "ONT/USDT", "TRX/USDT", "ETC/USDT")
ROUND5_EXAM = {"min_trades": 30, "min_profit_factor": 1.2, "max_dd_pct": 30.0,
               "quarters": 19, "worst_quarter_pct": -15.0}
ROUND5_FORWARD = {**ROUND5_EXAM, "min_trades": 20, "quarters": 4}


def select_round5(dev_strategies: dict[str, dict], bias: dict[str, bool],
                  robust: dict[str, str | None]) -> tuple[str | None, list[str]]:
    """The single eligible TrendBlend version (at most 3 tried) with the highest dev Calmar."""
    candidates = tuple(sorted(n for n in dev_strategies if n.startswith(ROUND5_PREFIX)))
    if len(candidates) > ROUND5_MAX_VERSIONS:
        raise SystemExit(f"{len(candidates)} TrendBlend versions tried, the limit is {ROUND5_MAX_VERSIONS}")
    return select_one(candidates, ROUND5_SELECT, dev_strategies, bias, robust)


def exam_round5(m: dict, stress_m: dict | None, bh: dict, bias_ok: bool | None,
                r: dict = ROUND5_EXAM, prefix: str = "E") -> tuple[str, list[tuple[bool, str]]]:
    """Round 5 exam (and forward test with ROUND5_FORWARD): PASS only if every rule holds.
    Consistency counts quarters with a gain against quarters with a loss; quarters spent fully
    in cash (exactly 0%) count as neither."""
    pf = m.get("profit_factor")
    full = [q for q in m.get("quarters", []) if not q["partial"]]
    up, down = sum(q["ret_pct"] > 0 for q in full), sum(q["ret_pct"] < 0 for q in full)
    worst = min((q["ret_pct"] for q in full), default=None)
    checks = [
        (m["trades"] >= r["min_trades"], f"{prefix}1 trades {m['trades']} (>= {r['min_trades']})"),
        (m["profit_pct"] > 0 and pf is not None and pf >= r["min_profit_factor"],
         f"{prefix}2 profit {m['profit_pct']:+.1f}% (> 0), profit factor {pf if pf is None else round(pf, 2)} "
         f"(>= {r['min_profit_factor']:g})"),
        (stress_m is not None and stress_m["profit_pct"] > 0,
         f"{prefix}3 profit at 0.15% fee " + ("not run" if stress_m is None else f"{stress_m['profit_pct']:+.1f}% (> 0)")),
        (m["max_dd_pct"] <= r["max_dd_pct"] and m["max_dd_pct"] < bh["max_dd_pct"],
         f"{prefix}4 max drawdown {m['max_dd_pct']:.1f}% (<= {r['max_dd_pct']:g}% and < buy & hold {bh['max_dd_pct']:.1f}%)"),
        (m["calmar"] > bh["calmar"], f"{prefix}5 Calmar {m['calmar']:.2f} > buy & hold {bh['calmar']:.2f}"),
        (len(full) == r["quarters"] and up >= down and worst is not None and worst >= r["worst_quarter_pct"],
         f"{prefix}6 {up} quarters up vs {down} down, {len(full) - up - down} in cash (of {len(full)}; need "
         f"{r['quarters']} with up >= down), worst quarter {'n/a' if worst is None else f'{worst:+.1f}%'} "
         f"(>= {r['worst_quarter_pct']:g}%)"),
        (bias_ok is True, f"{prefix}7 bias checks " + {True: "passed", False: "FAILED", None: "not run"}[bias_ok]),
    ]
    return ("PASS" if all(ok for ok, _ in checks) else "FAIL"), checks


# --------------------------------------------------------------------------- Round 6
# Pre-registered in docs/research/auction-value-preregistration.md (2026-10-12), before any version
# was built. Dev selection = Round 5's rule. The exam runs once on the protected holdout
# (2021-01 -> 2023-10, our 5 coins) with Round 5's exam rules over its 11 quarters.

ROUND6_PREFIX = "AuctionValue"   # every version of the idea
ROUND6_MAX_VERSIONS = 3
ROUND6_SELECT = ROUND5_SELECT
ROUND6_EXAM = {**ROUND5_EXAM, "quarters": 11}
ROUND6_FORWARD = {**ROUND6_EXAM, "min_trades": 20, "quarters": 4}


def select_round6(dev_strategies: dict[str, dict], bias: dict[str, bool],
                  robust: dict[str, str | None]) -> tuple[str | None, list[str]]:
    """The single eligible AuctionValue version (at most 3 tried) with the highest dev Calmar."""
    candidates = tuple(sorted(n for n in dev_strategies if n.startswith(ROUND6_PREFIX)))
    if len(candidates) > ROUND6_MAX_VERSIONS:
        raise SystemExit(f"{len(candidates)} AuctionValue versions tried, the limit is {ROUND6_MAX_VERSIONS}")
    return select_one(candidates, ROUND6_SELECT, dev_strategies, bias, robust)


def exam_round6(m: dict, stress_m: dict | None, bh: dict, bias_ok: bool | None,
                r: dict = ROUND6_EXAM, prefix: str = "E") -> tuple[str, list[tuple[bool, str]]]:
    """Round 6 exam (and forward test with ROUND6_FORWARD): Round 5's rules on the holdout's 11 quarters."""
    return exam_round5(m, stress_m, bh, bias_ok, r, prefix)


# --------------------------------------------------------------------------- Robustness check
# Plan: docs/research/robustness-check-plan.md (approved 2026-10-07, before any run).
# Runs on dev data only. A test keeps docs/TESTING_METHODOLOGY.md in sync with these numbers.

ROBUSTNESS = {
    "timing_step_hours": 6,             # R1 weekly strategies: a rebalance slot every 6h -> 28 slots
    "signal_delays": (1, 2, 3),         # R1 signal strategies: act on signals 1, 2, 3 candles late
    "min_profitable_share": 0.80,       # R1, R2: share of variants that must be profitable
    "min_median_calmar_ratio": 0.50,    # R1, R2, R3: median variant Calmar >= 50% of the original's
    "drop_top_trades": 3,               # R4: profit must stay > 0 without the best 3 trades
}


def variants_verdict(original: dict, variants: list[dict], all_profitable: bool = False) -> tuple[str, str]:
    """R1/R2 (share >= 80%) or R3 (all_profitable=True) verdict for one check."""
    import statistics
    r = ROBUSTNESS
    if not variants:
        return "SKIPPED", "no variants apply to this strategy"
    if original["profit_pct"] <= 0 or original["calmar"] <= 0:
        return "N/A", f"original not profitable (profit {original['profit_pct']:+.1f}%) - nothing to protect"
    profitable = sum(v["profit_pct"] > 0 for v in variants)
    need = len(variants) if all_profitable else r["min_profitable_share"] * len(variants)
    median_calmar = statistics.median(v["calmar"] for v in variants)
    ratio = median_calmar / original["calmar"]
    ok = profitable >= need and ratio >= r["min_median_calmar_ratio"]
    need_txt = "all" if all_profitable else f">= {r['min_profitable_share']:.0%}"
    return ("PASS" if ok else "FAIL"), (
        f"{profitable} of {len(variants)} variants profitable (need {need_txt}); median Calmar "
        f"{median_calmar:.2f} = {ratio:.0%} of the original's {original['calmar']:.2f} "
        f"(need >= {r['min_median_calmar_ratio']:.0%})")


def concentration_verdict(total_profit_abs: float, best_trades_abs: list[float]) -> tuple[str, str]:
    """R4: total profit (USDT) without the best N trades must stay > 0."""
    n = ROBUSTNESS["drop_top_trades"]
    if not best_trades_abs:
        return "SKIPPED", "no trades"
    if total_profit_abs <= 0:
        return "N/A", f"original not profitable ({total_profit_abs:+.0f} USDT) - nothing to protect"
    best = sorted(best_trades_abs, reverse=True)[:n]
    rest = total_profit_abs - sum(best)
    return ("PASS" if rest > 0 else "FAIL"), (
        f"profit {total_profit_abs:+.0f} USDT; without the best {n} trades ({sum(best):+.0f} USDT, "
        f"{sum(best) / total_profit_abs:.0%} of it): {rest:+.0f} USDT (need > 0)")


def robustness_overall(verdicts: dict[str, str]) -> str:
    applied = [v for v in verdicts.values() if v in ("PASS", "FAIL")]
    if not applied:
        return "N/A"
    return "ROBUST" if all(v == "PASS" for v in applied) else "FRAGILE"
