"""Tests for scripts/safety_check.py. Run: python3 scripts/lab.py test"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import safety_check  # noqa: E402

SAFE_BASE = {
    "dry_run": True,
    "trading_mode": "spot",
    "margin_mode": "",
    "exchange": {"name": "binance", "key": "", "secret": "", "ccxt_config": {}},
    "api_server": {"enabled": False, "password": "", "jwt_secret_key": ""},
    "telegram": {"enabled": False, "token": "", "chat_id": ""},
}

SAFE_COMPOSE = """\
services:
  safety:
    image: freqtradeorg/freqtrade:2026.9
  bot-ema:
    image: freqtradeorg/freqtrade:2026.9
    command: ["trade", "--dry-run", "--config", "user_data/configs/base.json"]
    ports:
      - "127.0.0.1:8081:8080"
    volumes:
      - ./user_data:/freqtrade/user_data
"""


class SafetyCheckTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "user_data" / "configs" / "dryrun").mkdir(parents=True)
        self.write_config("base.json", SAFE_BASE)
        self.write_config("backtest.json", {"dry_run": True, "fee": 0.001})
        (self.root / "docker-compose.yml").write_text(SAFE_COMPOSE)
        (self.root / ".env").write_text(
            "FREQTRADE__API_SERVER__PASSWORD=abc\nFREQTRADE__API_SERVER__JWT_SECRET_KEY=xyz\n"
        )

    def tearDown(self):
        shutil.rmtree(self.root)

    def write_config(self, name, data):
        path = self.root / "user_data" / "configs" / name
        path.write_text(json.dumps(data))
        return path

    def problems(self, environ=None):
        problems, _ = safety_check.run_checks(self.root, environ or {})
        return problems

    def assert_fails_with(self, text, environ=None):
        problems = self.problems(environ)
        self.assertTrue(problems, "expected the safety check to fail")
        self.assertTrue(any(text in p for p in problems), f"no problem mentions {text!r}: {problems}")

    # --- the happy path -------------------------------------------------------

    def test_safe_setup_passes(self):
        self.assertEqual(self.problems(), [])

    def test_this_repo_passes(self):
        problems, _ = safety_check.run_checks(REPO, {})
        self.assertEqual(problems, [])

    # --- dry_run ----------------------------------------------------------------

    def test_dry_run_false_in_base_fails(self):
        self.write_config("base.json", {**SAFE_BASE, "dry_run": False})
        self.assert_fails_with("dry_run is False")

    def test_dry_run_missing_from_base_fails(self):
        base = dict(SAFE_BASE)
        del base["dry_run"]
        self.write_config("base.json", base)
        self.assert_fails_with('must set "dry_run": true')

    def test_dry_run_string_true_fails(self):
        self.write_config("base.json", {**SAFE_BASE, "dry_run": "true"})
        self.assert_fails_with("dry_run is 'true'")

    def test_dry_run_false_in_override_fails(self):
        self.write_config("dryrun/ema.json", {"dry_run": False, "strategy": "EmaTrendV1"})
        self.assert_fails_with("dryrun/ema.json")

    def test_missing_base_fails(self):
        (self.root / "user_data" / "configs" / "base.json").unlink()
        self.assert_fails_with("base.json is missing")

    def test_config_in_user_data_root_is_checked(self):
        (self.root / "user_data" / "config.json").write_text(json.dumps({"dry_run": False}))
        self.assert_fails_with("user_data/config.json")

    # --- exchange keys ----------------------------------------------------------

    def test_exchange_key_fails(self):
        cfg = json.loads(json.dumps(SAFE_BASE))
        cfg["exchange"]["key"] = "abc123"
        self.write_config("base.json", cfg)
        self.assert_fails_with("exchange.key is set")

    def test_exchange_secret_in_override_fails(self):
        self.write_config("exchange-okx.json", {"exchange": {"name": "okx", "secret": "s3cr3t"}})
        self.assert_fails_with("exchange.secret is set")

    def test_ccxt_config_api_key_fails(self):
        cfg = json.loads(json.dumps(SAFE_BASE))
        cfg["exchange"]["ccxt_config"] = {"apiKey": "abc"}
        self.write_config("base.json", cfg)
        self.assert_fails_with("exchange.ccxt_config.apiKey")

    # --- spot only ----------------------------------------------------------------

    def test_futures_fails(self):
        self.write_config("base.json", {**SAFE_BASE, "trading_mode": "futures"})
        self.assert_fails_with("only 'spot' is allowed")

    def test_margin_mode_fails(self):
        self.write_config("base.json", {**SAFE_BASE, "margin_mode": "isolated"})
        self.assert_fails_with("margin_mode")

    # --- secrets that belong in .env ------------------------------------------------

    def test_ui_password_in_config_fails(self):
        cfg = json.loads(json.dumps(SAFE_BASE))
        cfg["api_server"]["password"] = "hunter2"
        self.write_config("base.json", cfg)
        self.assert_fails_with("api_server.password")

    def test_telegram_token_in_config_fails(self):
        cfg = json.loads(json.dumps(SAFE_BASE))
        cfg["telegram"]["token"] = "123:abc"
        self.write_config("base.json", cfg)
        self.assert_fails_with("telegram.token")

    # --- unreadable / sneaky configs ----------------------------------------------

    def test_unparseable_config_fails(self):
        (self.root / "user_data" / "configs" / "broken.json").write_text("{ not json ")
        self.assert_fails_with("cannot be read as strict JSON")

    def test_add_config_files_outside_configs_fails(self):
        self.write_config("backtest.json", {"dry_run": True, "add_config_files": ["../../secrets.json"]})
        self.assert_fails_with("points outside user_data/configs")

    # --- env files and the environment ----------------------------------------------

    def test_env_file_exchange_secret_fails(self):
        (self.root / ".env").write_text("FREQTRADE__EXCHANGE__SECRET=abc\n")
        self.assert_fails_with("FREQTRADE__EXCHANGE__SECRET is set")

    def test_env_file_empty_exchange_key_is_ok(self):
        (self.root / ".env").write_text("FREQTRADE__EXCHANGE__KEY=\n")
        self.assertEqual(self.problems(), [])

    def test_env_file_dry_run_false_fails(self):
        (self.root / ".env").write_text("FREQTRADE__DRY_RUN=false\n")
        self.assert_fails_with("dry_run must stay true")

    def test_env_file_dry_run_zero_fails(self):
        (self.root / ".env").write_text("FREQTRADE__DRY_RUN=0\n")
        self.assert_fails_with("dry_run must stay true")

    def test_env_file_generic_exchange_credential_fails(self):
        (self.root / ".env").write_text('export BINANCE_API_KEY="abc"\n')
        self.assert_fails_with("BINANCE_API_KEY looks like an exchange credential")

    def test_environment_variable_fails(self):
        self.assert_fails_with(
            "FREQTRADE__EXCHANGE__KEY is set", environ={"FREQTRADE__EXCHANGE__KEY": "abc"}
        )

    def test_environment_futures_fails(self):
        self.assert_fails_with(
            "only spot is allowed", environ={"FREQTRADE__TRADING_MODE": "futures"}
        )

    def test_ui_secrets_in_env_file_are_ok(self):
        (self.root / ".env").write_text(
            "FREQTRADE__API_SERVER__PASSWORD=pw\nFREQTRADE__TELEGRAM__TOKEN=123:abc\n"
        )
        self.assertEqual(self.problems(), [])

    # --- compose files ----------------------------------------------------------------

    def test_public_port_fails(self):
        (self.root / "docker-compose.yml").write_text(
            SAFE_COMPOSE.replace('"127.0.0.1:8081:8080"', '"8081:8080"')
        )
        self.assert_fails_with("not bound to 127.0.0.1")

    def test_trade_without_dry_run_fails(self):
        (self.root / "docker-compose.yml").write_text(
            SAFE_COMPOSE.replace('"trade", "--dry-run",', '"trade",')
        )
        self.assert_fails_with("without '--dry-run'")

    def test_trade_block_without_dry_run_fails(self):
        (self.root / "docker-compose.bots.yml").write_text(
            "services:\n  bot:\n    command:\n      - trade\n      - --config\n      - base.json\n"
        )
        self.assert_fails_with("docker-compose.bots.yml:3")

    def test_trade_block_with_dry_run_passes(self):
        (self.root / "docker-compose.bots.yml").write_text(
            "services:\n  bot:\n    command:\n      - trade\n      - --dry-run\n"
        )
        self.assertEqual(self.problems(), [])

    def test_compose_exchange_secret_var_fails(self):
        (self.root / "docker-compose.yml").write_text(
            SAFE_COMPOSE + "    environment:\n      - FREQTRADE__EXCHANGE__SECRET=${SECRET}\n"
        )
        self.assert_fails_with("exchange credential variable")

    # --- git ----------------------------------------------------------------------------

    @unittest.skipIf(shutil.which("git") is None, "git not installed")
    def test_tracked_env_file_fails(self):
        def git(*args):
            subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

        git("init", "-q")
        git("add", "-f", ".env")
        self.assert_fails_with("is tracked by git")


if __name__ == "__main__":
    unittest.main()
