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

## Phase 5: Backtesting ✅
- [x] `lab.py backtest` with all strategies in one run, plus an out-of-sample guard (`--allow-oos`)
- [x] `metrics.py`: mark-to-market risk numbers from the wallet value (fixes Freqtrade's 0% drawdown for buy & hold)
- [x] `report.py` leaderboard (markdown + CSV); `rules.py` promotion rules with stage-1 verdicts ready
- [x] Experiment log (`results/experiments.jsonl` → `docs/EXPERIMENT_LOG.md`), `lab.py exp list|decide`
- [x] `docs/TESTING_METHODOLOGY.md` written *before* any out-of-sample look; a test keeps it in sync with `rules.py`
- [x] In-sample leaderboards for 1h, 15m, 4h, plus a zero-fee diagnostic: fees are the main problem
- [x] 80 trades spot-checked: entries at the next candle's open

## Phase 6: Validation ✅
- [x] Hyperopt for 11 strategies → generated `…T` tuned versions (seed 42, 6 workers, reproducibility verified)
- [x] 4 hand-designed v2s for fewer trades (4h decisions via informative timeframe), all bias-checked
- [x] In-sample regime tests for all 23 versions
- [x] 10 candidates pre-registered from in-sample results, then Stage 1 run once: out-of-sample + 0.15% fee + 5m fills
- [x] Walk-forward (fixed and re-tuned modes) and all 6 regime windows for Stage 1 survivors
- [x] Result: **no strategy promoted**. EmaTrendV2 passed Stage 1 and failed Stage 2 on consistency (watch list)

## Phase 7: Paper trading ✅
- [x] `bots.json` registry → generated `docker-compose.bots.yml` + `dryrun/<bot>.json`
- [x] One dry-run container per bot: own SQLite DB, log and FreqUI port (127.0.0.1 only)
- [x] `lab.py bots up|down|status|logs|generate`, with status reading `dry_run` back from each bot
- [x] Running: `EmaTrendV2` (watch list, not promoted) + `BuyHoldV1` baseline, started 2026-10-06
- [x] Safety: planted `dry_run=false` keeps the bot from ever starting; API rejects missing/wrong login (401)
- [x] Optional Telegram alerts documented (per-bot env file, off by default)

## Phase 8: Docs ✅
- [x] Every markdown file filled with real results (summary tables, a status line per strategy, paper-trading check-in)
- [x] `docs/GLOSSARY.md`: 87 trading and testing terms in plain English
- [x] Pakistan section in `docs/RISK_AND_SAFETY.md`: Virtual Assets Act 2026, PVARA licensing status, State Bank of Pakistan April 2026 change, with dated sources
- [x] Final all-versions in-sample leaderboard (identical to the earlier run: backtests are reproducible)

## Next steps (suggested, not scheduled)

**Watch what's running**
- [ ] Check the paper bots every week or two (`lab.py bots status`). After about 2–3 months, compare `EmaTrendV2`'s live paper results with its backtest over the same dates (`lab.py backtest --period <start>-<end> --allow-oos`).

**Follow the leads the data gave us**
- [x] **EmaTrendV2 with quarterly re-tuning:** pre-registered and tested on 7 never-used quarters (2021-12 → 2023-09) on 2026-10-07. **Failed** (2 of 7 quarters profitable, −12.3%), so it's dropped. See `docs/research/`.
- [x] **Round 2 (2026-10-07):** fee-aware pullback, EmaTrendV2 + BTC filter, momentum rotation. Pre-registered dev/holdout split and a single exam. **All failed**; momentum rotation came closest (returns held up, drawdown too high). See `docs/research/round2-preregistration.md`.
- [x] **Momentum rotation with drawdown control (Round 3, 2026-10-07):** pre-registered; all 3 versions had ~50% dev drawdowns, so it was **dropped** before any forward test. It also showed that momentum rotation is sensitive to the exact rebalance hour.
- [x] **Robustness check (2026-10-07):** `lab.py robustness` (timing, nearby settings, leave one coin out, best trades removed). Calibrated on 3 strategies; it's a gate from the next round on.
- [x] **Momentum rotation at lower exposure (Round 4):** pre-registered 2026-10-08. **Exam FAIL** (narrow): DD 24.4% vs buy & hold 74.9%, but Calmar 1.59 vs 1.65 and one quarter at −12.2%. Momentum rotation is closed for historical testing.
  - **Versions:** V3 (about 50% invested) and V3b (volatility-scaled positions).
  - **Path:** dev selection with the robustness gate, then one exam on 2019–2020 (4 coins, never touched before), then a forward test if it passes.
  - **2026-10-08:** dev selection done. **V3 picked** (DD 29.7%, ROBUST); V3b dropped (DD 42.2%). The exam ran once the same day: FAIL.
  - See `docs/research/momentum-exposure-preregistration.md`.
- [ ] **Round 5: trend at four speeds with risk-based sizing (`TrendBlend`):** pre-registered 2026-10-09. Daily trend score plus volatility sizing, built on dev, then one exam on 9 never-traded coins (2019–23). See `docs/research/trend-blend-preregistration.md`.
- [ ] **Narrower hyperopt spaces:** several tuned stops hit the edges of the allowed range. Try fewer, more meaningful parameters (or none) rather than wider ranges.
- [ ] **Fee-aware design for the strategies with a real gross edge** (Trend Pullback: +66% before fees). Use higher timeframes, or require a minimum expected move per trade larger than the round-trip fee.

**Make the lab stronger**
- [ ] **Protections:** cooldown after a stoploss, pause after a drawdown. Freqtrade supports these natively.
- [ ] **More pairs, chosen once and then frozen,** to see whether results hold beyond 5 coins.
- [ ] **A paper-vs-backtest report:** a `lab.py` command that backtests a bot's live period and puts it next to its paper trades.
- [ ] **Clean-up command** for raw output: hyperopt result files reached about 2.4 GB (`user_data/hyperopt_results/` can be deleted at any time).

**Before *any* real money (not planned)**
- [ ] Everything in [RISK_AND_SAFETY](RISK_AND_SAFETY.md) > "What would be required before ever going live", including a PVARA-licensed platform.
