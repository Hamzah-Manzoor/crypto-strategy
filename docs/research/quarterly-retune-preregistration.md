# Pre-registration: EmaTrendV2 with quarterly re-tuning

**Written:** 2026-10-07, **before** any of the tests below were run. It's committed to git before the first result, so the commit time proves the order.
**Status:** APPROVED by Hamzah on 2026-10-07, before Test A was run.

## 1. The idea being tested

- **Where it comes from:** in Phase 6, `EmaTrendV2` re-tuned every quarter was the best near-miss:
  - 5 of 8 quarters profitable (62%, rule ≥ 60% ✅)
  - +23.3% over 2024-10 → 2026-10
  - walk-forward efficiency **0.49** (rule ≥ 0.5 ❌)
- **Why it can't be promoted on that evidence:** those 8 quarters overlap data we'd already looked at many times (in-sample, plus 9 out-of-sample looks). It needs **fresh** data.

## 2. The exact process (frozen, identical to the Phase 6 run)

| Setting | Value |
|---|---|
| Strategy | `EmaTrendV2` (code unchanged: 4h EMA crossover, 4h EMA200 filter, 1h engine) |
| Re-tune when | At the start of every calendar quarter (Jan 1, Apr 1, Jul 1, Oct 1) |
| Tuned on | The 12 months before that date |
| Tuner | Freqtrade hyperopt, `CalmarHyperOptLoss`, spaces `buy sell stoploss`, 150 epochs, seed 42, 6 workers, ≥ 25 trades |
| Search space | Unchanged: fast EMA ∈ {12, 21, 26}, slow EMA ∈ {50, 55, 72}, stoploss −15% … −3% |
| Costs | 0.1% fee per side, market orders, same 5 pairs, same 1000 USDT wallet rules |

**Known weakness, stated in advance:** in Phase 6 the tuner put the stoploss at about −3% (the tightest allowed) in 7 of 8 windows. A tight stop is sensitive to how prices move inside a candle. We test the process **as it is**; a different stop range would be a *different* idea needing its own fresh test.

## 3. Test A: fresh history (data never used in this lab)

- **Data:** Binance 1h + 4h candles for the same 5 pairs, back to 2020-08 (SOL's listing). Every candle before 2023-10-01 has never been part of a scored test here. A few months before that were only used as indicator warm-up.
- **Windows:**
  - First training window: 2020-12-01 → 2021-12-01. It starts in Dec 2020 so that even SOL has the 100 days of 4h history the indicators need.
  - Then train 12 months → test the next 3 months → slide 3 months.
  - That gives **7 test windows: 2021-12-01 → 2023-09-01**. They stop before our in-sample period begins, so they never touch data already used.
- **Market character:** the end of the 2021 bull run, the 2022 crash (Luna, FTX), and the 2023 recovery. That's very different from 2023–25.
- **Command:** `lab.py walkforward EmaTrendV2 --from 20201201 --to 20230901` (same settings as above).

**Pass rules for Test A (all must hold):**

| # | Rule | Threshold | Same as |
|---|---|---|---|
| A1 | Profitable test windows | ≥ 60%, i.e. at least **5 of 7** | Stage 2 rule 9 |
| A2 | Walk-forward efficiency | ≥ 0.5 | Stage 2 rule 10 |
| A3 | All 7 windows together, after fees | profit > 0 | Stage 1 rule 3 |
| A4 | Worst single-window max drawdown | ≤ 25% | Stage 1 rule 2 |

Buy & hold over the same windows is reported for context. It isn't a rule, because 2022 was a crash.

## 4. What happens next (decided now, not after seeing results)

- **If Test A passes:** the process goes live as a **new paper bot** `ema-trend-v2-retuned` with status `watch-list`. It runs next to the fixed `ema-trend-v2` and the buy & hold baseline.
  - Its first tuning uses 2025-10-01 → 2026-10-01 (the most recent full 12 months). That year's job as an out-of-sample test is over; from now on it's simply recent history to learn from.
  - It's re-tuned at every quarter start (next: **2027-01-01**) with `lab.py retune EmaTrendV2`. Every quarter's settings are saved in `results/retune/` and committed.
  - **Test B, live:** review on **2027-04-01**, after about 6 months and 2 quarterly re-tunes. It can be marked `promoted` if its paper result over that time is **> 0 after fees** and its **max drawdown ≤ 25%**. Otherwise it's dropped or stays on the watch list, with the reason written down.
- **If Test A fails:** the idea is **dropped**. Changing the process (e.g. a wider stop range, other epochs) and testing it again on these same 7 windows isn't allowed; it would be fitting the test. A changed process is a new idea and needs new fresh data.

## 5. Results

_To be filled in after Test A runs, without editing anything above this line._
