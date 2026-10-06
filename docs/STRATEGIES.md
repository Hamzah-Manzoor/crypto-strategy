# Strategies

**Shared rules for all 8:**
- Spot only, long only (buy then sell, never short), 1h candles, market orders, fee 0.1% per side.
- Up to 5 trades open at once, one per coin. Each trade gets an equal share of the free wallet.
- Shared code lives in `user_data/strategies/labkit/` (`base.py` for settings, `indicators.py` for helpers). Freqtrade never lists that folder as a strategy.
- **Status** is updated as each strategy moves through testing (see [TESTING_METHODOLOGY](TESTING_METHODOLOGY.md)).

| # | Strategy | Style | Holds for | Expect it to shine in | Expect it to struggle in | Status |
|---|---|---|---|---|---|---|
| 0 | `BuyHoldV1` | Baseline | whole period | bull markets | bear markets | baseline: IS +429% (DD 51%), OOS −35% (DD 63%) |
| 1 | `EmaTrendV1` | Trend following | days | long smooth trends | sideways chop | dropped: v2 replaced it |
| 2 | `AdxSupertrendV1` | Trend strength | days | strong breakouts | slow grinds, chop | dropped: tuned version failed stage 1 |
| 3 | `RsiBbReversionV1` | Mean reversion | hours | sideways with sharp dips | crashes | dropped: no edge even tuned |
| 4 | `DonchianBreakoutV1` | Breakout | ~1 day | range breakouts that run | fake-outs | dropped: v2 replaced it |
| 5 | `MacdVolumeV1` | Momentum | hours | impulsive swings | quiet drifts, V-reversals | dropped: OOS −0.7% (stage 1 FAIL) |
| 6 | `SqueezeBreakoutV1` | Volatility squeeze | hours to a day | coils that break upward | fake-outs, downtrends | dropped: tuned version failed stage 2 |
| 7 | `TrendPullbackV1` | Dip buying in uptrends | hours | steady uptrends | trend changes, crashes | dropped: v2 replaced it |
| 8 | `TrendPullbackV2` | Dip buying, 4h trend filter | hours | strong uptrends | trend changes | dropped: tuned OOS −1.8% |
| 9 | `EmaTrendV2` | Trend following on 4h | days | multi-week trends | sideways ranges | **watch list, paper-trading since 2026-10-06** (FreqUI :8081): stage 1 PASS (OOS +5.1%, DD 11.9%), stage 2 FAIL (3 of 8 quarters profitable) |
| 10 | `DonchianBreakoutV2` | Breakout on 4h | days | breakouts that run | failed breakouts | dropped: IS +52% → OOS −7.6% |
| 11 | `MacdVolumeV2` | Momentum + 4h trend | hours | trend-aligned bursts | choppy trend filter | dropped: worse than v1 in-sample |

All strategies, plus the tuned `…T` versions, passed the bias checks (details at the bottom). **Status after Phase 6:** no strategy passed both promotion stages, so none goes to paper trading as "promoted". `EmaTrendV2` came closest and is on the watch list. Each tuned `…T` version failed out-of-sample; see the [experiment log](EXPERIMENT_LOG.md) status table. Analysis: [RESULTS](RESULTS.md).

**Words used below:**
- **EMA:** a moving average that weights recent candles more.
- **ATR:** average candle size, a volatility measure.
- **ROI table:** take profit at X% after Y minutes.
- **Trailing stop:** a stop that follows price up.

The full glossary is in [GLOSSARY](GLOSSARY.md).

---

## 0. Buy & Hold (`BuyHoldV1`): baseline

- **Idea:** buy all 5 coins on the first candle (20% each) and never sell. Every strategy is compared against this.
- **Indicators:** none.
- **Entry / exit:** buy at the start. Never sell; open trades are valued at the end of the test.
- **Risk:** no stoploss, no ROI.
- **Why it matters:** in a bull market it's very hard to beat on raw profit. A strategy earns its place by beating it **on a risk-adjusted basis**: similar return with a much smaller drawdown, or doing far better in bear markets.
- **Known measurement issue:** Freqtrade measures drawdown on *closed* trades, so a strategy that never closes shows 0% drawdown. Since Phase 5, every risk number in this lab is measured on the wallet's value at every candle instead.
- **Status:** baseline in every run. In-sample (Oct 2023 → Oct 2025): **+429%**, max drawdown 51%. Out-of-sample (Oct 2025 → Oct 2026): **−35%**, max drawdown 63%. Paper-trading as the baseline bot since 2026-10-06.

## 1. EMA Trend (`EmaTrendV1`): trend following

- **Idea:** when a fast average crosses above a slow one, momentum turned up. Act only while price is above the 200-candle average (long-term uptrend).
- **Indicators:** EMA fast (12), EMA slow (50), EMA 200.
- **Entry:** fast EMA crosses above slow EMA **and** close > EMA200.
- **Exit:** fast EMA crosses below slow EMA.
- **Risk:**
  - Stoploss −8%.
  - Trailing stop: once +6%, sell on a 3% pullback from the best price.
  - ROI only at +30%.
  - Warm-up: 600 candles.
- **Tunable:** fast EMA ∈ {8, 12, 16, 21, 26}, slow EMA ∈ {34, 50, 72, 100}.
- **Should work:** long, smooth trends. **Should fail:** sideways chop (whipsaws: many small losses plus fees). It also exits late at tops.
- **Status: dropped.** In-sample −4.2% after fees, but +26% before fees: 675 trades of fees ate the edge. Tuned (`EmaTrendV1T`): +15.8%, but profit factor 1.09 was below the candidate rule. Replaced by `EmaTrendV2`.

## 2. ADX Supertrend (`AdxSupertrendV1`): trend strength

- **Idea:** Supertrend flips "up" when price closes above a volatility band. Take the flip only when ADX (trend strength, 0–100) confirms a real trend and buyers lead (+DI > −DI).
- **Indicators:** Supertrend (ATR 10, ×3.0), ADX 14, +DI/−DI 14.
- **Entry:** Supertrend flips up **and** ADX > 25 **and** +DI > −DI.
- **Exit:** Supertrend flips down.
- **Risk:**
  - Stoploss −10%.
  - Trailing stop: +6% trigger, 3% trail.
  - ROI only at +30%.
  - Warm-up: 300 candles.
- **Tunable:** ATR length ∈ {7, 10, 14}, multiplier ∈ {2.0 … 4.0}, ADX minimum 15–35.
- **Should work:** strong, sustained moves. **Should fail:** high ADX also appears at the *end* of trends, so it can buy into blow-off tops. It misses slow grinds and gets false flips in chop.
- **Status: dropped.** −13.9% in-sample, and it loses even with zero fees. Tuned (`AdxSupertrendV1T`): +14.4% in-sample, but out-of-sample only +1.6% with profit factor 1.09; it kept only 28% of its Sharpe (Stage 1 FAIL).

## 3. RSI + Bollinger Reversion (`RsiBbReversionV1`): mean reversion

- **Idea:** a close far below the 20-candle average (below the lower Bollinger Band) with low RSI (sellers exhausted) usually snaps back. Take the small, quick bounce.
- **Indicators:** RSI 14, Bollinger Bands (20, 2.0 standard deviations).
- **Entry:** RSI < 30 **and** close < lower band.
- **Exit:** close back above the middle band, **or** RSI > 65.
- **Risk:**
  - Stoploss −6%.
  - ROI: 6% any time, 3% after 6h, 1% after 24h.
  - No trailing stop.
  - Warm-up: 200 candles.
- **Tunable:** RSI entry 20–40, band width ∈ {1.5, 2.0, 2.5, 3.0}, RSI exit 55–75.
- **Should work:** sideways or gently rising markets with sharp dips (high win rate). **Should fail:** crashes, where "oversold" keeps getting more oversold. Losses are rarer but bigger than wins.
- **Status: dropped.** −41.9% in-sample, the worst of all, and still −23% with zero fees. Tuned: −0.1%. Buying dips in a strong bull market kept getting stopped out.

## 4. Donchian Breakout (`DonchianBreakoutV1`): breakout

- **Idea:** the "Turtle" rule. Buy a close above the highest high of the previous N candles when volume is above average; sell a close below the lowest low of the previous M candles.
- **Indicators:** Donchian channel high (N = 20) and low (M = 10), both built from *previous* candles only. Volume ratio against the previous 20 candles.
- **Entry:** close > previous 20-candle high **and** volume > 1.0 × average.
- **Exit:** close < previous 10-candle low.
- **Risk:**
  - Stoploss −10%.
  - Trailing stop: +6% trigger, 3% trail.
  - ROI only at +30%.
  - Warm-up: 120 candles (not recursive).
- **Tunable:** N ∈ {20, 30, 40, 55}, M ∈ {10, 15, 20}, volume multiplier 0.8–2.0.
- **Should work:** breakouts that keep running. Low win rate, big winners. **Should fail:** fake-outs in ranges; strings of small losses are normal.
- **Status: dropped.** −27.3% in-sample (1,329 trades), +19% before fees. Tuned: profit factor 1.08. Replaced by `DonchianBreakoutV2`.

## 5. MACD Volume (`MacdVolumeV1`): momentum

- **Idea:** a MACD cross above its signal line means momentum is turning up. Trust it only with a volume burst, while price is above EMA100.
- **Indicators:** MACD (12-26-9), volume ratio, EMA100.
- **Entry:** MACD crosses above signal **and** volume > 1.5 × average **and** close > EMA100.
- **Exit:** MACD crosses below signal.
- **Risk:**
  - Stoploss −8%.
  - ROI: 15% any time, 6% after 12h, 2% after 2 days.
  - No trailing stop.
  - Warm-up: 400 candles.
- **Tunable:** MACD set ∈ {12-26-9, 8-17-9, 5-35-5}, volume multiplier 1.0–3.0.
- **Should work:** impulsive moves after pauses. **Should fail:** quiet drifts (rarely trades) and sharp V-reversals (MACD is late at both ends).
- **Status: dropped.** The only original idea profitable after fees in-sample (+18.1%, max drawdown 7.6%). Out-of-sample it went flat (−0.7%, Sharpe 0): Stage 1 FAIL. The tuned `MacdVolumeV1T` did worse out-of-sample (−11%).

## 6. Squeeze Breakout (`SqueezeBreakoutV1`): volatility squeeze

- **Idea:** when Bollinger Bands shrink inside the Keltner Channel, volatility is unusually low and the market is coiling. Trade the release only if it breaks upward with momentum.
- **Indicators:** Bollinger Bands (20, 2), Keltner Channel (EMA 20 ± 1.5 × ATR 20), squeeze length (candles in a row), squeeze momentum (LazyBear style), EMA20.
- **Entry:** a squeeze of at least 6 candles ended within the last 3 candles **and** close > upper Bollinger Band **and** momentum > 0.
- **Exit:** momentum turns negative **or** close < EMA20.
- **Risk:**
  - Stoploss −8%.
  - Trailing stop: +6% trigger, 3% trail.
  - ROI only at +25%.
  - Warm-up: 200 candles.
- **Tunable:** Keltner multiplier ∈ {1.0, 1.25, 1.5, 2.0}, minimum squeeze length 3–20.
- **Should work:** consolidations that resolve upward. **Should fail:** fake-ups that reverse. In downtrends most releases break down, so it rarely trades (which is fine).
- **Status: dropped.** −13.9% in-sample on 1h (better on 4h). Tuned `SqueezeBreakoutV1T` passed Stage 1 (REVIEW: in the market ~1% of the time, +1.2% a year) but failed Stage 2: profitable in 3 of 8 quarters, −5.9% across them.

## 7. Trend Pullback (`TrendPullbackV1`): buy dips in uptrends

- **Idea:** in an uptrend (price > EMA200), sharp 1–3 candle dips (RSI over 2 candles < 10) tend to get bought. Buy the dip, sell the pop back above EMA5. It mixes trend following with mean reversion.
- **Indicators:** EMA200, EMA5, RSI(2).
- **Entry:** close > EMA200 **and** RSI(2) < 10.
- **Exit:** close > EMA5 **or** RSI(2) > 70.
- **Risk:**
  - Stoploss −8%.
  - ROI: 5% any time, 2.5% after 12h, break-even after 2 days.
  - No trailing stop.
  - Warm-up: 600 candles.
- **Tunable:** RSI(2) entry 3–20, RSI(2) exit 50–90.
- **Should work:** steady uptrends with normal noise (high win rate, short holds). **Should fail:** when the "dip" is the start of a crash (the EMA200 filter reacts late). Fees hurt the many small trades.
- **Status: dropped.** −22.7% in-sample over 1,941 trades, but **+66% before fees**: the clearest case of fees eating a real edge. Tuned: still −4.1%. Its v2 cut trades by two thirds.

---

## Version 2: hand-designed for fewer, better trades (Phase 6)

**Why:** Phase 5 showed that most v1 ideas have a small real edge that fees eat. Each v2 keeps its v1's idea, but:
- **Decides on 4h candles.** It reads them through Freqtrade's *informative timeframe* feature, while still running on the 1h engine, so stoplosses are checked every hour and it stays in the same leaderboard.
- **Adds a 4h uptrend filter.**
- **Holds longer**, with wider trailing stops (+10% trigger, 5% trail).

Each v2 subclasses its v1 (`class EmaTrendV2(EmaTrendV1)`) and overrides only what changed.

**Honesty note:** these designs were guided by the in-sample results, so their in-sample numbers are partly fitted to those dates. Only the out-of-sample check (Stage 1) and walk-forward (Stage 2) count.

### 8. Trend Pullback v2 (`TrendPullbackV2`)
- **Changes vs v1:**
  - Requires a 4h uptrend (4h close > 4h EMA50 > 4h EMA200).
  - Deeper dip: RSI(2) < 5 instead of < 10.
  - Holds for a bigger bounce: exits when close > EMA10 or RSI(2) > 80, instead of EMA5 / 70.
  - Larger ROI table: 8% / 4% after 12h / 1.5% after 2 days.
- **Risk:** stoploss −8%, no trailing stop, warm-up 600 candles.
- **Tunable:** RSI(2) entry 2–15, exit 60–95.
- **Status: dropped.** Untuned +3.9% in-sample. Tuned (`TrendPullbackV2T`, RSI(2) < 2): +10.2% in-sample, then −1.8% out-of-sample (Stage 1 FAIL).

### 9. EMA Trend v2 (`EmaTrendV2`)
- **Changes vs v1:**
  - Crossover of **4h** EMAs 21/55, instead of 1h 12/50.
  - Trend filter: 4h close > 4h EMA200.
  - Stoploss −10%.
  - Trailing stop starts at +10% with a 5% trail.
- **Tunable:** 4h fast EMA ∈ {12, 21, 26}, slow ∈ {50, 55, 72}.
- **Status: watch list, paper-trading since 2026-10-06 (FreqUI :8081). Not promoted.**
  - In-sample: +21.5% (126 trades, max drawdown 20.5%).
  - **Stage 1 PASS:** out-of-sample +5.1% with max drawdown 11.9% while buy & hold lost 35%; still positive at 0.15% fee and with 5m fills.
  - **Stage 2 FAIL:** profitable in only 3 of 8 quarters (rule: 60%).
  - Re-tuning it every quarter did better (5 of 8 quarters, +23%) but missed the efficiency rule (0.49 vs 0.5); a lead for future work.
  - The once-tuned `EmaTrendV2T` (+72% in-sample) lost 1% out-of-sample: overfitted.

### 10. Donchian Breakout v2 (`DonchianBreakoutV2`)
- **Changes vs v1:**
  - Channels built from **4h** candles. Entry: close above the previous 30 4h-candle high (about 5 days). Exit: close below the previous 10 4h-candle low (about 2 days).
  - It enters only on the first hour after the 4h breakout.
  - 4h volume must be at least 1.2× its average.
  - 4h EMA50 must be above EMA200.
  - Wider trailing stop.
- **Tunable:** entry channel ∈ {20, 30, 42, 55} 4h candles, exit ∈ {6, 10, 15}, volume 1.0–2.5×.
- **Status: dropped.** The biggest in-sample improvement (−27% → **+52%**), but out-of-sample −7.6% (tuned: −8.2%). Its in-sample success didn't generalise.

### 11. MACD Volume v2 (`MacdVolumeV2`)
- **Changes vs v1:**
  - Same 1h MACD signal, but only when the 4h trend is up (4h close > 4h EMA50 > 4h EMA200).
  - Volume burst raised to 2.0× (range 1.5–3.5).
- **Tunable:** MACD set, volume multiplier.
- **Status: dropped.** The 4h filter removed good trades: −5.8% in-sample (v1 was +18%). Tuned: +7.2% in-sample, but only 18 out-of-sample trades and −2.0%.

### Tuned versions (`…T`)
- `lab.py hyperopt <Strategy>` tunes a strategy on **in-sample data only**. It then writes a small generated subclass, for example `MacdVolumeV1T(MacdVolumeV1)`, containing only the tuned settings.
- The file header records how it was tuned: dates, loss, epochs, seed, the best epoch, and the experiment ID.
- Tuned files are never edited by hand. Re-tuning refuses to overwrite one without `--force`.

---

## Bias checks (Phase 4, `lab.py check-bias`)

Two automatic checks guard against strategies that look great only because they cheat:
- **Lookahead:** does a signal use candles from the future?
- **Recursive:** does an indicator need more warm-up history than the strategy asks for?

| Strategy | Lookahead (30 signals, Jan–Jun 2024, 5 pairs) | Warm-up candles | Worst indicator error at that warm-up |
|---|---|---:|---:|
| BuyHoldV1 | skipped: no indicators | 0 | n/a |
| EmaTrendV1 | no bias | 600 | 0.003% (EMA200) |
| AdxSupertrendV1 | no bias | 300 | 0.000% |
| RsiBbReversionV1 | no bias | 200 | 0.000% |
| DonchianBreakoutV1 | no bias | 120 | none (not recursive) |
| MacdVolumeV1 | no bias | 400 | 0.002% (EMA100) |
| SqueezeBreakoutV1 | no bias | 200 | 0.000% |
| TrendPullbackV1 | no bias | 600 | 0.003% (EMA200) |

- **v2 and tuned versions:** the 4 hand-designed v2s (warm-up 600, worst error 0.003%) and all 11 tuned `…T` versions also passed both checks in Phase 6. Full table: `results/checks/bias_check.md`.
- **The check can catch cheating:** a throw-away strategy that peeks one candle ahead was flagged with "has_bias: Yes".
- **The warm-up counts matter:** with only 100 warm-up candles, ADX would be off by 0.86% and MACD by 0.59%.
- **Full output:** `results/checks/bias_check.md` and `results/checks/lookahead.csv`.
