# Walk-forward · SqueezeBreakoutV1 · retuned · 1h

Re-tuned (CalmarHyperOptLoss, 150 epochs, seed 42, min 25 trades) on each 12-month training window, then tested on the next 3 months it never saw. Fee 0.10% per side.

| # | Train | Test | Train profit | Train trades | Test profit | Test max DD | Test trades | Buy & hold (test) |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 0 | 20231001-20241001 | 20241001-20250101 | +2.5% | 25 | +0.9% | 0.7% | 4 | +70.3% |
| 1 | 20240101-20250101 | 20250101-20250401 | +1.9% | 52 | -1.7% | 2.6% | 8 | -21.8% |
| 2 | 20240401-20250401 | 20250401-20250701 | -0.9% | 40 | -1.7% | 1.7% | 11 | +20.6% |
| 3 | 20240701-20250701 | 20250701-20251001 | -6.1% | 271 | -0.4% | 4.0% | 77 | +36.9% |
| 4 | 20241001-20251001 | 20251001-20260101 | -1.1% | 307 | -5.4% | 9.8% | 78 | -28.1% |
| 5 | 20250101-20260101 | 20260101-20260401 | -0.9% | 30 | +1.3% | 0.7% | 5 | -28.1% |
| 6 | 20250401-20260401 | 20260401-20260701 | +1.6% | 32 | -1.6% | 1.9% | 12 | -17.2% |
| 7 | 20250701-20260701 | 20260701-20261001 | +1.0% | 47 | +2.8% | 0.7% | 15 | +50.8% |

- **Profitable test windows:** 38% of 8
- **Stitched test result:** -5.9% (-3.0% a year) vs buy & hold +41.9% over the same windows
- **Walk-forward efficiency:** n/a (training windows were not profitable on average)
- **Worst test-window drawdown:** 9.8%
