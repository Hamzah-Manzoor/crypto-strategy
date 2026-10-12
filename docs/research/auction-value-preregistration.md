# Pre-registration: Auction Market Theory: trade where value is going (Round 6)

**Written:** 2026-10-12, before anything below was built or tested. It's committed to git first, so the commit time proves the order.

**Status:** designed with Hamzah on 2026-10-12.
- **Hamzah's choices:**
  - The idea: Auction Market Theory.
  - Approach C, "full AMT": read the market's state from where value moves, buy failed drops in sideways or rising markets, buy accepted rises in rising markets, and hold cash when value falls.
  - He approved the strategy rules and this testing plan ("Looks good, go ahead").
- **Carried over from Round 5:**
  - The goals: slow trades, low risk, decent returns.
  - "Balanced" risk: worst fall ≤ 30%, and beat buy & hold after adjusting for risk.
- **No extra review stop:** the exam runs once, after the pick is frozen and committed.

## 1. Why this idea

### What Auction Market Theory (AMT) says
Sources: J. Peter Steidlmayer, *Markets and Market Logic* (1986); Dalton, Jones & Dalton, *Mind Over Markets* (1990, 2013); Dalton, *Markets in Profile* (2007).

- **A market is a continuous auction.** Price moves up to find sellers and down to find buyers.
- **Value:**
  - The price range where most trading happened is where both sides agree the price is fair.
  - The **value area** is the busiest 70% of the volume.
  - The **point of control (POC)** is the single busiest price.
- **Balance:** price rotates inside value. Moves to the edges tend to get pushed back (*responsive* trading).
- **Imbalance:**
  - Price leaves value and is **accepted** outside it, meaning it stays there over time, not for a quick spike.
  - Value then moves after it, and a trend runs (*initiative* trading).
- **Failed auction:** price pokes outside value, finds no takers and returns inside. It then tends to travel to the other side of value.
- **Value migration:** where value moves from one period to the next shows who is in control.

### What the evidence says, and doesn't
- Most AMT evidence comes from discretionary futures day traders who read live order flow. There are few tests of fixed, written rules.
- **That's why this goes through the full process.** I can't promise it works.

### This lab's lessons, and the design that follows
| Lesson | Design choice |
|---|---|
| Hourly edges are about the size of the 0.1% fee (Round 1) | **Weekly value areas**, so each trade aims for a move of several percent |
| Trend carries over to unseen data (Round 5) | The **accepted-rise** setup goes with value when it moves up |
| Losses pile up in long falls (Rounds 2–4) | **Cash** whenever value is migrating down |
| Position-sizing code had a hidden bug (Round 5) | **Full slots only:** no top-ups, no partial sells |

## 2. The strategy (`AuctionValueV1`, frozen now)

### Sessions and decision time
- **A session is 24 hourly candles** ending with the 11:00 UTC candle, i.e. 12:00 UTC to 12:00 UTC.
- **The decision is made once a day** when that candle closes, at 12:00 UTC (5 pm Pakistan time). Trades happen at the 12:00 UTC open.

### Weekly value, as a volume profile
1. **Window:** the **7 sessions before today's session** (168 hourly candles).
   - Only windows made entirely of complete sessions count.
2. **Price grid:** steps of **0.25%** (on a log scale), from the window's lowest low to its highest high.
3. **Volume at each price:**
   - Each hourly candle's volume is spread evenly over its own low–high range.
   - A candle with no range puts all its volume in its one step.
4. **POC:** the middle price of the step with the most volume.
5. **Value area:**
   - Start at the POC. Keep adding the busier of the next step above and the next step below, until the area holds **70%** of the window's volume.
   - On a tie, add the step above. When one side runs out of steps, keep adding from the other side.
   - **Value low (VAL)** is the bottom of the area; **value high (VAH)** is the top.

### Market state
Compare this week's value (the 7 sessions before today) with the week before (the 7 sessions before those):
- **Rising:** VAH and VAL both higher.
- **Falling:** VAH and VAL both lower.
- **Sideways:** anything else.

### Buying, at the decision only, with at most one trade per coin at a time
| Setup (tag) | Allowed when | All of these must hold for today's session |
|---|---|---|
| **Failed drop** (`failed_drop`) | state is not falling | low < VAL, and VAL < close < VAH, and (VAH − close) ≥ **1.0** × (close − low) |
| **Accepted rise** (`accepted_rise`) | state is rising | close > VAH, and the session before also closed above *its own* VAH (**2** closes in a row) |

### Selling
| Trade | Target (checked within every hour) | Stop (checked within every hour) | At each daily decision |
|---|---|---|---|
| `failed_drop` | VAH at entry, the other side of value. Sold as soon as the price reaches it (Freqtrade `custom_roi`) | today's low at entry: if price returns there, the drop was real | sell if the state is falling (`value_falling`) |
| `accepted_rise` | none | VAL at entry: price fell through all of last week's value | sell if the session closed below the current weekly POC (from the 7 sessions before it) (`back_in_value`), or the state is falling (`value_falling`) |

- **Emergency stop:** −30% from the buy price, as a backstop only. The stops above trigger first.
- **Sizing:**
  - Every trade is one full slot: the wallet's value (cash plus coins at the latest close) × 0.99 ÷ `max_open_trades`. That's 5 on dev and in the exam.
  - No top-ups and no partial sells.

### Settings
These are fixed textbook values, not tuned, and there's no hyperopt:
- **7** sessions per profile (`PROFILE_SESSIONS`)
- **70%** value area (`VALUE_AREA`)
- **2** closes for acceptance (`ACCEPT_CLOSES`)
- reward ≥ **1.0** × risk (`MIN_REWARD_RISK`)
- **0.25%** price steps
- **−30%** emergency stop

### No peeking
- **Profiles** use only sessions that finished before today. Today's low and close come from today's finished candles.
- **The bias checks** (`check-bias`) check signals and indicators.
- **An order replay** (`scripts/round6_trade_check.py`) recomputes from candles every entry and every exit reason and price, and compares them with the backtest's trades.
- **A unit test** compares the profile maths with a slow, simple version.

### What I expect (written now, to compare later)
- About 30–50% of the time invested.
- Many small losses and fewer, bigger wins, with a win rate of about 40–55%.
- A worst fall of 10–25%.
- It will trail buy & hold in raging bull runs.

## 3. Data

| Data | Use in this round |
|---|---|
| **Dev:** 2023-10-01 → 2026-10-01, our 5 coins | Building, the robustness gate, and choosing **one** version |
| **Exam: the protected holdout, 2021-01-01 → 2023-10-01, our 5 coins** | The single exam, run once |
| From the day the exam passes | Forward test (paper bot plus a forward backtest) |

**Why the holdout is a fair exam here:**
- **The lab's rule:** a new idea family may use the holdout once, with its own pre-registration.
- **Volume-profile value areas are a new family.** The holdout has only judged:
  - a trend filter (`EmaTrendV3`, `EmaTrendV3b`);
  - momentum rotation (`MomentumRotationV1`, `MomentumRotationV1b`), in Round 2.
- **It covers a full cycle:** the 2021 boom, the 2022 crash (LUNA, FTX) and the 2023 recovery. That's 11 quarters.

**Honest caveats:**
1. **I know the broad history of 2021–23.** The defences are textbook settings fixed above, and rules written before any test.
2. **The buy & hold bar is high.**
   - On the holdout it made +397.6%, with a 92.1% worst fall: Calmar 0.86 (Round 2 exam run).
   - To beat that, a strategy with a 20% worst fall needs more than about 17% a year.

**Guard:** the holdout is already protected. `lab.py` refuses it without `--allow-holdout`, and every look is logged.

## 4. Choosing the one version for the exam (dev data, by rule)

### Versions
- `AuctionValueV1` is frozen above.
- If it fails on dev, I may build **at most 2 more versions** (3 in total).
  - Each gets a written reason in its docstring, built on dev data only.
  - All versions tried are reported.
- "...Live" paper-bot copies don't count as versions.

### Eligible if, on dev (2023-10 → 2026-10, 5 coins, 0.1% fee):
- max drawdown **≤ 30%**
- profit > 0, profit factor **≥ 1.2**, at least **30** trades
- Calmar **above buy & hold's** on the same run
- `check-bias` passed
- **ROBUST** in `lab.py robustness`

### Robustness neighbours for R2
Declared in the class before any run:
- `PROFILE_SESSIONS` 5 / 10
- `VALUE_AREA` 0.60 / 0.80
- `ACCEPT_CLOSES` 1 / 3
- `MIN_REWARD_RISK` 0.75 / 1.5

### R1 timing
- **Session boundaries at 4 times, 6 hours apart:** sessions ending with the 05, 11, 17 and 23 UTC candles.
- **Acting 1, 2 or 3 hours late** (`DELAY_HOURS`). That's 7 variants.
- **Why hours, not days:**
  - Round 5 used "1–3 days late" because its daily trend score barely changes from day to day.
  - Here each setup is about *today's* session, so acting 3 days late would be a different trade.
  - The robustness plan's rule for signal strategies is "signals acted on 1, 2, 3 candles late". This strategy runs on 1h candles, so that means hours.

### The pick
- The single eligible version with the highest dev Calmar.
- If none is eligible, the idea is dropped and no exam runs.

### Reported as information, not rules
- Dev profit split by setup (`failed_drop` vs `accepted_rise`).
- A dev run with 5-minute candles inside each hour (`--timeframe-detail 5m`). It shows how much the hourly stop and target fills flatter the result.

## 5. The exam (2021-01-01 → 2023-10-01, our 5 coins, run once)

**Setup:**
- The chosen version on BTC, ETH, SOL, BNB and XRP, with 5 slots.
- Compared against buy & hold of the same 5 coins, 1/5 each.
- One run at the normal 0.1% fee and one at 0.15% per side.

A pass needs **all** of:

| # | Rule | Threshold |
|---|---|---|
| E1 | Enough trades | ≥ 30 |
| E2 | Profitable | profit > 0 **and** profit factor ≥ 1.2 |
| E3 | Survives higher costs | profit > 0 at a 0.15% fee per side |
| E4 | Drawdown under control | max drawdown ≤ 30% **and** smaller than buy & hold's |
| E5 | Beats buy & hold, risk-adjusted | Calmar > buy & hold's Calmar |
| E6 | Consistent | over the 11 quarters, profitable quarters ≥ losing quarters (quarters spent fully in cash count as neither), and no quarter worse than −15% |
| E7 | No cheating | bias checks passed |

**Reported as information, not rules:**
- the 5-minute fill run on the exam period;
- profit by setup;
- the order replay.

## 6. What happens next (decided now)

**If the exam passes:**
- `AuctionValue` starts as a `watch-list` paper bot, `auction-value` (FreqUI port 8084).
  - It runs a "...Live" copy with the same catch-up for a sleeping laptop as `TrendBlendV2Live`, so a missed 5 pm decision is made on waking, before the day ends.
- A **12-month forward test** begins.
  - It's judged by a forward backtest on new prices using E1–E7. E1 becomes ≥ 20 trades over 4 quarters (`rules.ROUND6_FORWARD`).
  - **Inconclusive clause:** if fewer than 20 trades happen, the test is extended by 6 months.
  - It can only be marked **promoted** if the forward test also passes. Real money stays forbidden by the project's hard rules.

**If the exam fails:**
- The idea is dropped.
- The holdout counts as *used* for volume-profile / AMT ideas.

**Whatever happens:** results are appended below this line, without editing anything above it.

## 7. Results

_To be filled in at each stage, without editing anything above this line._

### Build and dev selection: 2026-10-12 → **pick: `AuctionValueV2`** (frozen before the exam)

**V1 followed its rules exactly, but wasn't eligible.**
- **Order replay** (`scripts/round6_trade_check.py`, which rebuilds every trade from candle files by clock time): all **437 of 437** trades match on entry time, setup, exit time, exit reason and exit price.
  - A first run showed 5 exit-price differences. All were stops hit in the hour the trade opened.
  - Freqtrade fills those at the stop price. The replay had wrongly assumed the "worst case" fill Freqtrade uses only for trailing stops, so the replay was fixed, not the strategy.
- **Dev result (E0353):** +30.6%, max DD **32.6%**, profit factor **1.14**, Calmar **0.29** (buy & hold 0.76), 437 trades.
- **Why, by setup and market state:**

  | Setup | State | Trades | Winners | Profit |
  |---|---|---:|---:|---:|
  | accepted rise | rising | 157 | 36% | +558 USDT |
  | failed drop | sideways | 94 | 51% | +125 USDT |
  | failed drop | rising | 186 | 26% | **−377 USDT** |

**V2 (version 2 of 3): failed drops only in sideways markets.**
- **AMT says** buying at the edge of value is a trade for a balanced market; when value is moving, you go with the move. V1 deviated from that by also buying failed drops while value was rising.
- **The honest note:** this change was *suggested by the dev breakdown*, and the textbook agrees with it. So it's partly fitted to dev data. The robustness gate and the one-time holdout exam are what check it.
- **Nothing else changed:** same setups, exits, sizing and settings.

**Dev results** (run `20261012-174213_dev_1h`, 2023-10 → 2026-10, 5 coins, 0.1% fee):

| Version | Profit | Max DD | Calmar | Profit factor | Trades | In market | Eligible |
|---|---:|---:|---:|---:|---:|---:|---|
| `AuctionValueV1` | +30.6% | 32.6% | 0.29 | 1.14 | 437 | 21% | no (DD, PF, Calmar) |
| **`AuctionValueV2`** | **+67.5%** | **22.0%** | **0.85** | **1.47** | **257** | **16%** | **yes** |
| buy & hold | +231.4% | 64.9% | 0.76 | n/a | 5 | 100% | baseline |

**V2's checks:**
- **Order replay:** all 257 of 257 trades match exactly.
  - Accepted rises: 157 trades, 36% winners, **+548 USDT**, median hold 4 days.
  - Failed drops: 100 trades, 49% winners, **+127 USDT**, median hold 1 day.
- **Bias checks:** passed (30 signals, no lookahead; recursive error 0.000% at 576 warm-up candles). Every robustness variant also passed.
- **5-minute fills (information, E0358):** the same 257 trades and the same profit. 72 exits move to a different minute within their hour, at the same price.
- **Robustness: ROBUST** (`results/robustness/20261012-174407_AuctionValueV2.md`).
  - **R1:** 7 of 7 timing variants profitable; median Calmar 73% of the original's. Sessions ending with the 05:00 or 23:00 UTC candle earn about half as much (Calmar 0.48 / 0.44).
  - **R2:** 7 of 8 settings variants profitable. The exception: **a 5-session week loses 1.1%** (DD 32.7%).
  - **R3:** 5 of 5 leave-one-coin-out runs profitable.
  - **R4:** **the 3 best trades are 86% of the profit** (XRP Nov 2024 +90%, ETH Feb–Mar 2024 +70%, XRP Jul 2025 +38%, all accepted rises). Without them it's +97 USDT, so it passes, but most of the money comes from a few trend rides.

**Selection by the rule** (`results/leaderboards/round6_selection.md`): **`AuctionValueV2`**, the only eligible version. V1 is reported, not eligible. The exam runs once on the holdout.

### Exam: 2026-10-12 → **PASS** (run once)

`AuctionValueV2` on BTC, ETH, SOL, BNB and XRP, 2021-01-01 → 2023-10-01, 5 slots (`results/leaderboards/exam_round6.md`):

| Rule | Result |
|---|---|
| E1 trades | 237 (≥ 30) ✅ |
| E2 profit, profit factor | +193.6%, 1.62 ✅ |
| E3 at 0.15% fee | +180.3% ✅ |
| E4 max drawdown | 21.8% (≤ 30% and < buy & hold's 92.1%) ✅ |
| E5 Calmar | 2.20 > buy & hold's 0.86 ✅ |
| E6 quarters | 6 up vs 5 down (0 in cash), worst −11.7% (≥ −15%) ✅ |
| E7 bias checks | passed ✅ |

- **Information runs:**
  - 5-minute intra-candle fills: +193.6%, the same as hourly.
  - Buy & hold (+397.6%, DD 92.1%) matches the Round 2 exam run on the same period.
- **Quarter by quarter (%):**
  - 2021: +46.7, +49.9, +35.2, −5.2
  - 2022: +11.3, −11.7, −2.7, −3.0
  - 2023: +18.1, −8.7, +4.1
  - Buy & hold over the same quarters: +452, +38, +190, +21, −24, −70, +10, −50, +68, −13, +2.

**Too good to trust without a check, so it was checked:**
- **Order replay:** all **237 of 237** exam trades match the written rules exactly.
- **Where the profit came from:** it isn't a bug, it's concentration.

  | | Trades | Winners | Profit |
  |---|---:|---:|---:|
  | accepted rises | 127 | 41% | **+2,731 USDT** |
  | failed drops | 110 | 26% | **−795 USDT** |

  - **The 3 best trades make 74% of the profit,** all accepted rises in the 2021 bull run: SOL Aug–Sep 2021 +93%, XRP Apr 2021 +156%, SOL Jul–Aug 2021 +106%. Without them: +510 USDT (+51%).
  - **By coin:** SOL +1,086, XRP +636, BNB +313, BTC −3, ETH −96 USDT.
  - **By year:** 2021 +1,819, 2022 −198, 2023 +315 USDT.

**What this means, recorded before the forward test:**
1. **The pass stands.** The rules were fixed in advance and all 7 held. Nothing is re-tested on the holdout.
2. **The money comes from the "accepted rise" half,** which is AMT's version of trend following. It rode the 2021 altcoin boom and mostly sat in cash through 2022.
3. **The "failed drop" half lost money on unseen data**, even restricted to sideways markets as in V2. On dev it earned +127 USDT; here −795.
   - Removing it would be a new version that needs its own fresh test, so it isn't done here.
   - The forward test reports both halves separately.
4. **Like `TrendBlendV2`, this is mostly a trend strategy.** Expect it to lag buy & hold in bull years and to depend on a few big runs.

**Next (as pre-registered):**
- Watch-list paper bot `auction-value` (port 8084) running `AuctionValueV2Live`.
- 12-month forward test from 2026-10-12, judged on 2027-10-12 by a forward backtest of `AuctionValueV2` under `rules.ROUND6_FORWARD`, with a report-only check on 2027-04-12.
- The holdout now counts as *used* for volume-profile / AMT ideas.
