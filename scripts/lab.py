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
    p = add("ft", cmd_ft)
    p.add_argument("ft_args", nargs=argparse.REMAINDER, help="-- <freqtrade args>")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    os.chdir(ROOT)
    args.func(args)


if __name__ == "__main__":
    main()
