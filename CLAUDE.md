# CLAUDE.md: context for Claude Code sessions

## Project goal
Crypto Strategy Lab: a Freqtrade-based lab for **testing many crypto spot trading strategies side by side** and improving them step by step, with honest validation. Strategy quality matters here; fancy infrastructure doesn't.

## Hard rules (never break these)
1. **No real money.** Only backtests and dry-run (paper trading). Never set `dry_run: false`.
2. **No API keys anywhere.** Exchange `key`/`secret`/`password` fields stay empty. Never add `FREQTRADE__EXCHANGE__KEY`-style variables. Dry-run only needs public price data.
3. **Safety check before every bot start.** `scripts/safety_check.py` runs automatically: from `lab.py`, from the compose `safety` service (every Freqtrade container depends on it) and from the git pre-commit hook. Never bypass it (no `--no-deps`, no `--no-verify`) and never weaken it to make something pass.
4. **Never commit** downloaded data, logs, databases, raw backtest/hyperopt output or `.env`. Summaries go in `results/`.

## Layout
| Path | What |
|---|---|
| `scripts/lab.py` | Task runner, the single entry point (stdlib only). `python3 scripts/lab.py --help` |
| `scripts/safety_check.py` | The safety gate (tests in `tests/test_safety_check.py`) |
| `scripts/metrics.py` | (container) result zip → `results/runs/<run>.json`, mark-to-market risk metrics |
| `scripts/report.py`, `rules.py` | leaderboards, stage-1/2 verdicts, `docs/RESULTS.md` auto block; `rules.py` = the only place thresholds live |
| `scripts/experiments.py`, `tuning.py`, `bots.py` | experiment log; hyperopt / walk-forward helpers; paper-bot generation + status client |
| `docker-compose.bots.yml` | GENERATED from `user_data/configs/bots.json`: one dry-run bot per entry |
| `docker-compose.yml` | Pinned image `freqtradeorg/freqtrade:2026.9@sha256:…`, `safety` + `freqtrade` (tools) services |
| `user_data/configs/` | `base.json` (always loaded first) plus small overrides: `backtest.json`, `exchange-*.json`, `dryrun/<bot>.json` |
| `user_data/strategies/` | One file per strategy **version** (`ema_trend_v1.py` → `class EmaTrendV1`) plus shared code in the `labkit/` sub-package (`base.py`: `LabBaseStrategy`; `indicators.py`: Supertrend, Keltner, Donchian…). Freqtrade doesn't scan sub-folders, so `labkit` is never listed as a strategy |
| `templates/strategy_template.py` | Copy this to start a new strategy |
| `results/` | Committed summaries: `runs/` (one JSON per backtest), `leaderboards/`, `experiments.jsonl`, `hyperopt/`, `walkforward/`, `checks/`, `regimes.json` |
| `docs/` | Methodology, results, decisions, roadmap, safety, glossary |

## Conventions
- **Host Python is stdlib only.** Anything needing pandas runs inside the container (`docker compose run --rm --entrypoint python freqtrade scripts/<x>.py`). `scripts/` is mounted at `/freqtrade/scripts`.
- **Configs are strict JSON** (no comments) so the safety check can parse them. Secrets (FreqUI password, JWT, Telegram) live only in `.env` as `FREQTRADE__SECTION__KEY` variables.
- **Fees:** 0.1% per side (`"fee": 0.001`) in every run. Stress runs use 0.15%.
- **Pairs are static:** BTC, ETH, SOL, BNB, XRP against USDT (StaticPairList). Main timeframe is 1h; 15m and 4h through a `--timeframe` override.
- **Strategy versioning:** never edit a version that has logged results. Make `xxx_v2.py` with `class XxxV2(XxxV1)` and add a "Changes vs v1" line in the docstring. Tuned params get baked into the new version's `buy_params`/`sell_params`. Hyperopt runs with `--disable-param-export`, so Freqtrade never silently auto-loads a `.json` next to a strategy.
- **Strategy comments explain the trading idea**, not the Python.
- **Shared strategy code:**
  - Import it with `from labkit.base import LabBaseStrategy` and `from labkit.indicators import ...`.
  - This also works inside hyperopt's parallel worker processes, because `docker-compose.yml` sets `PYTHONPATH=/freqtrade/user_data/strategies`. Don't remove that line.
- **Partial sells in `adjust_trade_position` are counted in purchase cost, not market value.**
  - Freqtrade sells `|returned stake| × trade.amount / trade.stake_amount`.
  - To sell X USDT at today's price, return `-X / (trade.amount × rate) × trade.stake_amount`.
  - TrendBlendV1 got this wrong: winners were over-trimmed, or not trimmed at all. See `TrendBlendV2`.
- **Strategies that size positions themselves** (custom stake, top-ups, trims) need an order replay check (e.g. `scripts/round5_position_check.py`), because Freqtrade's lookahead check only looks at signals.
- **Slow strategies:** `check-bias` re-runs lookahead analysis on the whole dev window when the 6-month window has fewer than 10 usable trades.
- **TA-Lib 0.8 is strict about types.** Pass floats where TA-Lib expects floats (`nbdev=1.0`, not `1`).
- **Lookahead analysis runs one strategy per call.** With `--strategy-list`, Freqtrade 2026.9 analyses the first strategy's trades for every strategy. `lab.py check-bias` already handles this.
- **Market loading is spot-only** (`ccxt_config.options.fetchMarkets.types = ["spot"]` in `base.json`), so runs never depend on Binance's futures API.
- Every backtest or hyperopt run through `lab.py` is logged to `results/experiments.jsonl`.
- **Results pipeline:**
  - `lab.py backtest` → Freqtrade zip in `user_data/backtest_results/<run_id>/` (ignored).
  - `scripts/metrics.py` (container, pandas) → `results/runs/<run_id>.json`.
  - `scripts/report.py` → `results/leaderboards/` and `docs/RESULTS.md`.
  - `scripts/experiments.py` → `docs/EXPERIMENT_LOG.md`.
- **Risk metrics are mark-to-market.** Never use Freqtrade's trade-based `max_drawdown`/`sortino`/`calmar`: they ignore open trades.
- **The fee is read from the trades, not the zip's config copy.** The copy ignores `--fee`.
- **Promotion thresholds live only in `scripts/rules.py`.** `docs/TESTING_METHODOLOGY.md` must match them (a test checks this). Changing a threshold needs a DECISIONS entry.
- **Zero-fee runs are diagnostics only.** They're logged as `diagnostic` and are never a result.
- **Tuning:**
  - `lab.py hyperopt X` writes a generated `XT` subclass. Never hand-edit it. Run `lab.py check-bias --strategies XT` right after.
  - Hyperopt uses exactly 6 workers: 11 ran out of memory, and results depend on the worker count.
- **Robustness gate (from Round 4 on):**
  - A candidate must be ROBUST in `lab.py robustness <Strategy>` (dev data) before it can be chosen for any exam or forward test. Rules: TESTING_METHODOLOGY section 11.
  - Neighbour settings for R2 go in the strategy class (`ROBUSTNESS_GRID`), or for frozen strategies in `user_data/strategies/labkit/robustness_grids.py`. Write them **before** running the check.
- **New research ideas get a pre-registration file** in `docs/research/` (process, data, pass rules, what happens on pass or fail). Commit and push it **before** running the test, then append the results below it without editing the rules.
- **Round 2 split:**
  - **Development:** 2023-10 → 2026-10 (`--period dev`).
  - **Protected holdout:** 2021-01 → 2023-10 (`--period holdout`). `lab.py` refuses it without `--allow-holdout`, and tuning on it is refused.
  - **The Round 2 exam has used it** for ideas A, B and C (pullback, EmaTrend + BTC filter, momentum rotation). Treat it as *used* for those idea families; a new family may use it once with its own pre-registration.
- **Round 4 exam period `exam2019` (2019-01 → 2021-01):**
  - 1h and 1d data exist only for BTC, ETH, BNB and XRP (from 2018-05). SOL listed in Aug 2020.
  - It's protected like the holdout, and it was **used once by the Round 4 momentum exam** (failed). Treat it as *used* for the momentum family.
- **Round 5 exam coins** (NEO, LTC, QTUM, ADA, IOTA, XLM, ONT, TRX, ETC; `rules.ROUND5_EXAM_COINS`):
  - 1h/1d data from their 2018 listings. No strategy here may trade them outside the Round 5 exam; `lab.py` refuses it.
  - The exam period is `exam5` (2019-01 → 2023-10).
- **Data before 2023-10-01 (1h and 4h go back to 2020-08-11):** the 7 quarters 2021-12 → 2023-09 were used once, for the quarterly re-tuning test. Treat them as *used* for that idea. Any other idea testing on them needs its own pre-registration.
- **Out-of-sample is precious:**
  - Choose candidates by a written in-sample rule first (log it in DECISIONS), then run `lab.py validate` **once**.
  - To re-score after fixing something that isn't fitted to results (e.g. bias checks), use `lab.py report`. It rebuilds Stage 1 from saved runs, without a new OOS look.
- **Walk-forward mode must match what would be deployed:** `--fixed` for untuned strategies, re-tuned (default) for the parent of a `…T`.
- **Paper bots:**
  - Edit only `user_data/configs/bots.json`. `docker-compose.bots.yml` and `user_data/configs/dryrun/*.json` are generated by `lab.py bots generate/up`.
  - A bot's role is `promoted` (passed both stages), `watch-list` (observation only) or `baseline`. Never label a strategy `promoted` unless `results/leaderboards/stage2_1h.json` says PASS.

## How to add a strategy
1. `cp templates/strategy_template.py user_data/strategies/my_idea_v1.py`, then rename the class to `MyIdeaV1`.
2. Fill in the docstring (idea / works when / fails when), indicators, entry/exit, stoploss, ROI, hyperopt params.
3. Hyperopt params must **not** be read inside `populate_indicators` (Freqtrade 2026.8+ warns about this). Precompute variants with `.range` and pick one in `populate_entry_trend`.
4. Set `startup_candle_count` to at least 3× the longest indicator period. Verify with `lab.py check-bias`.
5. Add a section to `docs/STRATEGIES.md`, run a backtest, and check the leaderboard.

## How to run things
```
python3 scripts/lab.py setup        # first time: folders, .env, git hook, image
python3 scripts/lab.py safety       # safety check on its own
python3 scripts/lab.py test         # unit tests (must pass before every commit)
python3 scripts/lab.py show-config  # merged config as Freqtrade sees it
python3 scripts/lab.py download     # candles (re-run to top up), then data check
python3 scripts/lab.py data-check   # coverage / gaps report
python3 scripts/lab.py regimes      # bull / bear / sideways windows per split
python3 scripts/lab.py check-bias   # lookahead + recursive analysis, must PASS for every strategy
python3 scripts/lab.py backtest     # all strategies, in-sample, 1h -> leaderboard + experiment log
python3 scripts/lab.py hyperopt X   # in-sample tuning -> generated XT (then check-bias XT)
python3 scripts/lab.py validate --strategies ...   # stage 1 (OOS look - pre-register candidates first)
python3 scripts/lab.py walkforward X [--fixed]     # stage 2 input
python3 scripts/lab.py stage2 --strategies ...     # stage 2 verdicts
python3 scripts/lab.py report       # rebuild leaderboards / RESULTS / EXPERIMENT_LOG (no Docker needed)
python3 scripts/lab.py exp decide <ID> keep|tweak|drop "why"
python3 scripts/lab.py bots up|down|status|logs    # paper bots from user_data/configs/bots.json
python3 scripts/lab.py ft -- <any freqtrade command and flags>
```
`README.md` has the full command table; `<command> --help` lists every option.

## What NOT to do
- Don't add API keys, set `dry_run: false`, switch to futures/margin, or bind ports to anything other than `127.0.0.1`.
- Don't run `freqtrade trade` without `--dry-run`, or outside the compose setup.
- Don't tune (hyperopt) on out-of-sample dates, and don't keep re-checking OOS while iterating. Every look at OOS is logged.
- Don't trust a backtest that looks too good (huge profit, few trades, tiny drawdown). Treat it as a bug or overfitting until proven otherwise.
- Don't change the pinned Freqtrade version casually. If you do, log it in `docs/DECISIONS.md` and re-run a reference backtest.
- Don't claim something works without running it and showing the output.

## Working style the user wants
- Plain, simple English. Short bullet points. Explain any jargon in one line.
- The project is built in phases (see `docs/ROADMAP.md`). Stop after each phase for review, and commit once per phase.
