# Bias checks

Freqtrade 2026.9, timeframe 1h. Strategies: BuyHoldV1, AdxSupertrendV1, AdxSupertrendV1T, DonchianBreakoutV1, DonchianBreakoutV1T, DonchianBreakoutV2, DonchianBreakoutV2T, EmaTrendV1, EmaTrendV1T, EmaTrendV2, EmaTrendV2T, MacdVolumeV1, MacdVolumeV1T, MacdVolumeV2, MacdVolumeV2T, RsiBbReversionV1, RsiBbReversionV1T, SqueezeBreakoutV1, SqueezeBreakoutV1T, TrendPullbackV1, TrendPullbackV1T, TrendPullbackV2, TrendPullbackV2T.

## Lookahead analysis - does any signal use future candles?

Timerange `20240101-20240701`, all 5 pairs, one strategy per run (with `--strategy-list`, Freqtrade 2026.9 analyses the first strategy's trades for every strategy). Freqtrade re-runs the backtest with the data cut off right after each signal; if the signal or an indicator changes, the strategy was peeking at candles it could not have seen. Pass = `has_bias` is exactly False.

| Strategy | Has bias | Signals checked | Biased entries | Biased exits | Biased indicators |
|---|---|---:|---:|---:|---|
| BuyHoldV1 | skipped | - | - | - | no indicators; its trades only close at the end of the test, which this check cannot evaluate |
| AdxSupertrendV1 | no | 30 | 0 | 0 | - |
| AdxSupertrendV1T | no | 30 | 0 | 0 | - |
| DonchianBreakoutV1 | no | 30 | 0 | 0 | - |
| DonchianBreakoutV1T | no | 30 | 0 | 0 | - |
| DonchianBreakoutV2 | no | 30 | 0 | 0 | - |
| DonchianBreakoutV2T | no | 30 | 0 | 0 | - |
| EmaTrendV1 | no | 30 | 0 | 0 | - |
| EmaTrendV1T | no | 30 | 0 | 0 | - |
| EmaTrendV2 | no | 30 | 0 | 0 | - |
| EmaTrendV2T | no | 30 | 0 | 0 | - |
| MacdVolumeV1 | no | 30 | 0 | 0 | - |
| MacdVolumeV1T | no | 30 | 0 | 0 | - |
| MacdVolumeV2 | no | 30 | 0 | 0 | - |
| MacdVolumeV2T | no | 16 | 0 | 0 | - |
| RsiBbReversionV1 | no | 30 | 0 | 0 | - |
| RsiBbReversionV1T | no | 30 | 0 | 0 | - |
| SqueezeBreakoutV1 | no | 30 | 0 | 0 | - |
| SqueezeBreakoutV1T | no | 20 | 0 | 0 | - |
| TrendPullbackV1 | no | 30 | 0 | 0 | - |
| TrendPullbackV1T | no | 30 | 0 | 0 | - |
| TrendPullbackV2 | no | 30 | 0 | 0 | - |
| TrendPullbackV2T | no | 30 | 0 | 0 | - |

## Recursive analysis - is `startup_candle_count` enough?

BTC/USDT, timerange `20240101-20250101`. Each column shows how far an indicator's last value is off when only that many warm-up candles are available, compared with using all history. Pass = worst error at the strategy's own startup count <= 0.05%.

### BuyHoldV1 (startup_candle_count = 0)

Skipped: no indicators, so nothing needs warm-up candles.

### AdxSupertrendV1 (startup_candle_count = 300)

| Indicators | 100 | 200 | 300 (from strategy) | 400 | 600 | 1000 |
|---|---|---|---|---|---|---|
| adx | 0.855% | 0.000% | 0.000% | 0.000% | - | - |
| plus_di | 0.008% | 0.000% | -0.000% | 0.000% | - | - |
| minus_di | -0.035% | -0.000% | 0.000% | -0.000% | - | - |

Worst indicator error at 300 startup candles: **0.000%** (limit 0.05%) → **PASS**

### AdxSupertrendV1T (startup_candle_count = None)

| Indicators | 100 | 200 | 300 (from strategy) | 400 | 600 | 1000 |
|---|---|---|---|---|---|---|
| adx | 0.855% | 0.000% | 0.000% | 0.000% | - | - |
| plus_di | 0.008% | 0.000% | -0.000% | 0.000% | - | - |
| minus_di | -0.035% | -0.000% | 0.000% | -0.000% | - | - |

Worst indicator error at None startup candles: **0.000%** (limit 0.05%) → **PASS**

### DonchianBreakoutV1 (startup_candle_count = 120)

No indicator changed with the number of warm-up candles (no recursive indicators).

### DonchianBreakoutV1T (startup_candle_count = None)

No indicator changed with the number of warm-up candles (no recursive indicators).

### DonchianBreakoutV2 (startup_candle_count = 600)

| Indicators | 100 | 200 | 400 | 600 (from strategy) | 1000 |
|---|---|---|---|---|---|
| ema50_4h | 0.266% | -0.001% | 0.000% | 0.000% | - |
| ema200_4h | nan% | 2.457% | -0.341% | -0.003% | 0.001% |

Worst indicator error at 600 startup candles: **0.003%** (limit 0.05%) → **PASS**

### DonchianBreakoutV2T (startup_candle_count = None)

| Indicators | 100 | 200 | 400 | 600 (from strategy) | 1000 |
|---|---|---|---|---|---|
| ema50_4h | 0.266% | -0.001% | 0.000% | 0.000% | - |
| ema200_4h | nan% | 2.457% | -0.341% | -0.003% | 0.001% |

Worst indicator error at None startup candles: **0.003%** (limit 0.05%) → **PASS**

### EmaTrendV1 (startup_candle_count = 600)

| Indicators | 100 | 200 | 400 | 600 (from strategy) | 1000 |
|---|---|---|---|---|---|
| ema_50 | -0.024% | -0.002% | -0.000% | 0.000% | - |
| ema_12 | -0.000% | -0.000% | - | - | - |
| ema_trend | nan% | 0.064% | 0.256% | -0.003% | 0.001% |

Worst indicator error at 600 startup candles: **0.003%** (limit 0.05%) → **PASS**

### EmaTrendV1T (startup_candle_count = None)

| Indicators | 100 | 200 | 400 | 600 (from strategy) | 1000 |
|---|---|---|---|---|---|
| ema_16 | -0.000% | -0.000% | - | - | - |
| ema_72 | -0.012% | -0.013% | 0.000% | 0.000% | 0.000% |
| ema_trend | nan% | 0.064% | 0.256% | -0.003% | 0.001% |

Worst indicator error at None startup candles: **0.003%** (limit 0.05%) → **PASS**

### EmaTrendV2 (startup_candle_count = 600)

| Indicators | 100 | 200 | 400 | 600 (from strategy) | 1000 |
|---|---|---|---|---|---|
| ema_21_4h | 0.000% | 0.000% | - | - | - |
| ema_55_4h | 0.391% | -0.001% | 0.000% | 0.000% | - |
| ema_trend_4h | nan% | 2.457% | -0.341% | -0.003% | 0.001% |

Worst indicator error at 600 startup candles: **0.003%** (limit 0.05%) → **PASS**

### EmaTrendV2T (startup_candle_count = None)

| Indicators | 100 | 200 | 400 | 600 (from strategy) | 1000 |
|---|---|---|---|---|---|
| ema_72_4h | 0.644% | 0.005% | -0.000% | 0.000% | 0.000% |
| ema_21_4h | 0.000% | 0.000% | - | - | - |
| ema_trend_4h | nan% | 2.457% | -0.341% | -0.003% | 0.001% |

Worst indicator error at None startup candles: **0.003%** (limit 0.05%) → **PASS**

### MacdVolumeV1 (startup_candle_count = 400)

| Indicators | 100 | 200 | 400 (from strategy) | 600 | 1000 |
|---|---|---|---|---|---|
| macd_12_26_9 | 0.593% | 0.001% | 0.000% | - | - |
| macd_signal_12_26_9 | 0.526% | 0.001% | 0.000% | - | - |
| ema_trend | -0.157% | -0.015% | 0.002% | 0.000% | 0.000% |

Worst indicator error at 400 startup candles: **0.002%** (limit 0.05%) → **PASS**

### MacdVolumeV1T (startup_candle_count = None)

| Indicators | 100 | 200 | 400 (from strategy) | 600 | 1000 |
|---|---|---|---|---|---|
| macd_8_17_9 | 0.054% | 0.000% | - | - | - |
| macd_signal_8_17_9 | 0.011% | 0.000% | - | - | - |
| ema_trend | -0.157% | -0.015% | 0.002% | 0.000% | 0.000% |

Worst indicator error at None startup candles: **0.002%** (limit 0.05%) → **PASS**

### MacdVolumeV2 (startup_candle_count = 600)

| Indicators | 100 | 200 | 400 | 600 (from strategy) | 1000 |
|---|---|---|---|---|---|
| ema50_4h | 0.266% | -0.001% | 0.000% | 0.000% | - |
| ema200_4h | nan% | 2.457% | -0.341% | -0.003% | 0.001% |
| macd_12_26_9 | 0.593% | 0.001% | 0.000% | - | - |
| macd_signal_12_26_9 | 0.526% | 0.001% | 0.000% | - | - |
| ema_trend | -0.157% | -0.015% | 0.002% | 0.000% | 0.000% |

Worst indicator error at 600 startup candles: **0.003%** (limit 0.05%) → **PASS**

### MacdVolumeV2T (startup_candle_count = None)

| Indicators | 100 | 200 | 400 | 600 (from strategy) | 1000 |
|---|---|---|---|---|---|
| ema50_4h | 0.266% | -0.001% | 0.000% | 0.000% | - |
| ema200_4h | nan% | 2.457% | -0.341% | -0.003% | 0.001% |
| macd_8_17_9 | 0.054% | 0.000% | - | - | - |
| macd_signal_8_17_9 | 0.011% | 0.000% | - | - | - |
| ema_trend | -0.157% | -0.015% | 0.002% | 0.000% | 0.000% |

Worst indicator error at None startup candles: **0.003%** (limit 0.05%) → **PASS**

### RsiBbReversionV1 (startup_candle_count = 200)

| Indicators | 100 | 200 (from strategy) | 400 | 600 | 1000 |
|---|---|---|---|---|---|
| rsi | 0.009% | 0.000% | 0.000% | - | - |
| bb_mid | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% |
| bb_lower_2.0 | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% |

Worst indicator error at 200 startup candles: **0.000%** (limit 0.05%) → **PASS**

### RsiBbReversionV1T (startup_candle_count = None)

| Indicators | 100 | 200 (from strategy) | 400 | 600 | 1000 |
|---|---|---|---|---|---|
| rsi | 0.009% | 0.000% | 0.000% | - | - |
| bb_mid | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% |
| bb_lower_3.0 | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% |

Worst indicator error at None startup candles: **0.000%** (limit 0.05%) → **PASS**

### SqueezeBreakoutV1 (startup_candle_count = 200)

| Indicators | 100 | 200 (from strategy) | 400 | 600 | 1000 |
|---|---|---|---|---|---|
| bb_upper | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% |
| momentum | -0.000% | -0.000% | -0.000% | -0.000% | -0.000% |
| ema20 | -0.000% | -0.000% | - | - | - |

Worst indicator error at 200 startup candles: **0.000%** (limit 0.05%) → **PASS**

### SqueezeBreakoutV1T (startup_candle_count = None)

| Indicators | 100 | 200 (from strategy) | 400 | 600 | 1000 |
|---|---|---|---|---|---|
| bb_upper | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% |
| momentum | -0.000% | -0.000% | -0.000% | -0.000% | -0.000% |
| ema20 | -0.000% | -0.000% | - | - | - |

Worst indicator error at None startup candles: **0.000%** (limit 0.05%) → **PASS**

### TrendPullbackV1 (startup_candle_count = 600)

| Indicators | 100 | 200 | 400 | 600 (from strategy) | 1000 |
|---|---|---|---|---|---|
| ema200 | nan% | 0.064% | 0.256% | -0.003% | 0.001% |

Worst indicator error at 600 startup candles: **0.003%** (limit 0.05%) → **PASS**

### TrendPullbackV1T (startup_candle_count = None)

| Indicators | 100 | 200 | 400 | 600 (from strategy) | 1000 |
|---|---|---|---|---|---|
| ema200 | nan% | 0.064% | 0.256% | -0.003% | 0.001% |

Worst indicator error at None startup candles: **0.003%** (limit 0.05%) → **PASS**

### TrendPullbackV2 (startup_candle_count = 600)

| Indicators | 100 | 200 | 400 | 600 (from strategy) | 1000 |
|---|---|---|---|---|---|
| ema50_4h | 0.266% | -0.001% | 0.000% | 0.000% | - |
| ema200_4h | nan% | 2.457% | -0.341% | -0.003% | 0.001% |
| ema200 | nan% | 0.064% | 0.256% | -0.003% | 0.001% |
| ema10 | -0.000% | - | - | - | - |

Worst indicator error at 600 startup candles: **0.003%** (limit 0.05%) → **PASS**

### TrendPullbackV2T (startup_candle_count = None)

| Indicators | 100 | 200 | 400 | 600 (from strategy) | 1000 |
|---|---|---|---|---|---|
| ema50_4h | 0.266% | -0.001% | 0.000% | 0.000% | - |
| ema200_4h | nan% | 2.457% | -0.341% | -0.003% | 0.001% |
| ema200 | nan% | 0.064% | 0.256% | -0.003% | 0.001% |
| ema10 | -0.000% | - | - | - | - |

Worst indicator error at None startup candles: **0.003%** (limit 0.05%) → **PASS**

## Result

**PASS** - no bias found.
