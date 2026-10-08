# Round 4 exam REHEARSAL on dev data (2024)

- Exam run: `20261008-124547_custom_1h` (20240101-20250101) · buy & hold +130.1%, max DD 36.5%, Calmar 3.55
- Fee stress (0.15%/side): `20261008-124554_custom_1h_fee0.15pct`
- 5m intra-candle fills (information, not a rule): not run

| Status | Strategy | Profit % | PF | Trades | Max DD % | Calmar | @0.15% fee | 5m fills | Quarters + | Worst quarter |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **FAIL** | `MomentumRotationV3_R3_noSOL` | +31.2 | 2.23 | 31 | 23.8 | 1.31 | +30.6 | n/a | 2 / 4 | -9.7 |

## Quarter by quarter (profit %)

| Strategy | 2024Q1 | 2024Q2 | 2024Q3 | 2024Q4 |
|---|---:|---:|---:|---:|
| buy & hold | +54.4 | -9.3 | -3.0 | +69.5 |
| `MomentumRotationV3_R3_noSOL` | +25.1 | -7.3 | -9.7 | +25.4 |

## Why

**MomentumRotationV3_R3_noSOL - FAIL**
- ✅ H1 trades 31 (>= 20)
- ✅ H2 profit +31.2% (> 0), profit factor 2.23 (>= 1.2)
- ✅ H3 profit at 0.15% fee +30.6% (> 0)
- ✅ H4 max drawdown 23.8% (<= 30% and < buy & hold 36.5%)
- ❌ H5 Calmar 1.31 > buy & hold 3.55
- ❌ H6 profitable in 2 of 4 quarters (>= 4 of 8), worst quarter -9.7% (>= -10%)
- ✅ H7 bias checks passed

Rules: docs/research/momentum-exposure-preregistration.md (numbers in scripts/rules.py → ROUND4_EXAM).
