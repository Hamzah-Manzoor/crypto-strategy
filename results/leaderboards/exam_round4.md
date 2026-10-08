# Round 4 exam · 2019-01 → 2021-01 · 4 coins · 1h

- Exam run: `20261008-130445_exam2019_1h` (20190101-20210101) · buy & hold +400.7%, max DD 74.9%, Calmar 1.65
- Fee stress (0.15%/side): `20261008-130454_exam2019_1h_fee0.15pct`
- 5m intra-candle fills (information, not a rule): not run

| Status | Strategy | Profit % | PF | Trades | Max DD % | Calmar | @0.15% fee | 5m fills | Quarters + | Worst quarter |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **FAIL** | `MomentumRotationV3_R3_noSOL` | +92.3 | 4.22 | 37 | 24.4 | 1.59 | +91.2 | n/a | 5 / 8 | -12.2 |

## Quarter by quarter (profit %)

| Strategy | 2019Q1 | 2019Q2 | 2019Q3 | 2019Q4 | 2020Q1 | 2020Q2 | 2020Q3 | 2020Q4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| buy & hold | +48.7 | +96.1 | -41.3 | -16.4 | -6.9 | +35.0 | +54.5 | +81.0 |
| `MomentumRotationV3_R3_noSOL` | +0.0 | +29.3 | -12.2 | -3.1 | +2.9 | +3.1 | +16.1 | +42.3 |

## Why

**MomentumRotationV3_R3_noSOL - FAIL**
- ✅ H1 trades 37 (>= 20)
- ✅ H2 profit +92.3% (> 0), profit factor 4.22 (>= 1.2)
- ✅ H3 profit at 0.15% fee +91.2% (> 0)
- ✅ H4 max drawdown 24.4% (<= 30% and < buy & hold 74.9%)
- ❌ H5 Calmar 1.59 > buy & hold 1.65
- ❌ H6 profitable in 5 of 8 quarters (>= 4 of 8), worst quarter -12.2% (>= -10%)
- ✅ H7 bias checks passed

Rules: docs/research/momentum-exposure-preregistration.md (numbers in scripts/rules.py → ROUND4_EXAM).
