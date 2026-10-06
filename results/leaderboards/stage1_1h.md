# Stage 1 · in-sample vs out-of-sample · 1h

- In-sample: `20261006-081317_is_1h` (20231001-20251001) · buy & hold +428.9%, max DD 51.3%, Calmar 2.53
- Out-of-sample: `20261006-081335_oos_1h` (20251001-20261001) · buy & hold -35.1%, max DD 62.9%, Calmar -0.56
- Fee stress (0.15%/side): `20261006-081347_oos_1h_fee0.15pct`
- 5m intra-candle fills (information, not a rule): `20261006-081359_oos_1h_detail5m`

| Status | Strategy | IS profit | OOS profit | OOS @0.15% fee | OOS 5m fills | IS Sharpe | OOS Sharpe | Sharpe kept | OOS max DD % | OOS Calmar | OOS PF | Trades IS / OOS |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **PASS** | `EmaTrendV2` | +21.5 | +5.1 | +4.4 | +6.3 | 0.65 | 0.45 | 69% | 11.9 | 0.43 | 1.26 | 126 / 39 |
| **REVIEW** | `SqueezeBreakoutV1T` | +2.6 | +1.2 | +0.4 | +1.2 | 0.41 | 0.35 | 85% | 2.4 | 0.50 | 1.28 | 66 / 40 |
| **FAIL** | `AdxSupertrendV1T` | +14.4 | +1.6 | +1.2 | +3.4 | 0.76 | 0.21 | 28% | 7.5 | 0.22 | 1.09 | 118 / 54 |
| **FAIL** | `MacdVolumeV1` | +18.1 | -0.7 | -6.7 | -0.7 | 0.72 | -0.00 | -0% | 16.7 | -0.04 | 0.98 | 695 / 330 |
| **FAIL** | `EmaTrendV2T` | +72.1 | -1.0 | -1.8 | +0.1 | 1.99 | -0.04 | -2% | 13.1 | -0.08 | 0.93 | 115 / 40 |
| **FAIL** | `TrendPullbackV2T` | +10.2 | -1.8 | -3.4 | -1.8 | 1.31 | -0.70 | -53% | 5.1 | -0.35 | 0.80 | 240 / 87 |
| **FAIL** | `DonchianBreakoutV2` | +52.2 | -7.6 | -8.6 | -5.6 | 1.19 | -0.53 | -44% | 18.9 | -0.40 | 0.70 | 197 / 57 |
| **FAIL** | `DonchianBreakoutV2T` | +70.4 | -8.2 | -9.1 | -6.2 | 1.45 | -0.53 | -37% | 19.6 | -0.42 | 0.68 | 188 / 52 |
| **FAIL** | `MacdVolumeV2T` | +7.2 | -2.0 | -2.4 | -2.0 | 1.16 | -1.10 | -95% | 3.8 | -0.53 | 0.43 | 81 / 18 |
| **FAIL** | `MacdVolumeV1T` | +25.5 | -11.0 | -13.8 | -11.0 | 1.21 | -2.06 | -171% | 14.0 | -0.79 | 0.51 | 372 / 159 |

## Why

**EmaTrendV2 - PASS**
- ✅ trades IS 126 (>= 50), OOS 39 (>= 20)
- ✅ OOS max drawdown 11.9% (<= 25% and < buy & hold 62.9%)
- ✅ OOS profit +5.1% (> 0), profit factor 1.26 (>= 1.2)
- ✅ OOS profit at 0.15% fee +4.4% (> 0)
- ✅ OOS Calmar 0.43 > buy & hold -0.56
- ✅ Sharpe IS 0.65 -> OOS 0.45 (keeps 69%, need >= 50%)
- ✅ bias checks passed

**SqueezeBreakoutV1T - REVIEW**
- ✅ trades IS 66 (>= 50), OOS 40 (>= 20)
- ✅ OOS max drawdown 2.4% (<= 25% and < buy & hold 62.9%)
- ✅ OOS profit +1.2% (> 0), profit factor 1.28 (>= 1.2)
- ✅ OOS profit at 0.15% fee +0.4% (> 0)
- ✅ OOS Calmar 0.50 > buy & hold -0.56
- ✅ Sharpe IS 0.41 -> OOS 0.35 (keeps 85%, need >= 50%)
- ✅ bias checks passed
- ❌ too good to be true? drawdown 2.4% < 3%

**AdxSupertrendV1T - FAIL**
- ✅ trades IS 118 (>= 50), OOS 54 (>= 20)
- ✅ OOS max drawdown 7.5% (<= 25% and < buy & hold 62.9%)
- ❌ OOS profit +1.6% (> 0), profit factor 1.09 (>= 1.2)
- ✅ OOS profit at 0.15% fee +1.2% (> 0)
- ✅ OOS Calmar 0.22 > buy & hold -0.56
- ❌ Sharpe IS 0.76 -> OOS 0.21 (keeps 28%, need >= 50%)
- ✅ bias checks passed

**MacdVolumeV1 - FAIL**
- ✅ trades IS 695 (>= 50), OOS 330 (>= 20)
- ✅ OOS max drawdown 16.7% (<= 25% and < buy & hold 62.9%)
- ❌ OOS profit -0.7% (> 0), profit factor 0.98 (>= 1.2)
- ❌ OOS profit at 0.15% fee -6.7% (> 0)
- ✅ OOS Calmar -0.04 > buy & hold -0.56
- ❌ Sharpe IS 0.72 -> OOS -0.00 (keeps -0%, need >= 50%)
- ✅ bias checks passed

**EmaTrendV2T - FAIL**
- ✅ trades IS 115 (>= 50), OOS 40 (>= 20)
- ✅ OOS max drawdown 13.1% (<= 25% and < buy & hold 62.9%)
- ❌ OOS profit -1.0% (> 0), profit factor 0.93 (>= 1.2)
- ❌ OOS profit at 0.15% fee -1.8% (> 0)
- ✅ OOS Calmar -0.08 > buy & hold -0.56
- ❌ Sharpe IS 1.99 -> OOS -0.04 (keeps -2%, need >= 50%)
- ✅ bias checks passed

**TrendPullbackV2T - FAIL**
- ✅ trades IS 240 (>= 50), OOS 87 (>= 20)
- ✅ OOS max drawdown 5.1% (<= 25% and < buy & hold 62.9%)
- ❌ OOS profit -1.8% (> 0), profit factor 0.8 (>= 1.2)
- ❌ OOS profit at 0.15% fee -3.4% (> 0)
- ✅ OOS Calmar -0.35 > buy & hold -0.56
- ❌ Sharpe IS 1.31 -> OOS -0.70 (keeps -53%, need >= 50%)
- ✅ bias checks passed

**DonchianBreakoutV2 - FAIL**
- ✅ trades IS 197 (>= 50), OOS 57 (>= 20)
- ✅ OOS max drawdown 18.9% (<= 25% and < buy & hold 62.9%)
- ❌ OOS profit -7.6% (> 0), profit factor 0.7 (>= 1.2)
- ❌ OOS profit at 0.15% fee -8.6% (> 0)
- ✅ OOS Calmar -0.40 > buy & hold -0.56
- ❌ Sharpe IS 1.19 -> OOS -0.53 (keeps -44%, need >= 50%)
- ✅ bias checks passed

**DonchianBreakoutV2T - FAIL**
- ✅ trades IS 188 (>= 50), OOS 52 (>= 20)
- ✅ OOS max drawdown 19.6% (<= 25% and < buy & hold 62.9%)
- ❌ OOS profit -8.2% (> 0), profit factor 0.68 (>= 1.2)
- ❌ OOS profit at 0.15% fee -9.1% (> 0)
- ✅ OOS Calmar -0.42 > buy & hold -0.56
- ❌ Sharpe IS 1.45 -> OOS -0.53 (keeps -37%, need >= 50%)
- ✅ bias checks passed

**MacdVolumeV2T - FAIL**
- ❌ trades IS 81 (>= 50), OOS 18 (>= 20)
- ✅ OOS max drawdown 3.8% (<= 25% and < buy & hold 62.9%)
- ❌ OOS profit -2.0% (> 0), profit factor 0.43 (>= 1.2)
- ❌ OOS profit at 0.15% fee -2.4% (> 0)
- ✅ OOS Calmar -0.53 > buy & hold -0.56
- ❌ Sharpe IS 1.16 -> OOS -1.10 (keeps -95%, need >= 50%)
- ✅ bias checks passed

**MacdVolumeV1T - FAIL**
- ✅ trades IS 372 (>= 50), OOS 159 (>= 20)
- ✅ OOS max drawdown 14.0% (<= 25% and < buy & hold 62.9%)
- ❌ OOS profit -11.0% (> 0), profit factor 0.51 (>= 1.2)
- ❌ OOS profit at 0.15% fee -13.8% (> 0)
- ❌ OOS Calmar -0.79 > buy & hold -0.56
- ❌ Sharpe IS 1.21 -> OOS -2.06 (keeps -171%, need >= 50%)
- ✅ bias checks passed

Rules: docs/TESTING_METHODOLOGY.md (thresholds in scripts/rules.py).
