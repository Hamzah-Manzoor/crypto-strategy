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
import os
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
DATA_START = "20230701"                  # 3 months of indicator warm-up before the in-sample period
REGIME_DATA_START = "20220101"           # extra BTC daily history so a 200-day average exists from day one

# Test periods (see docs/TESTING_METHODOLOGY.md). Tune on "is" only; "oos" is for checking.
PERIODS = {
    "is": ("20231001", "20251001"),
    "oos": ("20251001", "20261001"),
}

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


def run(cmd: list[str], check: bool = True, quiet: bool = False) -> subprocess.CompletedProcess:
    if not quiet:
        print(f"$ {shlex.join(cmd)}", flush=True)
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


def freqtrade(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a one-off Freqtrade command in the pinned container (after the safety gate)."""
    safety_gate()
    return run([*COMPOSE, "run", "--rm", "freqtrade", *args], check=check)


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
    p = add("ft", cmd_ft)
    p.add_argument("ft_args", nargs=argparse.REMAINDER, help="-- <freqtrade args>")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    os.chdir(ROOT)
    args.func(args)


if __name__ == "__main__":
    main()
