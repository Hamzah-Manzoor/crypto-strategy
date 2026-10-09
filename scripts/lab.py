#!/usr/bin/env python3
"""Crypto Strategy Lab task runner.

One entry point for every lab task (standard library only, works on macOS,
Linux and Windows). Every command that starts Freqtrade runs the safety check
first and refuses to continue if it fails.

    python3 scripts/lab.py <command> [options]
    python3 scripts/lab.py <command> --help
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import bots  # noqa: E402
import experiments  # noqa: E402
import report  # noqa: E402
import robustness  # noqa: E402
import rules  # noqa: E402
import safety_check  # noqa: E402
import tuning  # noqa: E402
from rules import BASELINE  # noqa: E402

COMPOSE = ["docker", "compose", "--project-directory", str(ROOT), "-f", str(ROOT / "docker-compose.yml")]
CONFIGS = "user_data/configs"  # same relative path on the host and in the container

EXCHANGES = ["binance", "bybit", "okx"]  # data sources, in order of preference
TIMEFRAMES = ["5m", "15m", "1h", "4h"]   # 1h main; 15m/4h alternatives; 5m only for --timeframe-detail
DATA_START = "20230501"                  # 5 months of warm-up before the in-sample period:
                                         # 600 startup candles on 4h = 100 days must fit
REGIME_DATA_START = "20220101"           # extra BTC daily history so a 200-day average exists from day one

# Test periods (see docs/TESTING_METHODOLOGY.md and docs/research/).
# Round 1: build on "is", check on "oos". The "oos" year was looked at 9 times and is now
# retired as a test: Round 2 builds on "dev" (= is + oos) and examines once on "holdout".
PERIODS = {
    "is": ("20231001", "20251001"),
    "oos": ("20251001", "20261001"),
    "dev": ("20231001", "20261001"),
    "holdout": ("20210101", "20231001"),
    "exam2019": ("20190101", "20210101"),  # Round 4 exam (4 coins: SOL listed Aug 2020)
    "exam5": ("20190101", "20231001"),     # Round 5 exam, on 9 coins never traded here (inside the protected years)
}
# Data no test may touch without --allow-holdout, and tuning may never touch. Every look is logged.
PROTECTED = {"holdout": PERIODS["holdout"], "exam2019": PERIODS["exam2019"]}
STANDARD_FEE = 0.001  # 0.1% per side (Binance spot)
STRESS_FEE = 0.0015   # stands in for slippage in the stage-1 stress run

# Hyperopt defaults (docs/TESTING_METHODOLOGY.md section 7)
HYPEROPT_LOSS = "CalmarHyperOptLoss"
HYPEROPT_SPACES = ["buy", "sell", "stoploss"]
HYPEROPT_EPOCHS = 300
HYPEROPT_SEED = 42
HYPEROPT_MIN_TRADES = 50
HYPEROPT_JOBS = 6  # parallel workers; 11 ran Docker's 8 GB out of memory (worker SIGKILL)

# Bias checks (lab.py check-bias): all inside the in-sample period.
BIAS_TIMEFRAME = "1h"
LOOKAHEAD_TIMERANGE = "20240101-20240703"   # ~6 months, all pairs. Ends on a Wednesday: a window ending
                                            # Monday 00:00 crashed Freqtrade 2026.9 on weekly trades closing on its last candle
LOOKAHEAD_LONG_TIMERANGE = "20231001-20260701"  # slow strategies (< 10 trades in the window above): all of dev,
                                                # also ending on a Wednesday
RECURSIVE_TIMERANGE = "20240101-20250101"   # >= 5000 candles, as the Freqtrade docs recommend
RECURSIVE_PAIR = "BTC/USDT"
RECURSIVE_STARTUPS = ["100", "200", "400", "600", "1000"]
RECURSIVE_MAX_PCT = 0.05  # max |indicator error| allowed at the strategy's own startup_candle_count

USER_DATA_DIRS = ["data", "backtest_results", "hyperopt_results", "logs", "db", "walkforward"]
RESULTS_DIRS = ["leaderboards", "hyperopt", "walkforward", "checks"]
GENERATED_SECRETS = [
    "FREQTRADE__API_SERVER__PASSWORD",
    "FREQTRADE__API_SERVER__JWT_SECRET_KEY",
    "FREQTRADE__API_SERVER__WS_TOKEN",
]


# --------------------------------------------------------------------------- helpers

def say(msg: str) -> None:
    print(f"\n==> {msg}", flush=True)


def die(msg: str) -> None:
    print(f"\nERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd: list[str], check: bool = True, quiet: bool = False, tee: bool = False) -> subprocess.CompletedProcess:
    """Run a command. quiet = capture silently; tee = show output live AND capture it."""
    if not quiet:
        print(f"$ {shlex.join(cmd)}", flush=True)
    if tee:
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        lines = []
        for line in proc.stdout:
            print(line, end="", flush=True)
            lines.append(line)
        result = subprocess.CompletedProcess(cmd, proc.wait(), "".join(lines), "")
    else:
        result = subprocess.run(cmd, cwd=ROOT, capture_output=quiet, text=True)
    if check and result.returncode != 0:
        die(f"command failed (exit {result.returncode}): {shlex.join(cmd)}")
    return result


def safety_gate() -> None:
    """Hard rule 3: run the safety check before anything starts."""
    if safety_check.main(["--root", str(ROOT)]) != 0:
        sys.exit(1)


def config_args(*names: str) -> list[str]:
    """--config flags for files in user_data/configs, base.json always first."""
    files = ["base.json", *[n for n in names if n != "base.json"]]
    args = []
    for name in files:
        if not (ROOT / CONFIGS / name).exists():
            die(f"config not found: {CONFIGS}/{name}")
        args += ["--config", f"{CONFIGS}/{name}"]
    return args


def freqtrade(args: list[str], check: bool = True, tee: bool = False) -> subprocess.CompletedProcess:
    """Run a one-off Freqtrade command in the pinned container (after the safety gate)."""
    safety_gate()
    # COLUMNS: keep Freqtrade's result tables on one line each, so they can be parsed and saved.
    return run([*COMPOSE, "run", "--rm", "-e", "COLUMNS=220", "freqtrade", *args], check=check, tee=tee)


def discover_strategies() -> list[str]:
    """Strategy class names in user_data/strategies/*.py (baseline first)."""
    names = []
    for f in sorted((ROOT / "user_data" / "strategies").glob("*.py")):
        names += re.findall(r"^class (\w+)\(", f.read_text(), re.MULTILINE)
    return sorted(names, key=lambda n: (not n.startswith("BuyHold"), n))


def strategy_startup(name: str) -> int | None:
    """startup_candle_count as written in the strategy file (None if not found)."""
    for f in (ROOT / "user_data" / "strategies").glob("*.py"):
        text = f.read_text()
        if re.search(rf"^class {name}\(", text, re.MULTILINE):
            m = re.search(r"^\s+startup_candle_count\s*=\s*(\d+)", text, re.MULTILINE)
            return int(m.group(1)) if m else None
    return None


def container_python(script: str, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run one of our scripts inside the Freqtrade container (it has pandas)."""
    safety_gate()
    return run([*COMPOSE, "run", "--rm", "--entrypoint", "python", "freqtrade",
                f"scripts/{script}", *args], check=check)


def data_exchange() -> str:
    """Exchange whose data we use: $LAB_EXCHANGE, else the first one with downloaded data."""
    chosen = os.environ.get("LAB_EXCHANGE")
    if chosen:
        if chosen not in EXCHANGES:
            die(f"LAB_EXCHANGE must be one of {EXCHANGES}")
        return chosen
    for name in EXCHANGES:
        if any((ROOT / "user_data" / "data" / name).glob("*.feather")):
            return name
    return EXCHANGES[0]


def exchange_configs(exchange: str) -> list[str]:
    """Override config that switches the data source (base.json is Binance)."""
    return [] if exchange == "binance" else [f"exchange-{exchange}.json"]


def docker_ready() -> bool:
    if shutil.which("docker") is None:
        return False
    return run(["docker", "info"], check=False, quiet=True).returncode == 0


# --------------------------------------------------------------------------- commands

def cmd_setup(args: argparse.Namespace) -> None:
    """Prepare the machine: folders, .env, git hook, Docker image."""
    say("Checking tools")
    if sys.version_info < (3, 10):
        die(f"Python 3.10+ needed, found {sys.version.split()[0]}")
    print(f"Python {sys.version.split()[0]} OK")
    if shutil.which("docker") is None:
        die("Docker is not installed. Install Docker Desktop: https://docs.docker.com/desktop/")
    if not docker_ready():
        die("Docker is installed but not running. Start Docker Desktop, wait for it to say "
            "'Engine running', then run setup again.")
    run(["docker", "compose", "version"])

    say("Creating folders")
    for d in USER_DATA_DIRS:
        (ROOT / "user_data" / d).mkdir(parents=True, exist_ok=True)
    for d in RESULTS_DIRS:
        (ROOT / "results" / d).mkdir(parents=True, exist_ok=True)
    print("user_data/{" + ",".join(USER_DATA_DIRS) + "}  results/{" + ",".join(RESULTS_DIRS) + "}")

    say("Creating .env (FreqUI login, git-ignored)")
    env_path = ROOT / ".env"
    if env_path.exists():
        print(".env already exists - left untouched")
    else:
        lines = []
        for line in (ROOT / ".env.example").read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and key in GENERATED_SECRETS and value == "":
                line = f"{key}={secrets.token_urlsafe(32)}"
            lines.append(line)
        env_path.write_text("\n".join(lines) + "\n")
        env_path.chmod(0o600)
        print("Created .env with a random FreqUI password and JWT secret (see it with: cat .env)")

    if (ROOT / ".git").exists():
        say("Activating the git pre-commit hook")
        hook = ROOT / "scripts" / "hooks" / "pre-commit"
        hook.chmod(0o755)
        run(["git", "config", "core.hooksPath", "scripts/hooks"])

    say("Safety check")
    safety_gate()

    say("Pulling the pinned Freqtrade image")
    run([*COMPOSE, "--profile", "tools", "pull"])
    freqtrade(["--version"])

    say("Setup complete. Next: python3 scripts/lab.py download")


def cmd_safety(args: argparse.Namespace) -> None:
    """Run the safety check (also runs automatically before every Freqtrade command)."""
    safety_gate()


def cmd_test(args: argparse.Namespace) -> None:
    """Run the unit tests (host tests, then the pandas tests inside the container)."""
    say("Host tests (standard library)")
    host = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], check=False)
    container = None
    if args.host_only:
        print("Skipping container tests (--host-only)")
    elif not docker_ready():
        print("Docker is not running: skipping container tests (start Docker Desktop to run them)")
    else:
        say("Container tests (pandas, inside the pinned Freqtrade image)")
        safety_gate()
        container = run([*COMPOSE, "run", "--rm", "--entrypoint", "python", "freqtrade",
                         "-m", "unittest", "discover", "-s", "tests/container", "-v"], check=False)
    failed = host.returncode or (container is not None and container.returncode)
    say("Tests " + ("FAILED" if failed else "passed"))
    sys.exit(1 if failed else 0)


def cmd_show_config(args: argparse.Namespace) -> None:
    """Show the merged config Freqtrade sees (secrets redacted)."""
    freqtrade(["show-config", *config_args(*args.configs)])


def cmd_download(args: argparse.Namespace) -> None:
    """Download candles for all pairs and timeframes (re-run any time to top up)."""
    exchange = args.exchange
    start, timeframes = args.start or DATA_START, args.timeframes or TIMEFRAMES
    cfg = config_args(*exchange_configs(exchange))
    pairs = ["--pairs", *args.pairs] if args.pairs else []  # default: the config's whitelist

    say(f"Downloading {', '.join(timeframes)} candles from {exchange}, starting {start}")
    # Pass 1 (--prepend) extends existing files back to `start`; pass 2 adds new candles.
    # On a fresh download pass 1 does all the work and pass 2 has nothing left to fetch.
    grid = freqtrade(["download-data", *cfg, *pairs, "--timeframes", *timeframes, "--prepend",
                      "--timerange", f"{start}-"], check=False)
    if grid.returncode == 0:
        grid = freqtrade(["download-data", *cfg, *pairs, "--timeframes", *timeframes,
                          "--timerange", f"{start}-"], check=False)

    say(f"Downloading BTC/USDT daily candles from {REGIME_DATA_START} (for market-regime labels)")
    extra = freqtrade(["download-data", *cfg, "--pairs", "BTC/USDT", "--timeframes", "1d",
                       "--timerange", f"{REGIME_DATA_START}-"], check=False)

    if grid.returncode or extra.returncode:
        fallback = EXCHANGES[EXCHANGES.index(exchange) + 1:]
        hint = f" Try another source: python3 scripts/lab.py download --exchange {fallback[0]}" if fallback else ""
        die(f"download from {exchange} failed (region block or network problem?).{hint} "
            "See docs/SETUP.md > Troubleshooting.")

    say("Checking the downloaded data")
    cmd_data_check(argparse.Namespace(exchange=exchange, start=args.start, timeframes=args.timeframes,
                                      pairs=args.pairs))


def cmd_data_check(args: argparse.Namespace) -> None:
    """Check coverage, gaps and bad candles; writes results/checks/data_check.md."""
    exchange = args.exchange or data_exchange()
    start, timeframes = args.start or DATA_START, args.timeframes or TIMEFRAMES
    pairs = args.pairs or []
    out = ("results/checks/data_check.md" if (start, timeframes, pairs) == (DATA_START, TIMEFRAMES, [])
           else f"results/checks/data_check_{start}_{'-'.join(timeframes)}"
                + (f"_{'-'.join(p.split('/')[0] for p in pairs)}" if pairs else "") + ".md")
    result = container_python("data_check.py", [
        "--exchange", exchange, "--start", start, "--timeframes", *timeframes, "--out", out,
        *(["--pairs", *pairs] if pairs else []),
    ], check=False)
    if result.returncode:
        die("data check failed - see the Problems list above and docs/SETUP.md > Troubleshooting")


def cmd_regimes(args: argparse.Namespace) -> None:
    """Pick bull / bear / sideways windows in each split; writes results/regimes.json."""
    container_python("regimes.py", [
        "--exchange", data_exchange(),
        "--is", "-".join(PERIODS["is"]), "--oos", "-".join(PERIODS["oos"]),
        "--days", str(args.days),
        "--out-json", "results/regimes.json", "--out-md", "results/checks/regimes.md",
    ])


def parse_rich_table(text: str, title: str) -> tuple[list[str], list[list[str]]]:
    """Header + rows of the first Freqtrade (rich) table after `title` in captured output."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if title in line), None)
    if start is None:
        return [], []
    header, rows = [], []
    for line in lines[start + 1:]:
        s = line.strip()
        if s.startswith("┃") and not header:
            header = [c.strip() for c in s.strip("┃").split("┃")]
        elif s.startswith("│"):
            rows.append([c.strip() for c in s.strip("│").split("│")])
        elif s.startswith("└"):
            break
    return header, rows


def pct(cell: str) -> float:
    """'-0.024%' -> 0.024 (absolute), '-' -> 0.0 (no difference), 'nan%' -> nan."""
    if cell in ("-", ""):
        return 0.0
    try:
        return abs(float(cell.rstrip("%")))
    except ValueError:
        return math.nan


def strategy_path_args(strategy_path: Path | None) -> list[str]:
    return ["--strategy-path", str(strategy_path.relative_to(ROOT))] if strategy_path else []


def recursive_check(strategy: str, strategy_path: Path | None = None) -> tuple[str, list[str]]:
    """Run recursive-analysis for one strategy; return (verdict, markdown lines)."""
    result = freqtrade([
        "recursive-analysis", *config_args("backtest.json"), "--strategy", strategy,
        *strategy_path_args(strategy_path),
        "-i", BIAS_TIMEFRAME, "-p", RECURSIVE_PAIR, "--timerange", RECURSIVE_TIMERANGE,
        "--startup-candle", *RECURSIVE_STARTUPS,
    ], check=False, tee=True)
    header, rows = parse_rich_table(result.stdout, "Recursive Analysis")
    # Freqtrade labels the strategy's own (possibly inherited) value "<n> (from strategy)".
    from_strategy = next((int(h.split()[0]) for h in header if "from strategy" in h), None)
    startup = from_strategy if from_strategy is not None else strategy_startup(strategy)
    md = [f"### {strategy} (startup_candle_count = {startup})", ""]
    if result.returncode != 0 or " - ERROR - " in result.stdout:
        return "FAIL", md + ["recursive-analysis reported an error - see console output.", ""]
    if not rows:
        return "PASS", md + ["No indicator changed with the number of warm-up candles "
                             "(no recursive indicators).", ""]

    col = next((i for i, h in enumerate(header) if "from strategy" in h), None)
    if col is None and startup is not None and str(startup) in header:
        col = header.index(str(startup))
    md += ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    md += ["| " + " | ".join(r) + " |" for r in rows]
    if col is None:
        return "FAIL", md + ["", "Could not find the strategy's own startup column.", ""]
    worst = max(pct(r[col]) for r in rows)
    verdict = "PASS" if worst <= RECURSIVE_MAX_PCT else "FAIL"
    worst_txt = "nan (not enough candles)" if math.isnan(worst) else f"{worst:.3f}%"
    return verdict, md + ["", f"Worst indicator error at {startup} startup candles: **{worst_txt}** "
                              f"(limit {RECURSIVE_MAX_PCT}%) → **{verdict}**", ""]


def run_bias_checks(strategies: list[str], skip_lookahead: bool = False, skip_recursive: bool = False,
                    strategy_path: Path | None = None, save_lookahead_csv: bool = True):
    """Lookahead + recursive analysis. Returns (status per strategy, markdown lines, failures).
    strategy_path: extra folder with (generated) strategy classes, e.g. robustness variants."""
    report = [
        "# Bias checks", "",
        f"Freqtrade 2026.9, timeframe {BIAS_TIMEFRAME}. Strategies: {', '.join(strategies)}.", "",
    ]
    failed = []
    status = {name: {"lookahead": "not run", "recursive": "not run"} for name in strategies}

    if not skip_lookahead:
        report += [
            "## Lookahead analysis - does any signal use future candles?", "",
            f"Timerange `{LOOKAHEAD_TIMERANGE}`, all 5 pairs, one strategy per run (with "
            "`--strategy-list`, Freqtrade 2026.9 analyses the first strategy's trades for every strategy). "
            "Freqtrade re-runs the backtest with the data cut off right after each signal; if the signal or "
            "an indicator changes, the strategy was peeking at candles it could not have seen. "
            "Pass = `has_bias` is exactly False.", "",
            "| Strategy | Has bias | Signals checked | Biased entries | Biased exits | Biased indicators |",
            "|---|---|---:|---:|---:|---|",
        ]
        rows_out = []
        for name in strategies:
            if strategy_startup(name) == 0:
                report.append(f"| {name} | skipped | - | - | - | no indicators; its trades only close at the "
                              "end of the test, which this check cannot evaluate |")
                status[name]["lookahead"] = "skipped"
                continue
            say(f"Lookahead analysis: {name}")
            tmp_csv = ROOT / "user_data" / "backtest_results" / f"lookahead_{name}.csv"

            def lookahead(timerange: str):
                tmp_csv.unlink(missing_ok=True)
                result = freqtrade([
                    "lookahead-analysis", *config_args("backtest.json"), "--strategy", name,
                    *strategy_path_args(strategy_path), "-i", BIAS_TIMEFRAME, "--timerange", timerange,
                    "--minimum-trade-amount", "10", "--targeted-trade-amount", "30",
                    "--lookahead-analysis-exportfilename", str(tmp_csv.relative_to(ROOT)),
                ], check=False, tee=True)
                row = next((r for r in csv.DictReader(tmp_csv.open()) if r.get("strategy") == name), None) \
                    if tmp_csv.exists() else None
                return result, row

            result, row = lookahead(LOOKAHEAD_TIMERANGE)
            too_few = re.search(r"less than minimum_trade_amount|too few trades", result.stdout)
            if too_few and (row is None or row.get("has_bias", "").strip() not in ("True", "False")):
                say(f"{name}: fewer than 10 trades in {LOOKAHEAD_TIMERANGE} (slow strategy) - "
                    f"re-running on {LOOKAHEAD_LONG_TIMERANGE}")
                result, row = lookahead(LOOKAHEAD_LONG_TIMERANGE)
                if row is not None:
                    row["timerange"] = LOOKAHEAD_LONG_TIMERANGE
            if result.returncode != 0 or row is None:
                failed.append(f"{name} (lookahead did not run)")
                status[name]["lookahead"] = "fail"
                report.append(f"| {name} | **not checked** | - | - | - | - |")
                continue
            rows_out.append(row)
            verdict = row.get("has_bias", "").strip()
            status[name]["lookahead"] = "pass" if verdict == "False" else "fail"
            if verdict != "False":
                failed.append(f"{name} (lookahead: {verdict})")
            shown = "no" if verdict == "False" else ("**YES**" if verdict == "True" else f"**{verdict}**")
            report.append(
                f"| {name} | {shown} | {row.get('total_signals', '')} | {row.get('biased_entry_signals', '')} | "
                f"{row.get('biased_exit_signals', '')} | {row.get('biased_indicators', '') or '-'} |"
                + (f" (slow strategy: window `{row['timerange']}`)" if row.get("timerange") else "")
            )
        if rows_out and save_lookahead_csv:
            with (ROOT / "results" / "checks" / "lookahead.csv").open("w", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(dict.fromkeys(k for r in rows_out for k in r)))
                writer.writeheader()
                writer.writerows(rows_out)
        report.append("")

    if not skip_recursive:
        report += [
            "## Recursive analysis - is `startup_candle_count` enough?", "",
            f"{RECURSIVE_PAIR}, timerange `{RECURSIVE_TIMERANGE}`. Each column shows how far an indicator's "
            "last value is off when only that many warm-up candles are available, compared with using all "
            f"history. Pass = worst error at the strategy's own startup count <= {RECURSIVE_MAX_PCT}%.", "",
        ]
        for name in strategies:
            if strategy_startup(name) == 0:
                report += [f"### {name} (startup_candle_count = 0)", "",
                           "Skipped: no indicators, so nothing needs warm-up candles.", ""]
                status[name]["recursive"] = "skipped"
                continue
            say(f"Recursive analysis: {name}")
            verdict, md = recursive_check(name, strategy_path)
            report += md
            status[name]["recursive"] = "pass" if verdict == "PASS" else "fail"
            if verdict != "PASS":
                failed.append(f"{name} (recursive)")

    return status, report, failed


def cmd_check_bias(args: argparse.Namespace) -> None:
    """Lookahead + recursive analysis on strategies; writes results/checks/bias_check.md."""
    strategies = args.strategies or discover_strategies()
    status, report, failed = run_bias_checks(strategies, args.skip_lookahead, args.skip_recursive)
    report += ["## Result", "", "**PASS** - no bias found." if not failed
               else "**FAIL**: " + ", ".join(failed), ""]
    out = ROOT / "results" / "checks" / "bias_check.md"
    out.write_text("\n".join(report))
    # Machine-readable verdicts for the promotion rules (merged, so a partial re-run keeps the others).
    json_path = ROOT / "results" / "checks" / "bias_check.json"
    saved = json.loads(json_path.read_text()).get("strategies", {}) if json_path.exists() else {}
    for name, s in status.items():
        merged = {**saved.get(name, {}), **{k: v for k, v in s.items() if v != "not run"}}
        merged["ok"] = all(merged.get(k) in ("pass", "skipped") for k in ("lookahead", "recursive"))
        saved[name] = merged
    json_path.write_text(json.dumps({"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                                     "strategies": saved}, indent=1, sort_keys=True) + "\n")
    say(f"Report written to {out.relative_to(ROOT)} and {json_path.relative_to(ROOT)}")
    if failed:
        die("bias check failed: " + ", ".join(failed))
    print("Bias check PASSED for all strategies.")


def resolve_period(period: str) -> tuple[str, str]:
    """Period name -> (label, Freqtrade timerange). Names: is, oos, full, a regime window
    from results/regimes.json (e.g. bull-is), or a literal yyyymmdd-yyyymmdd."""
    if period in PERIODS:
        return period, "-".join(PERIODS[period])
    if period == "full":
        return period, f"{PERIODS['is'][0]}-{PERIODS['oos'][1]}"
    regimes = ROOT / "results" / "regimes.json"
    windows = json.loads(regimes.read_text())["windows"] if regimes.exists() else {}
    if period in windows:
        return period, windows[period]["timerange"]
    if re.fullmatch(r"\d{8}-\d{8}", period):
        return "custom", period
    die(f"unknown period '{period}'. Use: {', '.join([*PERIODS, 'full', *windows])} or yyyymmdd-yyyymmdd")


def touches_protected(timerange: str) -> list[str]:
    """Names of protected periods the timerange overlaps (end dates are exclusive)."""
    start, _, end = timerange.partition("-")
    return [name for name, (p_start, p_end) in PROTECTED.items()
            if (not start or start < p_end) and (not end or end > p_start)]


def backtest_run(period: str, timeframe: str, fee: float, detail: str | None, strategies: list[str],
                 notes: str, allow_protected: bool, pairs: list[str] | None = None,
                 strategy_path: Path | None = None, max_open_trades: int | None = None) -> dict:
    """Backtest strategies in ONE Freqtrade run, summarise, log and report. Returns the run summary."""
    label, timerange = resolve_period(period)
    protected = touches_protected(timerange)
    oos = bool(protected)
    if protected and not allow_protected:
        die(f"period '{period}' ({timerange}) touches protected test data ({', '.join(protected)}: "
            f"{'-'.join(PROTECTED[protected[0]])}). Build and iterate on 'dev'. If this is the "
            "pre-registered exam, add --allow-holdout (every look is logged).")
    exam_coins = sorted(set(pairs or []) & set(rules.ROUND5_EXAM_COINS))
    if exam_coins and not allow_protected:
        die(f"{', '.join(exam_coins)} are Round 5 exam coins (docs/research/trend-blend-preregistration.md). "
            "Only the pre-registered exam may trade them.")
    if BASELINE not in strategies:
        strategies = [BASELINE, *strategies]  # always compare against buy & hold

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_id = f"{stamp}_{label}_{timeframe}"
    if abs(fee - STANDARD_FEE) > 1e-12:
        run_id += f"_fee{fee * 100:g}pct"
    if detail:
        run_id += f"_detail{detail}"
    run_dir = ROOT / "user_data" / "backtest_results" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    say(f"Backtesting {len(strategies)} strategies · {label} ({timerange}) · {timeframe} · fee {fee:.2%}"
        + (f" · detail {detail}" if detail else "") + (" · OUT-OF-SAMPLE LOOK" if oos else ""))
    ft_args = [
        "backtesting", *config_args(*exchange_configs(data_exchange()), "backtest.json"),
        "--strategy-list", *strategies, "--timeframe", timeframe, "--timerange", timerange,
        "--fee", str(fee), "--cache", "none", "--export", "trades", "--enable-protections",
        "--backtest-directory", str(run_dir.relative_to(ROOT)),
    ]
    if detail:
        ft_args += ["--timeframe-detail", detail]
    if notes:
        ft_args += ["--notes", notes]
    if pairs:
        ft_args += ["--pairs", *pairs]
    if max_open_trades:
        ft_args += ["--max-open-trades", str(max_open_trades)]
    ft_args += strategy_path_args(strategy_path)
    freqtrade(ft_args)

    zips = sorted(run_dir.glob("*.zip"))
    if len(zips) != 1:
        die(f"expected one result zip in {run_dir}, found {len(zips)}")
    summary = f"results/runs/{run_id}.json"
    container_python("metrics.py", ["--zip", str(zips[0].relative_to(ROOT)), "--out", summary,
                                    "--run-id", run_id, "--period", label, "--notes", notes])
    run_summary = report.load_run(ROOT / summary)
    board = report.write_run(run_summary)
    ids = experiments.log_run(run_summary, oos_look=oos)
    experiments.render()
    report.update_results_doc()
    print("\n" + board.read_text())
    say(f"Leaderboard: {board.relative_to(ROOT)} · experiments {ids[0]}..{ids[-1]} logged")
    return run_summary


def cmd_backtest(args: argparse.Namespace) -> None:
    """Backtest all strategies in one run, then build the leaderboard and log the experiment."""
    backtest_run(args.period, args.timeframe, args.fee, args.detail,
                 args.strategies or discover_strategies(), args.notes, args.allow_holdout)


def cmd_report(args: argparse.Namespace) -> None:
    """Rebuild every leaderboard, docs/RESULTS.md and docs/EXPERIMENT_LOG.md."""
    if args.recompute:
        for path in sorted((ROOT / "results" / "runs").glob("*.json")):
            run_summary = report.load_run(path)
            zip_path = ROOT / run_summary["zip"]
            if not zip_path.exists():
                print(f"skip {path.name}: raw result {run_summary['zip']} no longer exists")
                continue
            container_python("metrics.py", ["--zip", run_summary["zip"], "--out", str(path.relative_to(ROOT)),
                                            "--run-id", run_summary["run_id"], "--period", run_summary["period"],
                                            "--notes", run_summary.get("notes", "")])
    n = report.rebuild_all()
    if args.recompute:
        print(f"Updated measured fields of {experiments.refresh(report.all_runs())} experiment entries")
    experiments.render()
    print(f"Rebuilt {n} leaderboards, docs/RESULTS.md and docs/EXPERIMENT_LOG.md")


def cmd_exp(args: argparse.Namespace) -> None:
    """Experiment log: list entries or record a keep / tweak / drop decision."""
    if args.action == "decide":
        if len(args.rest) < 3:
            die('usage: lab.py exp decide <ID> keep|tweak|drop "why"')
        entry = experiments.decide(args.rest[0], args.rest[1], " ".join(args.rest[2:]))
        experiments.render()
        print(f"{entry['id']} {entry['strategy']} ({entry['period']} {entry['timeframe']}): "
              f"{entry['decision']} - {entry['decision_note']}")
        return
    entries = experiments.load()
    if args.strategy:
        entries = [e for e in entries if args.strategy.lower() in e["strategy"].lower()]
    print(f"{'ID':6} {'date':10} {'strategy':20} {'period':12} {'tf':4} {'profit%':>8} {'maxDD%':>7} "
          f"{'sharpe':>6} {'calmar':>6} {'trades':>6}  decision")
    def f(v, spec):
        return format(v, spec) if isinstance(v, (int, float)) else format("-", spec.lstrip("+").split(".")[0] or ">")

    for e in entries[-args.last:]:
        m = e["metrics"]
        print(f"{e['id']:6} {e['date'][:10]:10} {e['strategy']:20} {e['period'] + ('*' if e.get('oos_look') else ''):12} "
              f"{e['timeframe']:4} {f(m.get('profit_pct'), '>+8.1f')} {f(m.get('max_dd_pct'), '>7.1f')} "
              f"{f(m.get('sharpe'), '>6.2f')} {f(m.get('calmar'), '>6.2f')} {f(m.get('trades'), '>6')}  "
              f"{e['kind'][:4]} {e['decision']} {e.get('decision_note', '')}")


def run_hyperopt(strategy: str, timerange: str, timeframe: str, epochs: int, min_trades: int,
                 spaces: list[str] = HYPEROPT_SPACES, seed: int = HYPEROPT_SEED,
                 loss: str = HYPEROPT_LOSS) -> tuple[Path, dict]:
    """One Freqtrade hyperopt run; returns (result file, best epoch)."""
    results_dir = ROOT / "user_data" / "hyperopt_results"
    before = set(results_dir.glob("*.fthypt"))
    freqtrade([
        "hyperopt", *config_args(*exchange_configs(data_exchange()), "backtest.json"),
        "--strategy", strategy, "--timeframe", timeframe, "--timerange", timerange,
        "--hyperopt-loss", loss, "--spaces", *spaces, "--epochs", str(epochs),
        "--random-state", str(seed), "--min-trades", str(min_trades), "--fee", str(STANDARD_FEE),
        "--ignore-missing-spaces", "--disable-param-export", "-j", str(HYPEROPT_JOBS),
    ])
    new = sorted(set(results_dir.glob("*.fthypt")) - before)
    if len(new) != 1:
        die(f"expected one new hyperopt result file, found {len(new)}")
    best = tuning.best_epoch(new[0])
    # Completion is guaranteed by Freqtrade's exit code (freqtrade() stops on failure; an out-of-memory
    # worker crash exits 1). Fewer saved epochs than requested = duplicates Freqtrade skipped.
    best["epochs_requested"] = epochs
    if best["epochs_run"] < epochs:
        print(f"note: {epochs - best['epochs_run']} of {epochs} epochs skipped as duplicate settings")
    return new[0], best


def cmd_hyperopt(args: argparse.Namespace) -> None:
    """Tune a strategy on IN-SAMPLE data, save a tuned `…T` version, compare both."""
    timerange = "-".join(PERIODS["is"])
    if args.timerange:
        if touches_protected(args.timerange):
            die("hyperopt never runs on protected test data (that would make the exam meaningless)")
        timerange = args.timerange
    parent_file = tuning.find_strategy_file(args.strategy)
    name, file_name = tuning.tuned_names(args.strategy, parent_file)
    target = ROOT / "user_data" / "strategies" / file_name
    if target.exists() and not args.force:
        die(f"{target.relative_to(ROOT)} already exists and may have logged results. "
            "Use --force to replace it (the old version stays in git history).")

    say(f"Hyperopt {args.strategy} · {timerange} · {args.timeframe} · {args.epochs} epochs · seed {args.seed}")
    fthypt, best = run_hyperopt(args.strategy, timerange, args.timeframe, args.epochs, args.min_trades,
                                args.spaces, args.seed, args.loss)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    record = {
        "id": f"{stamp}_{args.strategy}", "strategy": args.strategy, "tuned_class": name,
        "timerange": timerange, "timeframe": args.timeframe, "fee": STANDARD_FEE, "loss": args.loss,
        "spaces": args.spaces, "epochs": args.epochs, "seed": args.seed, "min_trades": args.min_trades,
        "result_file": str(fthypt.relative_to(ROOT)), "best": best,
    }
    out = ROOT / "results" / "hyperopt" / args.strategy / f"{record['id']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=1) + "\n")
    exp_id = experiments.log_entry({
        "kind": "hyperopt", "run_id": record["id"], "strategy": args.strategy, "period": "is",
        "timerange": timerange, "timeframe": args.timeframe, "fee": STANDARD_FEE,
        "settings": best["params"], "metrics": best["metrics"],
        "notes": f"{args.loss}, {args.epochs} epochs, seed {args.seed}, best epoch {best['epoch']} "
                 f"(closed-trade metrics) -> {name}",
    })
    meta = {
        "Tuned on": f"in-sample {timerange}, {args.timeframe}, fee {STANDARD_FEE:.2%} per side",
        "Hyperopt": f"{args.loss}, spaces {' '.join(args.spaces)}, {args.epochs} epochs, seed {args.seed}, "
                    f"min trades {args.min_trades}",
        "Best epoch": f"{best['epoch']} of {best['epochs_run']}: {best['metrics']['trades']} trades, "
                      f"{best['metrics']['profit_pct']:+.1f}% (closed-trade numbers)",
        "Record": f"{out.relative_to(ROOT)} (experiment {exp_id})",
    }
    target.write_text(tuning.render_tuned(args.strategy, parent_file.stem, name, best["params"], meta))
    say(f"Best settings: {json.dumps(best['params'])}")
    say(f"Wrote {target.relative_to(ROOT)}; comparing {args.strategy} and {name} on in-sample")
    backtest_run("is", args.timeframe, STANDARD_FEE, None, [args.strategy, name],
                 f"hyperopt check: {args.strategy} vs tuned {name}", allow_protected=False)
    experiments.render()


def cmd_validate(args: argparse.Namespace) -> None:
    """Stage 1: in-sample vs out-of-sample, fee stress and 5m fills, then the verdicts."""
    strategies = args.strategies or discover_strategies()
    say("Stage 1 looks at OUT-OF-SAMPLE data. Every look is logged - do this with final candidates only.")
    is_run = backtest_run("is", args.timeframe, STANDARD_FEE, None, strategies, "stage 1: in-sample", False)
    oos_run = backtest_run("oos", args.timeframe, STANDARD_FEE, None, strategies, "stage 1: out-of-sample", True)
    stress = backtest_run("oos", args.timeframe, STRESS_FEE, None, strategies, "stage 1: fee stress 0.15%", True)
    detail = None if args.no_detail else backtest_run(
        "oos", args.timeframe, STANDARD_FEE, "5m", strategies, "stage 1: 5m intra-candle fills", True)
    md, rows = report.write_stage1(is_run, oos_run, stress, detail)
    report.update_results_doc()
    print("\n" + md.read_text())
    say(f"Stage 1 report: {md.relative_to(ROOT)}")


def wf_backtest(strategies: list[str], timerange: str, timeframe: str, run_dir: Path, run_id: str,
                strategy_path: Path | None = None) -> dict:
    """One walk-forward window backtest -> run summary (kept under user_data/walkforward)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    ft_args = [
        "backtesting", *config_args(*exchange_configs(data_exchange()), "backtest.json"),
        "--strategy-list", BASELINE, *strategies, "--timeframe", timeframe, "--timerange", timerange,
        "--fee", str(STANDARD_FEE), "--cache", "none", "--export", "trades", "--enable-protections",
        "--backtest-directory", str(run_dir.relative_to(ROOT)),
    ]
    if strategy_path:
        ft_args += ["--strategy-path", str(strategy_path.relative_to(ROOT))]
    freqtrade(ft_args)
    summary = run_dir.with_suffix(".json")
    container_python("metrics.py", ["--zip", str(next(run_dir.glob("*.zip")).relative_to(ROOT)), "--out",
                                    str(summary.relative_to(ROOT)), "--run-id", run_id, "--period", "walk-forward"])
    return report.load_run(summary)


def cmd_walkforward(args: argparse.Namespace) -> None:
    """Walk-forward: rolling 3-month test windows (re-tuned before each, or fixed settings)."""
    strategy, mode = args.strategy, ("fixed" if args.fixed else "retuned")
    parent_file = tuning.find_strategy_file(strategy)
    first, last = args.from_date or PERIODS["is"][0], args.to_date or PERIODS["oos"][1]
    windows = tuning.walkforward_windows(first, last, args.train_months, args.test_months, args.test_months)
    if not windows:
        die(f"no complete {args.train_months}+{args.test_months}-month window fits in {first}-{last}")
    if touches_protected(f"{first}-{last}") and not args.allow_holdout:
        die(f"{first}-{last} touches protected test data; walk-forward tunes on its windows. "
            "Only a pre-registered test may do this: add --allow-holdout.")
    custom = (first, last) != (PERIODS["is"][0], PERIODS["oos"][1])
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    # A custom range gets its dates in the id, so stage 2 (which reads the standard runs) never picks it up.
    wf_id = f"{stamp}_{strategy}_{mode}" + (f"_{first}-{last}" if custom else "")
    wf_dir = ROOT / "user_data" / "walkforward" / wf_id
    wf_dir.mkdir(parents=True, exist_ok=True)
    how = ("fixed settings (no tuning), each window scored on its own" if mode == "fixed"
           else f"re-tuned on the {args.train_months} months before each window ({args.epochs} epochs)")
    say(f"Walk-forward {strategy}: {len(windows)} windows of {args.test_months} months, {how}. "
        "Test windows include out-of-sample dates (logged).")

    rows = []
    for w in windows:
        k = w["k"]
        say(f"Window {k + 1}/{len(windows)}: train {w['train']}, test {w['test']}")
        if mode == "fixed":
            train = wf_backtest([strategy], w["train"], args.timeframe, wf_dir / f"train{k}", f"{wf_id}_train{k}")
            train_m, params, cls, path = train["strategies"][strategy], None, strategy, None
            train_profit, train_days, train_trades = train_m["profit_pct"], train_m["days"], train_m["trades"]
        else:
            fthypt, best = run_hyperopt(strategy, w["train"], args.timeframe, args.epochs, args.min_trades)
            fthypt.unlink()  # 50-175 MB each; the best settings are kept in the walk-forward record
            params, cls, path = best["params"], f"{strategy}WF{k}", wf_dir
            (wf_dir / f"{parent_file.stem}_wf{k}.py").write_text(tuning.render_tuned(
                strategy, parent_file.stem, cls, params,
                {"Walk-forward": f"{wf_id} window {k}", "Tuned on": w["train"], "Tested on": w["test"]}))
            train_profit, train_days = best["metrics"]["profit_pct"], best["metrics"]["days"]
            train_trades = best["metrics"]["trades"]
        test = wf_backtest([cls], w["test"], args.timeframe, wf_dir / f"test{k}", f"{wf_id}_test{k}", path)
        m, bh = test["strategies"][cls], test["strategies"][BASELINE]
        rows.append({
            "k": k, "train": w["train"], "test": w["test"], "params": params,
            "train_profit_pct": train_profit, "train_days": train_days, "train_trades": train_trades,
            "test_profit_pct": m["profit_pct"], "test_days": m["days"], "test_max_dd_pct": m["max_dd_pct"],
            "test_trades": m["trades"], "test_sharpe": m["sharpe"], "bh_test_profit_pct": bh["profit_pct"],
        })

    summ = tuning.walkforward_summary(rows)
    record = {"id": wf_id, "strategy": strategy, "mode": mode, "range": f"{first}-{last}", "timeframe": args.timeframe,
              "epochs": None if mode == "fixed" else args.epochs, "min_trades": args.min_trades,
              "train_months": args.train_months, "test_months": args.test_months, "loss": HYPEROPT_LOSS,
              "seed": HYPEROPT_SEED, "fee": STANDARD_FEE, "windows": rows, "summary": summ}
    (ROOT / "results" / "walkforward" / f"{wf_id}.json").write_text(json.dumps(record, indent=1) + "\n")
    eff = summ["wf_efficiency"]
    intro = (f"Fixed settings: `{strategy}` exactly as it would be deployed (nothing to tune), scored on each "
             f"{args.test_months}-month window. 'Train' = the same strategy over the {args.train_months} months before "
             "the window, used for the efficiency ratio."
             if mode == "fixed" else
             f"Re-tuned ({HYPEROPT_LOSS}, {args.epochs} epochs, seed {HYPEROPT_SEED}, min {args.min_trades} trades) on "
             f"each {args.train_months}-month training window, then tested on the next {args.test_months} months it "
             "never saw.")
    md_lines = [
        f"# Walk-forward · {strategy} · {mode} · {args.timeframe} · {first}-{last}", "",
        intro + f" Fee {STANDARD_FEE:.2%} per side.", "",
        "| # | Train | Test | Train profit | Train trades | Test profit | Test max DD | Test trades | Buy & hold (test) |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|",
        *[f"| {r['k']} | {r['train']} | {r['test']} | {r['train_profit_pct']:+.1f}% | {r['train_trades']} | "
          f"{r['test_profit_pct']:+.1f}% | {r['test_max_dd_pct']:.1f}% | {r['test_trades']} | {r['bh_test_profit_pct']:+.1f}% |"
          for r in rows],
        "",
        f"- **Profitable test windows:** {summ['profitable_windows_pct']:.0f}% of {summ['windows']}",
        f"- **Stitched test result:** {summ['stitched_profit_pct']:+.1f}% ({summ['stitched_cagr_pct']:+.1f}% a year) "
        f"vs buy & hold {summ['bh_stitched_profit_pct']:+.1f}% over the same windows",
        f"- **Walk-forward efficiency:** " + ("n/a (training windows were not profitable on average)" if eff is None
                                             else f"{eff:.2f} (test yearly return ÷ average training yearly return "
                                                  f"{summ['mean_train_yearly_pct']:+.1f}%)"),
        f"- **Worst test-window drawdown:** {summ['worst_window_dd_pct']:.1f}%", "",
    ]
    (ROOT / "results" / "walkforward" / f"{wf_id}.md").write_text("\n".join(md_lines))
    experiments.log_entry({
        "kind": "walkforward", "run_id": wf_id, "strategy": strategy, "period": f"walk-forward ({mode})",
        "timerange": f"{windows[0]['test'].split('-')[0]}-{windows[-1]['test'].split('-')[1]}",
        "timeframe": args.timeframe, "fee": STANDARD_FEE,
        "oos_look": bool(touches_protected(f"{windows[0]['train'].split('-')[0]}-{windows[-1]['test'].split('-')[1]}")),
        "settings": {"mode": mode, "epochs": record["epochs"]},
        "metrics": {"profit_pct": summ["stitched_profit_pct"], "max_dd_pct": summ["worst_window_dd_pct"],
                    "trades": summ["total_test_trades"], "profitable_windows_pct": summ["profitable_windows_pct"],
                    "wf_efficiency": eff},
        "notes": f"{mode}: {summ['profitable_windows_pct']:.0f}% windows profitable, efficiency "
                 + ("n/a" if eff is None else f"{eff:.2f}"),
    })
    experiments.render()
    print("\n".join(md_lines))
    say(f"Walk-forward report: results/walkforward/{wf_id}.md")


def latest_walkforward(strategy: str, mode: str) -> tuple[str | None, dict | None]:
    files = sorted((ROOT / "results" / "walkforward").glob(f"*_{strategy}_{mode}.json"))
    if not files:
        return None, None
    data = json.loads(files[-1].read_text())
    return data["id"], data["summary"]


def cmd_stage2(args: argparse.Namespace) -> None:
    """Stage 2: walk-forward results + all six regime windows -> promotion verdicts."""
    strategies = args.strategies
    if not strategies:
        s1 = ROOT / "results" / "leaderboards" / "stage1_1h.json"
        if not s1.exists():
            die("run lab.py validate first (or pass --strategies)")
        strategies = [k for k, v in json.loads(s1.read_text())["results"].items() if v in ("PASS", "REVIEW")]
        if not strategies:
            die("no strategy passed stage 1 - nothing to promote")
    windows = ["bull-is", "bear-is", "sideways-is", "bull-oos", "bear-oos", "sideways-oos"]
    regime_dd = {s: {} for s in strategies}
    regime_profit = {s: {} for s in strategies}
    for window in windows:
        run_summary = backtest_run(window, "1h", STANDARD_FEE, None, strategies, f"stage 2: regime {window}", True)
        for s in strategies:
            regime_dd[s][window] = run_summary["strategies"][s]["max_dd_pct"]
            regime_profit[s][window] = run_summary["strategies"][s]["profit_pct"]
    results = []
    for s in strategies:
        # The thing walk-forwarded must match the thing deployed: a tuned …T version is judged by
        # re-tuning its parent in every window; an untuned strategy by its fixed settings.
        base, mode = (s[:-1], "retuned") if s.endswith("T") else (s, "fixed")
        wf_id, wf = latest_walkforward(base, mode)
        results.append({"strategy": s, "wf_base": base, "wf_mode": mode, "wf_id": wf_id, "wf": wf,
                        "regime_dd": regime_dd[s], "regime_profit": regime_profit[s]})
    md = report.write_stage2(results)
    report.update_results_doc()
    print("\n" + md.read_text())


def bots_compose() -> list[str]:
    return [*COMPOSE, "-f", str(ROOT / "docker-compose.bots.yml")]


def ui_login() -> tuple[str, str]:
    env_path = ROOT / ".env"
    if not env_path.exists():
        die(".env is missing - run: python3 scripts/lab.py setup")
    env = safety_check.parse_env_file(env_path)
    user, password = env.get("FREQTRADE__API_SERVER__USERNAME"), env.get("FREQTRADE__API_SERVER__PASSWORD")
    if not user or not password or len(env.get("FREQTRADE__API_SERVER__JWT_SECRET_KEY", "")) < 32:
        die(".env needs FREQTRADE__API_SERVER__USERNAME, __PASSWORD and a 32+ character __JWT_SECRET_KEY "
            "(delete .env and run setup to regenerate)")
    return user, password


def print_bot_status(selected: list[dict]) -> bool:
    """Table of every bot's live state. Returns False if anything is wrong (loudly)."""
    user, password = ui_login()
    rows = [bots.bot_status(b, user, password) for b in selected]
    print(f"\n{'bot':14} {'strategy':12} {'role':10} {'FreqUI':22} {'state':8} {'dry_run':7} "
          f"{'open':>4} {'closed':>6} {'closed P/L':>10} {'all P/L':>8}  since")
    ok = True
    for r in rows:
        url = f"http://127.0.0.1:{r['port']}"
        if not r.get("reachable") or "error" in r:
            ok = False
            print(f"{r['name']:14} {r['strategy']:12} {r['status']:10} {url:22} DOWN     - {r.get('error', '')}")
            continue
        print(f"{r['name']:14} {r['running_strategy']:12} {r['status']:10} {url:22} {str(r['state']):8} "
              f"{str(r['dry_run']):7} {r['open_trades']:>4} {r['closed_trades']:>6} "
              f"{r['profit_closed_pct']:>+9.2f}% {r['profit_all_pct']:>+7.2f}%  {r['first_trade']}")
        if r["dry_run"] is not True:
            ok = False
            print("!" * 72 + f"\n!!  {r['name']} REPORTS dry_run={r['dry_run']} - STOP IT NOW: "
                  "python3 scripts/lab.py bots down\n" + "!" * 72)
    return ok


def cmd_bots(args: argparse.Namespace) -> None:
    """Paper-trading bots: generate | up | down | status | logs (one dry-run container per bot)."""
    registry = bots.load_registry()
    selected = [b for b in registry if not args.names or b["name"] in args.names]
    if args.names and len(selected) != len(set(args.names)):
        die(f"unknown bot name in {args.names}; known: {[b['name'] for b in registry]}")
    services = [f"bot-{b['name']}" for b in selected]

    if args.action == "generate":
        for path in bots.write_all(registry):
            print(f"wrote {path.relative_to(ROOT)}")
        safety_gate()
    elif args.action == "up":
        bots.write_all(registry)
        safety_gate()
        ui_login()
        say(f"Starting {len(services)} dry-run bot(s): {', '.join(services)}")
        run([*bots_compose(), "up", "-d", *services])
        say("Waiting for the bots' APIs (first start downloads ~600 candles per pair)")
        deadline = time.time() + args.wait
        pending = list(selected)
        while pending and time.time() < deadline:
            for b in list(pending):
                try:
                    bots.api_get(b["port"], "ping", timeout=2)
                    pending.remove(b)
                except OSError:
                    pass
            time.sleep(3)
        if pending:
            print(f"Not answering yet: {[b['name'] for b in pending]} - check: python3 scripts/lab.py bots logs")
        print_bot_status(selected)
        say("FreqUI: open the URLs above, log in with the username/password from .env "
            "(FREQTRADE__API_SERVER__USERNAME / __PASSWORD)")
    elif args.action == "down":
        say(f"Stopping {', '.join(services)}")
        run([*bots_compose(), "stop", *services])
        run([*bots_compose(), "rm", "-f", *services])
    elif args.action == "status":
        run([*bots_compose(), "ps", *services])
        if not print_bot_status(selected):
            sys.exit(1)
    elif args.action == "logs":
        run([*bots_compose(), "logs", "--tail", str(args.tail), *services])


def cmd_select(args: argparse.Namespace) -> None:
    """Round 2: apply the pre-registered dev rule to the latest dev run -> exam candidates."""
    run_summary = report.latest(report.all_runs(), "dev", "1h")
    if run_summary is None:
        die("no dev run yet: python3 scripts/lab.py backtest --period dev")
    md, selected = report.write_round2_selection(run_summary)
    print(md.read_text())


def cmd_exam(args: argparse.Namespace) -> None:
    """Round 2 exam on the protected holdout: normal fee, stress fee, 5m fills -> verdicts. Run ONCE."""
    saved = ROOT / "results" / "leaderboards" / "round2_selection.json"
    if not saved.exists():
        die("run lab.py select first and commit the candidate list before the exam")
    candidates = json.loads(saved.read_text())["selected"]
    if not candidates:
        die("no exam candidates were selected")
    if args.strategies and sorted(args.strategies) != sorted(candidates):
        die(f"--strategies must match the frozen candidate list {candidates}")
    say(f"Round 2 EXAM on protected data ({'-'.join(PERIODS['holdout'])}) for {', '.join(candidates)}")
    exam_run = backtest_run("holdout", "1h", STANDARD_FEE, None, candidates, "round 2 exam", True)
    stress = backtest_run("holdout", "1h", STRESS_FEE, None, candidates, "round 2 exam: fee stress 0.15%", True)
    detail = backtest_run("holdout", "1h", STANDARD_FEE, "5m", candidates, "round 2 exam: 5m fills", True) \
        if args.detail else None
    md, _ = report.write_exam(exam_run, stress, detail)
    report.update_results_doc()
    print("\n" + md.read_text())


def robust_backtest(strategies: list[str], timerange: str, run_dir: Path, run_id: str,
                    strategy_path: Path, pairs: list[str] | None = None) -> dict:
    """One robustness backtest (dev data, 0.1% fee) -> run summary, kept in the throwaway folder."""
    if set(pairs or []) & set(rules.ROUND5_EXAM_COINS):
        die("the robustness check never trades Round 5 exam coins")
    run_dir.mkdir(parents=True, exist_ok=True)
    ft_args = [
        "backtesting", *config_args(*exchange_configs(data_exchange()), "backtest.json"),
        "--strategy-list", *strategies, *strategy_path_args(strategy_path),
        "--timeframe", "1h", "--timerange", timerange, "--fee", str(STANDARD_FEE), "--cache", "none",
        "--export", "trades", "--enable-protections", "--backtest-directory", str(run_dir.relative_to(ROOT)),
    ]
    if pairs:
        ft_args += ["--pairs", *pairs]
    freqtrade(ft_args)
    summary = run_dir.with_suffix(".json")
    container_python("metrics.py", ["--zip", str(next(run_dir.glob("*.zip")).relative_to(ROOT)), "--out",
                                    str(summary.relative_to(ROOT)), "--run-id", run_id, "--period", "dev"])
    return report.load_run(summary)


def inspect_strategy(name: str) -> dict:
    """What the robustness check needs to know about a strategy (scripts/inspect_strategy.py)."""
    out = run([*COMPOSE, "run", "--rm", "--entrypoint", "python", "freqtrade",
               "scripts/inspect_strategy.py", name], quiet=True)
    json_line = next((line for line in reversed(out.stdout.splitlines()) if line.startswith("{")), None)
    if out.returncode != 0 or json_line is None:
        die(f"could not inspect {name}:\n{out.stdout}\n{out.stderr}")
    return json.loads(json_line)


def cmd_robustness(args: argparse.Namespace) -> None:
    """Robustness check on dev data: timing, nearby settings, leave-one-coin-out, lucky trades."""
    name = args.strategy
    _, timerange = resolve_period("dev")
    safety_gate()
    info = inspect_strategy(name)
    wanted, skip = set(args.checks), set(info["skip"])
    pairs = json.loads((ROOT / CONFIGS / "base.json").read_text())["exchange"]["pair_whitelist"]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    rid = f"{stamp}_{name}"
    folder = ROOT / "user_data" / "walkforward" / f"robust_{rid}"
    folder.mkdir(parents=True, exist_ok=True)
    r1 = robustness.timing_variants(info) if "R1" in wanted and "R1" not in skip else {}
    r2 = robustness.setting_variants(info) if "R2" in wanted and "R2" not in skip else {}
    r3 = robustness.coin_variants(info, pairs) if "R3" in wanted and "R3" not in skip else []
    sources = {**r1, **r2, **{r["class"]: r["source"] for r in r3 if r["class"]}}
    for cls, src in sources.items():
        (folder / f"{cls.lower()}.py").write_text(src)
    say(f"Robustness {name}: {len(r1)} timing, {len(r2)} settings, {len(r3)} leave-one-coin-out variants "
        f"on dev {timerange}")

    bias_failed = []
    if sources and not args.skip_bias:
        say(f"Bias-checking the {len(sources)} generated variants")
        _, _, bias_failed = run_bias_checks(list(sources), strategy_path=folder, save_lookahead_csv=False)

    main = robust_backtest([name, *r1, *r2], timerange, folder / "main", f"{rid}_main", folder)
    original = main["strategies"][name]
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def label(cls: str) -> str:
        tail = cls.split("_R", 1)[1][2:]
        if tail.startswith("delay"):
            return f"acting {tail[5:]} day(s) late"
        if tail.startswith("h") and tail[1:].isdigit():
            return f"{tail[1:]}:00 candle" + (" (original)" if [int(tail[1:])] == info["rebalance"] else "")
        if tail.startswith("d") and "h" in tail:
            day, hour = tail[1:].split("h")
            return f"{day_names[int(day)]} {hour}:00 candle" + (" (original)" if [int(day), int(hour)] == info["rebalance"] else "")
        if tail.startswith("late"):
            return f"signals {tail[4:]} candle(s) late"
        key, _, value = tail.rpartition("_")
        return f"{key} = {value.replace('p', '.').replace('m', '-')}"

    def row(m: dict, text: str) -> dict:
        return {"label": text, **{k: m[k] for k in ("profit_pct", "max_dd_pct", "calmar", "trades")}}

    rows = {"R1": [row(main["strategies"][c], label(c)) for c in r1],
            "R2": [row(main["strategies"][c], label(c)) for c in r2], "R3": []}
    for run_ in r3:
        coin = run_["left_out"].split("/")[0]
        summary = robust_backtest([run_["class"] or name], timerange, folder / f"no_{coin}", f"{rid}_no_{coin}",
                                  folder, pairs=run_["pairs"])
        rows["R3"].append(row(summary["strategies"][run_["class"] or name], f"without {coin}"))

    checks = {}
    for check, all_profitable in (("R1", False), ("R2", False), ("R3", True)):
        if check not in wanted:
            continue
        if check in skip:
            checks[check] = {"verdict": "SKIPPED", "detail": "does not apply to this strategy (declared skip)"}
        else:
            verdict, detail = rules.variants_verdict(original, rows[check], all_profitable)
            checks[check] = {"verdict": verdict, "detail": detail}
    if "R4" in wanted:
        verdict, detail = rules.concentration_verdict(original["profit_abs_total"], original["best_trades_profit_abs"])
        checks["R4"] = {"verdict": verdict, "detail": detail}
    if bias_failed:  # a generated variant peeks ahead: the check itself is broken, never trust it
        for c in checks.values():
            if c["verdict"] == "PASS":
                c.update(verdict="FAIL", detail=c["detail"] + " - but generated variants failed the bias check")
    overall = rules.robustness_overall({k: v["verdict"] for k, v in checks.items()})

    record = {"id": rid, "strategy": name, "timerange": timerange, "info": info, "overall": overall,
              "original": {k: original[k] for k in ("profit_pct", "max_dd_pct", "calmar", "trades",
                                                    "profit_abs_total", "best_trades_profit_abs")},
              "checks": checks, "variants": rows,
              "bias": {"checked": 0 if args.skip_bias else len(sources), "failed": bias_failed}}
    out_dir = ROOT / "results" / "robustness"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{rid}.json").write_text(json.dumps(record, indent=1) + "\n")
    md = out_dir / f"{rid}.md"
    md.write_text(robustness.render_report(record))
    experiments.log_entry({
        "kind": "robustness", "run_id": rid, "strategy": name, "period": "dev", "timerange": timerange,
        "timeframe": "1h", "fee": STANDARD_FEE, "settings": {"checks": sorted(wanted)},
        "metrics": {k: original[k] for k in ("profit_pct", "max_dd_pct", "calmar", "trades")},
        "notes": f"robustness {overall}: " + ", ".join(f"{k} {v['verdict']}" for k, v in checks.items()),
    })
    experiments.render()
    print("\n" + md.read_text())


def latest_robustness(name: str) -> dict | None:
    files = sorted((ROOT / "results" / "robustness").glob(f"*_{name}.json"))
    return json.loads(files[-1].read_text()) if files else None


def cmd_round4(args: argparse.Namespace) -> None:
    """Round 4 (momentum at lower exposure): pick one version on dev, then the one-time 2019-20 exam."""
    boards = ROOT / "results" / "leaderboards"
    saved = boards / "round4_selection.json"
    if args.action == "select":
        runs = [r for r in report.all_runs() if r["period"] == "dev" and r["timeframe"] == "1h"
                and abs((r.get("fee") or 0) - STANDARD_FEE) < 1e-9 and not r.get("timeframe_detail")
                and all(c in r["strategies"] for c in rules.ROUND4_CANDIDATES)]
        if not runs:
            die("no dev run with both Round 4 versions: lab.py backtest --period dev --strategies "
                + " ".join(rules.ROUND4_CANDIDATES))
        dev_run = max(runs, key=lambda r: r["run_id"])
        robust = {c: latest_robustness(c) for c in rules.ROUND4_CANDIDATES}
        pick, lines = rules.select_round4(dev_run["strategies"], report.load_bias(),
                                          {c: (r or {}).get("overall") for c, r in robust.items()})
        s = rules.ROUND4_SELECT
        md = boards / "round4_selection.md"
        md.write_text("\n".join([
            "# Round 4 · dev selection (pre-registered rule)", "",
            f"Dev run `{dev_run['run_id']}` ({dev_run['timerange']}, 1h, fee 0.10%). Rule: max drawdown <= "
            f"{s['max_dd_pct']:g}%, profit > 0, profit factor >= {s['min_profit_factor']:g}, >= {s['min_trades']} "
            f"trades, bias checks passed, robustness check {s['robustness']}; best dev Calmar wins.", "",
            "Robustness reports: " + (", ".join(f"`{r['id']}` ({r['overall']})" for r in robust.values() if r)
                                      or "none"), "",
            *lines, "", f"**Exam pick:** {f'`{pick}`' if pick else 'none - the idea is dropped, no exam'}", "",
        ]))
        saved.write_text(json.dumps({"dev_run": dev_run["run_id"], "pick": pick,
                                     "robustness": {c: (r or {}).get("id") for c, r in robust.items()}},
                                    indent=1) + "\n")
        print(md.read_text())
        return

    # exam: the frozen pick without SOL (as robustness check R3) + 4-coin buy & hold at 25% each
    if not saved.exists() or not json.loads(saved.read_text())["pick"]:
        die("no frozen pick: run lab.py round4 select and commit it before the exam")
    pick = json.loads(saved.read_text())["pick"]
    period, stem, title = "exam2019", "exam_round4", "Round 4 exam · 2019-01 → 2021-01 · 4 coins · 1h"
    if args.smoke:  # rehearse the exact pipeline on dev data; nothing protected is touched
        period, stem, title = "20240101-20250101", "exam_round4_smoke", "Round 4 exam REHEARSAL on dev data (2024)"
    elif (boards / f"{stem}.json").exists():
        die("the Round 4 exam has already run - it runs once (results/leaderboards/exam_round4.md)")
    whitelist = json.loads((ROOT / CONFIGS / "base.json").read_text())["exchange"]["pair_whitelist"]
    variant = next(v for v in robustness.coin_variants(inspect_strategy(pick), whitelist)
                   if v["left_out"] == "SOL/USDT")
    folder = ROOT / "user_data" / "walkforward" / f"{stem}_{datetime.now(timezone.utc):%Y%m%d-%H%M%S}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{variant['class'].lower()}.py").write_text(variant["source"])
    say(f"Round 4 {'REHEARSAL' if args.smoke else 'EXAM'}: {pick} on {', '.join(variant['pairs'])} "
        f"({resolve_period(period)[1]}), with buy & hold of the same coins")
    common = dict(pairs=variant["pairs"], strategy_path=folder, max_open_trades=len(variant["pairs"]))
    note = "round 4 exam" + (" rehearsal (dev data)" if args.smoke else "")
    exam_run = backtest_run(period, "1h", STANDARD_FEE, None, [variant["class"]], note, True, **common)
    stress = backtest_run(period, "1h", STRESS_FEE, None, [variant["class"]], note + ": fee stress 0.15%", True,
                          **common)
    md, _ = report.write_exam(exam_run, stress, None, title=title, stem=stem, exam_rules=rules.ROUND4_EXAM,
                              prefix="H", rules_ref="docs/research/momentum-exposure-preregistration.md "
                              "(numbers in scripts/rules.py → ROUND4_EXAM)",
                              bias_names={variant["class"]: pick})
    print("\n" + md.read_text())


def cmd_round5(args: argparse.Namespace) -> None:
    """Round 5 (TrendBlend): pick one version on dev, then the one-time exam on 9 never-traded coins."""
    boards = ROOT / "results" / "leaderboards"
    saved = boards / "round5_selection.json"
    versions = [s for s in discover_strategies() if s.startswith(rules.ROUND5_PREFIX)]
    if len(versions) > rules.ROUND5_MAX_VERSIONS:
        die(f"{len(versions)} TrendBlend versions exist ({', '.join(versions)}); the limit is {rules.ROUND5_MAX_VERSIONS}")
    if args.action == "select":
        runs = [r for r in report.all_runs() if r["period"] == "dev" and r["timeframe"] == "1h"
                and abs((r.get("fee") or 0) - STANDARD_FEE) < 1e-9 and not r.get("timeframe_detail")
                and any(n.startswith(rules.ROUND5_PREFIX) for n in r["strategies"])]
        if not runs:
            die("no dev run with a TrendBlend version: lab.py backtest --period dev --strategies <version>")
        dev_run = max(runs, key=lambda r: r["run_id"])
        candidates = [n for n in dev_run["strategies"] if n.startswith(rules.ROUND5_PREFIX)]
        robust = {c: latest_robustness(c) for c in candidates}
        pick, lines = rules.select_round5(dev_run["strategies"], report.load_bias(),
                                          {c: (r or {}).get("overall") for c, r in robust.items()})
        s = rules.ROUND5_SELECT
        md = boards / "round5_selection.md"
        md.write_text("\n".join([
            "# Round 5 · dev selection (pre-registered rule)", "",
            f"Dev run `{dev_run['run_id']}` ({dev_run['timerange']}, 1h, fee 0.10%). Rule: max drawdown <= "
            f"{s['max_dd_pct']:g}%, profit > 0, profit factor >= {s['min_profit_factor']:g}, >= {s['min_trades']} "
            f"trades, Calmar above buy & hold's, bias checks passed, robustness check {s['robustness']}; "
            "best dev Calmar wins.", "",
            f"Versions built ({len(versions)} of max {rules.ROUND5_MAX_VERSIONS}): "
            + ", ".join(f"`{v}`" for v in versions) + ". Versions not in this run were dropped earlier "
            "(see docs/research/trend-blend-preregistration.md).", "",
            "Robustness reports: " + (", ".join(f"`{r['id']}` ({r['overall']})" for r in robust.values() if r)
                                      or "none"), "",
            *lines, "", f"**Exam pick:** {f'`{pick}`' if pick else 'none - the idea is dropped, no exam'}", "",
        ]))
        saved.write_text(json.dumps({"dev_run": dev_run["run_id"], "pick": pick, "versions": versions,
                                     "robustness": {c: (r or {}).get("id") for c, r in robust.items()}},
                                    indent=1) + "\n")
        print(md.read_text())
        return

    if not saved.exists() or not json.loads(saved.read_text())["pick"]:
        die("no frozen pick: run lab.py round5 select and commit it before the exam")
    pick = json.loads(saved.read_text())["pick"]
    period, stem, pairs = "exam5", "exam_round5", list(rules.ROUND5_EXAM_COINS)
    title = "Round 5 exam · 2019-01 → 2023-10 · 9 coins never traded in this lab · 1h"
    if args.smoke:  # rehearse the exact pipeline on our own coins and dev dates; nothing protected is touched
        period, stem = "20240101-20250101", "exam_round5_smoke"
        pairs = json.loads((ROOT / CONFIGS / "base.json").read_text())["exchange"]["pair_whitelist"]
        title = "Round 5 exam REHEARSAL on dev data (our 5 coins, 2024)"
    elif (boards / f"{stem}.json").exists():
        die("the Round 5 exam has already run - it runs once (results/leaderboards/exam_round5.md)")
    say(f"Round 5 {'REHEARSAL' if args.smoke else 'EXAM'}: {pick} on {', '.join(pairs)} "
        f"({resolve_period(period)[1]}), with buy & hold of the same coins")
    common = dict(pairs=pairs, max_open_trades=len(pairs))
    note = "round 5 exam" + (" rehearsal (dev data)" if args.smoke else "")
    exam_run = backtest_run(period, "1h", STANDARD_FEE, None, [pick], note, True, **common)
    stress = backtest_run(period, "1h", STRESS_FEE, None, [pick], note + ": fee stress 0.15%", True, **common)
    md, _ = report.write_exam(exam_run, stress, None, title=title, stem=stem, exam_rules=rules.ROUND5_EXAM,
                              prefix="E", rules_ref="docs/research/trend-blend-preregistration.md "
                              "(numbers in scripts/rules.py → ROUND5_EXAM)", exam_fn=rules.exam_round5)
    print("\n" + md.read_text())


def cmd_ft(args: argparse.Namespace) -> None:
    """Run any raw Freqtrade command in the container (safety check first)."""
    if not args.ft_args:
        die("usage: lab.py ft -- <freqtrade command> [options]")
    ft_args = args.ft_args[1:] if args.ft_args[0] == "--" else args.ft_args
    freqtrade(ft_args)


# --------------------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lab.py", description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>", required=True)

    def add(name: str, func, **kwargs) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=func.__doc__.splitlines()[0], description=func.__doc__, **kwargs)
        p.set_defaults(func=func)
        return p

    add("setup", cmd_setup)
    add("safety", cmd_safety)
    p = add("test", cmd_test)
    p.add_argument("--host-only", action="store_true", help="skip the container tests (no Docker needed)")
    p = add("show-config", cmd_show_config)
    p.add_argument("configs", nargs="*", default=["backtest.json"],
                   help="override files in user_data/configs layered on base.json (default: backtest.json)")
    p = add("download", cmd_download)
    p.add_argument("--exchange", choices=EXCHANGES, default="binance",
                   help="data source (default: binance; fall back to bybit if it is blocked)")
    p.add_argument("--start", help=f"yyyymmdd (default {DATA_START}); earlier dates extend existing files")
    p.add_argument("--timeframes", nargs="+", help=f"default: {' '.join(TIMEFRAMES)}")
    p.add_argument("--pairs", nargs="+", help="default: the whitelist in base.json")
    p = add("data-check", cmd_data_check)
    p.add_argument("--exchange", choices=EXCHANGES, help="default: the exchange we have data for")
    p.add_argument("--start", help=f"data must start by this date (default {DATA_START})")
    p.add_argument("--timeframes", nargs="+", help=f"default: {' '.join(TIMEFRAMES)}")
    p.add_argument("--pairs", nargs="+", help="default: the whitelist in base.json")
    p = add("regimes", cmd_regimes)
    p.add_argument("--days", type=int, default=90, help="window length in days (default: 90)")
    p = add("check-bias", cmd_check_bias)
    p.add_argument("--strategies", nargs="+", help="default: every strategy in user_data/strategies")
    p.add_argument("--skip-lookahead", action="store_true")
    p.add_argument("--skip-recursive", action="store_true")
    p = add("backtest", cmd_backtest)
    p.add_argument("--period", default="is",
                   help="is (default), oos, full, a regime window like bull-is, or yyyymmdd-yyyymmdd")
    p.add_argument("--timeframe", default="1h", choices=["15m", "1h", "4h"])
    p.add_argument("--strategies", nargs="+", help="default: all (buy & hold is always added)")
    p.add_argument("--fee", type=float, default=STANDARD_FEE, help="per side, default 0.001 (0.1%%)")
    p.add_argument("--detail", choices=["5m"], help="simulate fills inside each candle with 5m data")
    p.add_argument("--notes", default="", help="free text stored with the result and the experiment log")
    p.add_argument("--allow-holdout", action="store_true",
                   help="allow periods that touch protected test data (the pre-registered exam only)")
    p.add_argument("--allow-oos", dest="allow_holdout", action="store_true", help=argparse.SUPPRESS)
    p = add("report", cmd_report)
    p.add_argument("--recompute", action="store_true", help="re-read the raw result zips (needs Docker)")
    p = add("exp", cmd_exp)
    p.add_argument("action", choices=["list", "decide"])
    p.add_argument("rest", nargs="*", help='decide: <ID> keep|tweak|drop "why"')
    p.add_argument("--strategy", help="list: filter by strategy name")
    p.add_argument("--last", type=int, default=40, help="list: show the last N entries")
    p = add("hyperopt", cmd_hyperopt)
    p.add_argument("strategy")
    p.add_argument("--epochs", type=int, default=HYPEROPT_EPOCHS)
    p.add_argument("--seed", type=int, default=HYPEROPT_SEED)
    p.add_argument("--loss", default=HYPEROPT_LOSS)
    p.add_argument("--spaces", nargs="+", default=HYPEROPT_SPACES)
    p.add_argument("--min-trades", type=int, default=HYPEROPT_MIN_TRADES)
    p.add_argument("--timeframe", default="1h", choices=["15m", "1h", "4h"])
    p.add_argument("--timerange", help="default: the whole in-sample period (out-of-sample is refused)")
    p.add_argument("--force", action="store_true", help="replace an existing tuned …T file")
    p = add("validate", cmd_validate)
    p.add_argument("--strategies", nargs="+", help="default: all")
    p.add_argument("--timeframe", default="1h", choices=["15m", "1h", "4h"])
    p.add_argument("--no-detail", action="store_true", help="skip the 5m intra-candle run")
    p = add("walkforward", cmd_walkforward)
    p.add_argument("strategy", help="re-tuned mode: the untuned parent; fixed mode: the strategy as deployed")
    p.add_argument("--fixed", action="store_true", help="no tuning: score the strategy's own settings per window")
    p.add_argument("--epochs", type=int, default=150)
    p.add_argument("--min-trades", type=int, default=25, help="per 12-month training window")
    p.add_argument("--train-months", type=int, default=12)
    p.add_argument("--test-months", type=int, default=3)
    p.add_argument("--timeframe", default="1h", choices=["15m", "1h", "4h"])
    p.add_argument("--from", dest="from_date", help="first training day yyyymmdd (default: in-sample start)")
    p.add_argument("--to", dest="to_date", help="last test day yyyymmdd, exclusive (default: out-of-sample end)")
    p.add_argument("--allow-holdout", action="store_true", help="allow ranges that touch protected test data")
    p = add("stage2", cmd_stage2)
    p.add_argument("--strategies", nargs="+", help="default: everything that passed stage 1")
    p = add("robustness", cmd_robustness)
    p.add_argument("strategy")
    p.add_argument("--checks", nargs="+", default=["R1", "R2", "R3", "R4"], choices=["R1", "R2", "R3", "R4"])
    p.add_argument("--skip-bias", action="store_true", help="skip bias checks of generated variants (not for real use)")
    p = add("select", cmd_select)
    p = add("exam", cmd_exam)
    p.add_argument("--strategies", nargs="+", help="optional; must equal the frozen candidate list")
    p.add_argument("--detail", action="store_true",
                   help="also run 5m intra-candle fills (needs 5m data for the holdout period)")
    p = add("round4", cmd_round4)
    p.add_argument("action", choices=["select", "exam"])
    p.add_argument("--smoke", action="store_true",
                   help="exam: rehearse the whole pipeline on 2024 dev data instead (touches nothing protected)")
    p = add("round5", cmd_round5)
    p.add_argument("action", choices=["select", "exam"])
    p.add_argument("--smoke", action="store_true",
                   help="exam: rehearse the whole pipeline on our 5 coins and 2024 dev data (touches nothing protected)")
    p = add("bots", cmd_bots)
    p.add_argument("action", choices=["generate", "up", "down", "status", "logs"])
    p.add_argument("names", nargs="*", help="bot names from bots.json (default: all)")
    p.add_argument("--tail", type=int, default=50, help="logs: lines per bot")
    p.add_argument("--wait", type=int, default=240, help="up: seconds to wait for the APIs")
    p = add("ft", cmd_ft)
    p.add_argument("ft_args", nargs=argparse.REMAINDER, help="-- <freqtrade args>")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    os.chdir(ROOT)
    args.func(args)


if __name__ == "__main__":
    main()
