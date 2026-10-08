#!/usr/bin/env python3
"""Check downloaded candle data before trusting any backtest built on it.

For every pair x timeframe it reports the first/last candle, how many candles
are missing, the longest gap, duplicates and impossible candles (e.g. high
below close). Exit code 1 if anything would make a backtest misleading.

Runs inside the Freqtrade container (needs pandas):
    python3 scripts/lab.py data-check
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

TF_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "2h": 120, "4h": 240, "1d": 1440}


def check_file(path: Path, timeframe: str, start: pd.Timestamp, now: pd.Timestamp,
               min_coverage: float, max_gap_hours: float) -> dict:
    row = {"file": path.name, "status": "OK", "problems": []}
    if not path.exists():
        row.update(status="FAIL", problems=["file missing - run: python3 scripts/lab.py download"])
        return row

    df = pd.read_feather(path)
    step = pd.Timedelta(minutes=TF_MINUTES[timeframe])
    dates = pd.to_datetime(df["date"], utc=True)

    first, last = dates.min(), dates.max()
    expected = int((last - first) / step) + 1
    unique = dates.nunique()
    duplicates = len(dates) - unique
    diffs = dates.sort_values().diff().dropna()
    longest_gap = (diffs.max() - step) if len(diffs) else pd.Timedelta(0)
    bad_ohlc = int(((df["high"] < df[["open", "close"]].max(axis=1))
                    | (df["low"] > df[["open", "close"]].min(axis=1))
                    | (df[["open", "high", "low", "close"]] <= 0).any(axis=1)).sum())

    row.update(
        first=first.strftime("%Y-%m-%d %H:%M"),
        last=last.strftime("%Y-%m-%d %H:%M"),
        candles=unique,
        missing=expected - unique,
        coverage=100.0 * unique / expected,
        longest_gap_h=longest_gap.total_seconds() / 3600,
        zero_volume=int((df["volume"] == 0).sum()),
    )

    if first > start + pd.Timedelta(days=1):
        row["problems"].append(f"starts {row['first']}, needed from {start:%Y-%m-%d}")
    if row["coverage"] < min_coverage:
        row["problems"].append(f"coverage {row['coverage']:.2f}% < {min_coverage}%")
    if row["longest_gap_h"] > max_gap_hours:
        row["problems"].append(f"gap of {row['longest_gap_h']:.1f}h > {max_gap_hours}h")
    if duplicates:
        row["problems"].append(f"{duplicates} duplicate timestamps")
    if bad_ohlc:
        row["problems"].append(f"{bad_ohlc} impossible candles (high/low outside open/close or <= 0)")
    if row["problems"]:
        row["status"] = "FAIL"
    elif now - last > pd.Timedelta(days=3):
        row["status"] = "WARN"
        row["problems"].append(f"stale: last candle {row['last']} - run download again")
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--exchange", default="binance")
    parser.add_argument("--timeframes", nargs="+", default=["5m", "15m", "1h", "4h"])
    parser.add_argument("--start", default="20230501", help="data must start by this date (yyyymmdd)")
    parser.add_argument("--min-coverage", type=float, default=98.0, help="percent")
    parser.add_argument("--max-gap-hours", type=float, default=24.0)
    parser.add_argument("--out", type=Path, help="also write the markdown report here")
    parser.add_argument("--pairs", nargs="+", help="default: the whitelist in base.json")
    args = parser.parse_args()

    config = json.loads(Path("user_data/configs/base.json").read_text())
    pairs = args.pairs or config["exchange"]["pair_whitelist"]
    data_dir = Path("user_data/data") / args.exchange
    start = pd.Timestamp(datetime.strptime(args.start, "%Y%m%d"), tz="UTC")
    now = pd.Timestamp(datetime.now(timezone.utc))

    rows = []
    for pair in pairs:
        for tf in args.timeframes:
            path = data_dir / f"{pair.replace('/', '_')}-{tf}.feather"
            rows.append({"pair": pair, "tf": tf,
                         **check_file(path, tf, start, now, args.min_coverage, args.max_gap_hours)})

    lines = [
        f"# Data check - {args.exchange}",
        "",
        f"Checked {now:%Y-%m-%d %H:%M} UTC. Rules: data from {start:%Y-%m-%d}, "
        f"coverage >= {args.min_coverage}%, no gap > {args.max_gap_hours:g}h, "
        "no duplicates, no impossible candles.",
        "",
        "| Pair | TF | First | Last | Candles | Missing | Coverage | Longest gap | Zero-vol | Status |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        if "first" not in r:
            lines.append(f"| {r['pair']} | {r['tf']} | - | - | - | - | - | - | - | {r['status']} |")
            continue
        lines.append(
            f"| {r['pair']} | {r['tf']} | {r['first']} | {r['last']} | {r['candles']:,} | "
            f"{r['missing']:,} | {r['coverage']:.2f}% | {r['longest_gap_h']:.1f}h | "
            f"{r['zero_volume']:,} | {r['status']} |"
        )
    issues = [r for r in rows if r["problems"]]
    if issues:
        lines += ["", "## Problems", ""]
        lines += [f"- **{r['pair']} {r['tf']}** ({r['status']}): {'; '.join(r['problems'])}" for r in issues]
    failed = any(r["status"] == "FAIL" for r in rows)
    lines += ["", f"**Result: {'FAIL' if failed else 'PASS'}**", ""]

    report = "\n".join(lines)
    print(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
