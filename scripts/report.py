#!/usr/bin/env python3
"""Leaderboards and the stage-1 promotion table, from run summaries.

Input: results/runs/<run_id>.json, written by scripts/metrics.py from
Freqtrade's backtest zip (metrics.py needs pandas, so it runs in Docker; this
file is standard library only and runs anywhere).

Output:
  results/leaderboards/<run_id>.md + .csv   one leaderboard per backtest run
  results/leaderboards/stage1_<tf>.md + .csv  in-sample vs out-of-sample verdicts
  docs/RESULTS.md                             the block between the AUTO markers

Usually called through lab.py (backtest / validate / report).
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import rules  # noqa: E402

RUNS = ROOT / "results" / "runs"
BOARDS = ROOT / "results" / "leaderboards"
RESULTS_DOC = ROOT / "docs" / "RESULTS.md"
AUTO_START, AUTO_END = "<!-- AUTO:START -->", "<!-- AUTO:END -->"
STANDARD_FEE = 0.001

CSV_FIELDS = [
    "rank", "strategy", "profit_pct", "cagr_pct", "max_dd_pct", "sharpe", "sortino", "calmar",
    "profit_factor", "win_rate_pct", "trades", "avg_hold_hours", "exposure_pct", "beats_bh",
    "flags", "timeframe", "timerange", "days", "market_change_pct", "code_sha",
]


# --------------------------------------------------------------------------- loading

def load_run(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def all_runs() -> list[dict]:
    return [load_run(p) for p in sorted(RUNS.glob("*.json"))]


def latest(runs: list[dict], period: str, timeframe: str, fee: float = STANDARD_FEE,
           detail: str | None = None) -> dict | None:
    """Most recent run matching a standard view (run ids start with a timestamp)."""
    match = [r for r in runs if r["period"] == period and r["timeframe"] == timeframe
             and abs((r.get("fee") or 0) - fee) < 1e-9 and (r.get("timeframe_detail") or None) == detail]
    return max(match, key=lambda r: r["run_id"]) if match else None


# --------------------------------------------------------------------------- formatting

def num(v, digits: int = 2, sign: bool = False) -> str:
    if v is None:
        return "n/a"
    return f"{v:+.{digits}f}" if sign else f"{v:.{digits}f}"


def hold(hours: float) -> str:
    return f"{hours:.1f}h" if hours < 48 else f"{hours / 24:.1f}d"


def table(header: list[str], rows: list[list[str]], align: str) -> list[str]:
    return ["| " + " | ".join(header) + " |", "|" + "|".join(align) + "|",
            *["| " + " | ".join(r) + " |" for r in rows]]


# --------------------------------------------------------------------------- leaderboard

def leaderboard(run: dict) -> list[dict]:
    """Strategies ranked by Calmar (return per unit of drawdown), best first."""
    bh = run["strategies"].get(rules.BASELINE)
    rows = []
    for m in run["strategies"].values():
        row = dict(m)
        if m["strategy"] == rules.BASELINE:
            row["beats_bh"] = "baseline"
        elif bh is None:
            row["beats_bh"] = "n/a"
        else:
            row["beats_bh"] = "yes" if m["calmar"] > bh["calmar"] else "no"
        row["flags"] = "; ".join(rules.suspicious_flags(m))
        rows.append(row)
    rows.sort(key=lambda r: r["calmar"], reverse=True)
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows


def run_header(run: dict) -> list[str]:
    any_m = next(iter(run["strategies"].values()))
    detail = run.get("timeframe_detail") or "none"
    lines = [
        f"Run `{run['run_id']}` · period **{run['period']}** · timerange `{run['timerange']}` "
        f"({any_m['days']:.0f} days) · timeframe **{run['timeframe']}** · intra-candle detail: {detail} · "
        f"fee {100 * (run.get('fee') or 0):.2f}% per side · market (avg of 5 pairs) {any_m['market_change_pct']:+.1f}%",
    ]
    if run.get("notes"):
        lines.append(f"Notes: {run['notes']}")
    return lines


def leaderboard_md(run: dict) -> str:
    rows = leaderboard(run)
    body = [[
        str(r["rank"]), f"`{r['strategy']}`", num(r["profit_pct"], 1, sign=True), num(r["cagr_pct"], 1, sign=True),
        num(r["max_dd_pct"], 1), num(r["sharpe"]), num(r["sortino"]), num(r["calmar"]),
        num(r["profit_factor"]), num(r["win_rate_pct"], 0), str(r["trades"]), hold(r["avg_hold_hours"]),
        f"{r['exposure_pct']:.0f}%", r["beats_bh"], r["flags"] or "",
    ] for r in rows]
    lines = [
        f"# Leaderboard · {run['period']} · {run['timeframe']}", "", *run_header(run), "",
        *table(["#", "Strategy", "Profit %", "CAGR %", "Max DD %", "Sharpe", "Sortino", "Calmar",
                "Profit factor", "Win %", "Trades", "Avg hold", "In market", "Beats B&H (Calmar)", "Flags"],
               body, ["---:", "---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:",
                      "---:", "---:", "---", "---"]),
        "",
        "How to read this:",
        "- **Sorted by Calmar** (yearly return ÷ worst drawdown): how much you earned per unit of pain.",
        "- **Max DD**, **Sharpe**, **Sortino** and **Calmar** use the wallet's value at every candle, open trades "
        "included (Freqtrade's own drawdown ignores open trades and shows 0% for buy & hold).",
        "- **In market** = average share of the wallet held in coins. **Profit factor** = gross wins ÷ gross losses "
        "(n/a when there was no losing trade).",
        f"- **Flags** = too good (or too thin) to trust without a closer look; only judged on periods of "
        f"{rules.FLAG_MIN_DAYS}+ days.",
        "",
    ]
    return "\n".join(lines)


def write_csv(rows: list[dict], path: Path, fields: list[str]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_run(run: dict) -> Path:
    BOARDS.mkdir(parents=True, exist_ok=True)
    md = BOARDS / f"{run['run_id']}.md"
    md.write_text(leaderboard_md(run))
    write_csv(leaderboard(run), BOARDS / f"{run['run_id']}.csv", CSV_FIELDS)
    return md


# --------------------------------------------------------------------------- stage 1

def load_bias() -> dict[str, bool]:
    path = ROOT / "results" / "checks" / "bias_check.json"
    if not path.exists():
        return {}
    return {name: v.get("ok") for name, v in json.loads(path.read_text()).get("strategies", {}).items()}


def stage1(is_run: dict, oos_run: dict, stress_run: dict | None, bias: dict[str, bool],
           detail_run: dict | None = None) -> list[dict]:
    bh_oos = oos_run["strategies"][rules.BASELINE]
    out = []
    for name, oos_m in oos_run["strategies"].items():
        if name == rules.BASELINE or name not in is_run["strategies"]:
            continue
        is_m = is_run["strategies"][name]
        stress_m = stress_run["strategies"].get(name) if stress_run else None
        detail_m = detail_run["strategies"].get(name) if detail_run else None
        status, checks = rules.stage1(is_m, oos_m, stress_m, bh_oos, bias.get(name))
        out.append({
            "strategy": name, "status": status, "checks": checks,
            "is_profit_pct": is_m["profit_pct"], "oos_profit_pct": oos_m["profit_pct"],
            "stress_profit_pct": stress_m["profit_pct"] if stress_m else None,
            "detail_profit_pct": detail_m["profit_pct"] if detail_m else None,
            "is_sharpe": is_m["sharpe"], "oos_sharpe": oos_m["sharpe"],
            "sharpe_kept": rules.sharpe_ratio_kept(is_m, oos_m),
            "oos_max_dd_pct": oos_m["max_dd_pct"], "oos_calmar": oos_m["calmar"],
            "oos_profit_factor": oos_m["profit_factor"], "is_trades": is_m["trades"], "oos_trades": oos_m["trades"],
        })
    order = {"PASS": 0, "REVIEW": 1, "FAIL": 2}
    out.sort(key=lambda r: (order[r["status"]], -r["oos_calmar"]))
    return out


def stage1_md(is_run: dict, oos_run: dict, stress_run: dict | None, rows: list[dict],
              detail_run: dict | None = None) -> str:
    bh_is, bh_oos = is_run["strategies"][rules.BASELINE], oos_run["strategies"][rules.BASELINE]
    body = [[
        f"**{r['status']}**", f"`{r['strategy']}`", num(r["is_profit_pct"], 1, sign=True), num(r["oos_profit_pct"], 1, sign=True),
        num(r["stress_profit_pct"], 1, sign=True), num(r.get("detail_profit_pct"), 1, sign=True),
        num(r["is_sharpe"]), num(r["oos_sharpe"]),
        "n/a" if r["sharpe_kept"] is None else f"{r['sharpe_kept']:.0%}", num(r["oos_max_dd_pct"], 1),
        num(r["oos_calmar"]), num(r["oos_profit_factor"]), f"{r['is_trades']} / {r['oos_trades']}",
    ] for r in rows]
    lines = [
        f"# Stage 1 · in-sample vs out-of-sample · {oos_run['timeframe']}", "",
        f"- In-sample: `{is_run['run_id']}` ({is_run['timerange']}) · buy & hold {bh_is['profit_pct']:+.1f}%, "
        f"max DD {bh_is['max_dd_pct']:.1f}%, Calmar {bh_is['calmar']:.2f}",
        f"- Out-of-sample: `{oos_run['run_id']}` ({oos_run['timerange']}) · buy & hold {bh_oos['profit_pct']:+.1f}%, "
        f"max DD {bh_oos['max_dd_pct']:.1f}%, Calmar {bh_oos['calmar']:.2f}",
        f"- Fee stress (0.15%/side): " + (f"`{stress_run['run_id']}`" if stress_run else "not run"),
        f"- 5m intra-candle fills (information, not a rule): " + (f"`{detail_run['run_id']}`" if detail_run else "not run"),
        "",
        *table(["Status", "Strategy", "IS profit", "OOS profit", "OOS @0.15% fee", "OOS 5m fills", "IS Sharpe",
                "OOS Sharpe", "Sharpe kept", "OOS max DD %", "OOS Calmar", "OOS PF", "Trades IS / OOS"],
               body, ["---", "---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:",
                      "---:"]),
        "", "## Why", "",
    ]
    for r in rows:
        lines.append(f"**{r['strategy']} - {r['status']}**")
        lines += [f"- {'✅' if ok else '❌'} {text}" for ok, text in r["checks"]]
        lines.append("")
    lines.append("Rules: docs/TESTING_METHODOLOGY.md (thresholds in scripts/rules.py).")
    return "\n".join(lines) + "\n"


def write_stage1(is_run: dict, oos_run: dict, stress_run: dict | None,
                 detail_run: dict | None = None) -> tuple[Path, list[dict]]:
    rows = stage1(is_run, oos_run, stress_run, load_bias(), detail_run)
    BOARDS.mkdir(parents=True, exist_ok=True)
    tf = oos_run["timeframe"]
    md = BOARDS / f"stage1_{tf}.md"
    md.write_text(stage1_md(is_run, oos_run, stress_run, rows, detail_run))
    flat = [{**{k: v for k, v in r.items() if k != "checks"},
             "failed_checks": " | ".join(t for ok, t in r["checks"] if not ok)} for r in rows]
    fields = list(flat[0]) if flat else ["strategy", "status"]
    write_csv(flat, BOARDS / f"stage1_{tf}.csv", fields)
    (BOARDS / f"stage1_{tf}.json").write_text(json.dumps({
        "is_run": is_run["run_id"], "oos_run": oos_run["run_id"],
        "stress_run": stress_run["run_id"] if stress_run else None,
        "detail_run": detail_run["run_id"] if detail_run else None,
        "results": {r["strategy"]: r["status"] for r in rows},
    }, indent=1) + "\n")
    return md, rows


# --------------------------------------------------------------------------- stage 2

def write_stage2(results: list[dict]) -> Path:
    """results: [{strategy, wf_base, wf (summary or None), wf_id, regime_dd {window: dd}, regime_profit {...}}]"""
    for r in results:
        r["status"], r["checks"] = rules.stage2(r["wf"], r["regime_dd"])
    windows = ["bull-is", "bear-is", "sideways-is", "bull-oos", "bear-oos", "sideways-oos"]
    body = []
    for r in results:
        wf = r["wf"] or {}
        eff = wf.get("wf_efficiency")
        body.append([f"**{r['status']}**", f"`{r['strategy']}`",
                     f"{wf.get('profitable_windows_pct', 0):.0f}%" if wf else "n/a",
                     "n/a" if eff is None else f"{eff:.2f}", num(wf.get("stitched_profit_pct"), 1, sign=True),
                     num(wf.get("bh_stitched_profit_pct"), 1, sign=True),
                     *[(f"{r['regime_profit'][w]:+.1f}% / {r['regime_dd'][w]:.1f}%" if w in r["regime_dd"] else "-")
                       for w in windows]])
    lines = [
        "# Stage 2 · walk-forward and market regimes · 1h", "",
        "Walk-forward = 8 rolling 3-month test windows. An untuned strategy is scored with its fixed settings; "
        "a tuned `…T` version through its parent re-tuned on the 12 months before each window. "
        "Regime cells: profit / max drawdown.", "",
        *table(["Status", "Strategy", "WF windows profitable", "WF efficiency", "WF stitched profit", "B&H same windows",
                *windows], body, ["---", "---", "---:", "---:", "---:", "---:", *["---:"] * len(windows)]),
        "", "## Why", "",
    ]
    for r in results:
        lines.append(f"**{r['strategy']} - {r['status']}**"
                     + (f" (walk-forward, {r.get('wf_mode', '?')}: `{r['wf_id']}`)" if r.get("wf_id") else ""))
        lines += [f"- {'✅' if ok else '❌'} {text}" for ok, text in r["checks"]]
        lines.append("")
    lines.append("Rules: docs/TESTING_METHODOLOGY.md (thresholds in scripts/rules.py).")
    BOARDS.mkdir(parents=True, exist_ok=True)
    md = BOARDS / "stage2_1h.md"
    md.write_text("\n".join(lines) + "\n")
    (BOARDS / "stage2_1h.json").write_text(json.dumps(
        {"results": {r["strategy"]: r["status"] for r in results},
         "details": [{k: v for k, v in r.items() if k != "checks"} for r in results]}, indent=1) + "\n")
    return md


# --------------------------------------------------------------------------- Round 2

def write_round2_selection(dev_run: dict) -> tuple[Path, list[str]]:
    selected, lines = rules.select_for_exam(dev_run["strategies"], load_bias())
    md = BOARDS / "round2_selection.md"
    md.write_text("\n".join([
        "# Round 2 · exam candidates (pre-registered dev rule)", "",
        f"Dev run `{dev_run['run_id']}` ({dev_run['timerange']}, {dev_run['timeframe']}, fee "
        f"{100 * (dev_run.get('fee') or 0):.2f}%). Rule: profit > 0, profit factor >= "
        f"{rules.DEV_SELECT['min_profit_factor']}, >= {rules.DEV_SELECT['min_trades']} trades, bias checks "
        f"passed; best {rules.DEV_SELECT['per_idea']} per idea by Calmar.", "",
        *lines, "", f"**Exam candidates:** {', '.join(f'`{s}`' for s in selected) or 'none'}", "",
    ]))
    (BOARDS / "round2_selection.json").write_text(json.dumps(
        {"dev_run": dev_run["run_id"], "selected": selected}, indent=1) + "\n")
    return md, selected


def write_exam(exam_run: dict, stress_run: dict | None, detail_run: dict | None) -> tuple[Path, dict]:
    bias = load_bias()
    bh = exam_run["strategies"][rules.BASELINE]
    rows = []
    for name, m in exam_run["strategies"].items():
        if name == rules.BASELINE:
            continue
        stress_m = stress_run["strategies"].get(name) if stress_run else None
        detail_m = detail_run["strategies"].get(name) if detail_run else None
        status, checks = rules.exam(m, stress_m, bh, bias.get(name))
        rows.append({"strategy": name, "status": status, "checks": checks, "m": m,
                     "stress": stress_m["profit_pct"] if stress_m else None,
                     "detail": detail_m["profit_pct"] if detail_m else None})
    rows.sort(key=lambda r: (r["status"] != "PASS", -r["m"]["calmar"]))
    body = [[f"**{r['status']}**", f"`{r['strategy']}`", num(r["m"]["profit_pct"], 1, sign=True),
             num(r["m"]["profit_factor"]), str(r["m"]["trades"]), num(r["m"]["max_dd_pct"], 1), num(r["m"]["calmar"]),
             num(r["stress"], 1, sign=True), num(r["detail"], 1, sign=True),
             f"{r['m'].get('quarters_profitable', 0)} / {r['m'].get('quarters_total', 0)}",
             num(r["m"].get("worst_quarter_pct"), 1, sign=True)] for r in rows]
    quarters = [q["quarter"] for q in bh.get("quarters", []) if not q["partial"]]

    def qrow(label, m):
        by_q = {q["quarter"]: q["ret_pct"] for q in m.get("quarters", [])}
        return [label, *[num(by_q.get(q), 1, sign=True) for q in quarters]]

    lines = [
        "# Round 2 exam · holdout · 1h", "",
        f"- Exam run: `{exam_run['run_id']}` ({exam_run['timerange']}) · buy & hold {bh['profit_pct']:+.1f}%, "
        f"max DD {bh['max_dd_pct']:.1f}%, Calmar {bh['calmar']:.2f}",
        "- Fee stress (0.15%/side): " + (f"`{stress_run['run_id']}`" if stress_run else "not run"),
        "- 5m intra-candle fills (information, not a rule): " + (f"`{detail_run['run_id']}`" if detail_run else "not run"),
        "",
        *table(["Status", "Strategy", "Profit %", "PF", "Trades", "Max DD %", "Calmar", "@0.15% fee", "5m fills",
                "Quarters +", "Worst quarter"], body,
               ["---", "---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:"]),
        "", "## Quarter by quarter (profit %)", "",
        *table(["Strategy", *quarters], [qrow("buy & hold", bh), *[qrow(f"`{r['strategy']}`", r["m"]) for r in rows]],
               ["---", *["---:"] * len(quarters)]),
        "", "## Why", "",
    ]
    for r in rows:
        lines.append(f"**{r['strategy']} - {r['status']}**")
        lines += [f"- {'✅' if ok else '❌'} {text}" for ok, text in r["checks"]]
        lines.append("")
    lines.append("Rules: docs/research/round2-preregistration.md (numbers in scripts/rules.py → EXAM).")
    BOARDS.mkdir(parents=True, exist_ok=True)
    md = BOARDS / "exam_round2.md"
    md.write_text("\n".join(lines) + "\n")
    verdicts = {r["strategy"]: r["status"] for r in rows}
    (BOARDS / "exam_round2.json").write_text(json.dumps({
        "exam_run": exam_run["run_id"], "stress_run": stress_run["run_id"] if stress_run else None,
        "detail_run": detail_run["run_id"] if detail_run else None, "results": verdicts}, indent=1) + "\n")
    return md, verdicts


# --------------------------------------------------------------------------- docs/RESULTS.md

def results_block(runs: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"_Generated by `lab.py report` on {now}. Do not edit inside the AUTO markers._", "",
             "> **Read in-sample tables with care:** tuned `…T` versions were tuned on these same dates, so they "
             "always look good here. Promotion depends only on the Stage 1 / Stage 2 verdicts further down.", ""]
    for tf in ("1h", "15m", "4h"):
        run = latest(runs, "is", tf)
        if not run:
            continue
        rows = leaderboard(run)
        lines += [f"### In-sample · {tf}", "", *run_header(run), ""]
        lines += table(
            ["#", "Strategy", "Profit %", "Max DD %", "Sharpe", "Calmar", "PF", "Trades", "In market", "Beats B&H", "Flags"],
            [[str(r["rank"]), f"`{r['strategy']}`", num(r["profit_pct"], 1, sign=True), num(r["max_dd_pct"], 1),
              num(r["sharpe"]), num(r["calmar"]), num(r["profit_factor"]), str(r["trades"]),
              f"{r['exposure_pct']:.0f}%", r["beats_bh"], r["flags"] or ""] for r in rows],
            ["---:", "---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---", "---"])
        lines += ["", f"Full table: [results/leaderboards/{run['run_id']}.md](../results/leaderboards/{run['run_id']}.md)", ""]
    exam = BOARDS / "exam_round2.json"
    if exam.exists():
        data = json.loads(exam.read_text())
        lines += ["### Round 2 exam verdicts (holdout 2021-01 → 2023-10)", "",
                  *[f"- `{k}`: **{v}**" for k, v in data["results"].items()], "",
                  "Details: [results/leaderboards/exam_round2.md](../results/leaderboards/exam_round2.md)", ""]
    s2 = BOARDS / "stage2_1h.json"
    if s2.exists():
        data = json.loads(s2.read_text())
        lines += ["### Stage 2 verdicts · 1h (promotion to paper trading)", "",
                  *[f"- `{k}`: **{v}**" for k, v in data["results"].items()], "",
                  "Details: [results/leaderboards/stage2_1h.md](../results/leaderboards/stage2_1h.md)", ""]
    for tf in ("1h", "15m", "4h"):
        s1 = BOARDS / f"stage1_{tf}.json"
        if s1.exists():
            data = json.loads(s1.read_text())
            lines += [f"### Stage 1 verdicts · {tf}", "",
                      *[f"- `{k}`: **{v}**" for k, v in data["results"].items()], "",
                      f"Details: [results/leaderboards/stage1_{tf}.md](../results/leaderboards/stage1_{tf}.md)", ""]
    return "\n".join(lines)


def update_results_doc(runs: list[dict] | None = None) -> None:
    runs = all_runs() if runs is None else runs
    text = RESULTS_DOC.read_text()
    if AUTO_START not in text or AUTO_END not in text:
        raise SystemExit(f"{RESULTS_DOC} is missing the {AUTO_START} / {AUTO_END} markers")
    head, rest = text.split(AUTO_START, 1)
    _, tail = rest.split(AUTO_END, 1)
    RESULTS_DOC.write_text(f"{head}{AUTO_START}\n{results_block(runs)}\n{AUTO_END}{tail}")


def rebuild_stage1_from_saved(runs: list[dict]) -> list[Path]:
    """Re-score saved stage-1 runs (e.g. after bias checks were completed).
    Uses the runs already on disk - never a new out-of-sample look."""
    by_id = {r["run_id"]: r for r in runs}
    written = []
    for path in sorted(BOARDS.glob("stage1_*.json")):
        ids = json.loads(path.read_text())
        is_run, oos_run = by_id.get(ids["is_run"]), by_id.get(ids["oos_run"])
        if not is_run or not oos_run:
            continue
        md, _ = write_stage1(is_run, oos_run, by_id.get(ids.get("stress_run")), by_id.get(ids.get("detail_run")))
        written.append(md)
    return written


def rebuild_all() -> int:
    runs = all_runs()
    for run in runs:
        write_run(run)
    rebuild_stage1_from_saved(runs)
    update_results_doc(runs)
    return len(runs)


if __name__ == "__main__":
    print(f"rebuilt {rebuild_all()} leaderboards and docs/RESULTS.md")
