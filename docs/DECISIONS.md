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

**2026-10-06: Hand-designed v2 strategies decide on 4h candles but run on the 1h engine.**
- Making the v2s plain 4h strategies would have split them from the 1h leaderboard, the 1h promotion rules and the 1h paper bots.
- Freqtrade's `@informative("4h")` merges *closed* 4h candles into the 1h chart, so stoploss and trailing stops are still checked every hour.
- The lookahead check passed for all 4 (30 signals each). That matters, because merged higher-timeframe data is a classic source of accidental lookahead.

**2026-10-06: Hyperopt runs with exactly 6 workers.**
- With 11 workers a worker was killed (SIGKILL, out of memory in Docker's 8 GB) after 88 of 300 epochs.
- With 6 workers, two runs with seed 42 gave the identical best epoch, settings and score. Results depend on the worker count, so it's pinned (`HYPEROPT_JOBS` in `lab.py`).
- A hyperopt run whose last epoch is below the requested count is rejected. (Freqtrade may legitimately skip a duplicate epoch.)
- The first `MacdVolumeV1` tuning (11 workers) was redone with 6 workers so `MacdVolumeV1T` is reproducible.

**2026-10-06: Tuned versions are generated `…T` subclasses.**
- Numbering tuned versions as V2 would have clashed with the hand-designed v2s. Instead, `MacdVolumeV1T` means "MacdVolumeV1 with hyperopt settings".
- The file is generated with a header recording how it was tuned (dates, loss, epochs, seed, best epoch, experiment ID). The settings are visible in the code, never in a hidden parameter file.

**2026-10-06 08:13 UTC: Stage 1 candidates chosen BEFORE any out-of-sample look.**
- **Rule (in-sample only):** from run `20261006-081119_is_1h` (all 23 versions, 1h, 0.1% fee), every strategy with profit > 0, profit factor ≥ 1.1 and at least 50 trades.
- **Candidates (10):** EmaTrendV2T, DonchianBreakoutV2T, MacdVolumeV1T, TrendPullbackV2T, MacdVolumeV1, AdxSupertrendV1T, MacdVolumeV2T, DonchianBreakoutV2, EmaTrendV2, SqueezeBreakoutV1T.
- **Why not all 23:** every extra strategy tested out-of-sample is another lottery ticket. Some would pass by luck alone. The other 13 lost money or barely broke even in-sample.
- **What "out-of-sample" means here:** these 10 have never been run on dates after 2025-10-01 (the experiment log has 0 out-of-sample looks so far). Stage 1 is run **once** on this list.
- **Known risks going in:**
  - The tuned stops of EmaTrendV2T (−3%) and several others (about −14.8%) sit at the edges of the allowed range.
  - The v2 designs were guided by in-sample results.

**2026-10-06: Stage 1 result: the tuned in-sample stars failed out-of-sample, and one hand-designed version passed.**
- Run once on the 10 pre-registered candidates. That was 3 out-of-sample runs: OOS, the 0.15% fee stress run and the 5m-fill run.
- **PASS:** `EmaTrendV2` (untuned): OOS +5.1% with 11.9% max drawdown, while buy & hold lost 35.1% (62.9% drawdown).
- **Collapsed:**
  - `EmaTrendV2T`: in-sample +72% → OOS −1%.
  - `DonchianBreakoutV2T`: +70% → −8%.
  - `MacdVolumeV1T`: +26% → −11%.
  - This is textbook overfitting: the tuner fitted settings to 2023-25 that didn't carry over.
- **Lesson:** in this lab, hand-designed structural changes (4h decisions, trend filter, fewer trades) generalised better than tuned settings. Tuning stays in the toolbox, but a tuned version gets no credit until it passes out-of-sample.

**2026-10-06: Bias checks were missing for the tuned `…T` versions; completed without a new out-of-sample look.**
- Stage 1 first failed `SqueezeBreakoutV1T` (and marked the other `…T` versions) on "bias checks not run". I hadn't run `check-bias` on generated `…T` classes.
- The bias check verifies the code reads no future data. It isn't fitted to any result, so it was run afterwards: all 11 `…T` versions passed.
- Stage 1 was then **re-scored from the saved runs** (`report.rebuild_stage1_from_saved`), with no new out-of-sample backtest.
- From now on, run `check-bias` right after `hyperopt` creates a `…T` file.

**2026-10-06: `SqueezeBreakoutV1T` REVIEW, explained.**
- It passed every Stage 1 rule but was flagged for a very small out-of-sample drawdown (2.4% < 3%).
- **Review:** the small drawdown comes from being in the market only about 1% of the time (66 trades in 2 years, short holds). It's not a sign of hidden lookahead (the bias check passed); it's just a very small strategy.
- It goes to Stage 2 for a complete verdict. Its out-of-sample return (+1.2% a year) is too small to matter in practice, whatever the verdict.

**2026-10-06: Walk-forward mode follows what is deployed (clarification after Stage 1).**
- The methodology said every walk-forward re-tunes each window. But `EmaTrendV2` passed Stage 1 **untuned**. Re-tuning it per window would test a different strategy ("EmaTrendV2 + periodic re-tuning") from the one that would be deployed.
- **Rule now:**
  - An untuned strategy gets a **fixed-settings** walk-forward: the same 8 test windows, same thresholds, nothing re-tuned.
  - A tuned `…T` version gets a **re-tuned** walk-forward of its parent.
- Both modes are run for `EmaTrendV2` for transparency. The thresholds weren't changed.

**2026-10-06: Phase 7 runs two paper bots even though nothing was promoted (your choice).**
- `EmaTrendV2` runs as a **watch-list** bot: it passed Stage 1 and failed Stage 2's consistency rule. `BuyHoldV1` runs as the **baseline**, started the same minute so the comparison is fair.
- Paper trading is free, and live prices are the cleanest out-of-sample data there is. A bot's role (`promoted` / `watch-list` / `baseline`) is written in `bots.json` and shown by `bots status`, so a watch-list bot is never mistaken for a promoted one.

**2026-10-06: Bot files are generated from one registry.**
- `bots.json` → `docker-compose.bots.yml` + `dryrun/<bot>.json`, so ports, database names, CORS origins and the `--dry-run` flag can't drift apart.
- The FreqUI login comes from `.env` through `FREQTRADE__API_SERVER__*` (Freqtrade validates the API block after merging environment variables, as confirmed by the bots starting). Optional Telegram settings come from a per-bot `.env.bot-<name>`, because one Telegram token can't be shared by two bots.

**2026-10-07: Pakistan legal facts are dated and sourced, not remembered.**
- The Pakistan section of RISK_AND_SAFETY was researched on 2026-10-07: PVARA's own site, The Block, CoinDesk, NextGen.pk, CoinMarketCap Academy.
- Each fact carries its date, because the licensing regime was mid-rollout: NOC deadline 5 Sept 2026, full licences expected Q4 2026.
- It's explicitly not legal advice and must be re-checked before any real-money decision.

**2026-10-07: The in-sample leaderboard in RESULTS carries a permanent caution.**
- Tuned `…T` versions top any in-sample table because they were tuned on it. `EmaTrendV2T` shows "beats buy & hold" there and lost money out-of-sample.
- `report.py` now always prints a warning above in-sample tables, and the RESULTS summary leads with the Stage 1 / Stage 2 verdicts.

**2026-10-07: Pre-registered test of "EmaTrendV2 re-tuned every quarter".**
- The rules are in `docs/research/quarterly-retune-preregistration.md`, approved and committed **before** any test ran.
- **Test A:** the identical Phase 6 process on 7 never-used quarters (Dec 2021 → Sep 2023). Pass if ≥ 5 of 7 quarters are profitable, efficiency ≥ 0.5, total profit > 0, and the worst quarter's drawdown ≤ 25%.
- **If it passes:** a 3rd paper bot, re-tuned quarterly, reviewed on 2027-04-01.
- **If it fails:** the idea is dropped, with no tweaking on the same data.

**2026-10-07: Quarterly re-tuning of EmaTrendV2 failed its pre-registered fresh-data test, so it's dropped.**
- **Test A** (7 never-used quarters, Dec 2021 → Sep 2023): 2 of 7 quarters profitable (needed 5), efficiency −0.84 (needed 0.5), total −12.3% (needed > 0). Only the drawdown rule passed (12.3% ≤ 25%).
- **As decided in advance:** no third paper bot and no tweaked retry on the same data.
- **Lessons:**
  - The Phase 6 near-miss came from over-used data.
  - EmaTrendV2's trend filter limits losses in crashes (−12% vs buy & hold −65%), but that's not an edge.
- Details: `docs/research/quarterly-retune-preregistration.md`.

**2026-10-07: Round 2 pre-registered: new data split, three ideas, no auto-tuning.**
- **Development:** 2023-10 → 2026-10. Round 1's out-of-sample year was looked at 9 times, so it's retired as a test and becomes building data.
- **Exam (protected holdout):** 2021-01 → 2023-10, run once.
- **Ideas:**
  - `TrendPullbackV3`: fee-aware dip buying.
  - `EmaTrendV3`: BTC 200-day market filter plus a losing-streak pause.
  - `MomentumRotationV1`: weekly top-2 by 30-day return.
- **Limits:** at most 3 versions per idea, and at most 2 per idea go to the exam, chosen by a fixed dev rule.
- **Exam rules:** see `docs/research/round2-preregistration.md`. X6 (≥ 6 of 11 quarters profitable, no quarter below −10%) replaces Round 1's 60% rule, *before* testing, because the exam holds a full crash year in which cash is the intended behaviour.

**2026-10-07: Round 2 exam candidates frozen before the exam.**
- **Candidates:** EmaTrendV3, EmaTrendV3b, MomentumRotationV1, MomentumRotationV1b, chosen by the pre-registered dev rule (`results/leaderboards/round2_selection.md`).
- **Idea A (fee-aware pullback) is dropped at the development stage:** its best profit factor was 1.01, below the 1.1 needed.
- **MomentumRotationV1 now uses a fixed 5-coin universe.** The earlier version ranked against `current_whitelist()`, and Freqtrade's lookahead check (which re-runs with only one pair) flagged that as bias. The root cause was confirmed in `freqtrade/optimize/analysis/lookahead.py`.

**2026-10-07: Round 2 exam: all 4 candidates failed, so ideas A, B and C are dropped for this round.**
- **Momentum rotation (top 3):** +452.9% on the 2021–23 holdout vs buy & hold +397.6%, Calmar 2.08 vs 0.86. But max drawdown 41.4% (cap 30%), and 5 of 11 profitable quarters with a −11.4% quarter (needed ≥ 6 and ≥ −10%).
- **EmaTrendV3 / V3b:** +2–3%, profit factor 1.04, 2 of 11 quarters profitable.
- **Thresholds are not relaxed after the fact.**
- **Lesson:** momentum rotation is the first idea whose return edge carried over to unseen data; its risk at market turns is the open problem.

**2026-10-07: Round 3 pre-registered: momentum rotation with drawdown control, judged on future data.**
- **Versions:** V2 (15% trailing stop per coin), V2b (BTC 100-day filter), V2c (both). All rebalance on Monday 12:00 UTC so a paper bot on the Mac doesn't sleep through it.
- **Selection on dev:** one version, chosen by rule: max drawdown ≤ 30%, PF ≥ 1.2, then the best Calmar. If none qualifies, the idea is dropped.
- **Exam:** a 12-month forward backtest, with a paper bot as a reality check. The 2021–23 holdout is not used.
- Details: `docs/research/momentum-drawdown-preregistration.md`.
