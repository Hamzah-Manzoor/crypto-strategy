# Round 2 exam · holdout · 1h

- Exam run: `20261007-102524_holdout_1h` (20210101-20231001) · buy & hold +397.6%, max DD 92.1%, Calmar 0.86
- Fee stress (0.15%/side): `20261007-102538_holdout_1h_fee0.15pct`
- 5m intra-candle fills (information, not a rule): `20261007-102551_holdout_1h_detail5m`

| Status | Strategy | Profit % | PF | Trades | Max DD % | Calmar | @0.15% fee | 5m fills | Quarters + | Worst quarter |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **FAIL** | `MomentumRotationV1b` | +452.9 | 2.02 | 53 | 41.4 | 2.08 | +444.5 | +452.9 | 5 / 11 | -11.4 |
| **FAIL** | `MomentumRotationV1` | +361.8 | 1.49 | 50 | 60.5 | 1.23 | +351.4 | +361.8 | 5 / 11 | -37.6 |
| **FAIL** | `EmaTrendV3` | +2.9 | 1.04 | 94 | 22.1 | 0.05 | +1.1 | +9.0 | 2 / 11 | -7.5 |
| **FAIL** | `EmaTrendV3b` | +2.4 | 1.04 | 96 | 22.5 | 0.04 | +0.5 | +8.4 | 2 / 11 | -7.9 |

## Quarter by quarter (profit %)

| Strategy | 2021Q1 | 2021Q2 | 2021Q3 | 2021Q4 | 2022Q1 | 2022Q2 | 2022Q3 | 2022Q4 | 2023Q1 | 2023Q2 | 2023Q3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| buy & hold | +451.6 | +38.0 | +189.9 | +20.5 | -23.9 | -70.4 | +10.4 | -49.7 | +68.2 | -12.6 | +2.0 |
| `MomentumRotationV1b` | +185.3 | +57.6 | +29.3 | -9.4 | +2.3 | +0.0 | +0.0 | +0.0 | +19.3 | -11.4 | -2.9 |
| `MomentumRotationV1` | +290.7 | +8.6 | +55.8 | -37.6 | +3.5 | +0.0 | +0.0 | +0.0 | +33.4 | -14.8 | -4.9 |
| `EmaTrendV3` | +16.0 | +8.2 | -3.2 | -7.5 | +0.0 | +0.0 | +0.0 | +0.0 | -2.0 | -5.8 | -0.8 |
| `EmaTrendV3b` | +16.0 | +8.2 | -3.2 | -7.9 | +0.0 | +0.0 | +0.0 | +0.0 | -2.0 | -5.8 | -0.9 |

## Why

**MomentumRotationV1b - FAIL**
- ✅ X1 trades 53 (>= 30)
- ✅ X2 profit +452.9% (> 0), profit factor 2.02 (>= 1.2)
- ✅ X3 profit at 0.15% fee +444.5% (> 0)
- ❌ X4 max drawdown 41.4% (<= 30% and < buy & hold 92.1%)
- ✅ X5 Calmar 2.08 > buy & hold 0.86
- ❌ X6 profitable in 5 of 11 quarters (>= 6 of 11), worst quarter -11.4% (>= -10%)
- ✅ X7 bias checks passed

**MomentumRotationV1 - FAIL**
- ✅ X1 trades 50 (>= 30)
- ✅ X2 profit +361.8% (> 0), profit factor 1.49 (>= 1.2)
- ✅ X3 profit at 0.15% fee +351.4% (> 0)
- ❌ X4 max drawdown 60.5% (<= 30% and < buy & hold 92.1%)
- ✅ X5 Calmar 1.23 > buy & hold 0.86
- ❌ X6 profitable in 5 of 11 quarters (>= 6 of 11), worst quarter -37.6% (>= -10%)
- ✅ X7 bias checks passed

**EmaTrendV3 - FAIL**
- ✅ X1 trades 94 (>= 30)
- ❌ X2 profit +2.9% (> 0), profit factor 1.04 (>= 1.2)
- ✅ X3 profit at 0.15% fee +1.1% (> 0)
- ✅ X4 max drawdown 22.1% (<= 30% and < buy & hold 92.1%)
- ❌ X5 Calmar 0.05 > buy & hold 0.86
- ❌ X6 profitable in 2 of 11 quarters (>= 6 of 11), worst quarter -7.5% (>= -10%)
- ✅ X7 bias checks passed

**EmaTrendV3b - FAIL**
- ✅ X1 trades 96 (>= 30)
- ❌ X2 profit +2.4% (> 0), profit factor 1.04 (>= 1.2)
- ✅ X3 profit at 0.15% fee +0.5% (> 0)
- ✅ X4 max drawdown 22.5% (<= 30% and < buy & hold 92.1%)
- ❌ X5 Calmar 0.04 > buy & hold 0.86
- ❌ X6 profitable in 2 of 11 quarters (>= 6 of 11), worst quarter -7.9% (>= -10%)
- ✅ X7 bias checks passed

Rules: docs/research/round2-preregistration.md (numbers in scripts/rules.py → EXAM).
