#!/usr/bin/env python3
"""Round 5 hand-check of TrendBlend's orders (Freqtrade's lookahead check does not look at sizes).

Replays a backtest's orders to rebuild the wallet, and at every daily decision recomputes, from
closed daily candles only, what the strategy's rules say should happen to each coin: buy, top up,
trim, sell everything, or nothing. Then compares that with the orders the backtest actually made.
Also counts how many decisions would have differed had the strategy peeked at the unfinished day.

Runs in the container:
    docker compose run --rm --entrypoint python freqtrade scripts/round5_position_check.py \\
        <backtest result dir> [--strategy TrendBlendV1] [--slots 5]
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "user_data" / "strategies"))
sys.path.insert(0, str(ROOT / "scripts"))
import tuning  # noqa: E402

DATA = ROOT / "user_data" / "data" / "binance"


def daily_view(cls, pair: str, peek: bool = False) -> pd.DataFrame:
    """The strategy's daily score and weight, indexed by the day they become usable."""
    daily = pd.read_feather(DATA / f"{pair.replace('/', '_')}-1d.feather")
    close = daily["close"]
    averages = [close.rolling(round(n * cls.SPEED_SCALE)).mean() for n in cls.SPEEDS]
    score = sum((close > a).astype(float) for a in averages).where(averages[-1].notna())
    vol = np.log(close).diff().rolling(cls.VOL_DAYS).std() * np.sqrt(365)
    weight = score / 4 * np.minimum(1.0, cls.TARGET_VOL / vol)
    usable_from = daily["date"] + pd.Timedelta(days=0 if peek else 1)   # a day is usable once it closed
    return pd.DataFrame({"score": score.to_numpy(), "weight": weight.to_numpy()},
                        index=usable_from.to_numpy()).shift(cls.DELAY_DAYS)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("result_dir")
    ap.add_argument("--strategy", default="TrendBlendV1")
    ap.add_argument("--slots", type=int, default=5)
    ap.add_argument("--wallet", type=float, default=1000.0)
    ap.add_argument("--ratio", type=float, default=0.99)
    args = ap.parse_args()

    module = tuning.find_strategy_file(args.strategy, ROOT / "user_data" / "strategies").stem
    cls = getattr(importlib.import_module(module), args.strategy)
    with zipfile.ZipFile(next(Path(args.result_dir).glob("*.zip"))) as z:
        name = next(n for n in z.namelist() if n.endswith(".json") and "_config" not in n and "meta" not in n)
        res = json.loads(z.read(name))["strategy"][args.strategy]
    trades = res["trades"]
    pairs = sorted({t["pair"] for t in trades})
    start, end = pd.Timestamp(res["backtest_start"], tz="UTC"), pd.Timestamp(res["backtest_end"], tz="UTC")

    hourly = {p: pd.read_feather(DATA / f"{p.replace('/', '_')}-1h.feather").set_index("date") for p in pairs}
    views = {p: daily_view(cls, p) for p in pairs}
    peeks = {p: daily_view(cls, p, peek=True) for p in pairs}

    orders = []
    for t in trades:
        fee = t["fee_open"]
        for o in t["orders"]:
            orders.append({"ts": pd.Timestamp(o["order_filled_timestamp"], unit="ms", tz="UTC"), "pair": t["pair"],
                           "buy": o["ft_order_side"] == "buy", "amount": o["amount"], "price": o["safe_price"],
                           "cost": o["cost"], "fee": fee, "tag": o["ft_order_tag"],
                           "closes": not o["ft_is_entry"] and o is t["orders"][-1] and not t["is_open"]})
    orders.sort(key=lambda o: o["ts"])
    # The amount step per coin (Freqtrade rounds order amounts down to it).
    def decimals(x: float) -> int:
        return len(f"{x:.10f}".rstrip("0").split(".")[1])        # 115.0 -> 0 (whole units)
    step = {p: 10.0 ** -max(decimals(o["amount"]) for o in orders if o["pair"] == p) for p in pairs}

    cash, held, i = args.wallet, {p: 0.0 for p in pairs}, 0
    checked, mismatches, peek_diff, actions = 0, [], 0, {"buy": 0, "top_up": 0, "trim": 0, "sell_all": 0}

    def apply(o):
        nonlocal cash
        cash += (-1 if o["buy"] else 1) * o["cost"] - o["cost"] * o["fee"]
        held[o["pair"]] += o["amount"] if o["buy"] else -o["amount"]
        if o["closes"]:
            held[o["pair"]] = 0.0

    decisions = pd.date_range(start.normalize() + pd.Timedelta(hours=cls.REBALANCE_HOUR + 1), end, freq="D")
    for when in decisions:
        while i < len(orders) and orders[i]["ts"] < when:       # everything before this decision
            apply(orders[i]); i += 1
        prev = when - pd.Timedelta(hours=1)
        marks = {p: hourly[p]["close"].get(prev, np.nan) for p in pairs}
        equity = cash + sum(held[p] * marks[p] for p in pairs if held[p] > 0)
        slot = equity * args.ratio / args.slots
        now = [o for o in orders[i:] if o["ts"] == when]
        for p in pairs:
            view, peek = views[p].asof(when), peeks[p].asof(when)
            score, weight = view["score"], view["weight"]
            rate = hourly[p]["open"].get(when, np.nan)
            mine = [o for o in now if o["pair"] == p and o["tag"] in ("trend_up", "top_up", "trim", "trend_gone")]
            expect = None                                       # (kind, stake)
            gap_ratio = (weight * slot - held[p] * rate) / (cls.BAND * slot) if held[p] > 0 else np.nan
            if held[p] <= 0:
                if weight >= cls.BAND:
                    expect = ("buy", weight * slot)
            elif score == 0:
                expect = ("sell_all", held[p] * rate)
            elif weight > 0:
                gap = weight * slot - held[p] * rate
                if abs(gap) >= cls.BAND * slot:
                    expect = ("top_up" if gap > 0 else "trim", abs(gap))
            # What a peeking strategy (using the unfinished day) would have decided instead.
            if held[p] <= 0 and (peek["weight"] >= cls.BAND) != (weight >= cls.BAND):
                peek_diff += 1
            elif held[p] > 0 and (peek["score"] == 0) != (score == 0):
                peek_diff += 1
            checked += 1
            if expect is None and not mine:
                continue
            if expect is None or len(mine) != 1:
                mismatches.append(f"{when} {p}: expected {expect and (expect[0], round(expect[1], 2))}, got "
                                  f"{[(o['tag'], round(o['cost'], 2)) for o in mine]} (gap = {gap_ratio:+.3f} x the "
                                  f"threshold; |x| >= 1 means act)")
                continue
            o, (kind, stake) = mine[0], expect
            tag_ok = {"buy": "trend_up", "top_up": "top_up", "trim": "trim", "sell_all": "trend_gone"}[kind] == o["tag"]
            tolerance = max(0.01 * stake, 1.5 * step[p] * o["price"])     # 1%, or the amount rounding
            size_ok = kind == "sell_all" or abs(o["cost"] - stake) <= tolerance
            if tag_ok and size_ok:
                actions[kind] += 1
            else:
                mismatches.append(f"{when} {p}: expected {kind} {stake:.2f}, got {o['tag']} {o['cost']:.2f}")
    while i < len(orders):
        apply(orders[i]); i += 1

    other = sum(o["tag"] not in ("trend_up", "top_up", "trim", "trend_gone") for o in orders)
    print(f"{args.strategy}: {len(trades)} trades, {len(orders)} orders, {len(decisions)} daily decisions x "
          f"{len(pairs)} coins = {checked} checks")
    print(f"  matched the rules: {sum(actions.values())} orders ({actions}); "
          f"{other} other orders (emergency stop / end of test)")
    print(f"  mismatches: {len(mismatches)}")
    for m in mismatches[:15]:
        print("   ", m)
    print(f"  final cash from the replay: {cash:.2f} (backtest final balance {res['final_balance']:.2f})")
    print(f"  if it had peeked at the unfinished day, {peek_diff} buy/sell-all decisions would have differed")


if __name__ == "__main__":
    main()
