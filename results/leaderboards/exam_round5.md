# Round 5 exam · 2019-01 → 2023-10 · 9 coins never traded in this lab · 1h

- Exam run: `20261009-163329_exam5_1h` (20190101-20231001) · buy & hold +124.2%, max DD 87.7%, Calmar 0.21
- Fee stress (0.15%/side): `20261009-163414_exam5_1h_fee0.15pct`
- 5m intra-candle fills (information, not a rule): not run

| Status | Strategy | Profit % | PF | Trades | Max DD % | Calmar | @0.15% fee | 5m fills | Quarters + | Worst quarter |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **PASS** | `TrendBlendV2` | +76.9 | 2.01 | 192 | 29.5 | 0.43 | +75.3 | n/a | 11 / 19 | -9.0 |

## Quarter by quarter (profit %)

| Strategy | 2019Q1 | 2019Q2 | 2019Q3 | 2019Q4 | 2020Q1 | 2020Q2 | 2020Q3 | 2020Q4 | 2021Q1 | 2021Q2 | 2021Q3 | 2021Q4 | 2022Q1 | 2022Q2 | 2022Q3 | 2022Q4 | 2023Q1 | 2023Q2 | 2023Q3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| buy & hold | +42.3 | +45.4 | -53.5 | -13.3 | -11.7 | +48.0 | +29.9 | +31.8 | +289.8 | +4.0 | +29.2 | -28.9 | -5.7 | -60.2 | +10.3 | -32.4 | +46.9 | -9.8 | -12.6 |
| `TrendBlendV2` | +3.9 | +14.3 | -9.0 | -1.7 | +0.4 | +3.6 | +12.8 | +5.4 | +44.9 | +12.8 | +1.0 | -6.5 | +0.9 | -5.7 | -4.1 | -6.1 | +6.8 | -3.9 | -0.9 |

## Why

**TrendBlendV2 - PASS**
- ✅ E1 trades 192 (>= 30)
- ✅ E2 profit +76.9% (> 0), profit factor 2.01 (>= 1.2)
- ✅ E3 profit at 0.15% fee +75.3% (> 0)
- ✅ E4 max drawdown 29.5% (<= 30% and < buy & hold 87.7%)
- ✅ E5 Calmar 0.43 > buy & hold 0.21
- ✅ E6 11 quarters up vs 8 down, 0 in cash (of 19; need 19 with up >= down), worst quarter -9.0% (>= -15%)
- ✅ E7 bias checks passed

Rules: docs/research/trend-blend-preregistration.md (numbers in scripts/rules.py → ROUND5_EXAM).
