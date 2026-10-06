# Walk-forward · EmaTrendV2 · retuned · 1h

Re-tuned (CalmarHyperOptLoss, 150 epochs, seed 42, min 25 trades) on each 12-month training window, then tested on the next 3 months it never saw. Fee 0.10% per side.

| # | Train | Test | Train profit | Train trades | Test profit | Test max DD | Test trades | Buy & hold (test) |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 0 | 20231001-20241001 | 20241001-20250101 | +27.7% | 58 | +9.4% | 6.0% | 17 | +70.3% |
| 1 | 20240101-20250101 | 20250101-20250401 | +28.3% | 60 | -6.4% | 8.4% | 16 | -21.8% |
| 2 | 20240401-20250401 | 20250401-20250701 | +10.2% | 54 | +4.6% | 7.5% | 18 | +20.6% |
| 3 | 20240701-20250701 | 20250701-20251001 | +16.2% | 57 | +13.6% | 3.8% | 11 | +36.9% |
| 4 | 20241001-20251001 | 20251001-20260101 | +35.3% | 58 | -8.8% | 11.4% | 7 | -28.1% |
| 5 | 20250101-20260101 | 20260101-20260401 | +20.1% | 51 | +1.2% | 2.5% | 4 | -28.1% |
| 6 | 20250401-20260401 | 20260401-20260701 | +26.7% | 56 | -2.5% | 5.6% | 17 | -17.2% |
| 7 | 20250701-20260701 | 20260701-20261001 | +17.2% | 39 | +12.5% | 5.0% | 19 | +50.8% |

- **Profitable test windows:** 62% of 8
- **Stitched test result:** +23.3% (+11.0% a year) vs buy & hold +41.9% over the same windows
- **Walk-forward efficiency:** 0.49 (test yearly return ÷ average training yearly return +22.7%)
- **Worst test-window drawdown:** 11.4%
