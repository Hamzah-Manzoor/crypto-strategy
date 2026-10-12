# Bias checks

Freqtrade 2026.9, timeframe 1h. Strategies: AuctionValueV2Live.

## Lookahead analysis - does any signal use future candles?

Timerange `20240101-20240703`, all 5 pairs, one strategy per run (with `--strategy-list`, Freqtrade 2026.9 analyses the first strategy's trades for every strategy). Freqtrade re-runs the backtest with the data cut off right after each signal; if the signal or an indicator changes, the strategy was peeking at candles it could not have seen. Pass = `has_bias` is exactly False.

| Strategy | Has bias | Signals checked | Biased entries | Biased exits | Biased indicators |
|---|---|---:|---:|---:|---|
| AuctionValueV2Live | no | 30 | 0 | 0 | - |

## Recursive analysis - is `startup_candle_count` enough?

BTC/USDT, timerange `20240101-20250101`. Each column shows how far an indicator's last value is off when only that many warm-up candles are available, compared with using all history. Pass = worst error at the strategy's own startup count <= 0.05%.

### AuctionValueV2Live (startup_candle_count = 576)

| Indicators | 100 | 200 | 400 | 576 (from strategy) | 600 | 1000 |
|---|---|---|---|---|---|---|
| av_val | nan% | nan% | - | - | - | - |
| av_poc | nan% | nan% | - | - | - | - |
| av_vah | nan% | nan% | - | - | - | - |
| av_state | nan% | nan% | - | - | - | - |

Worst indicator error at 576 startup candles: **0.000%** (limit 0.05%) → **PASS**

## Result

**PASS** - no bias found.
