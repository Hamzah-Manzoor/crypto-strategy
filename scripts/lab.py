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
import math
import os
import re
import secrets
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import safety_check  # noqa: E402

COMPOSE = ["docker", "compose", "--project-directory", str(ROOT), "-f", str(ROOT / "docker-compose.yml")]
CONFIGS = "user_data/configs"  # same relative path on the host and in the container

EXCHANGES = ["binance", "bybit", "okx"]  # data sources, in order of preference
TIMEFRAMES = ["5m", "15m", "1h", "4h"]   # 1h main; 15m/4h alternatives; 5m only for --timeframe-detail
DATA_START = "20230501"                  # 5 months of warm-up before the in-sample period:
                                         # 600 startup candles on 4h = 100 days must fit
REGIME_DATA_START = "20220101"           # extra BTC daily history so a 200-day average exists from day one

# Test periods (see docs/TESTING_METHODOLOGY.md). Tune on "is" only; "oos" is for checking.
PERIODS = {
    "is": ("20231001", "20251001"),
    "oos": ("20251001", "20261001"),
}

# Bias checks (lab.py check-bias): all inside the in-sample period.
BIAS_TIMEFRAME = "1h"
LOOKAHEAD_TIMERANGE = "20240101-20240701"   # 6 months, all pairs
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
    """Run the unit tests."""
    result = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], check=False)
    sys.exit(result.returncode)


def cmd_show_config(args: argparse.Namespace) -> None:
    """Show the merged config Freqtrade sees (secrets redacted)."""
    freqtrade(["show-config", *config_args(*args.configs)])


def cmd_download(args: argparse.Namespace) -> None:
    """Download candles for all pairs and timeframes (re-run any time to top up)."""
    exchange = args.exchange
    cfg = config_args(*exchange_configs(exchange))

    say(f"Downloading {', '.join(TIMEFRAMES)} candles from {exchange}, starting {DATA_START}")
    # Pass 1 (--prepend) extends existing files back to DATA_START; pass 2 adds new candles.
    # On a fresh download pass 1 does all the work and pass 2 has nothing left to fetch.
    grid = freqtrade(["download-data", *cfg, "--timeframes", *TIMEFRAMES, "--prepend",
                      "--timerange", f"{DATA_START}-"], check=False)
    if grid.returncode == 0:
        grid = freqtrade(["download-data", *cfg, "--timeframes", *TIMEFRAMES,
                          "--timerange", f"{DATA_START}-"], check=False)

    say(f"Downloading BTC/USDT daily candles from {REGIME_DATA_START} (for market-regime labels)")
    extra = freqtrade(["download-data", *cfg, "--pairs", "BTC/USDT", "--timeframes", "1d",
                       "--timerange", f"{REGIME_DATA_START}-"], check=False)

    if grid.returncode or extra.returncode:
        fallback = EXCHANGES[EXCHANGES.index(exchange) + 1:]
        hint = f" Try another source: python3 scripts/lab.py download --exchange {fallback[0]}" if fallback else ""
        die(f"download from {exchange} failed (region block or network problem?).{hint} "
            "See docs/SETUP.md > Troubleshooting.")

    say("Checking the downloaded data")
    cmd_data_check(argparse.Namespace(exchange=exchange))


def cmd_data_check(args: argparse.Namespace) -> None:
    """Check coverage, gaps and bad candles; writes results/checks/data_check.md."""
    exchange = args.exchange or data_exchange()
    result = container_python("data_check.py", [
        "--exchange", exchange, "--start", DATA_START, "--timeframes", *TIMEFRAMES,
        "--out", "results/checks/data_check.md",
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


def recursive_check(strategy: str) -> tuple[str, list[str]]:
    """Run recursive-analysis for one strategy; return (verdict, markdown lines)."""
    result = freqtrade([
        "recursive-analysis", *config_args("backtest.json"), "--strategy", strategy,
        "-i", BIAS_TIMEFRAME, "-p", RECURSIVE_PAIR, "--timerange", RECURSIVE_TIMERANGE,
        "--startup-candle", *RECURSIVE_STARTUPS,
    ], check=False, tee=True)
    startup = strategy_startup(strategy)
    md = [f"### {strategy} (startup_candle_count = {startup})", ""]
    header, rows = parse_rich_table(result.stdout, "Recursive Analysis")
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


def cmd_check_bias(args: argparse.Namespace) -> None:
    """Lookahead + recursive analysis on strategies; writes results/checks/bias_check.md."""
    strategies = args.strategies or discover_strategies()
    report = [
        "# Bias checks", "",
        f"Freqtrade 2026.9, timeframe {BIAS_TIMEFRAME}. Strategies: {', '.join(strategies)}.", "",
    ]
    failed = []

    if not args.skip_lookahead:
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
                continue
            say(f"Lookahead analysis: {name}")
            tmp_csv = ROOT / "user_data" / "backtest_results" / f"lookahead_{name}.csv"
            tmp_csv.unlink(missing_ok=True)
            result = freqtrade([
                "lookahead-analysis", *config_args("backtest.json"), "--strategy", name,
                "-i", BIAS_TIMEFRAME, "--timerange", LOOKAHEAD_TIMERANGE,
                "--minimum-trade-amount", "10", "--targeted-trade-amount", "30",
                "--lookahead-analysis-exportfilename", str(tmp_csv.relative_to(ROOT)),
            ], check=False, tee=True)
            row = next((r for r in csv.DictReader(tmp_csv.open()) if r.get("strategy") == name), None) \
                if tmp_csv.exists() else None
            if result.returncode != 0 or row is None:
                failed.append(f"{name} (lookahead did not run)")
                report.append(f"| {name} | **not checked** | - | - | - | - |")
                continue
            rows_out.append(row)
            verdict = row.get("has_bias", "").strip()
            if verdict != "False":
                failed.append(f"{name} (lookahead: {verdict})")
            shown = "no" if verdict == "False" else ("**YES**" if verdict == "True" else f"**{verdict}**")
            report.append(
                f"| {name} | {shown} | {row.get('total_signals', '')} | {row.get('biased_entry_signals', '')} | "
                f"{row.get('biased_exit_signals', '')} | {row.get('biased_indicators', '') or '-'} |"
            )
        if rows_out:
            with (ROOT / "results" / "checks" / "lookahead.csv").open("w", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(rows_out[0]))
                writer.writeheader()
                writer.writerows(rows_out)
        report.append("")

    if not args.skip_recursive:
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
                continue
            say(f"Recursive analysis: {name}")
            verdict, md = recursive_check(name)
            report += md
            if verdict != "PASS":
                failed.append(f"{name} (recursive)")

    report += ["## Result", "", "**PASS** - no bias found." if not failed
               else "**FAIL**: " + ", ".join(failed), ""]
    out = ROOT / "results" / "checks" / "bias_check.md"
    out.write_text("\n".join(report))
    say(f"Report written to {out.relative_to(ROOT)}")
    if failed:
        die("bias check failed: " + ", ".join(failed))
    print("Bias check PASSED for all strategies.")


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
    add("test", cmd_test)
    p = add("show-config", cmd_show_config)
    p.add_argument("configs", nargs="*", default=["backtest.json"],
                   help="override files in user_data/configs layered on base.json (default: backtest.json)")
    p = add("download", cmd_download)
    p.add_argument("--exchange", choices=EXCHANGES, default="binance",
                   help="data source (default: binance; fall back to bybit if it is blocked)")
    p = add("data-check", cmd_data_check)
    p.add_argument("--exchange", choices=EXCHANGES, help="default: the exchange we have data for")
    p = add("regimes", cmd_regimes)
    p.add_argument("--days", type=int, default=90, help="window length in days (default: 90)")
    p = add("check-bias", cmd_check_bias)
    p.add_argument("--strategies", nargs="+", help="default: every strategy in user_data/strategies")
    p.add_argument("--skip-lookahead", action="store_true")
    p.add_argument("--skip-recursive", action="store_true")
    p = add("ft", cmd_ft)
    p.add_argument("ft_args", nargs=argparse.REMAINDER, help="-- <freqtrade args>")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    os.chdir(ROOT)
    args.func(args)


if __name__ == "__main__":
    main()
