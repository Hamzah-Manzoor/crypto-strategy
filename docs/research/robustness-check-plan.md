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
