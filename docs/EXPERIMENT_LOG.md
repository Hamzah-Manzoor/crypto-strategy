# Experiment log

Every backtest / hyperopt run started through `lab.py` adds one row per strategy (newest first).
This page is rebuilt from `results/experiments.jsonl`. Edit decisions with:

```
python3 scripts/lab.py exp decide <ID> keep|tweak|drop "why"
```

- **Strategy** = class name, which includes the version (`EmaTrendV1` → `EmaTrendV2`).
- **Period** 👁 = an out-of-sample look. These are counted; tuning on OOS is not allowed.
- **Git** = commit the code was at (`+dirty` = uncommitted strategy/config/script changes).
- Risk numbers (Max DD, Sharpe, Calmar) are mark-to-market, from the wallet value at every candle.

**40 entries**, 0 of them out-of-sample looks.

| ID | Date | Kind | Strategy | Period | TF | Fee | Profit % | Max DD % | Sharpe | Calmar | Trades | Decision | Notes | Git |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| E0040 | 2026-10-06 | diagnostic | `TrendPullbackV1` | is | 15m | 0.00% | +108.3 | 8.0 | 3.13 | 5.52 | 7440 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0039 | 2026-10-06 | diagnostic | `SqueezeBreakoutV1` | is | 15m | 0.00% | -20.8 | 25.4 | -1.53 | -0.43 | 1528 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0038 | 2026-10-06 | diagnostic | `RsiBbReversionV1` | is | 15m | 0.00% | +79.2 | 30.4 | 1.64 | 1.11 | 2459 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0037 | 2026-10-06 | diagnostic | `MacdVolumeV1` | is | 15m | 0.00% | +4.8 | 14.7 | 0.24 | 0.16 | 2423 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0036 | 2026-10-06 | diagnostic | `EmaTrendV1` | is | 15m | 0.00% | +106.1 | 14.4 | 1.66 | 3.03 | 2753 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0035 | 2026-10-06 | diagnostic | `DonchianBreakoutV1` | is | 15m | 0.00% | -17.0 | 42.1 | -0.27 | -0.21 | 5023 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0034 | 2026-10-06 | diagnostic | `AdxSupertrendV1` | is | 15m | 0.00% | -11.1 | 19.0 | -0.46 | -0.30 | 892 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0033 | 2026-10-06 | backtest | `BuyHoldV1` | is | 15m | 0.00% | +429.2 | 51.9 | 1.62 | 2.50 | 5 | baseline | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0032 | 2026-10-06 | diagnostic | `TrendPullbackV1` | is | 1h | 0.00% | +66.1 | 10.3 | 2.14 | 2.80 | 1941 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0031 | 2026-10-06 | diagnostic | `SqueezeBreakoutV1` | is | 1h | 0.00% | +1.5 | 13.7 | 0.15 | 0.06 | 403 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0030 | 2026-10-06 | diagnostic | `RsiBbReversionV1` | is | 1h | 0.00% | -23.3 | 44.4 | -0.60 | -0.28 | 700 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0029 | 2026-10-06 | diagnostic | `MacdVolumeV1` | is | 1h | 0.00% | +53.8 | 6.0 | 1.74 | 3.98 | 695 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0028 | 2026-10-06 | diagnostic | `EmaTrendV1` | is | 1h | 0.00% | +26.2 | 21.9 | 0.75 | 0.56 | 675 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0027 | 2026-10-06 | diagnostic | `DonchianBreakoutV1` | is | 1h | 0.00% | +19.4 | 31.6 | 0.47 | 0.29 | 1337 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0026 | 2026-10-06 | diagnostic | `AdxSupertrendV1` | is | 1h | 0.00% | -6.0 | 15.5 | -0.27 | -0.20 | 240 | diagnostic | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0025 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.00% | +429.5 | 51.3 | 1.63 | 2.53 | 5 | baseline | DIAGNOSTIC ONLY: zero fees to measure gross edge; not a valid result | `2cf4970+dirty` |
| E0024 | 2026-10-06 | backtest | `TrendPullbackV1` | is | 15m | 0.10% | -89.0 | 89.0 | -9.53 | -0.75 | 7440 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0023 | 2026-10-06 | backtest | `SqueezeBreakoutV1` | is | 15m | 0.10% | -56.5 | 57.1 | -5.30 | -0.60 | 1528 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0022 | 2026-10-06 | backtest | `RsiBbReversionV1` | is | 15m | 0.10% | -31.9 | 52.7 | -0.90 | -0.33 | 2459 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0021 | 2026-10-06 | backtest | `MacdVolumeV1` | is | 15m | 0.10% | -59.7 | 61.2 | -3.26 | -0.60 | 2423 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0020 | 2026-10-06 | backtest | `EmaTrendV1` | is | 15m | 0.10% | -29.4 | 43.7 | -0.61 | -0.36 | 2753 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0019 | 2026-10-06 | backtest | `DonchianBreakoutV1` | is | 15m | 0.10% | -87.7 | 88.1 | -3.79 | -0.74 | 5014 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0018 | 2026-10-06 | backtest | `AdxSupertrendV1` | is | 15m | 0.10% | -37.6 | 39.4 | -1.88 | -0.53 | 892 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0017 | 2026-10-06 | backtest | `BuyHoldV1` | is | 15m | 0.10% | +428.6 | 51.9 | 1.62 | 2.50 | 5 | baseline | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0016 | 2026-10-06 | backtest | `TrendPullbackV1` | is | 4h | 0.10% | -22.7 | 29.4 | -0.92 | -0.41 | 560 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0015 | 2026-10-06 | backtest | `SqueezeBreakoutV1` | is | 4h | 0.10% | +6.5 | 9.5 | 0.46 | 0.34 | 128 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0014 | 2026-10-06 | backtest | `RsiBbReversionV1` | is | 4h | 0.10% | -22.2 | 34.0 | -0.85 | -0.35 | 231 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0013 | 2026-10-06 | backtest | `MacdVolumeV1` | is | 4h | 0.10% | +6.7 | 10.3 | 0.42 | 0.32 | 195 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0012 | 2026-10-06 | backtest | `EmaTrendV1` | is | 4h | 0.10% | -1.1 | 19.0 | 0.02 | -0.03 | 164 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0011 | 2026-10-06 | backtest | `DonchianBreakoutV1` | is | 4h | 0.10% | +0.6 | 33.1 | 0.13 | 0.01 | 493 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0010 | 2026-10-06 | backtest | `AdxSupertrendV1` | is | 4h | 0.10% | -3.0 | 11.2 | -0.16 | -0.14 | 65 | pending | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0009 | 2026-10-06 | backtest | `BuyHoldV1` | is | 4h | 0.10% | +429.4 | 50.7 | 1.65 | 2.56 | 5 | baseline | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0008 | 2026-10-06 | backtest | `TrendPullbackV1` | is | 1h | 0.10% | -22.7 | 32.2 | -1.02 | -0.38 | 1941 | tweak: strong gross edge (+66% at zero fee, PF 1.30) destroyed by fees over 1941 trades; needs far fewer, better trades | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0007 | 2026-10-06 | backtest | `SqueezeBreakoutV1` | is | 1h | 0.10% | -13.9 | 23.2 | -0.87 | -0.31 | 403 | tweak: no gross edge on 1h (+1.5% at zero fee) but +6.5% after fees on 4h - test as a 4h strategy | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0006 | 2026-10-06 | backtest | `RsiBbReversionV1` | is | 1h | 0.10% | -41.9 | 53.6 | -1.28 | -0.44 | 699 | drop: loses even with zero fees on 1h (-23%); buying dips in a strong bull market keeps getting stopped out; keep only for hyperopt in phase 6 | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0005 | 2026-10-06 | backtest | `MacdVolumeV1` | is | 1h | 0.10% | +18.1 | 7.6 | 0.72 | 1.15 | 695 | keep: only strategy profitable after fees (+18%, DD 7.6%); low exposure (8%) so it is far behind buy & hold in this bull period - candidate for stage 1 | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0004 | 2026-10-06 | backtest | `EmaTrendV1` | is | 1h | 0.10% | -4.2 | 26.1 | -0.03 | -0.08 | 675 | tweak: gross +26% at zero fee but 675 trades of fees make it -4%; try slower EMAs / 4h | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0003 | 2026-10-06 | backtest | `DonchianBreakoutV1` | is | 1h | 0.10% | -27.3 | 49.6 | -0.51 | -0.30 | 1329 | tweak: weak gross edge (+19% at zero fee); 1329 trades; try longer entry channel | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0002 | 2026-10-06 | backtest | `AdxSupertrendV1` | is | 1h | 0.10% | -13.9 | 20.4 | -0.69 | -0.35 | 240 | drop: loses even with zero fees on 1h (-6%) and 15m (-11%); keep only for hyperopt in phase 6 | first in-sample run, all v1 defaults | `2cf4970+dirty` |
| E0001 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | first in-sample run, all v1 defaults | `2cf4970+dirty` |
