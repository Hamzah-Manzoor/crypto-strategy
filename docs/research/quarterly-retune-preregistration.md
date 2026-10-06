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

### Test A: run 2026-10-07 → **FAIL**. The idea is dropped.

Run `20261006-204740_EmaTrendV2_retuned_20201201-20230901`. Full table: `results/walkforward/20261006-204740_EmaTrendV2_retuned_20201201-20230901.md`.

| # | Rule | Threshold | Result | |
|---|---|---|---|---|
| A1 | Profitable test windows | ≥ 5 of 7 | **2 of 7** (29%) | ❌ |
| A2 | Walk-forward efficiency | ≥ 0.5 | **−0.84** | ❌ |
| A3 | All 7 windows together, after fees | > 0 | **−12.3%** (−7.2% a year) | ❌ |
| A4 | Worst single-window drawdown | ≤ 25% | 12.3% | ✅ |

| Test window | Tuned settings | Trades | Result | Buy & hold |
|---|---|---:|---:|---:|
| Dec 2021 → Mar 2022 | EMA 26/50, stop −3.7% | 6 | −2.7% | −34.9% |
| Mar → Jun 2022 | EMA 26/50, stop −3.5% | 12 | +1.1% | −35.9% |
| Jun → Sep 2022 | EMA 26/55, stop −3.1% | 7 | −1.5% | −25.1% |
| Sep → Dec 2022 | EMA 12/72, stop −3.4% | 15 | −6.1% | −10.8% |
| Dec 2022 → Mar 2023 | EMA 12/50, stop −3.1% | 12 | −4.0% | +21.6% |
| Mar → Jun 2023 | EMA 12/50, stop −3.4% | 30 | −0.3% | +13.8% |
| Jun → Sep 2023 | EMA 12/50, stop −3.2% | 11 | +0.7% | −10.1% |

**What it means, in plain words:**
- **The re-tuning process has no edge on fresh data.** The settings it picked from each past year didn't carry over to the next quarter (efficiency −0.84: the training years made money, the following quarters lost).
- **The Phase 6 near-miss (5 of 8 quarters, +23%) was most likely luck,** on data we'd already looked at many times. That's exactly why this test was required.
- **It did protect capital in the crash.** −12.3% while buy & hold lost 65%, with a worst drawdown of only 12.3%. That comes from EmaTrendV2's 4h trend filter keeping it in cash during downtrends, not from the re-tuning. It's capital protection without an edge: it lost a little instead of a lot.
- **The known weakness showed up again.** In all 7 windows the tuner pushed the stop to the tightest allowed edge (−3.1% to −3.7%).

**Decision, as pre-registered:** the idea is **dropped**. No third paper bot. No tweaked version (wider stop range, other epochs) will be tried on these 7 quarters. The fixed `EmaTrendV2` watch-list bot keeps running; it's a different strategy and this test didn't cover it.

