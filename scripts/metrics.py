#!/usr/bin/env python3
"""Turn one Freqtrade backtest result (.zip) into a small summary JSON.

Why not just use Freqtrade's headline numbers? Its max drawdown, Sortino and
Calmar are built from CLOSED trades only. A strategy that holds positions
(Buy & Hold most of all) shows 0% drawdown while its open coins fall 17%.
So every risk number here comes from the wallet's mark-to-market value at
every candle (the `<strategy>_wallet.feather` file in the zip), with one
standard formula for every strategy:

    max drawdown = largest % fall of the wallet value from a previous peak
    Sharpe       = mean daily return / std of daily returns  x sqrt(365)
    Sortino      = mean daily return / downside deviation    x sqrt(365)
    CAGR         = (final / start) ^ (365 / days) - 1
    Calmar       = CAGR / max drawdown
    exposure     = average share of the wallet held in coins (time in market)

Trade statistics (count, win rate, profit factor, holding time) come from
Freqtrade's trade list. Risk-free rate is 0; crypto trades 365 days a year.

Runs inside the Freqtrade container (needs pandas):
    python scripts/metrics.py --zip <result.zip> --out results/runs/<run_id>.json --run-id <id>
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import sys
import zipfile
from pathlib import Path

import pandas as pd

DAYS_PER_YEAR = 365


def equity_curve(wallet: pd.DataFrame) -> pd.Series:
    """Wallet value (USDT) per candle: cash + every coin at that candle's price."""
    return wallet.groupby("date")["total_quote"].sum().sort_index()


def equity_metrics(equity: pd.Series, start_balance: float, final_balance: float, days: float) -> dict:
    curve = pd.concat([pd.Series([start_balance], index=[equity.index[0] - pd.Timedelta(seconds=1)]), equity])
    drawdown = 1 - curve / curve.cummax()

    daily = curve.resample("1D").last().dropna()
    returns = daily.pct_change().dropna()
    std = returns.std(ddof=1) if len(returns) > 1 else 0.0
    downside = math.sqrt((returns.clip(upper=0) ** 2).mean()) if len(returns) else 0.0
    mean = returns.mean() if len(returns) else 0.0

    total = final_balance / start_balance - 1
    cagr = (final_balance / start_balance) ** (DAYS_PER_YEAR / days) - 1 if days > 0 and final_balance > 0 else -1.0
    max_dd = float(drawdown.max())
    return {
        "profit_pct": 100 * total,
        "cagr_pct": 100 * cagr,
        "max_dd_pct": 100 * max_dd,
        "sharpe": mean / std * math.sqrt(DAYS_PER_YEAR) if std > 0 else 0.0,
        "sortino": mean / downside * math.sqrt(DAYS_PER_YEAR) if downside > 0 else 0.0,
        "calmar": cagr / max_dd if max_dd > 0 else 0.0,
    }


def quarterly_returns(equity: pd.Series, start_balance: float, start: pd.Timestamp, end: pd.Timestamp) -> list[dict]:
    """Wallet return per calendar quarter (mark-to-market). A quarter only partly inside the
    test is marked partial; rules count full quarters only."""
    if equity.empty:  # never traded: the wallet stayed flat the whole time
        equity = pd.Series(start_balance, index=pd.date_range(start, end, freq="D", inclusive="left"))
    curve = pd.concat([pd.Series([start_balance], index=[start]), equity])
    out, previous = [], start_balance
    first_q = pd.Timestamp(year=start.year, month=3 * ((start.month - 1) // 3) + 1, day=1, tz="UTC")
    for q_start in pd.date_range(first_q, end, freq="QS", inclusive="left"):
        q_end = q_start + pd.offsets.QuarterBegin(startingMonth=1)
        inside = curve[(curve.index >= q_start) & (curve.index < q_end)]
        if inside.empty:
            continue
        last = float(inside.iloc[-1])
        out.append({
            "quarter": f"{q_start.year}Q{(q_start.month - 1) // 3 + 1}",
            "ret_pct": round(100 * (last / previous - 1), 4),
            "partial": bool(start > q_start or end < q_end),
        })
        previous = last
    return out


def exposure_pct(wallet: pd.DataFrame, stake_currency: str) -> float:
    total = wallet.groupby("date")["total_quote"].sum()
    cash = wallet[wallet["currency"] == stake_currency].groupby("date")["total_quote"].sum()
    in_coins = (total - cash.reindex(total.index, fill_value=0.0)) / total
    return 100 * float(in_coins.mean())


def summarize_strategy(name: str, stats: dict, wallet: pd.DataFrame | None, code: bytes | None) -> dict:
    start, final = float(stats["starting_balance"]), float(stats["final_balance"])
    days = (stats["backtest_end_ts"] - stats["backtest_start_ts"]) / 1000 / 86400
    trades = int(stats["total_trades"])
    wins, losses = int(stats.get("wins", 0)), int(stats.get("losses", 0))

    out = {
        "strategy": name,
        "timeframe": stats["timeframe"],
        "timeframe_detail": stats.get("timeframe_detail") or None,  # Freqtrade uses "" for none
        "timerange": stats["timerange"],
        "start": stats["backtest_start"],
        "end": stats["backtest_end"],
        "days": round(days, 2),
        "trades": trades,
        "win_rate_pct": 100 * float(stats.get("winrate", 0.0)) if trades else 0.0,
        # Profit factor = gross wins / gross losses. Undefined (None) with no losing trade.
        "profit_factor": float(stats["profit_factor"]) if losses > 0 else None,
        "avg_hold_hours": float(stats.get("holding_avg_s", 0.0)) / 3600,
        "market_change_pct": 100 * float(stats.get("market_change", 0.0)),
        "final_balance": final,
        "stoploss": stats.get("stoploss"),
        "minimal_roi": stats.get("minimal_roi"),
        "trailing_stop": stats.get("trailing_stop"),
        "code_sha": hashlib.sha256(code).hexdigest()[:12] if code else None,
        # Freqtrade's own numbers, kept only to cross-check ours.
        "ft_trade_max_dd_pct": 100 * float(stats.get("max_relative_drawdown", 0.0)),
        "ft_wallet_max_dd_pct": 100 * float((stats.get("wallet_stats") or {}).get("max_relative_drawdown", math.nan)),
    }
    t_start = pd.Timestamp(stats["backtest_start_ts"], unit="ms", tz="UTC")
    t_end = pd.Timestamp(stats["backtest_end_ts"], unit="ms", tz="UTC")
    if wallet is not None and len(wallet):
        curve = equity_curve(wallet)
        out.update(equity_metrics(curve, start, final, days))
        out["exposure_pct"] = exposure_pct(wallet, stats.get("stake_currency", "USDT"))
        quarters = quarterly_returns(curve, start, t_start, t_end)
    else:  # no wallet file (no trades at all): flat line
        out.update(profit_pct=100 * (final / start - 1), cagr_pct=0.0, max_dd_pct=0.0,
                   sharpe=0.0, sortino=0.0, calmar=0.0, exposure_pct=0.0)
        quarters = quarterly_returns(pd.Series(dtype=float), start, t_start, t_end)
    profits = sorted((float(tr["profit_abs"]) for tr in stats.get("trades", [])), reverse=True)
    out["profit_abs_total"] = sum(profits)
    out["best_trades_profit_abs"] = profits[:3]   # for the robustness check R4
    full = [q for q in quarters if not q["partial"]]
    out["quarters"] = quarters
    out["quarters_total"] = len(full)
    out["quarters_profitable"] = sum(q["ret_pct"] > 0 for q in full)
    out["worst_quarter_pct"] = min((q["ret_pct"] for q in full), default=None)
    return {k: (round(v, 4) if isinstance(v, float) and math.isfinite(v) else v) for k, v in out.items()}


def summarize_zip(zip_path: Path) -> dict:
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        report_name = next(n for n in names if n.endswith(".json") and not n.endswith("_config.json"))
        report = json.loads(z.read(report_name))
        config = json.loads(z.read(next(n for n in names if n.endswith("_config.json"))))
        prefix = report_name[: -len(".json")]
        strategies = {}
        for name, stats in report["strategy"].items():
            wallet_name, code_name = f"{prefix}_{name}_wallet.feather", f"{prefix}_{name}.py"
            wallet = pd.read_feather(io.BytesIO(z.read(wallet_name))) if wallet_name in names else None
            code = z.read(code_name) if code_name in names else None
            strategies[name] = summarize_strategy(name, stats, wallet, code)
    return {"fee": applied_fee(report, config), "strategies": strategies}


def applied_fee(report: dict, config: dict) -> float | None:
    """The fee Freqtrade actually charged, read from the trades themselves.

    The config copy inside the zip keeps the file value (0.001) even when the run
    used `--fee 0.0015`, so it cannot be trusted for stress runs."""
    fees = {(t["fee_open"], t["fee_close"]) for s in report["strategy"].values() for t in s.get("trades", [])}
    if len(fees) > 1:
        raise SystemExit(f"trades in one run were charged different fees: {sorted(fees)}")
    if fees:
        fee_open, fee_close = fees.pop()
        if fee_open != fee_close:
            raise SystemExit(f"entry fee {fee_open} != exit fee {fee_close}")
        return fee_open
    return config.get("fee")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--period", default="custom")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    summary = summarize_zip(args.zip)
    first = next(iter(summary["strategies"].values()))
    run = {
        "run_id": args.run_id,
        "period": args.period,
        "timerange": first["timerange"],
        "timeframe": first["timeframe"],
        "timeframe_detail": first["timeframe_detail"],
        "fee": summary["fee"],
        "notes": args.notes,
        "zip": str(args.zip),
        "strategies": summary["strategies"],
    }

    # Cross-check our wallet drawdown against Freqtrade's wallet stats.
    for s in run["strategies"].values():
        ours, theirs = s["max_dd_pct"], s["ft_wallet_max_dd_pct"]
        if isinstance(theirs, float) and math.isfinite(theirs) and abs(ours - theirs) > 1.0:
            print(f"WARNING: {s['strategy']}: our max drawdown {ours:.2f}% vs Freqtrade wallet {theirs:.2f}%")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(run, indent=1) + "\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
