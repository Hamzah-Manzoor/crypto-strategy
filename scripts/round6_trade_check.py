#!/usr/bin/env python3
"""Round 6 hand-check of AuctionValue's trades (Freqtrade's lookahead check does not look at
stops, targets or exit prices).

Rebuilds every trade from the candle files alone, following the written rules in
docs/research/auction-value-preregistration.md: sessions by clock time, weekly value from the
7 sessions before, the market state, both setups, and every exit (daily exits at the next
open, then the stop, then the target - Freqtrade's order inside a candle). Then compares
that list with the backtest's trades, one by one. Also prints the profit of each setup.

Runs in the container:
    docker compose run --rm --entrypoint python freqtrade scripts/round6_trade_check.py \\
        <backtest result dir> [--strategy AuctionValueV1]
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "user_data" / "strategies"))
sys.path.insert(0, str(ROOT / "scripts"))
import tuning  # noqa: E402
from labkit.auction import value_area  # noqa: E402  (checked against a slow version in the tests)

DATA = ROOT / "user_data" / "data" / "binance"
HOUR, DAY = pd.Timedelta(hours=1), pd.Timedelta(days=1)


class Rules:
    """The written rules, computed by clock time from one coin's hourly candles."""

    def __init__(self, cls, candles: pd.DataFrame):
        self.c, self.cls, self.cache = candles, cls, {}
        self.week = cls.PROFILE_SESSIONS * DAY

    def value(self, start: pd.Timestamp) -> tuple[float, float, float]:
        """Value of the week of candles just before `start`."""
        if start not in self.cache:
            w = self.c.loc[start - self.week:start - HOUR]
            self.cache[start] = value_area(w["high"].to_numpy(), w["low"].to_numpy(), w["volume"].to_numpy(),
                                           self.cls.PRICE_STEP, self.cls.VALUE_AREA)
        return self.cache[start]

    def closed_above(self, start: pd.Timestamp) -> bool:
        last = start + 23 * HOUR
        return last in self.c.index and self.c.at[last, "close"] > self.value(start)[2]

    def decision(self, start: pd.Timestamp) -> dict | None:
        """What the rules say at the end of the session that starts at `start`."""
        last = start + 23 * HOUR
        if last not in self.c.index:
            return None
        val, poc, vah = self.value(start)
        prev_val, _, prev_vah = self.value(start - self.week)
        state = 1 if vah > prev_vah and val > prev_val else (-1 if vah < prev_vah and val < prev_val else 0)
        day = self.c.loc[start:last]
        low, close = day["low"].min(), day["close"].iloc[-1]
        d = {"state": state, "poc": poc, "close": close, "setup": None}
        drop_states = getattr(self.cls, "FAILED_DROP_STATES", (0, 1))      # V1: sideways or rising
        if (state in drop_states and low < val < close < vah
                and vah - close >= self.cls.MIN_REWARD_RISK * (close - low)):
            d.update(setup="failed_drop", stop=low, target=vah)
        elif state == 1 and all(self.closed_above(start - j * DAY) for j in range(self.cls.ACCEPT_CLOSES)):
            d.update(setup="accepted_rise", stop=val, target=None)
        return d


def expected_trades(cls, pair: str, start: pd.Timestamp, end: pd.Timestamp, ratio_stop: float) -> list[dict]:
    candles = pd.read_feather(DATA / f"{pair.replace('/', '_')}-1h.feather").set_index("date")
    rules = Rules(cls, candles)
    # Sessions start the hour after the decision candle; a decision acts when its session is over,
    # DELAY_HOURS later.
    decisions = {}
    for s in pd.date_range(start.normalize() - 2 * DAY + (cls.REBALANCE_HOUR + 1) * HOUR, end, freq="D"):
        acts = s + DAY + cls.DELAY_HOURS * HOUR
        if start <= acts <= end and (d := rules.decision(s)):
            decisions[acts] = d
    out, trade = [], None
    for t, row in candles.loc[start:end - HOUR].iterrows():
        d = decisions.get(t)
        if trade is None and d and d["setup"]:                   # entries first, at the open
            trade = {"pair": pair, "open": t, "tag": d["setup"], "rate": row["open"],
                     "stop": max(d["stop"], row["open"] * (1 - ratio_stop)), "target": d["target"]}
        if trade is None:
            continue
        reason = price = None
        if d and d["state"] == -1:
            reason, price = "value_falling", row["open"]
        elif d and trade["tag"] == "accepted_rise" and d["close"] < d["poc"]:
            reason, price = "back_in_value", row["open"]
        elif row["low"] <= trade["stop"]:
            reason = "stop"
            price = row["open"] if trade["stop"] > row["high"] else trade["stop"]
        elif trade["target"] is not None and row["high"] > trade["target"]:
            reason, price = "target", max(row["open"], trade["target"])
        if reason:
            out.append({**trade, "close": t, "reason": reason, "close_rate": price})
            trade = None
    if trade:
        out.append({**trade, "close": end, "reason": "force_exit", "close_rate": None})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("result_dir")
    ap.add_argument("--strategy", default="AuctionValueV1")
    args = ap.parse_args()

    module = tuning.find_strategy_file(args.strategy, ROOT / "user_data" / "strategies").stem
    cls = getattr(importlib.import_module(module), args.strategy)
    with zipfile.ZipFile(next(Path(args.result_dir).glob("*.zip"))) as z:
        name = next(n for n in z.namelist() if n.endswith(".json") and "_config" not in n and "meta" not in n)
        res = json.loads(z.read(name))["strategy"][args.strategy]
    start, end = pd.Timestamp(res["backtest_start"], tz="UTC"), pd.Timestamp(res["backtest_end"], tz="UTC")
    actual = sorted(res["trades"], key=lambda t: (t["pair"], t["open_timestamp"]))
    pairs = sorted({t["pair"] for t in actual})

    reasons = {"value_falling": "value_falling", "back_in_value": "back_in_value", "stop_loss": "stop",
               "trailing_stop_loss": "stop", "roi": "target", "force_exit": "force_exit"}
    mismatches, matched, total_expected = [], 0, 0
    for pair in pairs:
        exp = expected_trades(cls, pair, start, end, abs(cls.stoploss))
        got = [t for t in actual if t["pair"] == pair]
        total_expected += len(exp)
        by_open = {pd.Timestamp(t["open_date"]): t for t in got}
        for e in exp:
            g = by_open.pop(e["open"], None)
            if g is None:
                mismatches.append(f"{pair} {e['open']}: expected a {e['tag']} trade, the backtest has none")
                continue
            problems = []
            if g["enter_tag"] != e["tag"]:
                problems.append(f"tag {g['enter_tag']} (expected {e['tag']})")
            if pd.Timestamp(g["close_date"]) != e["close"]:
                problems.append(f"closed {g['close_date']} (expected {e['close']} by {e['reason']})")
            if reasons.get(g["exit_reason"], g["exit_reason"]) != e["reason"]:
                problems.append(f"exit {g['exit_reason']} (expected {e['reason']})")
            if e["close_rate"] is not None and abs(g["close_rate"] / e["close_rate"] - 1) > 0.001:
                problems.append(f"exit price {g['close_rate']:.6g} (expected {e['close_rate']:.6g})")
            if problems:
                mismatches.append(f"{pair} {e['open']} {e['tag']}: " + "; ".join(problems))
            else:
                matched += 1
        for t in by_open.values():
            mismatches.append(f"{pair} {t['open_date']}: backtest has a {t['enter_tag']} trade the rules don't give")

    print(f"{args.strategy}: {len(actual)} backtest trades, {total_expected} trades from the written rules "
          f"({start:%Y-%m-%d} -> {end:%Y-%m-%d})")
    print(f"  matched exactly (entry time, setup, exit time, reason, price within 0.1%): {matched}")
    print(f"  mismatches: {len(mismatches)}")
    for m in mismatches[:20]:
        print("   ", m)
    print("  profit by setup:")
    df = pd.DataFrame(actual)
    if len(df):
        for tag, g in df.groupby("enter_tag"):
            hours = (pd.to_datetime(g["close_date"]) - pd.to_datetime(g["open_date"])).dt.total_seconds() / 3600
            print(f"    {tag:14} {len(g):4} trades, {(g['profit_abs'] > 0).mean():5.1%} winners, "
                  f"profit {g['profit_abs'].sum():+9.2f} USDT, median hold {hours.median() / 24:.1f} days")
        print("  exits: " + ", ".join(f"{k} {v}" for k, v in df["exit_reason"].value_counts().items()))


if __name__ == "__main__":
    main()
