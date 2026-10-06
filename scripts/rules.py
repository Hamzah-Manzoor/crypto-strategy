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
