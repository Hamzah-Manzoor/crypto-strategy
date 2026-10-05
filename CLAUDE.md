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
| `docker-compose.yml` | Pinned image `freqtradeorg/freqtrade:2026.9@sha256:…`, `safety` + `freqtrade` (tools) services |
| `user_data/configs/` | `base.json` (always loaded first) plus small overrides: `backtest.json`, `exchange-*.json`, `dryrun/<bot>.json` |
| `user_data/strategies/` | One file per strategy **version** (`ema_trend_v1.py` → `class EmaTrendV1`) plus shared code in the `labkit/` sub-package (`base.py`: `LabBaseStrategy`; `indicators.py`: Supertrend, Keltner, Donchian…). Freqtrade doesn't scan sub-folders, so `labkit` is never listed as a strategy |
| `templates/strategy_template.py` | Copy this to start a new strategy |
| `results/` | Committed summaries: leaderboards, experiment log, hyperopt params, walk-forward reports |
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
- **TA-Lib 0.8 is strict about types.** Pass floats where TA-Lib expects floats (`nbdev=1.0`, not `1`).
- **Lookahead analysis runs one strategy per call.** With `--strategy-list`, Freqtrade 2026.9 analyses the first strategy's trades for every strategy. `lab.py check-bias` already handles this.
- **Market loading is spot-only** (`ccxt_config.options.fetchMarkets.types = ["spot"]` in `base.json`), so runs never depend on Binance's futures API.
- Every backtest or hyperopt run through `lab.py` is logged to `results/experiments.jsonl`.

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
python3 scripts/lab.py ft -- <any freqtrade command and flags>
```
More commands (download, backtest, report, hyperopt, walkforward, bots) are added phase by phase. `README.md` has the full table.

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
