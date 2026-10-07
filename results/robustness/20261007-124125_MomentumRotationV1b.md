# Robustness · MomentumRotationV1b

Run `20261007-124125_MomentumRotationV1b` · dev period `20231001-20261001` · 1h · fee 0.10% per side · original: +363.1%, max DD 39.6%, Calmar 1.68, 64 trades

## Verdict: **ROBUST**

| Check | Verdict | Detail |
|---|---|---|
| R1 | **PASS** | 28 of 28 variants profitable (need >= 80%); median Calmar 1.43 = 85% of the original's 1.68 (need >= 50%) |
| R2 | **PASS** | 6 of 6 variants profitable (need >= 80%); median Calmar 1.31 = 78% of the original's 1.68 (need >= 50%) |
| R3 | **PASS** | 5 of 5 variants profitable (need all); median Calmar 1.49 = 89% of the original's 1.68 (need >= 50%) |
| R4 | **PASS** | profit +3631 USDT; without the best 3 trades (+2249 USDT, 62% of it): +1383 USDT (need > 0) |

Bias check on all 39 generated variants: all passed

## R1 timing

| Variant | Profit % | Max DD % | Calmar | Trades |
|---|---:|---:|---:|---:|
| Mon 05:00 candle | +215.2 | 51.9 | 0.90 | 65 |
| Mon 11:00 candle | +206.7 | 49.9 | 0.91 | 65 |
| Mon 17:00 candle | +240.1 | 47.2 | 1.07 | 64 |
| Mon 23:00 candle | +312.1 | 38.4 | 1.57 | 59 |
| Tue 05:00 candle | +288.8 | 41.2 | 1.39 | 59 |
| Tue 11:00 candle | +259.3 | 42.2 | 1.26 | 59 |
| Tue 17:00 candle | +242.0 | 43.2 | 1.17 | 59 |
| Tue 23:00 candle | +270.1 | 52.0 | 1.05 | 66 |
| Wed 05:00 candle | +277.3 | 53.1 | 1.05 | 67 |
| Wed 11:00 candle | +287.1 | 52.4 | 1.09 | 66 |
| Wed 17:00 candle | +312.6 | 52.1 | 1.16 | 66 |
| Wed 23:00 candle | +520.3 | 42.8 | 1.95 | 61 |
| Thu 05:00 candle | +479.8 | 43.4 | 1.83 | 61 |
| Thu 11:00 candle | +446.5 | 42.7 | 1.78 | 61 |
| Thu 17:00 candle | +432.5 | 41.3 | 1.80 | 61 |
| Thu 23:00 candle | +356.1 | 41.1 | 1.60 | 76 |
| Fri 05:00 candle | +297.5 | 42.4 | 1.38 | 77 |
| Fri 11:00 candle | +324.0 | 43.1 | 1.43 | 76 |
| Fri 17:00 candle | +303.5 | 45.8 | 1.29 | 76 |
| Fri 23:00 candle | +360.2 | 46.6 | 1.42 | 62 |
| Sat 05:00 candle | +366.4 | 46.4 | 1.44 | 62 |
| Sat 11:00 candle | +368.4 | 45.7 | 1.47 | 62 |
| Sat 17:00 candle | +334.2 | 46.6 | 1.35 | 62 |
| Sat 23:00 candle | +396.0 | 41.4 | 1.70 | 64 |
| Sun 05:00 candle | +431.0 | 40.4 | 1.84 | 64 |
| Sun 11:00 candle | +387.2 | 41.4 | 1.68 | 64 |
| Sun 17:00 candle | +376.4 | 43.5 | 1.57 | 64 |
| Sun 23:00 candle (original) | +363.1 | 39.6 | 1.68 | 64 |

## R2 neighbouring settings

| Variant | Profit % | Max DD % | Calmar | Trades |
|---|---:|---:|---:|---:|
| LOOKBACK_DAYS = 20 | +271.2 | 43.6 | 1.26 | 69 |
| LOOKBACK_DAYS = 25 | +301.8 | 43.0 | 1.37 | 71 |
| LOOKBACK_DAYS = 35 | +274.8 | 46.6 | 1.19 | 62 |
| LOOKBACK_DAYS = 40 | +200.8 | 48.4 | 0.91 | 62 |
| TOP_N = 2 | +355.4 | 43.4 | 1.51 | 56 |
| TOP_N = 4 | +309.3 | 36.2 | 1.65 | 71 |

## R3 leave one coin out

| Variant | Profit % | Max DD % | Calmar | Trades |
|---|---:|---:|---:|---:|
| without BTC | +352.6 | 39.2 | 1.67 | 54 |
| without ETH | +418.6 | 34.9 | 2.09 | 54 |
| without SOL | +235.6 | 36.2 | 1.37 | 59 |
| without BNB | +301.1 | 39.4 | 1.49 | 55 |
| without XRP | +273.5 | 40.2 | 1.37 | 57 |

Rules: docs/TESTING_METHODOLOGY.md section 11 (numbers in scripts/rules.py → ROBUSTNESS).
