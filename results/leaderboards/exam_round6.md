# Round 6 exam · protected holdout 2021-01 → 2023-10 · our 5 coins · 1h

- Exam run: `20261012-175537_holdout_1h` (20210101-20231001) · buy & hold +397.6%, max DD 92.1%, Calmar 0.86
- Fee stress (0.15%/side): `20261012-175554_holdout_1h_fee0.15pct`
- 5m intra-candle fills (information, not a rule): `20261012-175610_holdout_1h_detail5m`

| Status | Strategy | Profit % | PF | Trades | Max DD % | Calmar | @0.15% fee | 5m fills | Quarters + | Worst quarter |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **PASS** | `AuctionValueV2` | +193.6 | 1.62 | 237 | 21.8 | 2.20 | +180.3 | +193.6 | 6 / 11 | -11.7 |

## Quarter by quarter (profit %)

| Strategy | 2021Q1 | 2021Q2 | 2021Q3 | 2021Q4 | 2022Q1 | 2022Q2 | 2022Q3 | 2022Q4 | 2023Q1 | 2023Q2 | 2023Q3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| buy & hold | +451.6 | +38.0 | +189.9 | +20.5 | -23.9 | -70.4 | +10.4 | -49.7 | +68.2 | -12.6 | +2.0 |
| `AuctionValueV2` | +46.7 | +49.9 | +35.2 | -5.2 | +11.3 | -11.7 | -2.7 | -3.0 | +18.1 | -8.7 | +4.1 |

## Why

**AuctionValueV2 - PASS**
- ✅ E1 trades 237 (>= 30)
- ✅ E2 profit +193.6% (> 0), profit factor 1.62 (>= 1.2)
- ✅ E3 profit at 0.15% fee +180.3% (> 0)
- ✅ E4 max drawdown 21.8% (<= 30% and < buy & hold 92.1%)
- ✅ E5 Calmar 2.20 > buy & hold 0.86
- ✅ E6 6 quarters up vs 5 down, 0 in cash (of 11; need 11 with up >= down), worst quarter -11.7% (>= -15%)
- ✅ E7 bias checks passed

Rules: docs/research/auction-value-preregistration.md (numbers in scripts/rules.py → ROUND6_EXAM).
