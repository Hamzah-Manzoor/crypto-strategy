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
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import experiments  # noqa: E402
import report  # noqa: E402
import safety_check  # noqa: E402
from rules import BASELINE  # noqa: E402

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
STANDARD_FEE = 0.001  # 0.1% per side (Binance spot); stress runs use 0.0015

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
    status = {name: {"lookahead": "not run", "recursive": "not run"} for name in strategies}

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
                status[name]["lookahead"] = "skipped"
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
                status[name]["recursive"] = "skipped"
                continue
            say(f"Recursive analysis: {name}")
            verdict, md = recursive_check(name)
            report += md
            status[name]["recursive"] = "pass" if verdict == "PASS" else "fail"
            if verdict != "PASS":
                failed.append(f"{name} (recursive)")

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


def touches_oos(timerange: str) -> bool:
    """True if any candle in the timerange is out-of-sample (IS end date is exclusive)."""
    start, _, end = timerange.partition("-")
    return not end or end > PERIODS["is"][1]


def backtest_run(period: str, timeframe: str, fee: float, detail: str | None, strategies: list[str],
                 notes: str, allow_oos: bool) -> dict:
    """Backtest strategies in ONE Freqtrade run, summarise, log and report. Returns the run summary."""
    label, timerange = resolve_period(period)
    oos = touches_oos(timerange)
    if oos and not allow_oos:
        die(f"period '{period}' ({timerange}) includes out-of-sample data. Tuning and iterating must use "
            "in-sample only. If this is a deliberate check, add --allow-oos (every OOS look is logged).")
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
        "--fee", str(fee), "--cache", "none", "--export", "trades",
        "--backtest-directory", str(run_dir.relative_to(ROOT)),
    ]
    if detail:
        ft_args += ["--timeframe-detail", detail]
    if notes:
        ft_args += ["--notes", notes]
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
                 args.strategies or discover_strategies(), args.notes, args.allow_oos)


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
    for e in entries[-args.last:]:
        m = e["metrics"]
        print(f"{e['id']:6} {e['date'][:10]:10} {e['strategy']:20} {e['period'] + ('*' if e.get('oos_look') else ''):12} "
              f"{e['timeframe']:4} {m['profit_pct']:>+8.1f} {m['max_dd_pct']:>7.1f} {m['sharpe']:>6.2f} "
              f"{m['calmar']:>6.2f} {m['trades']:>6}  {e['decision']} {e.get('decision_note', '')}")


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
    p = add("data-check", cmd_data_check)
    p.add_argument("--exchange", choices=EXCHANGES, help="default: the exchange we have data for")
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
    p.add_argument("--allow-oos", action="store_true", help="allow periods that include out-of-sample data")
    p = add("report", cmd_report)
    p.add_argument("--recompute", action="store_true", help="re-read the raw result zips (needs Docker)")
    p = add("exp", cmd_exp)
    p.add_argument("action", choices=["list", "decide"])
    p.add_argument("rest", nargs="*", help='decide: <ID> keep|tweak|drop "why"')
    p.add_argument("--strategy", help="list: filter by strategy name")
    p.add_argument("--last", type=int, default=40, help="list: show the last N entries")
    p = add("ft", cmd_ft)
    p.add_argument("ft_args", nargs=argparse.REMAINDER, help="-- <freqtrade args>")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    os.chdir(ROOT)
    args.func(args)


if __name__ == "__main__":
    main()
