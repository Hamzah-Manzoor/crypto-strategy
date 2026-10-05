#!/usr/bin/env python3
"""Pick bull, bear and sideways date windows for regime tests.

Windows are judged on the equal-weight basket of all 5 whitelist pairs (what
the strategies actually trade), using what prices did INSIDE each window:
  bull     = the window with the biggest basket rise
  bear     = the window with the biggest basket fall (not overlapping bull)
  sideways = the window where the basket stayed in the narrowest band and
             moved less than 10% end to end (not overlapping the other two)
A bull/bear window that moved less than 20% is marked "weak" - that split
simply had no strong trend of that kind.

Windows are picked separately inside the in-sample split (used while building
strategies) and the out-of-sample split (only used in the final check), so
regime tests never leak out-of-sample data into development.

Cross-check: the classic backward-looking BTC trend label
  bull = 90-day return > +20% and price above its 200-day average
  bear = 90-day return < -20% and price below its 200-day average
is shown per window and per month. It lags turns, so it is not the selector.

Runs inside the Freqtrade container (needs pandas):
    python3 scripts/lab.py regimes
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SIDEWAYS_MAX_MOVE = 0.10
STRONG_TREND = 0.20


def load(data_dir: Path, pair: str, tf: str) -> pd.DataFrame:
    path = data_dir / f"{pair.replace('/', '_')}-{tf}.feather"
    if not path.exists():
        sys.exit(f"missing {path} - run: python3 scripts/lab.py download")
    df = pd.read_feather(path)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    return df.set_index("date").sort_index()


def daily_from_4h(data_dir: Path, pairs: list[str], before: pd.Timestamp):
    """Daily open/close per pair (columns = pairs), complete days only."""
    opens, closes = {}, {}
    for pair in pairs:
        df = load(data_dir, pair, "4h")
        daily = df.resample("1D").agg({"open": "first", "close": "last"})
        daily = daily[daily.index < before]
        opens[pair], closes[pair] = daily["open"], daily["close"]
    return pd.DataFrame(opens).dropna(), pd.DataFrame(closes).dropna()


def btc_trend_labels(btc: pd.DataFrame) -> pd.Series:
    ret90 = btc["close"] / btc["close"].shift(90) - 1
    sma200 = btc["close"].rolling(200).mean()
    label = pd.Series("sideways", index=btc.index)
    label[(ret90 > STRONG_TREND) & (btc["close"] > sma200)] = "bull"
    label[(ret90 < -STRONG_TREND) & (btc["close"] < sma200)] = "bear"
    label[sma200.isna()] = None
    return label


def basket_path(opens: pd.DataFrame, closes: pd.DataFrame, start, end) -> pd.Series:
    """Value of 1 USDT split equally across all pairs at `start`'s open."""
    base = opens.loc[start]
    w = closes[(closes.index >= start) & (closes.index < end)]
    path = (w / base).mean(axis=1)
    return pd.concat([pd.Series([1.0], index=[start - pd.Timedelta(seconds=1)]), path])


def path_stats(path: pd.Series) -> dict:
    return {
        "ret": path.iloc[-1] - 1,
        "range": path.max() / path.min() - 1,
        "max_dd": (1 - path / path.cummax()).max(),
    }


def candidate_windows(opens, closes, lo, hi, days) -> pd.DataFrame:
    idx = closes.index[(closes.index >= lo) & (closes.index + pd.Timedelta(days=days) <= hi)]
    rows = []
    for start in idx:
        end = start + pd.Timedelta(days=days)
        rows.append({"start": start, "end": end, **path_stats(basket_path(opens, closes, start, end))})
    return pd.DataFrame(rows)


def no_overlap(cands: pd.DataFrame, chosen: list[dict]) -> pd.DataFrame:
    keep = [all(not (r.start < c["end"] and c["start"] < r.end) for c in chosen)
            for r in cands.itertuples()]
    return cands[keep]


def pick(cands: pd.DataFrame) -> dict[str, dict]:
    chosen: dict[str, dict] = {}
    chosen["bull"] = cands.loc[cands["ret"].idxmax()].to_dict()
    rest = no_overlap(cands, list(chosen.values()))
    chosen["bear"] = rest.loc[rest["ret"].idxmin()].to_dict()
    rest = no_overlap(cands, list(chosen.values()))
    flat = rest[rest["ret"].abs() < SIDEWAYS_MAX_MOVE]
    pool = flat if len(flat) else rest
    chosen["sideways"] = pool.loc[pool["range"].idxmin()].to_dict()

    notes = {
        "bull": chosen["bull"]["ret"] < STRONG_TREND,
        "bear": chosen["bear"]["ret"] > -STRONG_TREND,
        "sideways": not len(flat),
    }
    for name, weak in notes.items():
        chosen[name]["weak"] = bool(weak)
    return chosen


def ymd(ts) -> datetime:
    return pd.Timestamp(datetime.strptime(ts, "%Y%m%d"), tz="UTC")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--exchange", default="binance")
    parser.add_argument("--is", dest="is_range", default="20231001-20251001", help="in-sample yyyymmdd-yyyymmdd")
    parser.add_argument("--oos", dest="oos_range", default="20251001-20261001", help="out-of-sample yyyymmdd-yyyymmdd")
    parser.add_argument("--days", type=int, default=90, help="window length in days")
    parser.add_argument("--out-json", type=Path, default=Path("results/regimes.json"))
    parser.add_argument("--out-md", type=Path, default=Path("results/checks/regimes.md"))
    args = parser.parse_args()

    data_dir = Path("user_data/data") / args.exchange
    pairs = json.loads(Path("user_data/configs/base.json").read_text())["exchange"]["pair_whitelist"]
    today = pd.Timestamp(datetime.now(timezone.utc)).normalize()
    opens, closes = daily_from_4h(data_dir, pairs, before=today)
    data_end = closes.index[-1] + pd.Timedelta(days=1)

    btc = load(data_dir, "BTC/USDT", "1d")
    btc = btc[btc.index < today]
    labels = btc_trend_labels(btc)

    splits = {}
    for name, rng in (("is", args.is_range), ("oos", args.oos_range)):
        lo, hi = (ymd(x) for x in rng.split("-"))
        splits[name] = (lo, min(hi, data_end))
    if labels[labels.index >= splits["is"][0]].isna().any():
        sys.exit("not enough BTC daily history for the 200-day average - run download again")

    out = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": f"{args.exchange}, 5-pair equal-weight basket from 4h candles + BTC/USDT 1d, "
                  f"data up to {data_end - pd.Timedelta(days=1):%Y-%m-%d}",
        "method": (f"{args.days}-day windows picked separately inside in-sample and out-of-sample: "
                   "bull = biggest basket rise, bear = biggest basket fall, sideways = narrowest "
                   f"basket range with < {SIDEWAYS_MAX_MOVE:.0%} net move; no overlap within a split. "
                   f"'weak' = a bull/bear window that moved less than {STRONG_TREND:.0%}."),
        "windows": {},
    }
    for split, (lo, hi) in splits.items():
        for regime, w in pick(candidate_windows(opens, closes, lo, hi, args.days)).items():
            b = btc[(btc.index >= w["start"]) & (btc.index < w["end"])]
            in_window = labels[(labels.index >= w["start"]) & (labels.index < w["end"])]
            shares = in_window.value_counts(normalize=True).round(2).to_dict()
            out["windows"][f"{regime}-{split}"] = {
                "regime": regime,
                "split": "in-sample" if split == "is" else "out-of-sample",
                "start": f"{w['start']:%Y-%m-%d}",
                "end": f"{w['end'] - pd.Timedelta(days=1):%Y-%m-%d}",
                "timerange": f"{w['start']:%Y%m%d}-{w['end']:%Y%m%d}",
                "weak": w["weak"],
                "basket_return_pct": round(100 * w["ret"], 1),
                "basket_range_pct": round(100 * w["range"], 1),
                "basket_max_drawdown_pct": round(100 * w["max_dd"], 1),
                "btc_return_pct": round(100 * (b["close"].iloc[-1] / b["open"].iloc[0] - 1), 1),
                "btc_trend_rule_share": {k: shares.get(k, 0.0) for k in ("bull", "sideways", "bear")},
            }

    # Month-by-month view for the docs.
    lo = splits["is"][0]
    m_basket = []
    for month_start in pd.date_range(lo, data_end, freq="MS", inclusive="left"):
        month_end = min(month_start + pd.offsets.MonthBegin(1), data_end)
        m_basket.append((month_start, path_stats(basket_path(opens, closes, month_start, month_end))["ret"]))
    b = btc[btc.index >= lo]
    btc_month = b["close"].resample("MS").last() / b["open"].resample("MS").first() - 1
    label_month = labels[labels.index >= lo].resample("MS").agg(lambda s: s.mode().iloc[0])

    lines = [
        "# Market regimes", "", out["source"], "", out["method"], "",
        "| Window | Dates | Timerange | Basket return | Basket range | Basket max DD | BTC return | BTC trend rule (bull/side/bear) | Weak? |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for name, w in out["windows"].items():
        s = w["btc_trend_rule_share"]
        lines.append(
            f"| **{name}** | {w['start']} → {w['end']} | `{w['timerange']}` | {w['basket_return_pct']:+.1f}% | "
            f"{w['basket_range_pct']:.1f}% | {w['basket_max_drawdown_pct']:.1f}% | {w['btc_return_pct']:+.1f}% | "
            f"{s['bull']:.0%} / {s['sideways']:.0%} / {s['bear']:.0%} | {'weak' if w['weak'] else ''} |"
        )
    lines += ["", "## Month by month", "",
              "| Month | Split | 5-pair basket | BTC | BTC trend rule |", "|---|---|---:|---:|---|"]
    for month_start, ret in m_basket:
        split = "IS" if month_start < splits["is"][1] else "OOS"
        lines.append(f"| {month_start:%Y-%m} | {split} | {ret:+.1%} | {btc_month.get(month_start, float('nan')):+.1%} | "
                     f"{label_month.get(month_start, '')} |")
    report = "\n".join(lines) + "\n"

    print(report)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(out, indent=2) + "\n")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
