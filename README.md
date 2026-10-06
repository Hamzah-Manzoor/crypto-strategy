# Crypto Strategy Lab

A local lab for **testing many crypto trading strategies side by side** and improving them step by step, built on [Freqtrade](https://www.freqtrade.io/) 2026.9 and run with Docker.

- **Paper money only.** Everything runs as a backtest (on past data) or a dry-run (live prices, fake money).
- **No API keys.** Public price data is all it needs. A safety check blocks every start if a key appears anywhere.
- **Spot only:** BTC, ETH, SOL, BNB, XRP against USDT. Main timeframe is 1h; 15m and 4h are also supported.
- **Honest testing:**
  - Realistic fees (0.1% per side).
  - Risk measured on the wallet's real value over time.
  - In-sample vs out-of-sample splits, with candidates chosen before the out-of-sample look.
  - Walk-forward tests and bull/bear/sideways checks.

## Where things stand (2026-10-07)

All 8 build phases are done. See [ROADMAP](docs/ROADMAP.md).

- **23 strategy versions tested.** 8 original ideas, 4 hand-designed v2s, and 11 auto-tuned (`…T`) versions.
- **None has passed both promotion stages yet,** so none is "promoted" to paper trading.
- **What we learned** (details in [RESULTS](docs/RESULTS.md)):
  1. **Fees are the main enemy of busy strategies.** 5 of 7 original ideas made money before fees, but only 1 after.
  2. **Auto-tuning overfits.** The best tuned versions made +70% in-sample and then *lost* money out-of-sample.
  3. **The hand-designed `EmaTrendV2`** (trend following on 4h candles) passed the out-of-sample check: +5.1% while buy & hold lost 35%. It then failed the consistency check, making money in only 3 of 8 quarters.
- **Paper trading now:** `EmaTrendV2` (watch list) and a buy & hold baseline run as dry-run bots, with dashboards at http://127.0.0.1:8081 and :8082.

## Quick start (macOS)

You need Docker Desktop (running), Python 3.10+ and git. Nothing to pip install. Full guide: [SETUP](docs/SETUP.md).

```bash
cd crypto-strategy
python3 scripts/lab.py setup      # folders, .env with a random FreqUI password, git hook, pulls Freqtrade 2026.9
python3 scripts/lab.py download   # ~1 minute: about 3.4 years of candles, then a data check
python3 scripts/lab.py backtest   # all strategies on the in-sample period -> your first leaderboard
```

- **`backtest`:** prints the leaderboard, saves it in `results/leaderboards/`, updates `docs/RESULTS.md`, and logs the run in `docs/EXPERIMENT_LOG.md`.
- **`make` aliases:** every command has one, e.g. `make setup`, `make backtest ARGS="--period bull-is"`.

## Daily workflow

1. **Top up data:** `lab.py download`.
2. **Try an idea:** copy `templates/strategy_template.py` to `user_data/strategies/<idea>_v1.py`, or make a `_v2` of an existing one (never edit a version that has results).
3. **Check it doesn't cheat:** `lab.py check-bias --strategies MyIdeaV1`.
4. **Compare it in-sample:** `lab.py backtest --notes "what I changed"`. Also try the regime windows: `--period bull-is`, `bear-is`, `sideways-is`.
5. **Optionally tune it:** `lab.py hyperopt MyIdeaV1` (in-sample only; creates `MyIdeaV1T`). Then run `check-bias` on the `…T` version.
6. **Record the decision:** `lab.py exp decide <ID> keep|tweak|drop "why"`.
7. **When you have final candidates,** write the list in `docs/DECISIONS.md`, then run `lab.py validate --strategies …` **once**. After that, run `walkforward` and `stage2` for the ones that pass.
8. **Paper-trade it:** add it to `user_data/configs/bots.json` as `promoted` (only if Stage 2 passed) or `watch-list`, then run `lab.py bots up` and later `lab.py bots status`.

## All commands

`python3 scripts/lab.py <command>` (or `make <command>`). Every command that starts Freqtrade runs the safety check first. `<command> --help` shows all options.

| Command | What it does |
|---|---|
| **Setup** | |
| `setup` | Checks Docker, creates folders, generates `.env`, activates the git hook, pulls the pinned image |
| `safety` | Runs the safety check: dry-run only, no keys, spot only, local ports only, `trade --dry-run` |
| `test [--host-only]` | Unit tests: on the Mac, then the pandas tests inside the container |
| `show-config [overrides…]` | The merged config Freqtrade sees (secrets redacted) |
| `ft -- <args>` | Any raw Freqtrade command in the pinned container |
| **Data** | |
| `download [--exchange bybit\|okx]` | Candles for all pairs and timeframes (re-run to top up), then the data check |
| `data-check` | Coverage, gaps, duplicates and impossible candles → `results/checks/data_check.md` |
| `regimes [--days 90]` | Bull / bear / sideways windows inside in-sample and out-of-sample → `results/regimes.json` |
| **Strategies** | |
| `check-bias [--strategies …]` | Lookahead + recursive analysis → `results/checks/bias_check.md` |
| `backtest [--period is] [--timeframe 1h] [--strategies …] [--fee 0.001] [--detail 5m] [--notes …]` | All strategies in one run (buy & hold always included) → leaderboard + experiment log. Out-of-sample dates need `--allow-oos` |
| `hyperopt <Strategy> [--epochs 300]` | Tunes on in-sample only (seed 42, 6 workers), writes a `…T` version, compares both |
| **Validation** | |
| `validate [--strategies …]` | Stage 1: in-sample vs out-of-sample, 0.15% fee stress, 5m fills → `results/leaderboards/stage1_1h.md` |
| `walkforward <Strategy> [--fixed]` | 8 rolling 3-month test windows, re-tuned before each or with fixed settings → `results/walkforward/` |
| `stage2 [--strategies …]` | Stage 2: walk-forward + all 6 regime windows → `results/leaderboards/stage2_1h.md` |
| **Results** | |
| `report [--recompute]` | Rebuilds leaderboards, Stage 1, `docs/RESULTS.md` and `docs/EXPERIMENT_LOG.md` |
| `exp list [--strategy X]` / `exp decide <ID> keep\|tweak\|drop "why"` | Experiment log |
| **Paper trading** | |
| `bots up\|down\|status\|logs\|generate [names…]` | Dry-run bots from `user_data/configs/bots.json`: one container, database, log and FreqUI port each |

## Project layout

```
scripts/        lab.py (task runner) + safety_check, metrics, report, rules, experiments, tuning, bots, data_check, regimes
user_data/
  configs/      base.json + overrides (backtest, exchange fallbacks), bots.json, generated dryrun/*.json
  strategies/   one file per version (ema_trend_v2.py, generated ema_trend_v2t.py…) + labkit/ shared code
  data/ backtest_results/ hyperopt_results/ walkforward/ logs/ db/     (git-ignored raw data and output)
templates/      strategy_template.py - copy it to start a new strategy
results/        committed summaries: runs/, leaderboards/, hyperopt/, walkforward/, checks/, experiments.jsonl
tests/          unit tests (tests/container/ runs inside Docker)
docs/           everything below
```

## Docs

| Doc | What's in it |
|---|---|
| [SETUP](docs/SETUP.md) | Install, Docker, data download, paper bots, FreqUI, Telegram, troubleshooting |
| [STRATEGIES](docs/STRATEGIES.md) | Each strategy: idea, indicators, rules, risk settings, status |
| [TESTING_METHODOLOGY](docs/TESTING_METHODOLOGY.md) | How we test and the promotion rules (written before any out-of-sample look) |
| [RESULTS](docs/RESULTS.md) | Current leaderboards (auto-updated) and what they mean |
| [EXPERIMENT_LOG](docs/EXPERIMENT_LOG.md) | Every run, and the keep / tweak / drop decision per strategy |
| [RISK_AND_SAFETY](docs/RISK_AND_SAFETY.md) | Safety rules, the safety check, what going live would require, Pakistan rules (PVARA) |
| [ROADMAP](docs/ROADMAP.md) | Phases done and next ideas |
| [DECISIONS](docs/DECISIONS.md) | Why things are the way they are |
| [GLOSSARY](docs/GLOSSARY.md) | Plain-English meanings of every trading term used |

## Disclaimer

This is a research and learning project. Backtest results don't predict future returns. Nothing here is financial or legal advice.
