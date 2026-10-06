"""Tests for scripts/bots.py (paper-trading bot generation). Run: python3 scripts/lab.py test"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import bots  # noqa: E402
import safety_check  # noqa: E402

TWO_BOTS = [
    {"name": "ema-trend-v2", "strategy": "EmaTrendV2", "port": 8081, "status": "watch-list", "reason": "r"},
    {"name": "buy-hold", "strategy": "BuyHoldV1", "port": 8082, "status": "baseline", "reason": "r"},
]


class RegistryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def load(self, bot_list):
        path = self.tmp / "bots.json"
        path.write_text(json.dumps({"bots": bot_list}))
        return bots.load_registry(path)

    def test_valid_registry(self):
        self.assertEqual(len(self.load(TWO_BOTS)), 2)

    def test_project_registry_is_valid(self):
        self.assertTrue(bots.load_registry())

    def test_invalid_entries_are_rejected(self):
        bad = {
            "missing key": [{k: v for k, v in TWO_BOTS[0].items() if k != "port"}],
            "bad name": [{**TWO_BOTS[0], "name": "Bad Name!"}],
            "bad status": [{**TWO_BOTS[0], "status": "live"}],
            "low port": [{**TWO_BOTS[0], "port": 80}],
            "duplicate port": [TWO_BOTS[0], {**TWO_BOTS[1], "port": 8081}],
        }
        for case, bot_list in bad.items():
            with self.subTest(case), self.assertRaises(SystemExit):
                self.load(bot_list)


class GeneratedFilesTest(unittest.TestCase):
    def test_dryrun_config_is_safe_and_has_no_secrets(self):
        cfg = bots.dryrun_config(TWO_BOTS[0], TWO_BOTS)
        self.assertIs(cfg["dry_run"], True)
        self.assertEqual(cfg["strategy"], "EmaTrendV2")
        self.assertNotIn("password", cfg["api_server"])
        self.assertNotIn("jwt_secret_key", cfg["api_server"])
        self.assertEqual(safety_check.check_config(cfg, "generated"), [])
        # every bot's FreqUI may add the others
        self.assertIn("http://127.0.0.1:8082", cfg["api_server"]["CORS_origins"])

    def test_compose_passes_the_safety_check(self):
        text = bots.compose_text(TWO_BOTS, "freqtradeorg/freqtrade:2026.9@sha256:abc")
        self.assertEqual(safety_check.check_compose_text(text, "generated"), [])
        self.assertEqual(text.count('"--dry-run"'), 2)
        self.assertIn('"127.0.0.1:8081:8080"', text)
        self.assertEqual(text.count("condition: service_completed_successfully"), 2)
        self.assertIn("sqlite:////freqtrade/user_data/db/buy-hold.sqlite", text)

    def test_compose_uses_the_pinned_image(self):
        self.assertIn("@sha256:", bots.pinned_image())

    def test_write_all_removes_stale_bot_configs(self):
        tmp = Path(tempfile.mkdtemp())
        old_dir, old_compose = bots.DRYRUN_DIR, bots.COMPOSE_BOTS
        try:
            bots.DRYRUN_DIR, bots.COMPOSE_BOTS = tmp / "dryrun", tmp / "docker-compose.bots.yml"
            bots.DRYRUN_DIR.mkdir()
            (bots.DRYRUN_DIR / "old-bot.json").write_text("{}")
            bots.write_all(TWO_BOTS)
            self.assertEqual(sorted(p.name for p in bots.DRYRUN_DIR.glob("*.json")),
                             ["buy-hold.json", "ema-trend-v2.json"])
            self.assertTrue(bots.COMPOSE_BOTS.exists())
        finally:
            bots.DRYRUN_DIR, bots.COMPOSE_BOTS = old_dir, old_compose
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
