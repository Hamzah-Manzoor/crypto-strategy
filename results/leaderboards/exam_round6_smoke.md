# Round 6 exam REHEARSAL on dev data (our 5 coins, 2024)

- Exam run: `20261012-175414_custom_1h` (20240101-20250101) · buy & hold +121.0%, max DD 35.8%, Calmar 3.37
- Fee stress (0.15%/side): `20261012-175425_custom_1h_fee0.15pct`
- 5m intra-candle fills (information, not a rule): `20261012-175435_custom_1h_detail5m`

| Status | Strategy | Profit % | PF | Trades | Max DD % | Calmar | @0.15% fee | 5m fills | Quarters + | Worst quarter |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **FAIL** | `AuctionValueV2` | +52.3 | 2.36 | 88 | 13.3 | 3.91 | +49.7 | +52.3 | 3 / 4 | -5.6 |

## Quarter by quarter (profit %)

| Strategy | 2024Q1 | 2024Q2 | 2024Q3 | 2024Q4 |
|---|---:|---:|---:|---:|
| buy & hold | +62.7 | -13.5 | -1.4 | +59.5 |
| `AuctionValueV2` | +22.9 | -5.6 | +3.9 | +26.3 |

## Why

**AuctionValueV2 - FAIL**
- ✅ E1 trades 88 (>= 30)
- ✅ E2 profit +52.3% (> 0), profit factor 2.36 (>= 1.2)
- ✅ E3 profit at 0.15% fee +49.7% (> 0)
- ✅ E4 max drawdown 13.3% (<= 30% and < buy & hold 35.8%)
- ✅ E5 Calmar 3.91 > buy & hold 3.37
- ❌ E6 3 quarters up vs 1 down, 0 in cash (of 4; need 11 with up >= down), worst quarter -5.6% (>= -15%)
- ✅ E7 bias checks passed

Rules: docs/research/auction-value-preregistration.md (numbers in scripts/rules.py → ROUND6_EXAM).
