# Pre-registration: Momentum rotation at lower exposure (Round 4)

**Written:** 2026-10-08, before any version below was built or tested. It's committed to git first, so the commit time proves the order.
**Status:** go-ahead from Hamzah on 2026-10-08 ("please proceed if its a good one to have").
**Review stop:** the exam runs only after Hamzah has seen the dev results and the frozen pick.

## 1. Why this idea

- **The edge looks real.** `MomentumRotationV1b` is the only strategy in this lab whose edge held up on unseen data. On the Round 2 exam (2021–23) it made +452.9% vs buy & hold's +397.6%, with Calmar 2.08 vs 0.86.
- **It's also robust.** It passed every robustness check:
  - all 28 rebalance times;
  - nearby settings;
  - any 4 of the 5 coins;
  - and it stays profitable without its 3 best trades.
- **What blocked it:** drawdowns that are too big. It hit 41% on the exam and 40% on dev, against a 30% limit.
- **Round 3's drawdown controls failed.** Stops added churn, and the faster market filter never switched off during a slow 8-month bleed.
- **This round changes position size instead of timing.** Holding less money in the market lets the same edge produce smaller swings.
  - **Fixed exposure** simply scales risk down. Expect roughly half the drawdown *and* roughly half the return.
  - **Volatility scaling** shrinks positions when coins get wild, which is when momentum strategies tend to crash. It's a well-documented improvement for momentum (e.g. Barroso & Santa-Clara, 2015, "Momentum has its moments").

## 2. Data rules

| Data | Use in this round |
|---|---|
| 2023-10 → 2026-10 (dev) | Building, the robustness gate, and choosing **one** version |
| 2021-01 → 2023-10 (Round 2 holdout) | **Not used.** It's spent for the momentum family. |
| **2019-01-01 → 2021-01-01 (new exam, period `exam2019`)** | **No test in this lab has touched it** (checked: no experiment's timerange starts before 2021). It covers the 2019 rally and slide, the March 2020 COVID crash and the 2020 recovery. Only 4 of our coins traded on Binance then: BTC, ETH, BNB and XRP. SOL listed in Aug 2020. So the exam uses those 4. |
| From the day the exam passes | Forward test (paper bot plus a forward backtest) |

- **Guard:** from this commit on, `lab.py` protects `exam2019` the same way as the 2021–23 holdout. Backtests need `--allow-holdout`, and tuning is refused.
- **Why this window:** the first full calendar year with enough history for the 200-day Bitcoin average (that needs data from June 2018; XRP listed in May 2018), up to where the Round 2 holdout begins. It was chosen by data availability, not by looking at results.
- **Data check (2026-10-08, coverage only; no prices or results were looked at):**
  - all 4 coins have 1h and daily candles from June 2018;
  - 99.88% coverage, longest gap 10 hours;
  - report: `results/checks/data_check_20180605_1h-1d_BTC-ETH-BNB-XRP.md`.
- **Honest caveat:** I know the broad price history of 2019–20, as anyone does, but no strategy result from it. To limit that knowledge's influence, the exam rules below are Round 3's forward rules, unchanged except for the quarter count.

## 3. The versions (frozen now; at most these 2)

Both are `MomentumRotationV1b`:
- top 3 coins by 30-day return;
- positive momentum only;
- only while BTC's daily close is above its 200-day average;
- weekly rebalance, with positions held until they rotate out (not resized while held).

**Common change: rebalance on Monday at 12:00 UTC (5 pm Pakistan time),** the same slot as Round 3.
- **Why:** so the paper bot on the Mac doesn't sleep through it.
- The robustness check showed every rebalance time is profitable, so this is an operational choice, not a performance one. It's also one of the weaker slots on dev (Calmar 0.91 of a 0.90–1.95 range), so it doesn't flatter the result.

| Version | Size of each new position | Idea |
|---|---|---|
| `MomentumRotationV3` | **1/6** of the wallet when bought (`EXPOSURE = 0.5` × 1/3), so about half the wallet is invested when all 3 slots are full. The rest stays in cash. | Same edge, about half the swings |
| `MomentumRotationV3b` | **1/3 × min(1, 50% ÷ the coin's volatility)** of the wallet (`TARGET_VOL = 0.5`). Volatility is the standard deviation of the coin's last **30** daily returns, annualised (× √365). | Full slot in calm markets, smaller when a coin gets wild. For example, a coin at 100% volatility gets half a slot. |

- **No hyperopt is used.** The 0.5 exposure, the 50% volatility target and the 30-day window are fixed here.
- **Neighbour values for robustness check R2** go into each class before any run:
  - `EXPOSURE` 0.4 / 0.6 (V3) or `TARGET_VOL` 0.4 / 0.6 (V3b);
  - `LOOKBACK_DAYS` 20 / 25 / 35 / 40 and `TOP_N` 2 / 4 for both.
- **No peeking:** volatility uses only daily candles that have closed before the trade.
  - `check-bias` checks the indicator.
  - The position sizes get a check by hand, because Freqtrade's lookahead check doesn't look at sizes.

## 4. Choosing the one version for the exam (dev data, by rule)

A version is **eligible** only if all of these hold on dev (2023-10 → 2026-10, 5 coins, 0.1% fee):
- dev max drawdown **≤ 30%**
- profit > 0 and profit factor **≥ 1.2**
- at least **30** trades
- `check-bias` passed
- **ROBUST** in `lab.py robustness`. That's the gate from TESTING_METHODOLOGY section 11. Its leave-one-coin-out part also proves the version is profitable on dev without SOL.

**Pick the single eligible version with the highest dev Calmar.**
- **If none is eligible,** the idea is dropped and no exam runs.
- **The pick is committed and shown to Hamzah before the exam.**

## 5. The exam (2019-01-01 → 2021-01-01, run once)

**Setup:**
- **The chosen version, on 4 coins:** SOL is removed from its coin list and from the pair list, the same way as robustness check R3.
- **The comparison:** buy & hold of the same 4 coins at **25% each**. The run allows 4 open trades so buy & hold is fully invested. The momentum versions size their own positions, so this doesn't change them.
- **Two runs:** one at the normal 0.1% fee and one at a 0.15% fee per side. Both are logged as looks at protected data.

**The rules** are Round 3's forward rules (F1–F7), with the quarter rule applied to 8 quarters. A pass needs **all** of:

| # | Rule | Threshold |
|---|---|---|
| H1 | Enough trades | ≥ 20 |
| H2 | Profitable | profit > 0 **and** profit factor ≥ 1.2 |
| H3 | Survives higher costs | profit > 0 at a 0.15% fee per side |
| H4 | Drawdown under control | max drawdown ≤ 30% **and** smaller than buy & hold's |
| H5 | Beats buy & hold, risk-adjusted | Calmar > buy & hold's Calmar |
| H6 | Consistent | ≥ 4 of the 8 quarters profitable, and no quarter worse than −10% |
| H7 | No cheating | bias checks passed |

**20 trades is a thin sample.** That's why passing this exam leads to a forward test, not to promotion.

## 6. What happens next (decided now)

- **If the exam passes:**
  - The chosen version, on all 5 coins as designed, starts as a `watch-list` paper bot (`momentum-rotation`, FreqUI port 8083).
  - A **12-month forward test** begins under Round 3's forward rules F1–F7 (`rules.FORWARD`), including its "inconclusive" clause.
  - It can be marked **promoted** only if the forward test also passes. Real money stays forbidden by the project's hard rules.
- **If the exam fails:** momentum rotation is closed for historical testing, because this lab has no unused history left for it. Any new momentum idea could only be judged on future data.
- **Whatever happens:** results are appended below this line, without editing anything above it.

## 7. Results

_To be filled in at each stage, without editing anything above this line._

### Dev selection: run 2026-10-08 → **pick: `MomentumRotationV3`** (frozen; exam not run yet)

Dev run `20261008-123310_dev_1h` (2023-10-01 → 2026-10-01, 1h, 0.1% fee). Both versions passed `check-bias`. Selection: `results/leaderboards/round4_selection.md`.

| Version | Dev profit | Max DD | Calmar | PF | Trades | In market | Eligible? |
|---|---:|---:|---:|---:|---:|---:|---|
| `MomentumRotationV1b` (Round 2, Monday 00:00 UTC, full size) | +363.1% | 39.6% | 1.68 | 2.70 | 64 | 46% | reference only |
| `MomentumRotationV1bMonday` (full size, Monday 12:00 UTC) | +206.7% | 49.9% | 0.91 | 1.93 | 65 | 46% | reference only |
| `MomentumRotationV3` (half invested) | +95.6% | 29.7% | 0.84 | 2.17 | 65 | 25% | ✅ eligible and **ROBUST** → **pick** |
| `MomentumRotationV3b` (volatility-scaled) | +183.3% | 42.2% | 0.98 | 2.21 | 65 | 39% | ❌ max DD 42.2% > 30% |

Buy & hold on dev: +231.4%, max DD 64.9%, Calmar 0.76.

**Robustness check of V3: ROBUST** (`results/robustness/20261008-123421_MomentumRotationV3.md`):
- **R1 timing:** profitable at all 28 rebalance times (+95.6% … +201.2%, max DD 22.0–31.4%). Median Calmar 1.33, i.e. 157% of the original's. Monday 12:00 is again one of the weakest slots.
- **R2 settings:** all 8 neighbours profitable, median Calmar 95% of the original's. At 60% exposure the drawdown would be 34.4%; at 40%, 24.7%.
- **R3 coins:** all 5 leave-one-out runs profitable. **Without SOL: +73.9%, max DD 23.8%.** That's the closest dev picture of the 4-coin exam.
- **R4:** still +219 USDT without the 3 best trades. Those 3 trades made 77% of the profit, so it's still concentrated.
- V3b's robustness check wasn't run, because it was already ineligible.

**Hand-check of position sizes** (`scripts/round4_size_check.py` on the dev run):
- Every trade's stake matched the size expected from closed daily candles only: within 0.31% (median 0.03%), for all 65 trades of each version.
- If V3b had used Monday's unfinished day, 23 of its 65 sizes would have been off by more than 0.5%. So the check can tell the difference.

**What we learned:**
- **Halving the money invested worked about as expected.** At the same Monday 12:00 slot:
  - drawdown went from 49.9% to 29.7%;
  - profit went from +207% to +96%;
  - Calmar went from 0.91 to 0.84.
- **Volatility scaling barely did anything.** In 2023–26 the coins' 30-day volatility was often under 50% a year, so the median position was 92% of a full slot, and 28 of 65 trades got a full slot. My assumption that crypto usually runs at 50–100% volatility was wrong for this period.
- **Caution:** V3's dev drawdown of 29.7% is only just inside the 30% limit. The exam applies the same limit on data it has never seen.

**Exam rehearsal** (`lab.py round4 exam --smoke`, on 2024 dev data; experiments E0328–E0331, marked as a pipeline test, not a result):
- The whole exam pipeline ran end to end.
- Buy & hold put 247 USDT in each of the 4 coins (99% invested). V3 put 165 USDT in each position.
- Neither traded SOL.

**Next:** Hamzah reviews this pick. Then `lab.py round4 exam` runs **once** on 2019-01-01 → 2021-01-01. The command refuses to run a second time.

