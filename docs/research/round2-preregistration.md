# Pre-registration: Round 2 (three improved / new strategy ideas)

**Written:** 2026-10-07, before any Round 2 strategy was built or tested. It's committed to git first, so the commit time proves the order.
**Status:** APPROVED by Hamzah on 2026-10-07, before any Round 2 strategy was built or tested.

## 1. Why a Round 2, and how the data is split

Round 1 tested 23 versions. None passed both stages; tuned versions overfitted, and fees ate the small edges. Round 1 also used up most of our clean test data, so Round 2 gets a **new split**:

| Role | Dates | Why |
|---|---|---|
| **Development** ("dev") | 2023-10-01 → 2026-10-01 (36 months) | Round 1's in-sample year plus its old out-of-sample year. That year was looked at 9 times, so it's no longer a fair test and becomes building data. |
| **Exam** ("holdout") | 2021-01-01 → 2023-10-01 (33 months, 11 quarters) | Never scored by any Round 1 strategy: the 2021 bull run, the 2022 crash (Luna, FTX) and the 2023 recovery. A hard exam. |
| **Live** | from approval onward | Paper trading. The final judge. |

**Honest caveats:**
- **The exam period has been seen once.** The quarterly re-tuning test scored `EmaTrendV2` (re-tuned) on 2021-12 → 2023-09. From that we know the 4h trend filter kept it mostly in cash in 2022, and that the 2022 crash happened (which everyone knows anyway). Idea B below builds on `EmaTrendV2`, so its exam is slightly less clean than the other two.
- **The exam is *before* the development data in time.** That tests whether an idea works in a different market. It's not a forecast of the future; only live paper trading is.

**Guard:** `lab.py` will refuse any backtest touching 2021-01-01 → 2023-10-01 without an explicit `--allow-holdout`. Tuning on it is refused outright. Every exam run is logged as a protected-data look.

## 2. The three ideas (designed now, built on dev data only)

All three are long-only spot on the same 5 pairs, with a 0.1% fee per side, the 1h engine and market orders. None of them uses hyperopt: Round 1 showed tuning overfits.

### Idea A: `TrendPullbackV3`, fee-aware dip buying
- **Starting point:** v1 had the biggest edge before fees (+66% in-sample) but fees ate it. v3 only trades dips where the *expected* bounce is many times the 0.2% round-trip cost.
- **Decisions on 4h candles:**
  - **Buy** when the 4h close is above the 4h EMA200 (uptrend), the 4h RSI(2) is below 10 (sharp dip), and the gap up to the 4h EMA20 is at least **2.0%** (10× the round-trip fee). It enters on the first hour after that 4h candle closes.
  - **Sell** when price is back at the 4h EMA20 (the bounce happened) or the 4h RSI(2) is above 70. Stop −8%; the ROI table decays to break-even after 3 days.

### Idea B: `EmaTrendV3`, EmaTrendV2 plus a market filter and a losing-streak pause
- **Starting point:** EmaTrendV2 passed Stage 1 but was profitable in only 3 of 8 quarters. v3 keeps its 4h EMA 21/55 crossover and adds two filters:
  - **Market filter:** only enter when **Bitcoin's daily close is above its 200-day average**, for every pair. Crypto moves together, so a BTC bear market blocks all entries.
  - **Losing-streak pause** (Freqtrade protections): after 2 stoplosses within 3 days, pause all new entries for 24 hours; after any exit, wait 4 hours before re-entering that pair.
- **Unchanged from v2:** everything else.

### Idea C: `MomentumRotationV1`, a new style
- **The idea:** once a week (Monday 00:00 UTC), rank the 5 coins by their **30-day return**.
- **Hold** the **top 2** that are also positive over 30 days, 50/50, but only while Bitcoin's daily close is above its 200-day average. Otherwise hold cash.
- **Sell** at the weekly rebalance when a coin drops out of the top 2, turns negative, or the BTC filter turns off. A −20% emergency stop applies at any time.
- **Why it might work:** "the strongest coins keep rising for a while" (momentum) is a well-documented effect in crypto. It trades at most a few times a week, so fees barely matter.

## 3. Development rules (on dev data only)

- **At most 3 versions per idea** may be tried. Each one is logged in the experiment log, so the total number of tries is visible.
- **Every version must pass `check-bias`** (lookahead + recursive).
- **Which versions go to the exam** (decided by this rule, not by eye):
  - Keep versions with dev profit > 0, dev profit factor ≥ 1.1 and at least 30 dev trades.
  - From those, take **the best 2 per idea by dev Calmar**, so at most 6 exam candidates.
- **The candidate list is written into DECISIONS and committed before the exam runs.**

## 4. The exam (holdout 2021-01-01 → 2023-10-01, run once)

The candidates plus buy & hold run in **one** backtest. A candidate passes only if **all** of these hold:

| # | Rule | Threshold |
|---|---|---|
| X1 | Enough trades | ≥ 30 |
| X2 | Actually profitable | profit > 0 after fees **and** profit factor ≥ 1.2 |
| X3 | Survives higher costs | profit > 0 at a 0.15% fee per side |
| X4 | Drawdown under control | max drawdown ≤ 30% **and** smaller than buy & hold's |
| X5 | Beats buy & hold, risk-adjusted | Calmar > buy & hold's Calmar |
| X6 | Consistent | profitable in **≥ 6 of the 11 quarters**, **and** no quarter worse than **−10%** |
| X7 | No cheating | bias checks passed |

**Why X6 differs from Round 1's 60% rule, stated before testing:**
- The exam contains a full year of crash (2022). For filtered strategies, *flat* quarters in cash are the intended behaviour, but they don't count as "profitable".
- So X6 asks for at least half the quarters profitable **plus** a cap on how bad any quarter can be. That's a stricter limit on damage, and a looser one on cash quarters.
- **Changing these thresholds after seeing the exam isn't allowed.**

Information only (not rules): 5m intra-candle fills, the buy & hold quarter-by-quarter path.

## 5. What happens next (decided now)

- **Pass:** the strategy becomes a paper bot (`watch-list`). After about 6 months live, it can be marked `promoted` if its live result is > 0 after fees with max drawdown ≤ 25%.
- **Fail:** the idea is dropped for this round. Changed versions can't be re-examined on this same holdout; they need fresh data, meaning live paper results or a future holdout.
- **Whatever happens:** results are appended below this line without editing anything above it, then committed and pushed.

## 6. Results

_To be filled in after the exam, without editing anything above this line._

### 6a. Development outcome and frozen exam list (2026-10-07, BEFORE the exam)

Dev run `20261007-085621_dev_1h` (2023-10-01 → 2026-10-01, 1h, 0.1% fee). 6 Round 2 versions were tried, 2 per idea, under the limit of 3. All passed `check-bias`.

| Idea | Version | Dev profit | Max DD | Calmar | PF | Trades | Rule result |
|---|---|---:|---:|---:|---:|---:|---|
| C | `MomentumRotationV1b` (top 3) | +363.1% | 39.6% | 1.68 | 2.70 | 64 | **exam** |
| C | `MomentumRotationV1` (top 2) | +355.4% | 43.4% | 1.51 | 2.13 | 56 | **exam** |
| B | `EmaTrendV3` (BTC filter + pause) | +14.8% | 25.0% | 0.19 | 1.19 | 122 | **exam** |
| B | `EmaTrendV3b` (BTC filter only) | +14.2% | 25.0% | 0.18 | 1.18 | 123 | **exam** |
| A | `TrendPullbackV3b` | +1.1% | 15.3% | 0.02 | 1.01 | 239 | not eligible (PF < 1.1) |
| A | `TrendPullbackV3` | −7.7% | 22.6% | −0.12 | 0.91 | 271 | not eligible |

Buy & hold on dev: +231.4%, max DD 64.9%, Calmar 0.76.

Notes recorded before the exam:
- **`MomentumRotationV1` was inspected as "too good to be true".** The mechanics are correct: all entries are at the Monday 00:00 UTC rebalance, there are never more than 2 positions, and the big winners match real moves (SOL Oct 2023 → Jan 2024, XRP Nov 2024). But **80% of its dev profit came from 3 trades**; without them it's +70% over 3 years.
- **Its first bias check was a false alarm,** caused by Freqtrade's one-pair re-check combined with a pairlist-dependent ranking. It was fixed by giving the strategy a fixed 5-coin `UNIVERSE`, and it then passed with 0 biased signals out of 18.
- **Idea A is dropped at the development stage.** No third version was tried: with a profit factor near 1.0, more tries would be fishing.

**Frozen exam list:** `EmaTrendV3`, `EmaTrendV3b`, `MomentumRotationV1`, `MomentumRotationV1b`. Command: `python3 scripts/lab.py exam --detail`.
