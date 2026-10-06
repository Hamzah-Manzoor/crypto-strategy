# Decisions

Short log of key decisions and why. Newest at the bottom. Format: **date: decision.** Why.

---

**2026-10-06: Use Freqtrade as the engine.**
- It's mature, open source and Python. It has backtesting, hyperopt (auto-tuning), dry-run, lookahead/recursive bias checks and a web UI (FreqUI) built in.
- Writing our own engine would mean spending time on plumbing instead of strategy quality.

**2026-10-06: Run everything through Docker Compose.**
- Same engine on every machine, nothing to install except Docker, and the Python on the Mac stays untouched.
- Each paper-trading bot is its own container.

**2026-10-06: Pin `freqtradeorg/freqtrade:2026.9` by tag *and* digest (`sha256:989aff56…`).**
- 2026.9 was the latest stable release (29 Sep 2026) and has an arm64 build for Apple Silicon.
- A tag can be re-pushed. The digest can't, so the engine never changes under us.
- Upgrading means a deliberate change logged here, followed by a reference backtest.

**2026-10-06: Binance spot data, with Bybit then OKX as fallbacks.**
- Binance has the deepest liquidity and longest public history for these pairs.
- If downloads fail (for example a region block), override configs `exchange-bybit.json` / `exchange-okx.json` switch the data source without editing `base.json`.

**2026-10-06: Static whitelist BTC, ETH, SOL, BNB, XRP / USDT.**
- They're liquid, so a backtest at "candle open" prices is not far from reality.
- The list is static so results are repeatable. A dynamic "top volume" list changes every day, so a backtest couldn't be re-run with the same pairs.

**2026-10-06: Spot only, long only, no leverage.**
- Keeps the risk simple to reason about while we learn what works.
- Futures add funding fees, liquidations and shorting rules.

**2026-10-06: Fee 0.1% per side in every run, plus a 0.15% stress run.**
- 0.1% is Binance's standard spot fee without discounts.
- Freqtrade doesn't simulate slippage (getting a worse price than expected), so the 0.15% stress run stands in for it.

**2026-10-06: Market orders, priced from the "other" side of the order book.**
- A backtest assumes you buy at the candle's price.
- Market orders in dry-run behave closest to that assumption, so paper results and backtests are comparable.

**2026-10-06: Equal split of the wallet, 5 open trades max (`stake_amount: unlimited`).**
- Starting wallet is 1000 USDT. Each new trade gets an equal share of the free balance, so profits compound.
- With 5 pairs and 5 slots, no pair is ever starved. The buy-and-hold baseline naturally becomes "20% in each coin".

**2026-10-06: The FreqUI API block lives only in the per-bot dry-run configs; its secrets live only in `.env`.**
- Freqtrade 2026.9 requires `jwt_secret_key` to be 32+ characters whenever an `api_server` block exists.
- Keeping the block out of `base.json` means backtests don't need it. The bots get username, password and JWT secret from `.env` through `FREQTRADE__API_SERVER__*` variables.

**2026-10-06: Three layers of safety checks.**
1. `lab.py` runs `safety_check.py` before starting anything.
2. The compose `safety` service runs it inside Docker, and every Freqtrade service depends on it. So even a raw `docker compose run` refuses to start.
3. The git pre-commit hook runs it and blocks data, logs, DBs and `.env`.
- Bots will also run `trade --dry-run`, which makes Freqtrade itself strip exchange secrets and simulate trades.

**2026-10-06: Host scripts use the Python standard library only.**
- Nothing to pip install on the Mac.
- Anything that needs pandas runs inside the Freqtrade container, which already has it.

**2026-10-06: Hyperopt never auto-exports parameters next to the strategy (`disableparamexport`).**
- Freqtrade silently loads `<Strategy>.json` if it sits next to a strategy file. Then two backtests of the "same" strategy can use different settings without anyone noticing.
- Tuned params go into a new versioned class instead (`EmaTrendV2`), so the code always shows exactly what ran.

**2026-10-06: Data from 2023-07-01, test periods start 2023-10-01.**
- The first 3 months only "warm up" slow indicators such as a 200-candle average. No trades are scored there.
- **In-sample** is 2023-10-01 → 2025-10-01 (build and tune). **Out-of-sample** is 2025-10-01 → 2026-10-01 (check only).
- BTC daily candles also go back to 2022-01-01, only so the 200-day average used in the regime cross-check exists from the first test day.

**2026-10-06: Regime windows are picked inside each split and judged on the 5-coin basket.**
- **First attempt:** picking by BTC alone over the whole range. Its "sideways" window (May–Sep 2025) was flat for BTC (+7%) but the 5-coin basket rose +36% (the ETH/XRP rally). That isn't sideways for what we trade.
- **Second problem:** the biggest bear market (Nov 2025 → Feb 2026, basket −45%) sits entirely in out-of-sample. Using it during development would leak test data.
- **What we do now:**
  - Windows are judged on the equal-weight basket, using what prices did *inside* the window. The backward-looking BTC trend rule is kept only as a cross-check, because it lags turns.
  - Bull, bear and sideways windows are chosen separately in-sample (for development) and out-of-sample (final check only).
  - A window that moved less than 20% is labelled "weak" instead of being passed off as a trend.
- See `results/checks/regimes.md`.

**2026-10-06: Note that in-sample is bull-heavy.**
- In-sample (Oct 2023 → Oct 2025) includes two big rallies: the late-2024 US-election rally (+137% basket in 90 days) and the Feb–Mar 2024 run.
- Its worst stretch is the Feb–Apr 2025 drop (basket −28%).
- Out-of-sample contains a deeper bear (−45%). So a strategy tuned only on in-sample has never seen a long bear market. Out-of-sample is a tough but fair test.

**2026-10-06: Binance used; Bybit is the working fallback; OKX not reachable here.**
- From this connection in Pakistan, `api.binance.com`, `data.binance.vision` and `api.bybit.com` answered. A real test download through `exchange-bybit.json` worked (and was deleted afterwards).
- `www.okx.com` failed DNS lookup. The OKX override config stays for other networks.

**2026-10-06: Shared strategy code lives in the `labkit/` sub-package, with `PYTHONPATH` set in compose.**
- **Why a sub-package:** Freqtrade treats every strategy class in a *top-level* file of `user_data/strategies/` as a strategy, so a top-level base class would show up as a broken strategy. It doesn't scan sub-folders.
- **Why `PYTHONPATH`:** hyperopt's parallel worker processes failed with `ModuleNotFoundError: labkit`. Freqtrade only puts the strategy folder on the import path while it loads strategies. Setting `PYTHONPATH=/freqtrade/user_data/strategies` on the container fixed it; tested with a 2-worker hyperopt.
- **Alternative rejected:** copying helpers into every strategy file. Bugs would then be fixed in one copy and not the others.

**2026-10-06: Load spot markets only from Binance.**
- **What happened:** one hyperopt start timed out on `fapi.binance.com`, Binance's *futures* API, which CCXT queries by default even for spot.
- **What we do:** `base.json` sets `ccxt_config.options.fetchMarkets.types = ["spot"]`. That's one request instead of three, and no dependency on an API we never trade on.

**2026-10-06: Lookahead analysis runs one strategy at a time.**
- **The quirk:** with `--strategy-list`, Freqtrade 2026.9 loaded all strategies in every analysis and reported the *first* strategy's trades (Buy & Hold's never-closed trades) for all of them. As a result, every strategy came back "too few trades, test failed".
- **What we do:**
  - `lab.py check-bias` runs `--strategy` per strategy.
  - Buy & Hold is skipped there (no indicators, and its trades only close at the end).
  - Any result other than an explicit `False` counts as a failure, never as a silent pass.
- **Verified that the check really detects bias:** a throw-away strategy that peeks one candle ahead (`shift(-1)`) was flagged ("has_bias: Yes", indicator `next_close`).

**2026-10-06: Data start moved from 2023-07-01 to 2023-05-01.**
- The slowest strategies need 600 warm-up candles. On 4h candles that's 100 days, but 2023-07-01 → 2023-10-01 is only 92 days. Freqtrade would have silently started 4h tests about 8 days late.
- With data from 2023-05-01, every timeframe starts scoring on exactly 2023-10-01. Checked in the 4h log: "Loading data from 2023-06-23 … Backtesting with data from 2023-10-01".
- `lab.py download` now runs a `--prepend` pass, so older data can be added to existing files.

**2026-10-06: Open issue for Phase 5: Freqtrade's drawdown ignores open trades.**
- In the smoke backtest, Buy & Hold showed **0% drawdown** over Q1 2024, although prices dipped. Freqtrade's max drawdown is built from *closed* trades only, and Buy & Hold closes nothing until the end.
- Comparing strategies with Buy & Hold "on a risk-adjusted basis" needs drawdown from the wallet value over time (mark-to-market). The report script in Phase 5 must use Freqtrade's wallet-based metrics, or compute drawdown itself.

**2026-10-06: All risk metrics are computed from the wallet's mark-to-market value.**
- Freqtrade's headline drawdown, Sortino and Calmar only count closed trades. For buy & hold over Q1 2024 they showed 0% drawdown, Sortino −100 and Calmar −100, while the real wallet fell 17.5%.
- `scripts/metrics.py` rebuilds the wallet value at every candle from the `<strategy>_wallet.feather` file in each result zip. Our drawdown matches Freqtrade's separate wallet statistics exactly.
- Sharpe and Sortino use daily returns × √365, with a risk-free rate of 0. Calmar = CAGR ÷ max drawdown.

**2026-10-06: Leaderboards are sorted by Calmar.**
- It answers "how much did I earn per unit of worst pain", which is the honest way to compare against buy & hold.
- Raw profit would crown buy & hold in every bull market.

**2026-10-06: The fee is read from the trades, not from the config copy in the zip.**
- The config copy inside a result zip keeps the file value (0.001) even when the run used `--fee`.
- Trusting it mislabelled our zero-fee runs. It would also have silently broken the 0.15% fee stress rule.
- `metrics.py` now reads `fee_open`/`fee_close` from the trades, and fails loudly if they disagree.

**2026-10-06: Promotion rules frozen before any out-of-sample look.**
- `scripts/rules.py` and `docs/TESTING_METHODOLOGY.md` were written before running OOS. A unit test keeps the doc and the code in sync.
- Backtests that touch OOS dates refuse to run without `--allow-oos`, and those runs are marked 👁 in the experiment log.

**2026-10-06: Phase 5 finding: costs, not signals, are the main problem for most v1 strategies.**
- A zero-fee diagnostic showed 5 of 7 strategies profitable before fees in-sample (1h). After 0.1% per side, only MACD Volume stays profitable.
- The edge per trade (~0.1–0.3%) is about the size of the round-trip fee.
- Phase 6 therefore focuses on fewer, better trades: higher timeframes, stricter filters, tuning that includes fees. Zero-fee runs stay diagnostics only and never count as results.
