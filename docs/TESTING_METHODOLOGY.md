# Testing methodology

**The question:** does a strategy have a real, repeatable edge after costs, or did it just get lucky on the data we tested it on?

The rules below were written on **2026-10-06, before any out-of-sample result was looked at**. They live in code in `scripts/rules.py`, and a unit test fails if this page and the code disagree. Changing a threshold later needs a dated entry in [DECISIONS](DECISIONS.md) explaining why.

---

## 1. Data and periods

| Period | Dates | Used for |
|---|---|---|
| Warm-up | 2023-05-01 → 2023-10-01 | Indicators settle (up to 600 candles). No trades are scored. |
| **In-sample (IS)** | 2023-10-01 → 2025-10-01 (24 months) | Building, comparing and tuning strategies |
| **Out-of-sample (OOS)** | 2025-10-01 → 2026-10-01 (12 months) | **Checking only.** Never tuned on. |

- **Data:** Binance spot, BTC/ETH/SOL/BNB/XRP against USDT. 1h is the main timeframe; 15m and 4h are secondary (same strategies, `--timeframe` override).
- **Out-of-sample discipline:**
  - Any backtest that touches a date after 2025-10-01 refuses to run without `--allow-oos`.
  - Every such run is marked 👁 in the [experiment log](EXPERIMENT_LOG.md) and counted.
  - Iterating while repeatedly peeking at OOS slowly turns it into in-sample. The count makes that visible.
- **The periods aren't alike:**
  - In-sample is **bull-heavy**: the late-2024 election rally took the basket up 137% in 90 days.
  - Out-of-sample contains a **deep bear market** (basket −45%, Nov 2025 → Feb 2026), then a recovery.
  - A strategy tuned on in-sample has never seen a long bear market, so OOS is a hard but fair test.

## 2. Costs and fill assumptions

- **Fee 0.1% per side** (Binance spot standard) in every run, so a round trip costs 0.2%.
- **Market orders**, filled at the open of the candle after the signal. Freqtrade never lets a signal trade on the candle that produced it.
- **Slippage isn't simulated by Freqtrade.** Two checks cover it:
  - **Stress run** at **0.15% per side**. A strategy must still be profitable out-of-sample at that cost.
  - **Intra-candle detail** (`--detail 5m`). Freqtrade replays each 1h candle as twelve 5m candles, so stoploss, take-profit and trailing-stop hits happen in a realistic order. A big gap between the 1h and 1h+5m results is a red flag.
- **Wallet:**
  - 1000 USDT, at most 5 open trades (one per coin).
  - Each new trade gets an equal share of the free balance (`stake_amount: unlimited`), so profits compound.
  - 1% is always kept in cash.

## 3. How results are measured

`scripts/metrics.py` reads Freqtrade's result zip. **Every risk number comes from the wallet's mark-to-market value at every candle**: cash plus every coin at that candle's price.

Freqtrade's own drawdown, Sortino and Calmar only count *closed* trades. In a test they showed **0% drawdown** for buy & hold over a period when the real wallet fell **17.5%**. Ours matches Freqtrade's separate wallet statistics exactly (checked: 17.5152% and 13.1375%).

| Metric | Meaning | Formula |
|---|---|---|
| Profit % | total return after all fees | final ÷ start − 1 |
| CAGR % | yearly growth rate | (final ÷ start)^(365 ÷ days) − 1 |
| Max DD % | worst fall of the wallet from a previous peak | max(1 − value ÷ running peak) |
| Sharpe | return per unit of ups-and-downs | mean daily return ÷ std × √365 |
| Sortino | return per unit of *downside* moves | mean daily return ÷ downside deviation × √365 |
| Calmar | return per unit of worst pain | CAGR ÷ max DD |
| Profit factor | gross wins ÷ gross losses | n/a with no losing trade |
| Win % | share of trades that made money | |
| Avg hold | average time a trade stays open | |
| In market | average share of the wallet held in coins | |
| IS→OOS Sharpe kept | how much of the edge survived out-of-sample | OOS Sharpe ÷ IS Sharpe |

Leaderboards are **sorted by Calmar**. Ignoring risk, buy & hold wins almost every bull market. The value of an active strategy is earning similar money with much less drawdown, or protecting the wallet in bear markets.

## 4. The baseline

`BuyHoldV1` buys all 5 coins (20% each) at the start and holds them. It's added to **every** backtest automatically. "Beats buy & hold" always means **on a risk-adjusted basis** (Calmar), never on raw profit alone.

## 5. Bias checks (`lab.py check-bias`)

| Check | What it catches | Pass rule |
|---|---|---|
| Lookahead analysis | Signals or indicators that use future candles | `has_bias` exactly False, over 30 signals × 5 pairs (Jan–Jun 2024; from 2026-10-07 the window ends 3 Jul 2024, see DECISIONS) |
| Recursive analysis | Indicators that need more warm-up history than the strategy asks for | Worst indicator error ≤ 0.05% at the strategy's own `startup_candle_count` (BTC/USDT, 2024) |

- The lookahead check was shown to work: a deliberately cheating strategy was flagged.
- Results are saved in `results/checks/bias_check.json`, and the promotion rules read them.

## 6. Market regimes (`lab.py regimes`)

Windows are 90 days, picked on the **5-coin basket** (what we trade) by what prices did *inside* the window. They're chosen separately inside each split, so regime tests never leak OOS data into development.

| Window | Dates | Basket | Basket max DD | BTC | Use |
|---|---|---:|---:|---:|---|
| `bull-is` | 2024-10-26 → 2025-01-23 | +137.4% | 16.5% | +55.8% | development |
| `bear-is` | 2025-01-26 → 2025-04-25 | −27.9% | 40.6% | −9.7% | development |
| `sideways-is` | 2024-04-04 → 2024-07-02 | −6.3% | 17.7% | −5.8% | development |
| `bull-oos` | 2026-06-28 → 2026-09-25 | +54.7% | 6.9% | +40.1% | final check only |
| `bear-oos` | 2025-11-08 → 2026-02-05 | −44.7% | 46.8% | −39.1% | final check only |
| `sideways-oos` | 2026-03-04 → 2026-06-01 | +0.8% | 13.9% | +4.5% | final check only |

- Regime tests use the **untuned v1** settings. A tuned version would otherwise look good partly because it was tuned on the same dates.
- Run them with `lab.py backtest --period bull-is` (and so on).

## 7. Tuning (hyperopt), Phase 6

| Setting | Value | Why |
|---|---|---|
| Data | In-sample only | Tuning on OOS would make OOS meaningless |
| Loss | `CalmarHyperOptLoss` | Optimise return per unit of drawdown, matching how we rank |
| Spaces | `buy sell stoploss` (not `roi`) | ROI tables overfit very easily |
| Epochs | 300 | |
| Seed | `--random-state 42` | Reproducible (see below) |
| Workers | 6 parallel (`-j 6`) | 11 workers ran Docker's 8 GB out of memory and a worker was killed mid-run |
| `--min-trades` | 50 | Throws away "great" results that come from a handful of trades |
| Parameter grids | Short lists of sensible values | Coarse grids overfit less than fine ones |

- **Reproducibility, verified 2026-10-06:**
  - Two runs of `MacdVolumeV1` with seed 42 and 6 workers gave the **identical** best epoch (134), settings and score.
  - The result depends on the worker count, so the count is fixed at 6.
  - A run that stops early (the last epoch number is below the requested count) is rejected.
  - Freqtrade may skip an epoch whose settings repeat an earlier one. That's normal.
- **Tuned settings become a new, generated class** named with a `T`: `MacdVolumeV1T(MacdVolumeV1)`, with the values written into the code and a header recording how it was tuned. They're never loaded from a hidden parameter file.
- `lab.py hyperopt` then backtests the parent and the tuned version side by side on in-sample.
- **A tuned version always looks better in-sample, because that's where it was tuned.** It must pass the same out-of-sample rules as everything else.
- **Freqtrade's Calmar loss uses closed-trade drawdown internally.** That's fine for strategies that hold for hours or days. Our leaderboards still judge everything on the mark-to-market numbers.

## 8. Walk-forward, Phase 6

For strategies that pass Stage 1 (`lab.py walkforward <Strategy>`):
1. Tune on 12 months, test on the next 3 months, then slide forward 3 months.
   - That gives **8 test windows**, from 2024-10-01 to 2026-10-01: 4 in in-sample dates, 4 in out-of-sample dates.
2. Each window is re-tuned only on the 12 months before it. Settings: Calmar loss, 150 epochs, seed 42, at least 25 trades.
   - The tuned settings go into a uniquely named throwaway class, `XxxWF3`.
3. Only the test windows are scored, at the normal 0.1% fee. Buy & hold over the same windows is shown for comparison.
4. **The thing walk-forwarded must be the thing deployed** (clarified 2026-10-06, see DECISIONS):
   - **Tuned `…T` version:** *re-tuned* walk-forward of its parent (`lab.py walkforward <Parent>`). The `…T` was produced by tuning, so the tuning process is what gets tested.
   - **Untuned strategy (default settings):** *fixed-settings* walk-forward (`lab.py walkforward <Strategy> --fixed`). There's nothing to tune, so the deployed settings are scored window by window. The "training" window is the same strategy over the preceding 12 months, used for the efficiency ratio.

- **Walk-forward efficiency** = yearly return on the test windows ÷ yearly return on their training windows. Near 1 means the tuning carries forward; near 0 or negative means it was fitting noise.

## 9. Overfitting warning signs

Treat a result as a bug or as overfitting until proven otherwise if you see any of these:
- **Too good:** Sharpe above 3, win rate above 80%, profit factor above 3, or drawdown below 3% over months of crypto. The report flags these automatically.
- **Too few trades:** under 30. A handful of lucky trades can look like genius.
- **Big in-sample vs out-of-sample gap:** less than half of the in-sample Sharpe survives.
- **A "best" setting in a narrow spike:** neighbouring values do much worse. Real edges sit on plateaus.
- **One pair or one month makes all the money:** check `results_per_pair` and the monthly breakdown.
- **Breaks with small changes:** a slightly higher fee (stress run) or 5m intra-candle fills (`--detail 5m`) wreck the result.
- **Many versions tried on the same data:** with enough tries, something always looks good by chance. The experiment log counts the tries.

## 10. Promotion rules

A strategy goes to paper trading (Phase 7) only after passing **both** stages, on the 1h timeframe.

### Stage 1: in-sample vs out-of-sample (`lab.py validate`)

| # | Rule | Threshold |
|---|---|---|
| 1 | Enough trades | ≥ 50 in-sample **and** ≥ 20 out-of-sample |
| 2 | Drawdown under control | OOS max DD ≤ 25%, **and** smaller than buy & hold's OOS max DD |
| 3 | Actually profitable | OOS profit > 0, **and** OOS profit factor ≥ 1.2 |
| 4 | Survives higher costs | OOS profit still > 0 at 0.15% fee per side |
| 5 | Beats buy & hold, risk-adjusted | OOS Calmar > buy & hold's OOS Calmar |
| 6 | Edge survives out-of-sample | IS Sharpe > 0, **and** OOS Sharpe ≥ 50% of IS Sharpe |
| 7 | No cheating | Lookahead and recursive checks passed |
| 8 | Not "too good to be true" | No flag from section 9 (else status **REVIEW**: a human must explain it first) |

Statuses:
- **PASS:** all rules pass.
- **FAIL:** any of rules 1–7 fails.
- **REVIEW:** rules 1–7 pass but rule 8 flags something.

### Stage 2: robustness (Phase 6)

| # | Rule | Threshold |
|---|---|---|
| 9 | Walk-forward consistency | ≥ 60% of walk-forward test windows profitable |
| 10 | Walk-forward efficiency | ≥ 0.5 |
| 11 | No regime wipe-out | Max DD ≤ 30% in every regime window (bull, bear, sideways; IS and OOS) |

**After promotion:** the strategy paper-trades as its own dry-run bot. It's watched for the gap between paper results and backtest results, which is the last reality check.

---

**How it went when these rules were applied (Phases 5–6):** 23 versions were tested, and 10 were pre-registered for Stage 1. 1 passed and 1 was flagged REVIEW; both then failed Stage 2, so none was promoted. The full story is in [RESULTS](RESULTS.md), and every run is in the [experiment log](EXPERIMENT_LOG.md).

---

## 11. Robustness check (added 2026-10-07)

**Why:** Round 3 showed that moving momentum rotation's rebalance by 12 hours nearly halved its profit. A real edge must survive small, arbitrary changes. The full plan is in `docs/research/robustness-check-plan.md`.

It runs on **dev data only** (`lab.py robustness <Strategy>`). From the next research round on, it's a **gate before any exam or forward test**.

| Check | What gets varied | Passes if |
|---|---|---|
| R1 Timing | Weekly strategies: a rebalance slot every 6 hours (28 slots). Signal strategies: signals acted on 1, 2, 3 candles late | ≥ 80% of variants profitable **and** median variant Calmar ≥ 50% of the original's |
| R2 Nearby settings | Each declared setting moved to its neighbours, one at a time | ≥ 80% of variants profitable **and** median variant Calmar ≥ 50% of the original's |
| R3 Leave one coin out | 5 runs, each without one coin | all 5 profitable **and** median Calmar ≥ 50% of the original's |
| R4 Concentration | Remove the 3 best trades from the original's trade list | profit still > 0 |

- **Verdict:** ROBUST only if every applicable check passes, otherwise FRAGILE.
- **Skipped:** checks that can't apply (e.g. no settings to vary).
- **N/A:** the original isn't profitable.
