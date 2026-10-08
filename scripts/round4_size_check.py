#!/usr/bin/env python3
"""Round 4 hand-check of position sizes (Freqtrade's lookahead check does not look at sizes).

Recomputes every MomentumRotationV3 / V3b trade's expected stake from data the strategy could have
seen (closed daily candles only) and compares it with the stake the backtest used. Also shows how far
off the sizes would be if the strategy had peeked at the unfinished day. Runs in the container:
    docker compose run --rm --entrypoint python freqtrade scripts/round4_size_check.py <backtest result dir>
"""
import json, sys, zipfile
from pathlib import Path
import numpy as np, pandas as pd

zpath = next(Path(sys.argv[1]).glob("*.zip"))
with zipfile.ZipFile(zpath) as z:
    name = next(n for n in z.namelist() if n.endswith(".json") and "_config" not in n and "meta" not in n)
    res = json.loads(z.read(name))
daily = {p: pd.read_feather(f"user_data/data/binance/{p.replace('/', '_')}-1d.feather").set_index("date")["close"]
         for p in ("BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT")}

def vol_at(pair, last_daily):  # annualised vol of the 30 daily log returns up to and including `last_daily`
    c = daily[pair].loc[:last_daily]
    return np.log(c).diff().iloc[-30:].std() * np.sqrt(365)

for strat in ("MomentumRotationV3", "MomentumRotationV3b"):
    trades = sorted(res["strategy"][strat]["trades"], key=lambda t: t["open_date"])
    errs, wrong_errs, scales = [], [], []
    for t in trades:
        t_open = pd.Timestamp(t["open_date"])
        closed = sum(x["profit_abs"] for x in trades if pd.Timestamp(x["close_date"]) <= t_open)
        open_fees = sum(x["stake_amount"] * x["fee_open"] for x in trades
                        if pd.Timestamp(x["open_date"]) <= t_open and pd.Timestamp(x["close_date"]) > t_open
                        and x is not t and x["open_date"] <= t["open_date"])
        total = (1000 + closed - open_fees) * 0.99   # Freqtrade default tradable_balance_ratio
        if strat == "MomentumRotationV3":
            expected = total * 0.5 / 3
        else:
            seen = t_open.floor("D") - pd.Timedelta(days=1)   # Sunday's candle, closed Monday 00:00
            scale = min(1.0, 0.5 / vol_at(t["pair"], seen)); scales.append(scale)
            expected = total / 3 * scale
            peek = min(1.0, 0.5 / vol_at(t["pair"], t_open.floor("D")))  # Monday's unfinished candle
            wrong_errs.append(abs(t["stake_amount"] / (total / 3 * peek) - 1))
        errs.append(abs(t["stake_amount"] / expected - 1))
    print(f"{strat}: {len(trades)} trades, stake vs expected: max error {max(errs):.3%}, "
          f"median {np.median(errs):.3%}")
    if scales:
        print(f"  size scale min(1, 50%/vol): min {min(scales):.2f}, median {np.median(scales):.2f}, "
              f"max {max(scales):.2f}; full slot in {sum(s >= 0.999 for s in scales)} of {len(scales)} trades")
        print(f"  if it had peeked at Monday's unfinished day: max error {max(wrong_errs):.2%}, "
              f"trades off by >0.5%: {sum(e > 0.005 for e in wrong_errs)}")
