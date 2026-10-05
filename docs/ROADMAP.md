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

## Phase 3: Data
- [ ] `lab.py download`: 5 pairs × 5m/15m/1h/4h from 2023-07-01
- [ ] Bybit / OKX fallback tested if Binance fails
- [ ] `data_check.py`: coverage and gap report
- [ ] `regimes.py`: bull / bear / sideways windows from BTC data
- [ ] `docs/SETUP.md`

## Phase 4: Strategies
- [ ] `lab_base.py`, `lab_indicators.py`, `templates/strategy_template.py`
- [ ] 8 strategies: BuyHold, EmaTrend, AdxSupertrend, RsiBbReversion, DonchianBreakout, MacdVolume, SqueezeBreakout, TrendPullback
- [ ] Lookahead analysis: no bias
- [ ] Recursive analysis: `startup_candle_count` is enough
- [ ] `docs/STRATEGIES.md`

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
