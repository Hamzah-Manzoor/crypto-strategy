# Glossary

Plain-English meanings of the terms used in this project, grouped by topic. Where a term has a specific setting in this lab, that's mentioned too.

## Trading basics

| Term | Meaning |
|---|---|
| **Spot trading** | Buying a coin with money you have and owning it. No borrowing. This lab is spot only. |
| **Futures / leverage** | Trading with borrowed money or contracts that multiply gains *and* losses, and can wipe out an account. Not used here. |
| **Long / short** | *Long* = buy, hoping the price rises. *Short* = profit when the price falls (needs borrowing). Every strategy here is long only. |
| **Pair** | What is traded against what. `BTC/USDT` = Bitcoin priced in USDT (a dollar-pegged coin). We trade 5 pairs. |
| **Candle (OHLCV)** | One time slice of price: **O**pen, **H**igh, **L**ow, **C**lose and **V**olume. A "1h candle" covers one hour. |
| **Timeframe** | The candle size a strategy looks at: 15m, 1h (our main one), 4h. |
| **Order book** | The live list of buy and sell offers on an exchange. |
| **Spread** | The gap between the best buy price and the best sell price. You lose it every time you trade immediately. |
| **Market order / limit order** | *Market* = buy or sell now at the best available price. *Limit* = only at your price or better (may never fill). This lab uses market orders, closest to how backtests assume fills. |
| **Fee** | What the exchange charges per trade. We use 0.1% per side (buy and sell), so 0.2% per round trip. |
| **Slippage** | Getting a worse price than expected because the price moved or the order was large. Freqtrade doesn't simulate it, so we stress-test with a 0.15% fee instead. |
| **Stake / stake amount** | Money put into one trade. Here: an equal share of the free wallet (`unlimited`), so profits compound. |
| **Wallet / starting balance** | The money a backtest or paper bot starts with: 1000 USDT (fake). |
| **Exposure / "in market"** | Share of time (or of the wallet) actually held in coins rather than cash. Buy & hold ≈ 100%; most strategies here are in the market 2–25% of the time. |

## Running a strategy

| Term | Meaning |
|---|---|
| **Strategy** | A set of rules that decides when to buy and when to sell. |
| **Entry / exit signal** | The moment the rules say "buy" or "sell". The trade happens at the *next* candle's open, never at a price that was already known. |
| **Stoploss** | Automatic sell if a trade loses X%. Example: −8%. It limits damage. |
| **Trailing stop** | A stoploss that moves up as the price rises, locking in gains. Example: once +10% in profit, sell if the price falls 5% from its best. |
| **ROI table** | Take-profit rules by time: "sell at +6% any time, +3% after 6 hours…". |
| **Backtest** | Replaying past prices to see what a strategy *would have* done. Cheap and fast, but easy to fool yourself with. |
| **Dry-run / paper trading** | Running a strategy on **live** prices with **fake** money. No real orders. Everything in this lab runs this way. |
| **Live trading** | Real money, real orders. **Not done in this project.** See [RISK_AND_SAFETY](RISK_AND_SAFETY.md). |
| **Freqtrade** | The open-source trading-bot engine this lab is built on (pinned to version 2026.9). |
| **FreqUI** | Freqtrade's web dashboard. Each paper bot has one, on 127.0.0.1:8081, :8082… |
| **Docker / container / Compose** | A way to run programs in sealed boxes (containers) so they behave the same everywhere. Compose starts several at once. |
| **Baseline** | The simple thing to beat. Here: **Buy & Hold**, which buys all 5 coins on day one and never sells. |

## Indicators (the inputs strategies look at)

| Term | Meaning |
|---|---|
| **SMA** | Simple Moving Average: the plain average of the last N closes. |
| **EMA** | Exponential Moving Average: like the SMA, but recent candles count more, so it reacts faster. |
| **Crossover** | When a fast average crosses above (buy) or below (sell) a slow one. It signals that momentum turned. |
| **RSI** | Relative Strength Index, 0–100. Below ~30 = "oversold" (fell a lot recently); above ~70 = "overbought". RSI(2) looks at only 2 candles, so it catches very short dips. |
| **Bollinger Bands** | Lines drawn 2 standard deviations above and below a 20-candle average. Price outside the bands is unusually far from normal. |
| **ATR** | Average True Range: the average candle size. A measure of volatility. |
| **Keltner Channel** | Lines drawn a multiple of ATR around an EMA. |
| **Squeeze** | Bollinger Bands shrinking inside the Keltner Channel: unusually quiet market, often before a big move. |
| **ADX / +DI / −DI** | ADX (0–100) = how *strong* a trend is, whatever its direction. +DI > −DI means buyers are stronger. |
| **Supertrend** | A volatility-based line under (uptrend) or over (downtrend) the price. It flips when price closes through it. |
| **MACD** | Difference between two EMAs, plus a "signal" average of that difference. A cross above the signal = momentum turning up. |
| **Donchian Channel** | Highest high and lowest low of the last N candles. Closing above the high = breakout. |
| **Volume ratio** | This candle's volume ÷ the recent average. Above 1 = more trading than usual. |
| **Informative timeframe** | Using a bigger timeframe's candles (e.g. 4h) inside a smaller-timeframe strategy (1h), using only *finished* bigger candles. The v2 strategies decide this way. |
| **Startup candles / warm-up** | History a strategy needs before its indicators are reliable. An EMA200 needs about 600 candles. |

## Strategy styles

| Term | Meaning |
|---|---|
| **Trend following** | Buy when a rise seems to be starting; ride it; get out when it turns. Many small losses, a few big wins. |
| **Mean reversion** | Buy unusual drops, expecting a bounce back to normal. Many small wins, occasional big losses. |
| **Breakout** | Buy when price escapes a recent range. |
| **Momentum** | Buy when the speed of the move is picking up. |
| **Whipsaw** | Being thrown in and out by false signals in a sideways market. Each time costs a small loss plus fees. |

## Measuring results

| Term | Meaning |
|---|---|
| **Profit %** | Total gain or loss over the test, after fees. |
| **CAGR** | Compound Annual Growth Rate: the yearly growth rate that would give the same total. Lets you compare different test lengths. |
| **Drawdown** | A fall in the wallet's value from its previous high. |
| **Max drawdown (Max DD)** | The worst such fall. It's the pain you'd have had to sit through. Example: buy & hold had 51% in-sample. |
| **Mark-to-market** | Valuing open positions at the current price instead of waiting until they're sold. Our drawdowns are measured this way. Freqtrade's built-in number only counts *closed* trades, and showed 0% for buy & hold. |
| **Volatility** | How much the value jumps around. |
| **Sharpe ratio** | Return per unit of volatility (yearly). Above ~1 is decent, above ~2 is very good, and above 3 over months is suspicious. |
| **Sortino ratio** | Like Sharpe, but only *downward* moves count as risk. |
| **Calmar ratio** | Yearly return ÷ max drawdown: "how much did I earn per unit of worst pain?" Our leaderboards sort by this. |
| **Profit factor (PF)** | Total money won ÷ total money lost across trades. Above 1 = profitable; we require ≥ 1.2 out-of-sample. |
| **Win rate** | Share of trades that made money. A high win rate alone means nothing if the losses are big. |
| **Expectancy** | Average profit per trade, after fees. |
| **Fee drag** | How much fees reduce results. In Phase 5, fees turned +66% into −23% for one strategy. |
| **Leaderboard** | Strategies ranked side by side for the same period, fee and timeframe. |

## Testing honestly

| Term | Meaning |
|---|---|
| **In-sample (IS)** | Data used to build and tune strategies: 2023-10-01 → 2025-10-01. |
| **Out-of-sample (OOS)** | Data kept aside and only used to *check*: 2025-10-01 → 2026-10-01. If you tune on it, it stops being a fair test. |
| **Overfitting / curve fitting** | Rules or settings that match past noise instead of a real pattern. They look great in-sample and fail later. Our tuned versions did exactly this (+72% in-sample → −1% out-of-sample). |
| **Lookahead bias** | A backtest accidentally using information from the future (e.g. tomorrow's close). It makes results look impossibly good. Checked by `lookahead-analysis`. |
| **Recursive analysis** | A check that indicators get enough warm-up history to be accurate. |
| **Hyperopt** | Freqtrade's automatic tuner: tries many settings and keeps the best by a score. |
| **Epoch** | One hyperopt attempt (one set of settings, one full backtest). We run 300. |
| **Loss function** | The score hyperopt tries to optimise. Ours is Calmar-based. |
| **Search space** | The settings hyperopt may choose from. A best value stuck at the *edge* of the space is a warning sign. |
| **Seed (random state)** | A fixed starting number that makes a random search repeatable (42 here, with exactly 6 workers). |
| **Plateau vs spike** | A real edge works for a *range* of settings (a plateau). If only one exact value works (a spike), it's probably luck. |
| **Walk-forward** | Repeatedly tune on a past window (12 months), test on the next unseen window (3 months), and slide forward. It shows whether results hold up over time. |
| **Walk-forward efficiency** | Return in the test windows ÷ return in the training windows. ~1 = it carries over; near 0 = it was fitting noise. |
| **Market regime** | The market's mood over a period: **bull** (rising), **bear** (falling) or **sideways** (going nowhere). |
| **Stress test** | Re-running under harsher assumptions (higher fees, 5-minute fills) to see if the result survives. |
| **Intra-candle detail** | Replaying each 1h candle as twelve 5m candles, so stoploss and take-profit hits happen in the realistic order. |
| **Pre-registration** | Writing down which strategies you'll test, and the pass rules, *before* looking at the result. It stops you moving the goalposts. |
| **Multiple testing / data snooping** | Test enough strategies and one will look good by luck. That's why only 10 pre-chosen candidates got the out-of-sample check. |
| **Promotion** | Passing both validation stages, which earns a strategy a paper-trading slot as "promoted". None has yet. |
| **Watch list** | Paper-traded for observation only, *not* promoted (EmaTrendV2). |

## Safety and regulation

| Term | Meaning |
|---|---|
| **API key / secret** | The password-like codes that let software trade on your exchange account. **Never used in this lab.** |
| **Trade-only key** | An API key allowed to place trades but **not** withdraw funds. The minimum safety for any future live setup. |
| **IP whitelist** | An exchange setting that makes an API key work only from listed internet addresses. |
| **KYC / AML** | Know Your Customer / Anti-Money Laundering: identity and source-of-funds checks licensed platforms must do. |
| **VASP** | Virtual Asset Service Provider: a business offering crypto services (exchange, custody, wallet…). |
| **PVARA** | Pakistan Virtual Assets Regulatory Authority: the regulator that licenses VASPs in Pakistan under the Virtual Assets Act 2026. |
| **NOC** | No-Objection Certificate: an early, preliminary clearance from PVARA. **Not** a full licence to operate. |
