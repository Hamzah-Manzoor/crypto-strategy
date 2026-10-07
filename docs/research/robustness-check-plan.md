# Plan: a robustness check for every strategy

**Written:** 2026-10-07. **Status:** APPROVED by Hamzah on 2026-10-07, before the check was built or run.

## 1. Why

- **What happened:** Round 3 found that moving momentum rotation's weekly rebalance by just 12 hours nearly halved its dev profit (+363% → +207%), even though it bought the same coins in 42 of 45 weeks. Nothing in our pipeline would have caught that before an exam.
- **The principle:** a real edge shouldn't depend on one arbitrary choice: the exact hour, one exact setting, one lucky coin, or a few lucky trades.
- **The goal:** a check that **pokes each of those choices and sees whether the result survives.** It runs on **dev data only**, so it never uses protected test data, and it becomes a gate that any future candidate must pass *before* an exam or forward test.

## 2. The four checks

Every check runs the strategy many times with one thing changed, in **one Freqtrade run** (`--strategy-list`), on the dev period (2023-10 → 2026-10) at the normal 0.1% fee.

| # | Check | What gets varied | Why |
|---|---|---|---|
| **R1** | **Timing** | *Weekly strategies* (those that declare a rebalance day/hour): the rebalance slot every 6 hours across the week, **28 variants**. *Signal strategies* (everything else): entries and exits executed **1, 2 and 3 hours late**, 3 variants. | Catches results that depend on the exact hour (the Round 3 problem) |
| **R2** | **Neighbouring settings** | Each key setting moved to nearby values, one at a time (e.g. lookback 30 → 20, 25, 35, 40 days; EMA 21 → 16, 26). The neighbours are written into the strategy's code (`ROBUSTNESS_GRID`) **before** the check is run on it. | A real edge sits on a plateau, not a narrow spike |
| **R3** | **Leave one coin out** | 5 runs, each without one of the 5 coins | Catches results that come from one coin's lucky run (e.g. SOL ×170 in 2021) |
| **R4** | **Concentration** | No re-run: from the original's trade list, the profit after removing its 3 best trades | Catches results that come from a few lucky trades (`MomentumRotationV1`: 80% of dev profit from 3 trades) |

**How R1 delays signals without cheating:** the "late" variants take the strategy's own buy and sell signals and act on them 1–3 candles *later*, `signal.shift(k)`. That uses only past information, so it can't introduce lookahead. `check-bias` still runs on every generated variant class.

## 3. Pass rules (fixed now, before the check is run on any strategy)

| Check | A strategy passes if… |
|---|---|
| R1 Timing | ≥ **80%** of the variants are profitable **and** the median variant's Calmar is ≥ **50%** of the original's |
| R2 Settings | ≥ **80%** of the variants are profitable **and** the median variant's Calmar is ≥ **50%** of the original's |
| R3 Coins | **all 5** leave-one-out runs are profitable **and** their median Calmar is ≥ **50%** of the original's |
| R4 Concentration | profit is still **> 0** after removing the 3 best trades |

**Overall:** ROBUST only if every check that applies passes. Otherwise FRAGILE, with the failing checks named.
- **Skipped checks:** a check is skipped only where it can't apply, e.g. R2 when a strategy has no adjustable settings, like buy & hold. The report says so.
- **Unprofitable originals:** if the original isn't profitable on dev, the result is "not applicable"; there's nothing to protect.

## 4. Where it fits in the pipeline (from the next round on)

```
build on dev → check-bias → ROBUSTNESS (new gate) → choose candidates → exam / forward test → paper bot
```

- **Future pre-registrations** must require ROBUST on dev before a version can be chosen for an exam or forward test.
- **Past verdicts (Rounds 1–3) are not changed.** The check is only applied to old strategies as a calibration (step 6), never to rescue them.

## 5. What gets built

| File | Change |
|---|---|
| `scripts/robustness.py` | Generates the variant classes into a throwaway folder (`user_data/walkforward/robust_<id>/`, git-ignored), the same way walk-forward does. Then it runs them, reads the results and applies the rules. |
| `scripts/rules.py` | `ROBUSTNESS` thresholds plus a verdict function (the only place the numbers live) |
| `scripts/lab.py` | `python3 scripts/lab.py robustness <Strategy> [--checks R1 R2 R3 R4]`. Dev only: protected data is refused. |
| Strategy files | An optional `ROBUSTNESS_GRID = {"LOOKBACK_DAYS": [20, 25, 35, 40], …}` per strategy, for R2 |
| `results/robustness/<strategy>_<date>.md/.json` | The report (committed): every variant's profit, drawdown and Calmar, and each check's verdict |
| `docs/TESTING_METHODOLOGY.md` | New section with the rules; a test keeps it in sync with `rules.py` |
| `tests/` | Unit tests: variant generation (valid Python, correct shifts, correct coin lists), the verdict rules, the doc sync |

## 6. Calibration (proving the check works, like the "cheating strategy" for lookahead)

On **dev data only**, run the full check on three existing strategies, with the expectations written down *now*:

| Strategy | Expected | Why |
|---|---|---|
| `MomentumRotationV1b` | **Large spread in R1 (timing)** and possibly a weak R4 | We already know a 12h shift costs ~45% of its dev profit. Its top-2 sibling `MomentumRotationV1` made ~80% of its dev profit from 3 trades. |
| `EmaTrendV2` | Unknown, a genuine first look | The current watch-list paper bot |
| `BuyHoldV1` | R1 and R2 skipped (no timing, no settings); R3 passes; R4 passes | A sanity reference |

- **What calibration is for:** to see whether the check flags what we *know* is fragile.
- **What it can't do:** if it doesn't flag MomentumRotationV1b, the thresholds still **aren't** loosened or tightened after seeing the numbers. Any change would be a dated DECISIONS entry, applied only from the next round on.

## 7. Steps and review stops

1. **Commit this plan** and the thresholds in `rules.py` and the methodology doc, before running anything.
2. **Build** `robustness.py`, the command and the tests. All tests must pass.
3. **Run the calibration (section 6),** commit the reports, and **stop to show you the results.**

**Cost:** about 10–20 minutes per strategy on this Mac. The 28 timing variants run in one Freqtrade run.

## 8. Calibration results (2026-10-07, dev data 2023-10 → 2026-10)

Reports: `results/robustness/`. Thresholds were unchanged throughout.

| Strategy | R1 Timing | R2 Settings | R3 Coins | R4 Best 3 trades removed | Verdict | Matched expectation? |
|---|---|---|---|---|---|---|
| `BuyHoldV1` | skipped | skipped (no settings) | ✅ 5/5 profitable, median Calmar 87% | ✅ +493 USDT left | **ROBUST** | ✅ as expected |
| `EmaTrendV2` | ✅ 3/3 profitable when signals are 1–3h late, median 124% | ✅ 4/4, median 85% | ✅ 5/5, median 54% | ✅ +126 USDT left (65% from top 3) | **ROBUST** | first look |
| `MomentumRotationV1b` | ✅ **28/28 slots profitable** (+207% … +520%), median Calmar 85% | ✅ 6/6, median 78% | ✅ 5/5 (still +236% without SOL), median 89% | ✅ +1,383 USDT left (62% from top 3) | **ROBUST** | ⚠️ partly. The spread *is* large (Calmar 0.90 … 1.95), but the rules don't call it fragile |

**Tooling issues found and fixed during calibration** (not strategy problems):
1. **Window end date.** The lookahead window ended on Monday 2024-07-01 00:00, exactly when weekly trades close, and Freqtrade 2026.9 crashed on that trade (`KeyError … not in index`). Proven with one change: the same variant passed with the window ending Wednesday 2024-07-03, which is the window used from now on.
2. **Left-out coin crash.** Leave-one-coin-out variants crashed in the bias check on the coin they leave out, because the bias check runs all 5 coins. Now the left-out coin simply never trades.

The first MomentumRotationV1b run (marked FRAGILE purely because of these crashes) was discarded and re-run; experiment E0320 is marked invalid.

**What calibration taught us:**
- **Momentum rotation isn't a timing fluke.** It's profitable at every one of the 28 rebalance times, in every nearby setting, without any single coin, and without its 3 best trades. Timing changes *how much* it makes, not *whether* it makes money.
  - This **corrects the Round 3 write-up**, which over-generalised from two slots. Monday 12:00 happens to be the second-worst of 28.
  - Its real blocker is unchanged: **~40% drawdowns** (Round 2 exam: 41%). The robustness check doesn't measure drawdown size, and isn't meant to.
- **EmaTrendV2 is robust but small:** a stable edge of about +36% over 3 years after fees, with a 20% max drawdown. Its Stage 2 failure was about *consistency over time* (lumpy quarters), which is a different property.
- **The check works as a gate** for what it measures: it would flag strategies that only work at one hour, one setting, with one coin, or from a few trades.
  - **Its limit:** a median-based rule doesn't punish a wide spread as long as every variant stays profitable.
  - **No change made.** Per the plan, any change to the rules would be a dated DECISIONS entry applied from the next round.
