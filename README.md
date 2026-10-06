# Crypto Strategy Lab

A local lab for **testing many crypto trading strategies side by side** and improving them step by step, built on [Freqtrade](https://www.freqtrade.io/) and run with Docker.

- **Paper money only.** Everything runs as a backtest (on past data) or a dry-run (live prices, fake money).
- **No API keys.** Public price data is all it needs. A safety check blocks every start if a key appears anywhere.
- **Spot only:** BTC, ETH, SOL, BNB, XRP against USDT. Main timeframe is 1h; 15m and 4h are also supported.
- **Honest testing:** realistic fees (0.1% per side), in-sample vs out-of-sample splits, walk-forward tests, and bull/bear/sideways market checks. A strategy has to earn its place on the leaderboard.

> **Status:** Phase 7 of 8 (paper trading) is done. No strategy passed both promotion stages; `EmaTrendV2` (watch list) and a buy & hold baseline are paper-trading. See [RESULTS](docs/RESULTS.md). See [docs/ROADMAP.md](docs/ROADMAP.md).

## Quick start (macOS)

You need Docker Desktop (running), Python 3.10+ and git. Nothing to pip install.

```bash
cd crypto-strategy
python3 scripts/lab.py setup      # folders, .env with a random FreqUI password, git hook, pulls Freqtrade 2026.9
python3 scripts/lab.py test       # unit tests
python3 scripts/lab.py safety     # should print: [safety] OK ...
python3 scripts/lab.py download   # ~1 minute, about 3.4 years of candles, then a data check
python3 scripts/lab.py regimes    # bull / bear / sideways test windows
```

Then your first leaderboard (about a minute):

```bash
python3 scripts/lab.py backtest --period is --timeframe 1h --notes "my first run"
```

It prints the leaderboard, saves it to `results/leaderboards/`, updates `docs/RESULTS.md`, and logs the run in `docs/EXPERIMENT_LOG.md`.

Every command also has a `make` alias: `make setup`, `make test`, `make backtest ARGS="--period oos"`.

## Daily workflow (once all phases are done)

1. `lab.py download` to top up price data.
2. Change or add a strategy version (`templates/strategy_template.py`).
3. `lab.py backtest --period is` builds the in-sample leaderboard.
4. If it looks good, run `lab.py validate` (out-of-sample + stress fees) and `lab.py walkforward <Strategy>`.
5. `lab.py exp decide <id> keep|tweak|drop "why"` records the decision.
6. Strategies that pass the promotion rules go to paper trading: add them to `user_data/configs/bots.json`, then run `lab.py bots up` and `lab.py bots status`. FreqUI runs at http://127.0.0.1:8081 (login in `.env`).

## All commands

`python3 scripts/lab.py <command>` (or `make <command>`). Every command that starts Freqtrade runs the safety check first.

| Command | What it does | Available |
|---|---|---|
| `setup` | Checks Docker, creates folders, generates `.env`, activates the git hook, pulls the pinned image | ✅ Phase 2 |
| `safety` | Runs the safety check (dry_run only, no keys, spot only, local ports only) | ✅ Phase 2 |
| `test` | Runs the unit tests | ✅ Phase 2 |
| `show-config [overrides…]` | Shows the merged config Freqtrade sees (secrets redacted) | ✅ Phase 2 |
| `ft -- <args>` | Runs any raw Freqtrade command in the pinned container | ✅ Phase 2 |
| `download [--exchange bybit\|okx]` | Downloads price data for all pairs and timeframes, then runs the data check | ✅ Phase 3 |
| `data-check` | Checks data coverage, gaps, duplicates and bad candles | ✅ Phase 3 |
| `regimes [--days 90]` | Picks bull / bear / sideways windows inside in-sample and out-of-sample | ✅ Phase 3 |
| `check-bias [--strategies …]` | Lookahead + recursive analysis on all strategies; writes `results/checks/bias_check.md` | ✅ Phase 4 |
| `backtest [--period is] [--timeframe 1h] [--fee 0.001] [--detail 5m] [--notes …]` | Backtests all strategies in one run (buy & hold always included), logs it and builds the leaderboard. Refuses out-of-sample dates without `--allow-oos` | ✅ Phase 5 |
| `report [--recompute]` | Rebuilds leaderboards, `docs/RESULTS.md` and `docs/EXPERIMENT_LOG.md` | ✅ Phase 5 |
| `exp list [--strategy X]` / `exp decide <ID> keep\|tweak\|drop "why"` | Experiment log | ✅ Phase 5 |
| `validate [--strategies …]` | Stage 1: in-sample vs out-of-sample, 0.15% fee stress, 5m fills → `results/leaderboards/stage1_1h.md` | ✅ Phase 6 |
| `hyperopt <Strategy> [--epochs 300]` | Tunes on in-sample only (seed 42, 6 workers), writes a `…T` tuned version, compares both | ✅ Phase 6 |
| `walkforward <Strategy> [--fixed]` | 8 rolling 3-month test windows: re-tuned before each, or fixed settings | ✅ Phase 6 |
| `stage2 [--strategies …]` | Stage 2: walk-forward + all 6 regime windows → promotion verdicts | ✅ Phase 6 |
| `bots up\|down\|status\|logs\|generate [names…]` | Paper-trading bots from `user_data/configs/bots.json`: one dry-run container, database, log and FreqUI port each | ✅ Phase 7 |

## Project layout

```
scripts/        lab.py (task runner), safety_check.py, report and validation scripts
user_data/      configs/ (base + overrides), strategies/, plus git-ignored data/logs/db/results
templates/      strategy_template.py - copy it to start a new strategy
results/        committed summaries: leaderboards, experiment log, hyperopt params
docs/           methodology, results, decisions, roadmap, safety, glossary
```

## Docs

- [SETUP](docs/SETUP.md): install, Docker, data download, troubleshooting
- [STRATEGIES](docs/STRATEGIES.md): each strategy's idea, rules, risk settings and status
- [TESTING_METHODOLOGY](docs/TESTING_METHODOLOGY.md): how we test, and the promotion rules
- [RESULTS](docs/RESULTS.md): current leaderboard
- [EXPERIMENT_LOG](docs/EXPERIMENT_LOG.md): every run and the decision taken
- [RISK_AND_SAFETY](docs/RISK_AND_SAFETY.md): safety rules and what going live would require
- [ROADMAP](docs/ROADMAP.md) · [DECISIONS](docs/DECISIONS.md) · [GLOSSARY](docs/GLOSSARY.md)

Some of these are written in later phases.

## Disclaimer

This is a research and learning project. Backtest results don't predict future returns. Nothing here is financial advice.
