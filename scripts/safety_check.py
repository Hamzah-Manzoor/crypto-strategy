#!/usr/bin/env python3
"""Safety check: refuse to run anything that could touch real money.

The lab only runs in backtest / dry-run (paper trading) mode with NO exchange
API keys. This script fails loudly (exit code 1) if any of these is true:

  - a config sets `dry_run` to anything other than true (or base.json lacks it)
  - a config, .env file, compose file or the current environment holds an
    exchange key / secret / password
  - a config or env var switches away from spot (futures / margin)
  - a committed config holds a FreqUI or Telegram secret (those live in .env)
  - a compose file publishes a port on all network interfaces (FreqUI is local only)
  - a compose file starts `trade` without `--dry-run`
  - .env is tracked by git

It is run by `scripts/lab.py` before anything starts, by the `safety` service
in docker-compose.yml (which every Freqtrade container depends on), and by the
git pre-commit hook. Standard library only, so it runs on the host and inside
the Freqtrade container.

Usage:
    python3 scripts/safety_check.py [--root PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Mirrors Freqtrade's own list of sensitive exchange fields
# (freqtrade/configuration/config_secrets.py), compared case-insensitively,
# plus the extra names CCXT uses for some exchanges.
SENSITIVE_EXCHANGE_FIELDS = {
    "key", "api_key", "apikey", "secret", "password", "uid",
    "account_id", "accountid", "wallet_address", "walletaddress",
    "private_key", "privatekey", "token", "login", "twofa", "passphrase",
}

# Secrets that are fine in the git-ignored .env, but never in a committed config.
LOCAL_ONLY_SECRETS = [
    ("api_server", "password"),
    ("api_server", "jwt_secret_key"),
    ("api_server", "ws_token"),
    ("telegram", "token"),
    ("telegram", "chat_id"),
    ("discord", "webhook_url"),
    ("webhook", "url"),
]

# Env var names that look like exchange credentials, whatever tool they are for.
EXCHANGE_CREDENTIAL_VAR = re.compile(
    r"(BINANCE|BYBIT|OKX|KUCOIN|KRAKEN|COINBASE|BITGET|GATE|MEXC|HTX|HUOBI|EXCHANGE|CCXT)"
    r".*(KEY|SECRET|PASSWORD|PASSPHRASE|UID|TOKEN)",
    re.IGNORECASE,
)


def _is_empty(value) -> bool:
    return value is None or value == "" or value == {} or value == []


def _walk(node, path: str):
    """Yield (dotted_path, key, value) for every key in a nested dict/list."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else str(key)
            yield here, str(key), value
            yield from _walk(value, here)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, f"{path}[{i}]")


def deep_merge(base: dict, override: dict) -> dict:
    """Same idea as Freqtrade's config merge: override wins, dicts merge."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


# --------------------------------------------------------------------------- configs

def check_config(cfg: dict, label: str) -> list[str]:
    problems = []

    if "dry_run" in cfg and cfg["dry_run"] is not True:
        problems.append(f"{label}: dry_run is {cfg['dry_run']!r} - it must be true")

    for path, key, value in _walk(cfg.get("exchange", {}), "exchange"):
        if key.lower() in SENSITIVE_EXCHANGE_FIELDS and not _is_empty(value):
            problems.append(f"{label}: {path} is set - exchange keys are not allowed in this lab")

    if "trading_mode" in cfg and cfg["trading_mode"] != "spot":
        problems.append(f"{label}: trading_mode is {cfg['trading_mode']!r} - only 'spot' is allowed")
    if not _is_empty(cfg.get("margin_mode")):
        problems.append(f"{label}: margin_mode is {cfg['margin_mode']!r} - must be empty (spot only)")

    for section, key in LOCAL_ONLY_SECRETS:
        value = cfg.get(section, {}).get(key) if isinstance(cfg.get(section), dict) else None
        if not _is_empty(value):
            problems.append(
                f"{label}: {section}.{key} is set in a committed file - put it in .env instead"
            )
    return problems


def _config_files(root: Path) -> list[Path]:
    """Every config Freqtrade could be pointed at in this repo."""
    files = set((root / "user_data" / "configs").rglob("*.json"))
    files |= set((root / "user_data").glob("*.json"))
    files |= set(root.glob("*.json"))
    return sorted(files)


def check_configs(root: Path) -> tuple[list[str], int]:
    problems = []
    configs_dir = (root / "user_data" / "configs").resolve()
    files = _config_files(root)
    loaded: dict[Path, dict] = {}

    for f in files:
        label = str(f.relative_to(root))
        try:
            data = json.loads(f.read_text())
        except (OSError, ValueError) as exc:
            problems.append(f"{label}: cannot be read as strict JSON ({exc}) - cannot verify it is safe")
            continue
        if not isinstance(data, dict):
            problems.append(f"{label}: top level is not a JSON object - cannot verify it is safe")
            continue
        loaded[f] = data
        problems += check_config(data, label)

        for extra in data.get("add_config_files", []) or []:
            target = (f.parent / extra).resolve()
            if not target.is_relative_to(configs_dir):
                problems.append(f"{label}: add_config_files points outside user_data/configs ({extra})")
            elif not target.exists():
                problems.append(f"{label}: add_config_files points to a missing file ({extra})")

    base_path = root / "user_data" / "configs" / "base.json"
    base = loaded.get(base_path)
    if base is None:
        if base_path.exists():
            pass  # already reported as unreadable above
        else:
            problems.append("user_data/configs/base.json is missing - every run builds on it")
    else:
        if base.get("dry_run") is not True:
            problems.append("user_data/configs/base.json: must set \"dry_run\": true explicitly")
        # What Freqtrade actually sees when an override is layered on top of base.json.
        for f, data in loaded.items():
            if f == base_path or not f.resolve().is_relative_to(configs_dir):
                continue
            merged = deep_merge(base, data)
            label = f"base.json + {f.relative_to(root / 'user_data' / 'configs')}"
            if merged.get("dry_run") is not True:
                problems.append(f"{label}: merged dry_run is {merged.get('dry_run')!r}")
            if merged.get("trading_mode", "spot") != "spot":
                problems.append(f"{label}: merged trading_mode is {merged.get('trading_mode')!r}")
    return problems, len(files)


# --------------------------------------------------------------------------- env vars

def parse_env_file(path: Path) -> dict[str, str]:
    values = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def check_env(env: dict[str, str], label: str) -> list[str]:
    problems = []
    for name, value in env.items():
        upper = name.upper()
        filled = value.strip() != ""
        if upper.startswith("FREQTRADE__EXCHANGE__"):
            parts = [p.lower() for p in upper.split("__")[2:]]
            if filled and any(p in SENSITIVE_EXCHANGE_FIELDS for p in parts):
                problems.append(f"{label}: {name} is set - exchange keys are not allowed in this lab")
        elif upper == "FREQTRADE__DRY_RUN" and value.strip().lower() not in ("true", "t"):
            problems.append(f"{label}: {name}={value!r} - dry_run must stay true")
        elif upper == "FREQTRADE__TRADING_MODE" and value.strip().lower() != "spot":
            problems.append(f"{label}: {name}={value!r} - only spot is allowed")
        elif upper == "FREQTRADE__MARGIN_MODE" and filled:
            problems.append(f"{label}: {name}={value!r} - margin is not allowed")
        elif (not upper.startswith("FREQTRADE__") and filled
              and EXCHANGE_CREDENTIAL_VAR.search(upper)):
            problems.append(f"{label}: {name} looks like an exchange credential - remove it")
    return problems


def check_env_files(root: Path) -> tuple[list[str], int]:
    problems = []
    files = sorted(p for p in root.glob(".env*") if p.is_file())
    for f in files:
        problems += check_env(parse_env_file(f), str(f.relative_to(root)))
    return problems, len(files)


# --------------------------------------------------------------------------- compose

_TRADE_CMD = re.compile(r"""(^|[\s\["',])trade([\s\]"',]|$)""")
_EXCHANGE_SECRET_VAR = re.compile(
    r"FREQTRADE__EXCHANGE__\w*(" + "|".join(sorted(SENSITIVE_EXCHANGE_FIELDS)) + r")\b",
    re.IGNORECASE,
)


def _check_command(command: str, label: str, n: int) -> list[str]:
    if _TRADE_CMD.search(command) and "--dry-run" not in command:
        return [f"{label}:{n}: starts 'trade' without '--dry-run'"]
    return []


def check_compose_text(text: str, label: str) -> list[str]:
    """Line-based checks, so no YAML library is needed. Handles both
    `command: [...]` on one line and a `command:` block of `- item` lines."""
    problems = []
    block, block_indent, block_start, block_items = None, 0, 0, []

    def close_block():
        if block == "command":
            problems.extend(_check_command(" ".join(block_items), label, block_start))

    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if block and indent <= block_indent and not stripped.startswith("-"):
            close_block()
            block = None
        elif block and indent < block_indent:
            close_block()
            block = None

        if _EXCHANGE_SECRET_VAR.search(stripped):
            problems.append(f"{label}:{n}: passes an exchange credential variable - not allowed")
        if re.search(r"FREQTRADE__DRY_RUN\s*[:=]\s*[\"']?(false|f|0)\b", stripped, re.IGNORECASE):
            problems.append(f"{label}:{n}: sets FREQTRADE__DRY_RUN to false - not allowed")

        key, _, rest = stripped.partition(":")
        if key in ("ports", "command") and rest.strip() in ("", ">", "|", ">-", "|-"):
            block, block_indent, block_start, block_items = key, indent, n, []
            continue
        if key == "command":
            problems.extend(_check_command(stripped, label, n))
            continue

        if block == "command":
            block_items.append(stripped.lstrip("-").strip().strip("\"'"))
        elif block == "ports" and stripped.startswith("-"):
            entry = stripped[1:].strip().strip("\"'")
            if not entry.startswith("127.0.0.1:"):
                problems.append(
                    f"{label}:{n}: port '{entry}' is not bound to 127.0.0.1 - FreqUI must stay local"
                )
    close_block()
    return problems


def check_compose_files(root: Path) -> tuple[list[str], int]:
    problems = []
    files = sorted(set(root.glob("docker-compose*.y*ml")) | set(root.glob("compose*.y*ml")))
    for f in files:
        problems += check_compose_text(f.read_text(), str(f.relative_to(root)))
    return problems, len(files)


# --------------------------------------------------------------------------- git

def check_git(root: Path) -> tuple[list[str], str]:
    if not (root / ".git").exists():
        return [], "no git repo here"
    if shutil.which("git") is None:
        return [], "git not installed here (the host check covers it)"
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        return [], "git ls-files failed"
    tracked = [p for p in result.stdout.split("\0") if p]
    problems = [
        f"{p}: is tracked by git - secrets must never be committed (git rm --cached {p})"
        for p in tracked
        if Path(p).name.startswith(".env") and Path(p).name != ".env.example"
    ]
    return problems, "checked"


# --------------------------------------------------------------------------- main

def run_checks(root: Path, environ: dict[str, str] | None = None) -> tuple[list[str], str]:
    root = root.resolve()
    environ = dict(os.environ) if environ is None else environ
    config_problems, n_configs = check_configs(root)
    env_problems, n_env = check_env_files(root)
    compose_problems, n_compose = check_compose_files(root)
    git_problems, git_note = check_git(root)
    problems = (
        config_problems + env_problems
        + check_env(environ, "current environment")
        + compose_problems + git_problems
    )
    summary = (
        f"{n_configs} config file(s), {n_env} env file(s), {n_compose} compose file(s), "
        f"current environment, git ({git_note})"
    )
    return problems, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent,
                        help="repo root to check (default: this repo)")
    args = parser.parse_args(argv)

    problems, summary = run_checks(args.root)
    if problems:
        bar = "=" * 72
        print(bar, file=sys.stderr)
        print("!!  SAFETY CHECK FAILED - refusing to start anything", file=sys.stderr)
        print(bar, file=sys.stderr)
        for i, p in enumerate(problems, start=1):
            print(f"  {i}. {p}", file=sys.stderr)
        print(bar, file=sys.stderr)
        print("This lab only runs backtests and dry-run bots with NO exchange keys.", file=sys.stderr)
        print("See docs/RISK_AND_SAFETY.md.", file=sys.stderr)
        return 1
    print(f"[safety] OK - dry_run everywhere, spot only, no exchange keys. Checked: {summary}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
