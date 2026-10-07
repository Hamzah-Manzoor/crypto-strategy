# Bias checks

Freqtrade 2026.9, timeframe 1h. Strategies: MomentumRotationV2, MomentumRotationV2b, MomentumRotationV2c, MomentumRotationV1bMonday.

## Lookahead analysis - does any signal use future candles?

Timerange `20240101-20240701`, all 5 pairs, one strategy per run (with `--strategy-list`, Freqtrade 2026.9 analyses the first strategy's trades for every strategy). Freqtrade re-runs the backtest with the data cut off right after each signal; if the signal or an indicator changes, the strategy was peeking at candles it could not have seen. Pass = `has_bias` is exactly False.

| Strategy | Has bias | Signals checked | Biased entries | Biased exits | Biased indicators |
|---|---|---:|---:|---:|---|
| MomentumRotationV2 | no | 28 | 0 | 0 | - |
| MomentumRotationV2b | no | 20 | 0 | 0 | - |
| MomentumRotationV2c | no | 27 | 0 | 0 | - |
| MomentumRotationV1bMonday | no | 20 | 0 | 0 | - |

## Recursive analysis - is `startup_candle_count` enough?

BTC/USDT, timerange `20240101-20250101`. Each column shows how far an indicator's last value is off when only that many warm-up candles are available, compared with using all history. Pass = worst error at the strategy's own startup count <= 0.05%.

### MomentumRotationV2 (startup_candle_count = None)

| Indicators | 100 | 200 | 210 (from strategy) | 400 | 600 | 1000 |
|---|---|---|---|---|---|---|
| btc_ok_1d | nan% | - | - | - | - | - |

Worst indicator error at None startup candles: **0.000%** (limit 0.05%) → **PASS**

### MomentumRotationV2b (startup_candle_count = None)

No indicator changed with the number of warm-up candles (no recursive indicators).

### MomentumRotationV2c (startup_candle_count = None)

No indicator changed with the number of warm-up candles (no recursive indicators).

### MomentumRotationV1bMonday (startup_candle_count = None)

| Indicators | 100 | 200 | 210 (from strategy) | 400 | 600 | 1000 |
|---|---|---|---|---|---|---|
| btc_ok_1d | nan% | - | - | - | - | - |

Worst indicator error at None startup candles: **0.000%** (limit 0.05%) → **PASS**

## Result

**PASS** - no bias found.
