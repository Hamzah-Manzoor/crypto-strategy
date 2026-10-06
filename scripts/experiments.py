#!/usr/bin/env python3
"""Experiment log: one entry per strategy per backtest / hyperopt run.

Storage: results/experiments.jsonl (one JSON object per line, append-only,
committed to git). docs/EXPERIMENT_LOG.md is rebuilt from it.

Each entry records what ran (strategy class = version, code hash, git commit),
on what (period, timerange, timeframe, fee), the key metrics, notes, and the
decision taken afterwards: keep / tweak / drop (pending until decided).

    python3 scripts/lab.py exp list [--strategy EmaTrend] [--last 20]
    python3 scripts/lab.py exp decide E0012 tweak "whipsaws in chop; try a wider slow EMA"
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "results" / "experiments.jsonl"
DOC = ROOT / "docs" / "EXPERIMENT_LOG.md"
DECISIONS = ("keep", "tweak", "drop", "pending", "baseline", "diagnostic")
METRIC_KEYS = ("profit_pct", "cagr_pct", "max_dd_pct", "sharpe", "sortino", "calmar",
               "profit_factor", "win_rate_pct", "trades", "avg_hold_hours", "exposure_pct")
BASELINE = "BuyHoldV1"


def load(log: Path = LOG) -> list[dict]:
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines() if line.strip()]


def save(entries: list[dict], log: Path = LOG) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in entries))


def git_version() -> str:
    """Short commit hash, '+dirty' if strategy or script files have uncommitted changes."""
    def git(*args):
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True).stdout.strip()
    commit = git("rev-parse", "--short", "HEAD") or "no-git"
    dirty = git("status", "--porcelain", "--", "user_data/strategies", "user_data/configs", "scripts")
    return commit + ("+dirty" if dirty else "")


def next_id(entries: list[dict]) -> str:
    return f"E{len(entries) + 1:04d}"


def log_run(run: dict, kind: str = "backtest", oos_look: bool = False, log: Path = LOG) -> list[str]:
    """Append one entry per strategy in a run summary (from scripts/metrics.py)."""
    entries = load(log)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    version, ids = git_version(), []
    diagnostic = run.get("fee") == 0  # zero-fee runs only measure gross edge; never a valid result
    for name, m in run["strategies"].items():
        entry = {
            "id": next_id(entries),
            "date": now,
            "kind": "diagnostic" if diagnostic else kind,
            "run_id": run["run_id"],
            "strategy": name,
            "code_sha": m.get("code_sha"),
            "git": version,
            "period": run["period"],
            "timerange": run["timerange"],
            "timeframe": run["timeframe"],
            "timeframe_detail": run.get("timeframe_detail"),
            "fee": run.get("fee"),
            "oos_look": oos_look,
            "settings": {k: m.get(k) for k in ("stoploss", "minimal_roi", "trailing_stop")},
            "metrics": {k: m.get(k) for k in METRIC_KEYS},
            "notes": run.get("notes", ""),
            "decision": "baseline" if name == BASELINE else ("diagnostic" if diagnostic else "pending"),
            "decision_note": "",
        }
        entries.append(entry)
        ids.append(entry["id"])
    save(entries, log)
    return ids


def refresh(runs: list[dict], log: Path = LOG) -> int:
    """After metrics are recomputed, update the measured fields of matching entries.
    IDs, dates, notes and decisions are never touched. Returns entries updated."""
    by_key = {(r["run_id"], name): (r, m) for r in runs for name, m in r["strategies"].items()}
    entries, changed = load(log), 0
    for e in entries:
        match = by_key.get((e["run_id"], e["strategy"]))
        if not match:
            continue
        r, m = match
        new = {"fee": r.get("fee"), "timeframe_detail": r.get("timeframe_detail"), "code_sha": m.get("code_sha"),
               "settings": {k: m.get(k) for k in ("stoploss", "minimal_roi", "trailing_stop")},
               "metrics": {k: m.get(k) for k in METRIC_KEYS}}
        if r.get("fee") == 0 and e["decision"] == "pending":
            new.update(kind="diagnostic", decision="diagnostic")
        if any(e.get(k) != v for k, v in new.items()):
            e.update(new)
            changed += 1
    save(entries, log)
    return changed


def decide(entry_id: str, decision: str, note: str, log: Path = LOG) -> dict:
    if decision not in ("keep", "tweak", "drop"):
        raise SystemExit("decision must be keep, tweak or drop")
    entries = load(log)
    for e in entries:
        if e["id"] == entry_id:
            e["decision"], e["decision_note"] = decision, note
            e["decided"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
            save(entries, log)
            return e
    raise SystemExit(f"no experiment with id {entry_id}")


def _cell(v, digits=1, sign=False) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, int):
        return str(v)
    return f"{v:+.{digits}f}" if sign else f"{v:.{digits}f}"


def row(e: dict) -> str:
    m = e["metrics"]
    fee = f"{100 * e['fee']:.2f}%" if e.get("fee") is not None else "?"
    detail = f"+{e['timeframe_detail']}" if e.get("timeframe_detail") else ""
    period = e["period"] + (" 👁" if e.get("oos_look") else "")
    decision = e["decision"] + (f": {e['decision_note']}" if e.get("decision_note") else "")
    return (f"| {e['id']} | {e['date'][:10]} | {e['kind']} | `{e['strategy']}` | {period} | {e['timeframe']}{detail} | "
            f"{fee} | {_cell(m.get('profit_pct'), sign=True)} | {_cell(m.get('max_dd_pct'))} | "
            f"{_cell(m.get('sharpe'), 2)} | {_cell(m.get('calmar'), 2)} | {_cell(m.get('trades'))} | "
            f"{decision} | {e.get('notes') or ''} | `{e['git']}` |")


def render(log: Path = LOG, doc: Path = DOC) -> None:
    entries = load(log)
    lines = [
        "# Experiment log",
        "",
        "Every backtest / hyperopt run started through `lab.py` adds one row per strategy (newest first).",
        "This page is rebuilt from `results/experiments.jsonl`. Edit decisions with:",
        "",
        "```",
        'python3 scripts/lab.py exp decide <ID> keep|tweak|drop "why"',
        "```",
        "",
        "- **Strategy** = class name, which includes the version (`EmaTrendV1` → `EmaTrendV2`).",
        "- **Period** 👁 = an out-of-sample look. These are counted; tuning on OOS is not allowed.",
        "- **Git** = commit the code was at (`+dirty` = uncommitted strategy/config/script changes).",
        "- Risk numbers (Max DD, Sharpe, Calmar) are mark-to-market, from the wallet value at every candle.",
        "",
        f"**{len(entries)} entries**, {sum(1 for e in entries if e.get('oos_look'))} of them out-of-sample looks.",
        "",
        "| ID | Date | Kind | Strategy | Period | TF | Fee | Profit % | Max DD % | Sharpe | Calmar | Trades | Decision | Notes | Git |",
        "|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|",
        *[row(e) for e in reversed(entries)],
        "",
    ]
    doc.write_text("\n".join(lines))


if __name__ == "__main__":
    render()
    print(f"rendered {DOC.relative_to(ROOT)} from {len(load())} entries")
