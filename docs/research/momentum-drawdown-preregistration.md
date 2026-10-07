# Pre-registration: Momentum rotation with drawdown control (Round 3)

**Written:** 2026-10-07, before any version below was built or tested. It's committed to git first, so the commit time proves the order.
**Status:** APPROVED by Hamzah on 2026-10-07, before any version was built or tested.

## 1. Why this idea

- **The starting point:** in Round 2, `MomentumRotationV1b` was the first strategy in this lab whose edge held up on unseen data. On the 2021–23 holdout it made **+452.9%** vs buy & hold **+397.6%** (Calmar 2.08 vs 0.86).
- **Why it still failed:** its **max drawdown of 41.4%** broke the 30% rule, and so did its consistency: 5 of 11 quarters profitable, one at −11.4%.
- **Where the losses came from:** market turns, e.g. late 2021, when it kept holding the previous month's winners for up to a week while they fell.
- **This round tests one question:** can a simple drawdown control keep most of the return while cutting the drawdown below 30%?

## 2. Data rules

| Data | Use in this round |
|---|---|
| 2021-01 → 2023-10 (Round 2 holdout) | **Not used at all.** It's spent for the momentum family; looking again would be fitting the exam. |
| 2023-10 → 2026-10 (dev) | Building the versions below, and choosing **one** of them. |
| **2026-10-08 onward (forward)** | **The exam.** Prices that don't exist yet, so nothing can have been fitted to them. |

## 3. The versions (frozen now; at most these 3)

All three are `MomentumRotationV1b` (top 3 of the 5 coins by 30-day return, positive momentum only, BTC daily close above its 200-day average, 1/3 of the wallet each), with two changes:

**Operational change, in all three:**
- **Rebalance on Monday at 12:00 UTC (5 pm in Pakistan),** using Sunday's closed daily candle.
- **Why:** the old Monday 00:00 UTC time is 5 am in Pakistan, when the Mac is likely asleep. A paper bot would then miss rebalances and its results would be meaningless.
- This is the only reason for the change. Its effect on results is measured on dev data below.

**Drawdown control (the variable being tested):**

| Version | Control | Idea |
|---|---|---|
| `MomentumRotationV2` | **15% trailing stop per coin**: sell a coin as soon as it falls 15% below its highest price since it was bought, any day of the week | Stop riding a winner all the way down while waiting for Monday |
| `MomentumRotationV2b` | **Faster market filter**: BTC daily close above its **100-day** average (instead of 200-day) | Step aside earlier when the whole market turns |
| `MomentumRotationV2c` | Both of the above | |

- **After a mid-week exit, the money stays in cash** until the next Monday rebalance.
- **No hyperopt is used.** The 15% and 100-day values are fixed here, before any test.

## 4. Choosing the one version that goes forward (dev data, by rule)

1. Each version must pass `check-bias`.
2. Run all three on dev (2023-10 → 2026-10), alongside `MomentumRotationV1b` and buy & hold.
3. **Eligible** = dev max drawdown **≤ 30%**, dev profit > 0, profit factor **≥ 1.2**, at least **30** trades.
4. **Pick the single eligible version with the highest dev Calmar.**
5. **If none is eligible, the idea is dropped** and no forward test starts. The drawdown control would have failed even on the data it was built on.
6. The pick is written into this file and committed **before** the forward test starts.

## 5. The forward exam (judged on new data only)

- **Forward period:** from the commit that freezes the pick until **12 months later**.
- **Interim review:** at 6 months. It's a report only, except for one early stop: if the forward max drawdown already exceeds 30%, the idea is dropped right then.

**Primary judge: forward backtest.** At review time, download the new candles and backtest the frozen strategy (plus buy & hold) on exactly the forward period, at 0.1% fee. This is deterministic and unaffected by the Mac sleeping or losing internet.

Pass rules at 12 months (all must hold):

| # | Rule | Threshold |
|---|---|---|
| F1 | Enough trades | ≥ 20 |
| F2 | Profitable | profit > 0 after fees **and** profit factor ≥ 1.2 |
| F3 | Survives higher costs | profit > 0 at 0.15% fee |
| F4 | Drawdown under control | max drawdown **≤ 30%** |
| F5 | Beats buy & hold, risk-adjusted | Calmar > buy & hold's Calmar over the same period |
| F6 | Consistent | ≥ 2 of the 4 quarters profitable, and no quarter worse than −10% |
| F7 | No cheating | bias checks passed |

**"Inconclusive" rather than "fail":** if Bitcoin spends more than half the forward period below its filter average and the strategy makes fewer than 20 trades as a result, the verdict is **inconclusive** and the test is extended by 6 months with the same rules. Sitting out a bear market is the intended behaviour, not a failure, but it isn't proof of an edge either.

**Secondary check: paper bot (reality check, not the judge).** The chosen version also runs as a `watch-list` paper bot (`momentum-rotation`, FreqUI port 8083). At each review, its paper trades are compared with the forward backtest for the weeks the bot was running:
- **They match** (same coins bought at ≥ 90% of rebalances, P/L within ±5 percentage points): the backtest is a faithful picture of how the bot behaves.
- **They don't match:** find the cause (missed rebalances, connection drops, order-book prices) and write it down **before** trusting either number.

**If it passes:** it becomes this lab's first **promoted** strategy. That means paper trading under the `promoted` label. Real money stays forbidden by the project's hard rules; going live would need everything in RISK_AND_SAFETY, including a PVARA-licensed platform.

**If it fails:** momentum rotation with these controls is dropped. Any further change is a new idea with its own pre-registration and its own fresh forward period.

## 6. Results

_To be filled in at each stage, without editing anything above this line._
