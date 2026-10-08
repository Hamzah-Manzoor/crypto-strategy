# Robustness · MomentumRotationV3

Run `20261008-123421_MomentumRotationV3` · dev period `20231001-20261001` · 1h · fee 0.10% per side · original: +95.6%, max DD 29.7%, Calmar 0.84, 65 trades

## Verdict: **ROBUST**

| Check | Verdict | Detail |
|---|---|---|
| R1 | **PASS** | 28 of 28 variants profitable (need >= 80%); median Calmar 1.33 = 157% of the original's 0.84 (need >= 50%) |
| R2 | **PASS** | 8 of 8 variants profitable (need >= 80%); median Calmar 0.80 = 95% of the original's 0.84 (need >= 50%) |
| R3 | **PASS** | 5 of 5 variants profitable (need all); median Calmar 0.85 = 101% of the original's 0.84 (need >= 50%) |
| R4 | **PASS** | profit +956 USDT; without the best 3 trades (+738 USDT, 77% of it): +219 USDT (need > 0) |

Bias check on all 41 generated variants: all passed

## R1 timing

| Variant | Profit % | Max DD % | Calmar | Trades |
|---|---:|---:|---:|---:|
| Mon 05:00 candle | +97.9 | 31.2 | 0.82 | 65 |
| Mon 11:00 candle (original) | +95.6 | 29.7 | 0.84 | 65 |
| Mon 17:00 candle | +106.1 | 27.7 | 0.98 | 64 |
| Mon 23:00 candle | +132.8 | 22.0 | 1.48 | 59 |
| Tue 05:00 candle | +126.6 | 23.9 | 1.31 | 59 |
| Tue 11:00 candle | +115.7 | 24.5 | 1.19 | 59 |
| Tue 17:00 candle | +110.1 | 25.3 | 1.11 | 59 |
| Tue 23:00 candle | +124.9 | 30.6 | 1.01 | 66 |
| Wed 05:00 candle | +127.8 | 31.4 | 1.00 | 67 |
| Wed 11:00 candle | +130.8 | 30.7 | 1.04 | 66 |
| Wed 17:00 candle | +138.9 | 30.5 | 1.10 | 66 |
| Wed 23:00 candle | +201.2 | 24.5 | 1.81 | 61 |
| Thu 05:00 candle | +189.4 | 24.8 | 1.71 | 61 |
| Thu 11:00 candle | +179.7 | 24.3 | 1.68 | 61 |
| Thu 17:00 candle | +172.1 | 23.5 | 1.68 | 61 |
| Thu 23:00 candle | +151.3 | 23.4 | 1.54 | 76 |
| Fri 05:00 candle | +131.6 | 24.3 | 1.33 | 77 |
| Fri 11:00 candle | +140.1 | 24.9 | 1.36 | 76 |
| Fri 17:00 candle | +133.6 | 26.7 | 1.22 | 76 |
| Fri 23:00 candle | +151.8 | 27.2 | 1.32 | 62 |
| Sat 05:00 candle | +151.5 | 27.1 | 1.32 | 62 |
| Sat 11:00 candle | +150.5 | 26.6 | 1.35 | 62 |
| Sat 17:00 candle | +140.0 | 27.4 | 1.24 | 62 |
| Sat 23:00 candle | +152.2 | 24.4 | 1.48 | 64 |
| Sun 05:00 candle | +162.4 | 23.7 | 1.60 | 64 |
| Sun 11:00 candle | +151.5 | 24.3 | 1.48 | 64 |
| Sun 17:00 candle | +147.8 | 25.5 | 1.38 | 64 |
| Sun 23:00 candle | +143.5 | 22.9 | 1.50 | 64 |

## R2 neighbouring settings

| Variant | Profit % | Max DD % | Calmar | Trades |
|---|---:|---:|---:|---:|
| EXPOSURE = 0.4 | +74.6 | 24.7 | 0.82 | 65 |
| EXPOSURE = 0.6 | +117.4 | 34.4 | 0.86 | 65 |
| LOOKBACK_DAYS = 20 | +93.5 | 32.5 | 0.76 | 71 |
| LOOKBACK_DAYS = 25 | +97.2 | 25.9 | 0.98 | 73 |
| LOOKBACK_DAYS = 35 | +90.6 | 31.2 | 0.77 | 66 |
| LOOKBACK_DAYS = 40 | +56.0 | 29.7 | 0.54 | 64 |
| TOP_N = 2 | +97.6 | 36.1 | 0.71 | 57 |
| TOP_N = 4 | +92.5 | 25.2 | 0.97 | 71 |

## R3 leave one coin out

| Variant | Profit % | Max DD % | Calmar | Trades |
|---|---:|---:|---:|---:|
| without BTC | +105.9 | 27.7 | 0.98 | 54 |
| without ETH | +118.1 | 26.8 | 1.11 | 54 |
| without SOL | +73.9 | 23.8 | 0.85 | 59 |
| without BNB | +86.4 | 27.8 | 0.83 | 55 |
| without XRP | +79.1 | 28.7 | 0.75 | 58 |

Rules: docs/TESTING_METHODOLOGY.md section 11 (numbers in scripts/rules.py → ROBUSTNESS).
