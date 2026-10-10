# Pre-registration: Trend at four speeds with risk-based sizing (Round 5)

**Written:** 2026-10-09, before anything below was built or tested. It's committed to git first, so the commit time proves the order.
**Status:** designed with Hamzah on 2026-10-09.
- **Hamzah's choices:**
  - "Balanced" risk: worst fall ≤ 30%, beat buy & hold after adjusting for risk over a full cycle.
  - Approach A, trend at four speeds.
  - He approved the strategy rules ("I trust, just make me a good strategy").
- **Delegated to me:** the testing plan below, which follows the lab's usual process.
- **No extra review stop:** the exam runs once, after the pick is frozen and committed.

## 1. Why this idea

- **Hamzah's goal:** a slow strategy (days to months per trade), low risk, decent returns, built from the most reliable indicators.
- **The most reliable edge in crypto is trend:** hold what's rising and step aside during long falls.
  - Time-series momentum in crypto: Liu & Tsyvinski, *Risks and Returns of Cryptocurrency*, 2021.
  - Moving-average rules predicting Bitcoin returns: Detzel et al., 2021.
  - A century of trend following across markets: Hurst, Ooi & Pedersen, 2017.
- **Most popular indicators measure that same trend.** EMA crossovers, MACD, ADX, Supertrend and Donchian all do. Stacking them adds settings to overfit, not information.
- **This lab's own lessons:**
  - Hourly strategies drown in noise and fees (Round 1).
  - All-or-nothing positions whipsaw (Round 3).
  - A fixed 50% of the wallet invested controlled risk, but lagged in a raging bull market (Round 4).
- **The design follows from that.**
  - **Daily decisions.**
  - **Trend measured at four speeds,** so no single setting decides everything and positions grow and shrink gradually.
  - **Position sizes set by each coin's recent volatility,** so wild coins get less money and calm uptrends get more.

## 2. The strategy (`TrendBlendV1`, frozen now)

**Once a day, on the 11:00 UTC hourly candle (trades at 12:00 UTC = 5 pm Pakistan time),** using only daily candles that have already closed, for each coin:

1. **Trend score:** 1 point each for a daily close above the 20-, 50-, 100- and 200-day simple moving averages. That gives 0 to 4.
2. **Volatility:** the standard deviation of the last 30 daily log returns × √365, i.e. how much the coin swings per year.
3. **Weight:** score ÷ 4 × min(1, 30% ÷ volatility). For example, score 4 at 60% volatility gives a weight of 0.5.
4. **Target position:** weight × one slot.
   - A slot is the wallet's current value (cash plus coins at the latest price, × 0.99 for fees) divided by the number of coin slots (`max_open_trades`: 5 on dev, 9 in the exam).
5. **Trading rules:**
   - **Buy** a coin we don't hold when its weight is at least 0.25.
   - **Top up or trim** a coin we hold when target and holding differ by at least 0.25 of a slot, back to the target.
   - **Sell everything** when the score is 0.
   - Nothing happens at any other hour.
6. **Emergency stop:** −25% from the average buy price, as a disaster backstop only.

**Fixed settings (textbook values, no tuning, no hyperopt):**
- moving averages of 20 / 50 / 100 / 200 days (`SPEED_SCALE = 1.0`)
- volatility over `VOL_DAYS = 30`
- target `TARGET_VOL = 0.30`
- trading threshold `BAND = 0.25` of a slot
- stop −25%

**No peeking:**
- Daily values enter the hourly data only after each day closes.
- `check-bias` checks the signals and indicators.
- A replay script checks every order's size by hand, because Freqtrade's lookahead check doesn't look at position sizes.

**What I expect (written now, to compare later):**
- About half the wallet invested in strong uptrends; mostly cash in bear markets.
- Worst falls of 15–30%.
- It will trail buy & hold in strong bull years.

## 3. Data

| Data | Use in this round |
|---|---|
| **Dev:** 2023-10-01 → 2026-10-01, our 5 coins | Building, the robustness gate, and choosing **one** version |
| **Exam: 2019-01-01 → 2023-10-01, 9 coins this lab has never traded** | The single exam, run once |
| From the day the exam passes | Forward test (paper bot plus a forward backtest) |

**The exam coins, chosen by a fixed rule, not by hand:**
- **The rule:** every Binance USDT pair still listed on 2026-10-09 whose daily data starts before 2018-06-15 (enough history for the 200-day average by 2019-01-01), minus our 5 coins and stablecoins.
- **The result (checked 2026-10-09):** **NEO, LTC, QTUM, ADA, IOTA, XLM, ONT, TRX, ETC.**
- **No strategy in this lab has ever traded any of them.**
- **Why this is a fair exam:**
  - The strategy is built only on our 5 coins over 2023–26.
  - It's then judged on different coins over different years.
  - Those years are a full cycle: the 2019 rally, the COVID crash, the 2021 boom, the 2022 crash (LUNA, FTX) and the 2023 recovery.
- **Honest caveats:**
  1. **I know the broad history of 2019–23,** and earlier rounds tested related ideas on our own coins in those years. The defences: the settings are textbook values fixed above, and the coins are new.
  2. **Survivorship:** coins delisted since 2018 (e.g. EOS, XMR, WAVES, ICX) can't be downloaded. Most delisted coins crashed, so leaving them out makes **buy & hold** look better. That works against this strategy, not for it.
- **Guard:**
  - From this commit on, `lab.py` refuses any backtest that includes an exam coin unless it's the exam.
  - The exam years are already protected (`holdout`, `exam2019`).

## 4. Choosing the one version for the exam (dev data, by rule)

- **Versions allowed:** `TrendBlendV1` is frozen above. If it fails on dev, I may build **at most 2 more versions** (3 in total). Each gets a written reason in its docstring and is built on dev data only. All versions tried are reported.
- **Eligible** if, on dev (2023-10 → 2026-10, 5 coins, 0.1% fee):
  - max drawdown **≤ 30%**
  - profit > 0, profit factor **≥ 1.2**, at least **30** trades
  - Calmar **above buy & hold's** on the same run
  - `check-bias` passed
  - **ROBUST** in `lab.py robustness`
- **Robustness neighbours for R2,** declared in the class before any run:
  - `TARGET_VOL` 0.25 / 0.35
  - `SPEED_SCALE` 0.75 / 1.25 (all four averages 25% shorter or longer)
  - `VOL_DAYS` 20 / 45
  - `BAND` 0.125 / 0.5
- **R1 timing for a daily strategy:** decide at 4 different hours, 6 hours apart, and act 1, 2 or 3 days late. That's 7 variants.
- **The pick:** the single eligible version with the highest dev Calmar. If none is eligible, the idea is dropped and no exam runs.

## 5. The exam (2019-01-01 → 2023-10-01, 9 new coins, run once)

**Setup:**
- The chosen version on the 9 exam coins, with 9 slots.
- Compared against buy & hold of the same 9 coins, 1/9 each.
- One run at the normal 0.1% fee and one at 0.15% per side.

A pass needs **all** of:

| # | Rule | Threshold |
|---|---|---|
| E1 | Enough trades | ≥ 30 |
| E2 | Profitable | profit > 0 **and** profit factor ≥ 1.2 |
| E3 | Survives higher costs | profit > 0 at a 0.15% fee per side |
| E4 | Drawdown under control | max drawdown ≤ 30% **and** smaller than buy & hold's |
| E5 | Beats buy & hold, risk-adjusted | Calmar > buy & hold's Calmar |
| E6 | Consistent | profitable quarters ≥ losing quarters (quarters spent fully in cash count as neither), and no quarter worse than −15% |
| E7 | No cheating | bias checks passed |

**One change from earlier rounds, made before any test:** the worst-quarter limit is −15% instead of −10%.
- **Why:** with a 30% limit on the worst fall, a −10% quarter limit made one bad quarter in 19 close to a coin flip.
- **"Profitable ≥ losing quarters"** replaces "≥ half profitable", because a trend strategy is *supposed* to sit in cash during bear quarters.
- This is recorded in DECISIONS and applies from this round on. It is not applied to past rounds.

## 6. What happens next (decided now)

- **If the exam passes:**
  - `TrendBlend` (on our 5 coins) starts as a `watch-list` paper bot (`trend-blend`, FreqUI port 8083).
  - A **12-month forward test** begins, judged by a forward backtest on new prices using E1–E7. E1 is ≥ 20 trades over 4 quarters.
  - **Inconclusive clause, as in Round 3:** if fewer than 20 trades happen because most coins spent most of the year below their averages, the test is extended by 6 months.
  - It can only be marked **promoted** if the forward test also passes. Real money stays forbidden by the project's hard rules.
- **If the exam fails:** the idea is dropped, and the 9-coin 2019–23 exam counts as *used* for trend ideas.
- **Whatever happens:** results are appended below this line, without editing anything above it.

## 7. Results

_To be filled in at each stage, without editing anything above this line._

### Build and dev selection: 2026-10-09 → **pick: `TrendBlendV2`** (frozen before the exam)

**V1 had a coding bug, found before any selection. It's fixed in V2, with no rule change.**
- **How it was found:** the order replay (`scripts/round5_position_check.py`) checks every daily decision against the written rules.
  - V1's buys, top-ups and full sells all matched.
  - Its **partial sells (trims) didn't:** 202 mismatches.
- **The cause:** Freqtrade counts a partial sell in *purchase cost*, while V1 asked in *market value*.
  - A position in profit was trimmed too much.
  - A big winner couldn't be trimmed at all once the request exceeded the whole position. SOL in late 2023 was refused day after day.
- **The fix:** V1 already had a logged result, so the fix is a new version, `TrendBlendV2`. That's version 2 of the 3 allowed. V1's dev run (E0337: +96.9%, DD 19.0%) is marked INVALID.
- **V2's replay:**
  - 310 of 313 orders match the rules exactly.
  - The other 3 sit within 0.3% of the ¼-slot threshold, where the replay's wallet value (about 1 USDT off) tips them.
  - The rebuilt wallet ends within 1.3 USDT of the backtest.
  - Had the strategy peeked at the unfinished day, 196 buy/sell decisions would have been different, so the check can tell.

**Dev run** `20261009-160432_dev_1h` (2023-10-01 → 2026-10-01, 5 coins, 0.1% fee). Selection: `results/leaderboards/round5_selection.md`.

| | Profit | CAGR | Max DD | Sharpe | Calmar | PF | Trades | Avg hold | In market |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `TrendBlendV2` | +134.4% | +32.8% | **17.7%** | 1.64 | **1.85** | 4.26 | 92 | 40 days | 30% |
| Buy & hold | +231.4% | +49.0% | 64.9% | 0.94 | 0.76 | — | 5 | — | 100% |

- **Every eligibility rule passed:**
  - DD ≤ 30%, PF ≥ 1.2, ≥ 30 trades;
  - Calmar above buy & hold's;
  - `check-bias` passed (slow strategy, so the whole-dev lookahead window was used: 30 signals, none biased);
  - **ROBUST.**
- **Why the profit factor is so high (4.26, above the "suspicious" level of 3):** it's the shape trend following should have.
  - **Losses:** 68 small ones, averaging −6 USDT, the worst −20.
  - **Wins:** 24 long ones, averaging +73 USDT, held 5–9 months through real trends (e.g. XRP Nov 2024 → Apr 2025, SOL and BTC in the 2023–24 bull market).
  - **Spread:** every coin contributed 219–357 USDT. The top 3 trades made 45% of the profit.

**Robustness check: ROBUST** (`results/robustness/20261009-160550_TrendBlendV2.md`). **All 20 variants were profitable, with max DD between 13.8% and 21.0%.**
- **R1 timing:**
  - Decided at 05:00, 11:00, 17:00 or 23:00 UTC: Calmar 1.79–2.37.
  - Acting 1, 2 or 3 days late: still +90% to +116%. The median of the 7 variants is 96% of the original's Calmar.
- **R2 settings:**
  - All 8 neighbours profitable, median 93%.
  - A 25% volatility target gave DD 14.8% and +102%; a 35% target gave DD 21.0% and +139%.
- **R3 coins:** profitable without any one coin (+87% to +108%), median 89%.
- **R4:** still +741 USDT without the 3 best trades.

**Exam rehearsal** (`lab.py round5 exam --smoke`, on our 5 coins in 2024; experiments E0341–E0344, marked as a pipeline test, not a result): the whole exam pipeline ran end to end.

**Next:** `lab.py round5 exam` runs **once**, on the 9 new coins over 2019-01-01 → 2023-10-01. The command refuses to run a second time.

### Exam: run 2026-10-09 → **PASS** (all 7 rules)

The exam ran once, after the pick was frozen and pushed (commit `cb6adfb`): `lab.py round5 exam`. Runs: `20261009-163329_exam5_1h` and fee stress `20261009-163414_exam5_1h_fee0.15pct`. Report: `results/leaderboards/exam_round5.md`.

| 2019-01-01 → 2023-10-01, 9 new coins | Profit | Per year | Max DD | Calmar | Sharpe | PF | Trades | In market |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `TrendBlendV2` | +76.9% | +12.8% | **29.5%** | **0.43** | 0.79 | 2.01 | 192 | 15% |
| Buy & hold, 1/9 in each coin | +124.2% | +18.5% | 87.7% | 0.21 | 0.62 | — | 9 | 99% |

| # | Rule | Result |
|---|---|---|
| E1 | ≥ 30 trades | ✅ 192 |
| E2 | profit > 0 and PF ≥ 1.2 | ✅ +76.9%, PF 2.01 |
| E3 | profit > 0 at a 0.15% fee | ✅ +75.3% |
| E4 | max DD ≤ 30% and below buy & hold's | ✅ 29.5% vs 87.7% |
| E5 | Calmar > buy & hold's | ✅ 0.43 vs 0.21 |
| E6 | up quarters ≥ down quarters, none worse than −15% | ✅ 11 up vs 8 down, worst −9.0% (2019 Q3) |
| E7 | bias checks passed | ✅ |

Quarter by quarter (profit %):

| | 19Q1 | 19Q2 | 19Q3 | 19Q4 | 20Q1 | 20Q2 | 20Q3 | 20Q4 | 21Q1 | 21Q2 | 21Q3 | 21Q4 | 22Q1 | 22Q2 | 22Q3 | 22Q4 | 23Q1 | 23Q2 | 23Q3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Buy & hold | +42.3 | +45.4 | −53.5 | −13.3 | −11.7 | +48.0 | +29.9 | +31.8 | +289.8 | +4.0 | +29.2 | −28.9 | −5.7 | −60.2 | +10.3 | −32.4 | +46.9 | −9.8 | −12.6 |
| TrendBlendV2 | +3.9 | +14.3 | −9.0 | −1.7 | +0.4 | +3.6 | +12.8 | +5.4 | +44.9 | +12.8 | +1.0 | −6.5 | +0.9 | −5.7 | −4.1 | −6.1 | +6.8 | −3.9 | −0.9 |

**Checked for bugs before accepting:**
- **The order replay on the exam run** (`round5_position_check.py --slots 9`) found all **469 rule-driven orders matching the rules**.
  - The one exception is 15 May 2019, when a Binance outage left no decision candle. Doing nothing is correct there.
  - The first replay also flagged 9 orders 1–2% too small on ONT and IOTA. The cause was in **the check script**, not the strategy: those coins trade in whole units, and the script estimated their step as 0.1. Fixed; the dev replay is unchanged.
- **Buy & hold matches real prices:** ADA +527%, TRX +375%, ETC +227%, LTC +120%, QTUM +5%, XLM +2%, NEO −1%, IOTA −57%, ONT −70%. The average is the +124% shown.
- **Data:** each coin's daily data starts at its 2018 listing, as expected. Nothing traded before its 200-day average existed.

**Honest reading:**
- **What it did:** it kept the worst fall to 29.5% while buy & hold fell 88%, and it was twice as good per unit of risk (Calmar 0.43 vs 0.21).
  - In 2022 it lost 15% in total while the coins fell about 75%.
  - In the 2019 crash quarter it lost 9% against buy & hold's 54%.
- **Returns were modest:** +12.8% a year, with only 15% of the wallet in coins on average.
- **The gains were lumpy:**
  - The early-2021 altcoin boom (Q1 +44.9%) did a lot of the work, and the top 3 trades made 60% of the profit. It stays profitable without them.
  - 7 of 9 coins were profitable; ONT (−55 USDT) and IOTA (−23 USDT) lost.
- **Margins were thin:**
  - The worst fall, 29.5%, was just inside the 30% limit.
  - At a 0.15% fee it reached 30.0%. E4 is judged at the normal fee.

**Decision, as pre-registered:**
- **It passes the exam.** It isn't promoted.
- `TrendBlendV2` started as a **`watch-list` paper bot** (`trend-blend`, FreqUI http://127.0.0.1:8083) on our 5 coins at 2026-10-09 16:36 UTC.
- **The 12-month forward test** runs from **2026-10-09 to 2027-10-09**.
  - **The judge:** a forward backtest on our 5 coins over exactly that period, under `rules.ROUND5_FORWARD` (E1–E7 with ≥ 20 trades over 4 quarters), plus the inconclusive clause.
  - **Report-only check at 6 months (2027-04-09):** no decision is taken then.
  - **The paper bot** is the reality check, compared with the forward backtest as in Round 3.
- The 9-coin 2019–23 exam now counts as **used** for trend ideas.

### Paper bot change: catch-up after a sleeping laptop (2026-10-10)

**The problem:**
- Hamzah's laptop is usually asleep at 5 pm Pakistan time (12:00 UTC), so the paper bot would skip that day's decision.
- On 2026-10-10 a brief background wake (macOS "DarkWake" at 5:08–5:11 pm) happened to let it trade at 12:10 UTC, but that was luck.

**The change:** the bot now runs **`TrendBlendV2Live`**, a copy that only changes *when* the bot may act.
- It makes each day's decision the first time it's awake between 12:00 and 22:59 UTC (5 pm – 4 am Pakistan time).
- It uses the same closed daily candle as V2.
- Each coin is reviewed once per day, with no decision on stale prices straight after waking, and no same-day re-buy after an emergency stop.

**What is *not* changed:** the strategy being judged is still **`TrendBlendV2`**, and the forward test's verdict is still a forward backtest of V2, which doesn't depend on the laptop.

**Evidence that the copy makes V2's decisions:**
- **Laptop never asleep** (backtest, dev 2023–26): **identical to V2, order for order** (318 orders, same final balance). Experiments E0349–E0351.
- **Laptop asleep 12:00–15:59 UTC every day for 3 years** (simulated): **identical to V2 deciding at 16:00 UTC, order for order** (315 orders, same final balance). It acted at the first awake hour, as intended.
- **Other checks:** `check-bias` passed; container unit tests cover the decision window.
- **On the live bot:** switched at 19:41 UTC on 2026-10-10. The 4 open positions were kept, each was marked as reviewed for the day, and no extra orders were made.

**Effect on the paper-bot reality check:** if the laptop is awake at some point between 5 pm and 4 am, the bot acts that day, only later and at that hour's prices. A day is only skipped if the laptop sleeps through the whole window.

