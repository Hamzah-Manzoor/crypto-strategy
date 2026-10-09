# Round 5 exam REHEARSAL on dev data (our 5 coins, 2024)

- Exam run: `20261009-163212_custom_1h` (20240101-20250101) · buy & hold +121.0%, max DD 35.8%, Calmar 3.37
- Fee stress (0.15%/side): `20261009-163224_custom_1h_fee0.15pct`
- 5m intra-candle fills (information, not a rule): not run

| Status | Strategy | Profit % | PF | Trades | Max DD % | Calmar | @0.15% fee | 5m fills | Quarters + | Worst quarter |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **FAIL** | `TrendBlendV2` | +43.6 | 4.83 | 33 | 17.1 | 2.53 | +43.0 | n/a | 2 / 4 | -8.2 |

## Quarter by quarter (profit %)

| Strategy | 2024Q1 | 2024Q2 | 2024Q3 | 2024Q4 |
|---|---:|---:|---:|---:|
| buy & hold | +62.7 | -13.5 | -1.4 | +59.5 |
| `TrendBlendV2` | +33.9 | -8.2 | -4.5 | +22.4 |

## Why

**TrendBlendV2 - FAIL**
- ✅ E1 trades 33 (>= 30)
- ✅ E2 profit +43.6% (> 0), profit factor 4.83 (>= 1.2)
- ✅ E3 profit at 0.15% fee +43.0% (> 0)
- ✅ E4 max drawdown 17.1% (<= 30% and < buy & hold 35.8%)
- ❌ E5 Calmar 2.53 > buy & hold 3.37
- ❌ E6 2 quarters up vs 2 down, 0 in cash (of 4; need 19 with up >= down), worst quarter -8.2% (>= -15%)
- ✅ E7 bias checks passed

Rules: docs/research/trend-blend-preregistration.md (numbers in scripts/rules.py → ROUND5_EXAM).
