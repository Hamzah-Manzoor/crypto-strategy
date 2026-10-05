# Market regimes

binance, 5-pair equal-weight basket from 4h candles + BTC/USDT 1d, data up to 2026-10-04

90-day windows picked separately inside in-sample and out-of-sample: bull = biggest basket rise, bear = biggest basket fall, sideways = narrowest basket range with < 10% net move; no overlap within a split. 'weak' = a bull/bear window that moved less than 20%.

| Window | Dates | Timerange | Basket return | Basket range | Basket max DD | BTC return | BTC trend rule (bull/side/bear) | Weak? |
|---|---|---|---:|---:|---:|---:|---|---|
| **bull-is** | 2024-10-26 → 2025-01-23 | `20241026-20250124` | +137.4% | 149.1% | 16.5% | +55.8% | 91% / 9% / 0% |  |
| **bear-is** | 2025-01-26 → 2025-04-25 | `20250126-20250426` | -27.9% | 68.4% | 40.6% | -9.7% | 16% / 80% / 4% |  |
| **sideways-is** | 2024-04-04 → 2024-07-02 | `20240404-20240703` | -6.3% | 22.7% | 17.7% | -5.8% | 59% / 41% / 0% |  |
| **bull-oos** | 2026-06-28 → 2026-09-25 | `20260628-20260926` | +54.7% | 56.1% | 6.9% | +40.1% | 22% / 68% / 10% |  |
| **bear-oos** | 2025-11-08 → 2026-02-05 | `20251108-20260206` | -44.7% | 87.8% | 46.8% | -39.1% | 0% / 47% / 53% |  |
| **sideways-oos** | 2026-03-04 → 2026-06-01 | `20260304-20260602` | +0.8% | 17.1% | 13.9% | +4.5% | 0% / 61% / 39% |  |

## Month by month

| Month | Split | 5-pair basket | BTC | BTC trend rule |
|---|---|---:|---:|---|
| 2023-10 | IS | +27.7% | +28.5% | sideways |
| 2023-11 | IS | +15.6% | +8.9% | bull |
| 2023-12 | IS | +26.7% | +12.1% | bull |
| 2024-01 | IS | -5.2% | +0.7% | bull |
| 2024-02 | IS | +33.8% | +43.6% | bull |
| 2024-03 | IS | +29.2% | +16.6% | bull |
| 2024-04 | IS | -18.9% | -14.9% | bull |
| 2024-05 | IS | +14.6% | +11.3% | bull |
| 2024-06 | IS | -7.4% | -7.1% | sideways |
| 2024-07 | IS | +8.8% | +3.0% | sideways |
| 2024-08 | IS | -13.8% | -8.7% | sideways |
| 2024-09 | IS | +7.6% | +7.4% | sideways |
| 2024-10 | IS | +0.7% | +11.0% | sideways |
| 2024-11 | IS | +84.3% | +37.2% | bull |
| 2024-12 | IS | -3.8% | -2.9% | bull |
| 2025-01 | IS | +14.6% | +9.5% | bull |
| 2025-02 | IS | -25.7% | -17.7% | sideways |
| 2025-03 | IS | -7.3% | -2.1% | sideways |
| 2025-04 | IS | +7.0% | +14.1% | sideways |
| 2025-05 | IS | +13.4% | +11.1% | sideways |
| 2025-06 | IS | +0.5% | +2.4% | bull |
| 2025-07 | IS | +24.5% | +8.0% | bull |
| 2025-08 | IS | +6.0% | -6.5% | sideways |
| 2025-09 | IS | +4.8% | +5.4% | sideways |
| 2025-10 | OOS | -5.0% | -3.9% | sideways |
| 2025-11 | OOS | -20.5% | -17.6% | sideways |
| 2025-12 | OOS | -5.2% | -3.0% | bear |
| 2026-01 | OOS | -12.6% | -10.2% | sideways |
| 2026-02 | OOS | -18.5% | -14.9% | bear |
| 2026-03 | OOS | +1.1% | +2.0% | bear |
| 2026-04 | OOS | +4.1% | +11.8% | bear |
| 2026-05 | OOS | -0.5% | -3.5% | sideways |
| 2026-06 | OOS | -19.6% | -20.4% | sideways |
| 2026-07 | OOS | +6.8% | +7.3% | sideways |
| 2026-08 | OOS | +29.3% | +25.0% | sideways |
| 2026-09 | OOS | +9.8% | +6.4% | bull |
| 2026-10 | OOS | +2.7% | +3.5% | bull |
