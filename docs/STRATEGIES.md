# Strategies

**Shared rules for all 8:**
- Spot only, long only (buy then sell, never short), 1h candles, market orders, fee 0.1% per side.
- Up to 5 trades open at once, one per coin. Each trade gets an equal share of the free wallet.
- Shared code lives in `user_data/strategies/labkit/` (`base.py` for settings, `indicators.py` for helpers). Freqtrade never lists that folder as a strategy.
- **Status** is updated as each strategy moves through testing (see [TESTING_METHODOLOGY](TESTING_METHODOLOGY.md)).

| # | Strategy | Style | Holds for | Expect it to shine in | Expect it to struggle in | Status |
|---|---|---|---|---|---|---|
| 0 | `BuyHoldV1` | Baseline | whole period | bull markets | bear markets | baseline |
| 1 | `EmaTrendV1` | Trend following | days | long smooth trends | sideways chop | v1, bias-checked |
| 2 | `AdxSupertrendV1` | Trend strength | days | strong breakouts | slow grinds, chop | v1, bias-checked |
| 3 | `RsiBbReversionV1` | Mean reversion | hours | sideways with sharp dips | crashes | v1, bias-checked |
| 4 | `DonchianBreakoutV1` | Breakout | ~1 day | range breakouts that run | fake-outs | v1, bias-checked |
| 5 | `MacdVolumeV1` | Momentum | hours | impulsive swings | quiet drifts, V-reversals | v1, bias-checked |
| 6 | `SqueezeBreakoutV1` | Volatility squeeze | hours to a day | coils that break upward | fake-outs, downtrends | v1, bias-checked |
| 7 | `TrendPullbackV1` | Dip buying in uptrends | hours | steady uptrends | trend changes, crashes | v1, bias-checked |

"Bias-checked" means the strategy passed lookahead and recursive analysis (details at the bottom). It does **not** yet say whether it makes money; that comes in Phases 5 and 6.

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
- **Known measurement issue:** Freqtrade measures drawdown on *closed* trades, so a strategy that never closes shows 0% drawdown. Phase 5 fixes this by measuring drawdown on the wallet's value over time.

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

- **The check can catch cheating:** a throw-away strategy that peeks one candle ahead was flagged with "has_bias: Yes".
- **The warm-up counts matter:** with only 100 warm-up candles, ADX would be off by 0.86% and MACD by 0.59%.
- **Full output:** `results/checks/bias_check.md` and `results/checks/lookahead.csv`.
