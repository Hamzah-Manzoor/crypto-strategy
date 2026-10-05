# Roadmap

Each phase ends with a review stop and one git commit.

## Phase 1: Plan ✅
- [x] Detect OS and tools (macOS 26.5, Apple Silicon, Docker 29.4, Python 3.14)
- [x] Check the current Freqtrade docs and release (2026.9)
- [x] Folder tree, file list and strategy list agreed

## Phase 2: Setup ✅
- [x] git repo with a repo-local author identity
- [x] `.gitignore` (data, logs, DBs, raw results, `.env`)
- [x] Docker Compose with the pinned image (tag + digest) and a `safety` gate service
- [x] Configs: `base.json`, `backtest.json`, `exchange-bybit.json`, `exchange-okx.json`
- [x] `safety_check.py` + 31 unit tests
- [x] `lab.py`: `setup`, `safety`, `test`, `show-config`, `ft`
- [x] Git pre-commit hook (blocks data/logs/DBs/secrets, runs the safety check)
- [x] `CLAUDE.md`, `README.md`, `DECISIONS.md`, `ROADMAP.md`, `RISK_AND_SAFETY.md`

## Phase 3: Data ✅
- [x] `lab.py download`: 5 pairs × 5m/15m/1h/4h from 2023-07-01 (extended to 2023-05-01 in Phase 4), plus BTC 1d from 2022-01-01
- [x] Fallback checked: a real Bybit download worked through `exchange-bybit.json`; OKX did not resolve via DNS (Binance used)
- [x] `data_check.py`: 100% coverage, 0 gaps (and shown to catch gaps, duplicates and bad candles)
- [x] `regimes.py`: bull / bear / sideways windows inside each split, judged on the 5-coin basket
- [x] `docs/SETUP.md`

## Phase 4: Strategies ✅
- [x] `labkit/base.py`, `labkit/indicators.py`, `templates/strategy_template.py`
- [x] 8 strategies: BuyHold, EmaTrend, AdxSupertrend, RsiBbReversion, DonchianBreakout, MacdVolume, SqueezeBreakout, TrendPullback
- [x] Lookahead analysis: no bias (7 strategies × 30 signals; a deliberately cheating strategy *was* caught)
- [x] Recursive analysis: `startup_candle_count` is enough (worst error 0.003%)
- [x] `lab.py check-bias` saves `results/checks/bias_check.md`
- [x] Hyperopt parallel workers can import `labkit` (`PYTHONPATH` set in compose)
- [x] `docs/STRATEGIES.md`

## Phase 5: Backtesting
- [ ] `lab.py backtest` with all strategies in one run
- [ ] `report.py` leaderboard (markdown + CSV) with promotion rules applied
- [ ] Experiment log (`results/experiments.jsonl` → `docs/EXPERIMENT_LOG.md`)
- [ ] `docs/TESTING_METHODOLOGY.md` (rules written down *before* looking at out-of-sample)
- [ ] In-sample leaderboards for 1h, 15m, 4h

## Phase 6: Validation
- [ ] Out-of-sample check + stress fees + 5m intra-candle detail
- [ ] Market regime tests
- [ ] Hyperopt (fixed seed) → v2 strategies
- [ ] Walk-forward for strategies that pass stage 1

## Phase 7: Paper trading
- [ ] `bots.json` registry → generated `docker-compose.bots.yml`
- [ ] One container per promoted strategy: own DB, log, FreqUI port
- [ ] `lab.py bots up|down|status|logs`
- [ ] Optional Telegram alerts documented

## Phase 8: Docs
- [ ] Every markdown file filled with real results
- [ ] `docs/GLOSSARY.md`
- [ ] Pakistan / PVARA section in `docs/RISK_AND_SAFETY.md`

## Later ideas (not scheduled)
- [ ] Protections (cooldown after losses, max-drawdown pause)
- [ ] More pairs, chosen once and then frozen, to test whether results generalise
- [ ] Multi-timeframe confirmation (e.g. 4h trend filter on 1h entries)
