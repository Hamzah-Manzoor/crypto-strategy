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

**296 entries**, 45 of them out-of-sample looks (in 9 runs).

## Current status per strategy version

| Strategy | Decision | Why | From |
|---|---|---|---|
| `EmaTrendV3` | **keep** | Round 2 dev: selected for the exam by the pre-registered rule | E0291 |
| `EmaTrendV3b` | **keep** | Round 2 dev: selected for the exam by the pre-registered rule | E0292 |
| `MomentumRotationV1` | **keep** | Round 2 dev: selected for the exam by the pre-registered rule | E0293 |
| `MomentumRotationV1b` | **keep** | Round 2 dev: selected for the exam by the pre-registered rule | E0294 |
| `EmaTrendV2` | **tweak** | EmaTrendV2 fixed walk-forward: 38% windows profitable (rule 60%), efficiency 0.88 - lumpy trend-follower returns | E0237 |
| `AdxSupertrendV1T` | **drop** | stage 1 FAIL | E0210 |
| `AdxSupertrendV1` | **drop** | AdxSupertrendV1T: OOS PF 1.09 and only 28% of IS Sharpe kept (stage 1 FAIL) | E0077 |
| `DonchianBreakoutV1` | **drop** | DonchianBreakoutV1T IS +19.0% but PF 1.08 < 1.1; not a candidate | E0069 |
| `DonchianBreakoutV2T` | **drop** | stage 1 FAIL | E0206 |
| `DonchianBreakoutV2` | **drop** | DonchianBreakoutV2 untuned: IS +52% but OOS -7.6% (stage 1 FAIL) | E0212 |
| `EmaTrendV1` | **drop** | EmaTrendV1T IS +15.8% but PF 1.09 < 1.1; not a candidate | E0065 |
| `EmaTrendV2T` | **drop** | stage 1 FAIL | E0205 |
| `EmaTrendV2` + quarterly re-tuning | **drop** | pre-registered fresh-data test FAILED: 2 of 7 quarters profitable, efficiency -0.84, -12.3% (buy & hold -65.3%) - process dropped, no retry on same data | E0281 |
| `MacdVolumeV1T` | **drop** | stage 1 FAIL | E0207 |
| `MacdVolumeV1` | **drop** | MacdVolumeV1 untuned: OOS -0.7%, Sharpe gone (stage 1 FAIL) | E0209 |
| `MacdVolumeV2T` | **drop** | stage 1 FAIL | E0211 |
| `MacdVolumeV2` | **drop** | MacdVolumeV2T: only 18 OOS trades and -2.0% (stage 1 FAIL) | E0097 |
| `RsiBbReversionV1` | **drop** | RsiBbReversionV1T breaks even in-sample (-0.1%); idea does not work here | E0081 |
| `SqueezeBreakoutV1T` | **drop** | SqueezeBreakoutV1T: stage 1 REVIEW, stage 2 FAIL; +1.2% a year is too small to matter | E0214 |
| `SqueezeBreakoutV1` | **drop** | SqueezeBreakoutV1T: passed stage 1 (REVIEW, ~1% exposure) but failed stage 2 (38% windows, efficiency n/a) | E0073 |
| `SqueezeBreakoutV1` + quarterly re-tuning | **drop** | SqueezeBreakoutV1 re-tuned walk-forward: 38% windows, stitched -5.9% | E0238 |
| `TrendPullbackV1` | **drop** | TrendPullbackV1T still loses in-sample (-4.1%); not a candidate | E0061 |
| `TrendPullbackV2T` | **drop** | stage 1 FAIL | E0208 |
| `TrendPullbackV2` | **drop** | TrendPullbackV2T: IS +10.2% but OOS -1.8% (stage 1 FAIL) | E0085 |
| `TrendPullbackV3` | **drop** | Round 2 dev: not eligible for exam (profit factor below 1.1) - idea A dropped | E0289 |
| `TrendPullbackV3b` | **drop** | Round 2 dev: not eligible for exam (profit factor below 1.1) - idea A dropped | E0290 |

## All entries

Rows from comparison runs stay `pending` unless that row needed its own decision.

| ID | Date | Kind | Strategy | Period | TF | Fee | Profit % | Max DD % | Sharpe | Calmar | Trades | Decision | Notes | Git |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| E0296 | 2026-10-07 | backtest | `TrendPullbackV1` | dev | 1h | 0.10% | -43.4 | 50.8 | -1.66 | -0.34 | 2714 | pending | Round 2 dev: all 6 versions (2 per idea) + Round 1 ancestors | `bc0e5cd+dirty` |
| E0295 | 2026-10-07 | backtest | `EmaTrendV2` | dev | 1h | 0.10% | +36.0 | 20.5 | 0.71 | 0.53 | 165 | pending | Round 2 dev: all 6 versions (2 per idea) + Round 1 ancestors | `bc0e5cd+dirty` |
| E0294 | 2026-10-07 | backtest | `MomentumRotationV1b` | dev | 1h | 0.10% | +363.1 | 39.6 | 1.48 | 1.68 | 64 | keep: Round 2 dev: selected for the exam by the pre-registered rule | Round 2 dev: all 6 versions (2 per idea) + Round 1 ancestors | `bc0e5cd+dirty` |
| E0293 | 2026-10-07 | backtest | `MomentumRotationV1` | dev | 1h | 0.10% | +355.4 | 43.4 | 1.30 | 1.51 | 56 | keep: Round 2 dev: selected for the exam by the pre-registered rule | Round 2 dev: all 6 versions (2 per idea) + Round 1 ancestors | `bc0e5cd+dirty` |
| E0292 | 2026-10-07 | backtest | `EmaTrendV3b` | dev | 1h | 0.10% | +14.2 | 25.0 | 0.38 | 0.18 | 123 | keep: Round 2 dev: selected for the exam by the pre-registered rule | Round 2 dev: all 6 versions (2 per idea) + Round 1 ancestors | `bc0e5cd+dirty` |
| E0291 | 2026-10-07 | backtest | `EmaTrendV3` | dev | 1h | 0.10% | +14.8 | 25.0 | 0.40 | 0.19 | 122 | keep: Round 2 dev: selected for the exam by the pre-registered rule | Round 2 dev: all 6 versions (2 per idea) + Round 1 ancestors | `bc0e5cd+dirty` |
| E0290 | 2026-10-07 | backtest | `TrendPullbackV3b` | dev | 1h | 0.10% | +1.1 | 15.3 | 0.09 | 0.02 | 239 | drop: Round 2 dev: not eligible for exam (profit factor below 1.1) - idea A dropped | Round 2 dev: all 6 versions (2 per idea) + Round 1 ancestors | `bc0e5cd+dirty` |
| E0289 | 2026-10-07 | backtest | `TrendPullbackV3` | dev | 1h | 0.10% | -7.7 | 22.6 | -0.23 | -0.12 | 271 | drop: Round 2 dev: not eligible for exam (profit factor below 1.1) - idea A dropped | Round 2 dev: all 6 versions (2 per idea) + Round 1 ancestors | `bc0e5cd+dirty` |
| E0288 | 2026-10-07 | backtest | `BuyHoldV1` | dev | 1h | 0.10% | +231.4 | 64.9 | 0.94 | 0.76 | 5 | baseline | Round 2 dev: all 6 versions (2 per idea) + Round 1 ancestors | `bc0e5cd+dirty` |
| E0287 | 2026-10-07 | backtest | `TrendPullbackV1` | dev | 1h | 0.10% | -43.4 | 50.8 | -1.66 | -0.34 | 2714 | pending | Round 2 dev: first versions of ideas A/B/C vs their Round 1 ancestors | `bc0e5cd+dirty` |
| E0286 | 2026-10-07 | backtest | `EmaTrendV2` | dev | 1h | 0.10% | +36.0 | 20.5 | 0.71 | 0.53 | 165 | pending | Round 2 dev: first versions of ideas A/B/C vs their Round 1 ancestors | `bc0e5cd+dirty` |
| E0285 | 2026-10-07 | backtest | `MomentumRotationV1` | dev | 1h | 0.10% | +355.4 | 43.4 | 1.30 | 1.51 | 56 | pending | Round 2 dev: first versions of ideas A/B/C vs their Round 1 ancestors | `bc0e5cd+dirty` |
| E0284 | 2026-10-07 | backtest | `EmaTrendV3` | dev | 1h | 0.10% | +14.8 | 25.0 | 0.40 | 0.19 | 122 | pending | Round 2 dev: first versions of ideas A/B/C vs their Round 1 ancestors | `bc0e5cd+dirty` |
| E0283 | 2026-10-07 | backtest | `TrendPullbackV3` | dev | 1h | 0.10% | -7.7 | 22.6 | -0.23 | -0.12 | 271 | pending | Round 2 dev: first versions of ideas A/B/C vs their Round 1 ancestors | `bc0e5cd+dirty` |
| E0282 | 2026-10-07 | backtest | `BuyHoldV1` | dev | 1h | 0.10% | +231.4 | 64.9 | 0.94 | 0.76 | 5 | baseline | Round 2 dev: first versions of ideas A/B/C vs their Round 1 ancestors | `bc0e5cd+dirty` |
| E0281 | 2026-10-06 | walkforward | `EmaTrendV2` | walk-forward (retuned) | 1h | 0.10% | -12.3 | 12.3 | n/a | n/a | 93 | drop: pre-registered fresh-data test FAILED: 2 of 7 quarters profitable, efficiency -0.84, -12.3% (buy & hold -65.3%) - process dropped, no retry on same data | retuned: 29% windows profitable, efficiency -0.84 | `fdeea75+dirty` |
| E0280 | 2026-10-06 | backtest | `TrendPullbackV2T` | is | 1h | 0.10% | +10.2 | 3.7 | 1.31 | 1.35 | 240 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0279 | 2026-10-06 | backtest | `TrendPullbackV2` | is | 1h | 0.10% | +3.9 | 9.2 | 0.27 | 0.21 | 675 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0278 | 2026-10-06 | backtest | `TrendPullbackV1T` | is | 1h | 0.10% | -4.1 | 12.0 | -0.29 | -0.17 | 715 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0277 | 2026-10-06 | backtest | `TrendPullbackV1` | is | 1h | 0.10% | -22.7 | 32.2 | -1.02 | -0.38 | 1941 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0276 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | is | 1h | 0.10% | +2.6 | 3.5 | 0.41 | 0.36 | 66 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0275 | 2026-10-06 | backtest | `SqueezeBreakoutV1` | is | 1h | 0.10% | -13.9 | 23.2 | -0.87 | -0.31 | 403 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0274 | 2026-10-06 | backtest | `RsiBbReversionV1T` | is | 1h | 0.10% | -0.1 | 18.2 | 0.05 | -0.00 | 254 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0273 | 2026-10-06 | backtest | `RsiBbReversionV1` | is | 1h | 0.10% | -41.9 | 53.6 | -1.28 | -0.44 | 699 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0272 | 2026-10-06 | backtest | `MacdVolumeV2T` | is | 1h | 0.10% | +7.2 | 3.4 | 1.16 | 1.05 | 81 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0271 | 2026-10-06 | backtest | `MacdVolumeV2` | is | 1h | 0.10% | -1.5 | 12.6 | -0.10 | -0.06 | 261 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0270 | 2026-10-06 | backtest | `MacdVolumeV1T` | is | 1h | 0.10% | +25.5 | 5.7 | 1.21 | 2.12 | 372 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0269 | 2026-10-06 | backtest | `MacdVolumeV1` | is | 1h | 0.10% | +18.1 | 7.6 | 0.72 | 1.15 | 695 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0268 | 2026-10-06 | backtest | `EmaTrendV2T` | is | 1h | 0.10% | +72.1 | 9.6 | 1.99 | 3.26 | 115 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0267 | 2026-10-06 | backtest | `EmaTrendV2` | is | 1h | 0.10% | +21.5 | 20.5 | 0.65 | 0.50 | 126 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0266 | 2026-10-06 | backtest | `EmaTrendV1T` | is | 1h | 0.10% | +15.8 | 25.5 | 0.51 | 0.30 | 539 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0265 | 2026-10-06 | backtest | `EmaTrendV1` | is | 1h | 0.10% | -4.2 | 26.1 | -0.03 | -0.08 | 675 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0264 | 2026-10-06 | backtest | `DonchianBreakoutV2T` | is | 1h | 0.10% | +70.4 | 13.7 | 1.45 | 2.23 | 188 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0263 | 2026-10-06 | backtest | `DonchianBreakoutV2` | is | 1h | 0.10% | +52.2 | 23.1 | 1.19 | 1.01 | 197 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0262 | 2026-10-06 | backtest | `DonchianBreakoutV1T` | is | 1h | 0.10% | +19.0 | 25.6 | 0.49 | 0.35 | 683 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0261 | 2026-10-06 | backtest | `DonchianBreakoutV1` | is | 1h | 0.10% | -27.3 | 49.6 | -0.51 | -0.30 | 1329 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0260 | 2026-10-06 | backtest | `AdxSupertrendV1T` | is | 1h | 0.10% | +14.4 | 6.5 | 0.76 | 1.06 | 118 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0259 | 2026-10-06 | backtest | `AdxSupertrendV1` | is | 1h | 0.10% | -13.9 | 20.4 | -0.69 | -0.35 | 240 | pending | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0258 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | final in-sample leaderboard, all 23 versions (Phase 8) | `f8f79d6` |
| E0257 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | sideways-oos 👁 | 1h | 0.10% | -0.7 | 1.2 | -1.94 | -2.46 | 9 | pending | stage 2: regime sideways-oos | `fa623ac+dirty` |
| E0256 | 2026-10-06 | backtest | `EmaTrendV2` | sideways-oos 👁 | 1h | 0.10% | -1.0 | 5.0 | -0.19 | -0.77 | 15 | pending | stage 2: regime sideways-oos | `fa623ac+dirty` |
| E0255 | 2026-10-06 | backtest | `BuyHoldV1` | sideways-oos 👁 | 1h | 0.10% | +0.8 | 15.6 | -0.30 | 0.22 | 5 | baseline | stage 2: regime sideways-oos | `fa623ac+dirty` |
| E0254 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | bear-oos 👁 | 1h | 0.10% | +0.9 | 1.7 | 0.86 | 2.26 | 12 | pending | stage 2: regime bear-oos | `fa623ac+dirty` |
| E0253 | 2026-10-06 | backtest | `EmaTrendV2` | bear-oos 👁 | 1h | 0.10% | -0.1 | 2.7 | -0.05 | -0.22 | 4 | pending | stage 2: regime bear-oos | `fa623ac+dirty` |
| E0252 | 2026-10-06 | backtest | `BuyHoldV1` | bear-oos 👁 | 1h | 0.10% | -44.0 | 46.9 | -3.60 | -1.93 | 5 | baseline | stage 2: regime bear-oos | `fa623ac+dirty` |
| E0251 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | bull-oos 👁 | 1h | 0.10% | +1.3 | 1.4 | 1.11 | 3.64 | 9 | pending | stage 2: regime bull-oos | `fa623ac+dirty` |
| E0250 | 2026-10-06 | backtest | `EmaTrendV2` | bull-oos 👁 | 1h | 0.10% | +12.6 | 5.2 | 2.40 | 12.00 | 16 | pending | stage 2: regime bull-oos | `fa623ac+dirty` |
| E0249 | 2026-10-06 | backtest | `BuyHoldV1` | bull-oos 👁 | 1h | 0.10% | +53.6 | 7.8 | 3.97 | 60.53 | 5 | baseline | stage 2: regime bull-oos | `fa623ac+dirty` |
| E0248 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | sideways-is | 1h | 0.10% | -0.1 | 1.1 | -0.55 | -0.52 | 15 | pending | stage 2: regime sideways-is | `fa623ac+dirty` |
| E0247 | 2026-10-06 | backtest | `EmaTrendV2` | sideways-is | 1h | 0.10% | -10.0 | 13.2 | -2.16 | -2.63 | 19 | pending | stage 2: regime sideways-is | `fa623ac+dirty` |
| E0246 | 2026-10-06 | backtest | `BuyHoldV1` | sideways-is | 1h | 0.10% | -7.1 | 21.3 | -0.48 | -1.21 | 5 | baseline | stage 2: regime sideways-is | `fa623ac+dirty` |
| E0245 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | bear-is | 1h | 0.10% | -1.4 | 2.0 | -2.64 | -2.76 | 5 | pending | stage 2: regime bear-is | `fa623ac+dirty` |
| E0244 | 2026-10-06 | backtest | `EmaTrendV2` | bear-is | 1h | 0.10% | -7.9 | 8.6 | -4.31 | -3.31 | 8 | pending | stage 2: regime bear-is | `fa623ac+dirty` |
| E0243 | 2026-10-06 | backtest | `BuyHoldV1` | bear-is | 1h | 0.10% | -27.8 | 43.6 | -1.36 | -1.68 | 5 | baseline | stage 2: regime bear-is | `fa623ac+dirty` |
| E0242 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | bull-is | 1h | 0.10% | +1.0 | 1.2 | 1.54 | 3.45 | 3 | pending | stage 2: regime bull-is | `fa623ac+dirty` |
| E0241 | 2026-10-06 | backtest | `EmaTrendV2` | bull-is | 1h | 0.10% | +2.1 | 8.1 | 0.54 | 1.09 | 22 | pending | stage 2: regime bull-is | `fa623ac+dirty` |
| E0240 | 2026-10-06 | backtest | `BuyHoldV1` | bull-is | 1h | 0.10% | +134.4 | 22.5 | 5.49 | 135.83 | 5 | baseline | stage 2: regime bull-is | `fa623ac+dirty` |
| E0239 | 2026-10-06 | walkforward | `EmaTrendV2` | walk-forward (retuned) 👁 | 1h | 0.10% | +23.3 | 11.4 | n/a | n/a | 109 | drop: superseded by E0281: the near-miss did not hold on fresh 2021-2023 data | retuned: 62% windows profitable, efficiency 0.49 | `fa623ac+dirty` |
| E0238 | 2026-10-06 | walkforward | `SqueezeBreakoutV1` | walk-forward (retuned) 👁 | 1h | 0.10% | -5.9 | 9.8 | n/a | n/a | 210 | drop: SqueezeBreakoutV1 re-tuned walk-forward: 38% windows, stitched -5.9% | retuned: 38% windows profitable, efficiency n/a | `fa623ac+dirty` |
| E0237 | 2026-10-06 | walkforward | `EmaTrendV2` | walk-forward (fixed) 👁 | 1h | 0.10% | +11.2 | 12.2 | n/a | n/a | 103 | tweak: EmaTrendV2 fixed walk-forward: 38% windows profitable (rule 60%), efficiency 0.88 - lumpy trend-follower returns | fixed: 38% windows profitable, efficiency 0.88 | `fa623ac+dirty` |
| E0236 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | oos 👁 | 1h+5m | 0.10% | +1.2 | 2.4 | 0.35 | 0.50 | 40 | pending | stage 1: 5m intra-candle fills | `fa623ac+dirty` |
| E0235 | 2026-10-06 | backtest | `EmaTrendV2` | oos 👁 | 1h+5m | 0.10% | +6.3 | 11.9 | 0.52 | 0.53 | 39 | pending | stage 1: 5m intra-candle fills | `fa623ac+dirty` |
| E0234 | 2026-10-06 | backtest | `DonchianBreakoutV2` | oos 👁 | 1h+5m | 0.10% | -5.6 | 18.9 | -0.36 | -0.29 | 56 | pending | stage 1: 5m intra-candle fills | `fa623ac+dirty` |
| E0233 | 2026-10-06 | backtest | `MacdVolumeV2T` | oos 👁 | 1h+5m | 0.10% | -2.0 | 3.8 | -1.10 | -0.53 | 18 | pending | stage 1: 5m intra-candle fills | `fa623ac+dirty` |
| E0232 | 2026-10-06 | backtest | `AdxSupertrendV1T` | oos 👁 | 1h+5m | 0.10% | +3.4 | 7.5 | 0.37 | 0.45 | 54 | pending | stage 1: 5m intra-candle fills | `fa623ac+dirty` |
| E0231 | 2026-10-06 | backtest | `MacdVolumeV1` | oos 👁 | 1h+5m | 0.10% | -0.7 | 16.7 | -0.00 | -0.04 | 330 | pending | stage 1: 5m intra-candle fills | `fa623ac+dirty` |
| E0230 | 2026-10-06 | backtest | `TrendPullbackV2T` | oos 👁 | 1h+5m | 0.10% | -1.8 | 5.1 | -0.70 | -0.35 | 87 | pending | stage 1: 5m intra-candle fills | `fa623ac+dirty` |
| E0229 | 2026-10-06 | backtest | `MacdVolumeV1T` | oos 👁 | 1h+5m | 0.10% | -11.0 | 14.0 | -2.06 | -0.79 | 159 | pending | stage 1: 5m intra-candle fills | `fa623ac+dirty` |
| E0228 | 2026-10-06 | backtest | `DonchianBreakoutV2T` | oos 👁 | 1h+5m | 0.10% | -6.2 | 19.6 | -0.37 | -0.32 | 51 | pending | stage 1: 5m intra-candle fills | `fa623ac+dirty` |
| E0227 | 2026-10-06 | backtest | `EmaTrendV2T` | oos 👁 | 1h+5m | 0.10% | +0.1 | 13.1 | 0.07 | 0.01 | 40 | pending | stage 1: 5m intra-candle fills | `fa623ac+dirty` |
| E0226 | 2026-10-06 | backtest | `BuyHoldV1` | oos 👁 | 1h+5m | 0.10% | -35.1 | 62.9 | -0.60 | -0.56 | 5 | baseline | stage 1: 5m intra-candle fills | `fa623ac+dirty` |
| E0225 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | oos 👁 | 1h | 0.15% | +0.4 | 2.8 | 0.13 | 0.14 | 40 | pending | stage 1: fee stress 0.15% | `fa623ac+dirty` |
| E0224 | 2026-10-06 | backtest | `EmaTrendV2` | oos 👁 | 1h | 0.15% | +4.4 | 12.3 | 0.40 | 0.35 | 39 | pending | stage 1: fee stress 0.15% | `fa623ac+dirty` |
| E0223 | 2026-10-06 | backtest | `DonchianBreakoutV2` | oos 👁 | 1h | 0.15% | -8.6 | 19.5 | -0.60 | -0.44 | 57 | pending | stage 1: fee stress 0.15% | `fa623ac+dirty` |
| E0222 | 2026-10-06 | backtest | `MacdVolumeV2T` | oos 👁 | 1h | 0.15% | -2.4 | 4.1 | -1.26 | -0.58 | 18 | pending | stage 1: fee stress 0.15% | `fa623ac+dirty` |
| E0221 | 2026-10-06 | backtest | `AdxSupertrendV1T` | oos 👁 | 1h | 0.15% | +1.2 | 7.9 | 0.17 | 0.15 | 54 | pending | stage 1: fee stress 0.15% | `fa623ac+dirty` |
| E0220 | 2026-10-06 | backtest | `MacdVolumeV1` | oos 👁 | 1h | 0.15% | -6.7 | 20.9 | -0.47 | -0.32 | 330 | pending | stage 1: fee stress 0.15% | `fa623ac+dirty` |
| E0219 | 2026-10-06 | backtest | `TrendPullbackV2T` | oos 👁 | 1h | 0.15% | -3.4 | 6.1 | -1.38 | -0.57 | 87 | pending | stage 1: fee stress 0.15% | `fa623ac+dirty` |
| E0218 | 2026-10-06 | backtest | `MacdVolumeV1T` | oos 👁 | 1h | 0.15% | -13.8 | 16.5 | -2.55 | -0.84 | 159 | pending | stage 1: fee stress 0.15% | `fa623ac+dirty` |
| E0217 | 2026-10-06 | backtest | `DonchianBreakoutV2T` | oos 👁 | 1h | 0.15% | -9.1 | 20.1 | -0.60 | -0.45 | 52 | pending | stage 1: fee stress 0.15% | `fa623ac+dirty` |
| E0216 | 2026-10-06 | backtest | `EmaTrendV2T` | oos 👁 | 1h | 0.15% | -1.8 | 13.7 | -0.10 | -0.13 | 40 | pending | stage 1: fee stress 0.15% | `fa623ac+dirty` |
| E0215 | 2026-10-06 | backtest | `BuyHoldV1` | oos 👁 | 1h | 0.15% | -35.2 | 62.9 | -0.60 | -0.56 | 5 | baseline | stage 1: fee stress 0.15% | `fa623ac+dirty` |
| E0214 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | oos 👁 | 1h | 0.10% | +1.2 | 2.4 | 0.35 | 0.50 | 40 | drop: SqueezeBreakoutV1T: stage 1 REVIEW, stage 2 FAIL; +1.2% a year is too small to matter | stage 1: out-of-sample | `fa623ac+dirty` |
| E0213 | 2026-10-06 | backtest | `EmaTrendV2` | oos 👁 | 1h | 0.10% | +5.1 | 11.9 | 0.45 | 0.43 | 39 | keep: EmaTrendV2 passed stage 1 (OOS +5.1%, DD 11.9% vs buy & hold -35%) but failed stage 2: profitable in only 3 of 8 quarters - watch list, not promoted | stage 1: out-of-sample | `fa623ac+dirty` |
| E0212 | 2026-10-06 | backtest | `DonchianBreakoutV2` | oos 👁 | 1h | 0.10% | -7.6 | 18.9 | -0.53 | -0.40 | 57 | drop: DonchianBreakoutV2 untuned: IS +52% but OOS -7.6% (stage 1 FAIL) | stage 1: out-of-sample | `fa623ac+dirty` |
| E0211 | 2026-10-06 | backtest | `MacdVolumeV2T` | oos 👁 | 1h | 0.10% | -2.0 | 3.8 | -1.10 | -0.53 | 18 | drop: stage 1 FAIL | stage 1: out-of-sample | `fa623ac+dirty` |
| E0210 | 2026-10-06 | backtest | `AdxSupertrendV1T` | oos 👁 | 1h | 0.10% | +1.6 | 7.5 | 0.21 | 0.22 | 54 | drop: stage 1 FAIL | stage 1: out-of-sample | `fa623ac+dirty` |
| E0209 | 2026-10-06 | backtest | `MacdVolumeV1` | oos 👁 | 1h | 0.10% | -0.7 | 16.7 | -0.00 | -0.04 | 330 | drop: MacdVolumeV1 untuned: OOS -0.7%, Sharpe gone (stage 1 FAIL) | stage 1: out-of-sample | `fa623ac+dirty` |
| E0208 | 2026-10-06 | backtest | `TrendPullbackV2T` | oos 👁 | 1h | 0.10% | -1.8 | 5.1 | -0.70 | -0.35 | 87 | drop: stage 1 FAIL | stage 1: out-of-sample | `fa623ac+dirty` |
| E0207 | 2026-10-06 | backtest | `MacdVolumeV1T` | oos 👁 | 1h | 0.10% | -11.0 | 14.0 | -2.06 | -0.79 | 159 | drop: stage 1 FAIL | stage 1: out-of-sample | `fa623ac+dirty` |
| E0206 | 2026-10-06 | backtest | `DonchianBreakoutV2T` | oos 👁 | 1h | 0.10% | -8.2 | 19.6 | -0.53 | -0.42 | 52 | drop: stage 1 FAIL | stage 1: out-of-sample | `fa623ac+dirty` |
| E0205 | 2026-10-06 | backtest | `EmaTrendV2T` | oos 👁 | 1h | 0.10% | -1.0 | 13.1 | -0.04 | -0.08 | 40 | drop: stage 1 FAIL | stage 1: out-of-sample | `fa623ac+dirty` |
| E0204 | 2026-10-06 | backtest | `BuyHoldV1` | oos 👁 | 1h | 0.10% | -35.1 | 62.9 | -0.60 | -0.56 | 5 | baseline | stage 1: out-of-sample | `fa623ac+dirty` |
| E0203 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | is | 1h | 0.10% | +2.6 | 3.5 | 0.41 | 0.36 | 66 | pending | stage 1: in-sample | `fa623ac+dirty` |
| E0202 | 2026-10-06 | backtest | `EmaTrendV2` | is | 1h | 0.10% | +21.5 | 20.5 | 0.65 | 0.50 | 126 | pending | stage 1: in-sample | `fa623ac+dirty` |
| E0201 | 2026-10-06 | backtest | `DonchianBreakoutV2` | is | 1h | 0.10% | +52.2 | 23.1 | 1.19 | 1.01 | 197 | pending | stage 1: in-sample | `fa623ac+dirty` |
| E0200 | 2026-10-06 | backtest | `MacdVolumeV2T` | is | 1h | 0.10% | +7.2 | 3.4 | 1.16 | 1.05 | 81 | pending | stage 1: in-sample | `fa623ac+dirty` |
| E0199 | 2026-10-06 | backtest | `AdxSupertrendV1T` | is | 1h | 0.10% | +14.4 | 6.5 | 0.76 | 1.06 | 118 | pending | stage 1: in-sample | `fa623ac+dirty` |
| E0198 | 2026-10-06 | backtest | `MacdVolumeV1` | is | 1h | 0.10% | +18.1 | 7.6 | 0.72 | 1.15 | 695 | pending | stage 1: in-sample | `fa623ac+dirty` |
| E0197 | 2026-10-06 | backtest | `TrendPullbackV2T` | is | 1h | 0.10% | +10.2 | 3.7 | 1.31 | 1.35 | 240 | pending | stage 1: in-sample | `fa623ac+dirty` |
| E0196 | 2026-10-06 | backtest | `MacdVolumeV1T` | is | 1h | 0.10% | +25.5 | 5.7 | 1.21 | 2.12 | 372 | pending | stage 1: in-sample | `fa623ac+dirty` |
| E0195 | 2026-10-06 | backtest | `DonchianBreakoutV2T` | is | 1h | 0.10% | +70.4 | 13.7 | 1.45 | 2.23 | 188 | pending | stage 1: in-sample | `fa623ac+dirty` |
| E0194 | 2026-10-06 | backtest | `EmaTrendV2T` | is | 1h | 0.10% | +72.1 | 9.6 | 1.99 | 3.26 | 115 | pending | stage 1: in-sample | `fa623ac+dirty` |
| E0193 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | stage 1: in-sample | `fa623ac+dirty` |
| E0192 | 2026-10-06 | backtest | `TrendPullbackV2T` | sideways-is | 1h | 0.10% | -0.9 | 1.5 | -2.04 | -2.38 | 14 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0191 | 2026-10-06 | backtest | `TrendPullbackV2` | sideways-is | 1h | 0.10% | -0.8 | 2.3 | -1.19 | -1.41 | 47 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0190 | 2026-10-06 | backtest | `TrendPullbackV1T` | sideways-is | 1h | 0.10% | -2.9 | 3.3 | -3.50 | -3.42 | 77 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0189 | 2026-10-06 | backtest | `TrendPullbackV1` | sideways-is | 1h | 0.10% | -7.3 | 8.6 | -3.47 | -3.08 | 178 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0188 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | sideways-is | 1h | 0.10% | -0.1 | 1.1 | -0.55 | -0.52 | 15 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0187 | 2026-10-06 | backtest | `SqueezeBreakoutV1` | sideways-is | 1h | 0.10% | -7.1 | 8.6 | -3.79 | -2.99 | 67 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0186 | 2026-10-06 | backtest | `RsiBbReversionV1T` | sideways-is | 1h | 0.10% | -1.5 | 9.1 | -0.55 | -0.66 | 48 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0185 | 2026-10-06 | backtest | `RsiBbReversionV1` | sideways-is | 1h | 0.10% | -6.1 | 11.8 | -1.68 | -1.91 | 99 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0184 | 2026-10-06 | backtest | `MacdVolumeV2T` | sideways-is | 1h | 0.10% | +1.1 | 0.2 | 1.66 | 22.05 | 2 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0183 | 2026-10-06 | backtest | `MacdVolumeV2` | sideways-is | 1h | 0.10% | +0.7 | 1.5 | 0.80 | 2.05 | 14 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0182 | 2026-10-06 | backtest | `MacdVolumeV1T` | sideways-is | 1h | 0.10% | +2.6 | 3.0 | 1.37 | 3.60 | 42 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0181 | 2026-10-06 | backtest | `MacdVolumeV1` | sideways-is | 1h | 0.10% | -0.8 | 4.2 | -0.25 | -0.73 | 82 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0180 | 2026-10-06 | backtest | `EmaTrendV2T` | sideways-is | 1h | 0.10% | -0.2 | 5.2 | -0.02 | -0.14 | 15 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0179 | 2026-10-06 | backtest | `EmaTrendV2` | sideways-is | 1h | 0.10% | -10.0 | 13.2 | -2.16 | -2.63 | 19 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0178 | 2026-10-06 | backtest | `EmaTrendV1T` | sideways-is | 1h | 0.10% | -4.8 | 8.5 | -1.51 | -2.14 | 53 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0177 | 2026-10-06 | backtest | `EmaTrendV1` | sideways-is | 1h | 0.10% | -6.4 | 8.7 | -1.76 | -2.70 | 60 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0176 | 2026-10-06 | backtest | `DonchianBreakoutV2T` | sideways-is | 1h | 0.10% | -1.7 | 4.9 | -0.65 | -1.40 | 10 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0175 | 2026-10-06 | backtest | `DonchianBreakoutV2` | sideways-is | 1h | 0.10% | +0.0 | 2.8 | 0.06 | 0.05 | 11 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0174 | 2026-10-06 | backtest | `DonchianBreakoutV1T` | sideways-is | 1h | 0.10% | -4.4 | 7.9 | -1.16 | -2.12 | 67 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0173 | 2026-10-06 | backtest | `DonchianBreakoutV1` | sideways-is | 1h | 0.10% | -15.3 | 18.6 | -2.90 | -2.62 | 147 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0172 | 2026-10-06 | backtest | `AdxSupertrendV1T` | sideways-is | 1h | 0.10% | -3.4 | 5.8 | -1.18 | -2.25 | 25 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0171 | 2026-10-06 | backtest | `AdxSupertrendV1` | sideways-is | 1h | 0.10% | -5.9 | 6.7 | -2.25 | -3.24 | 35 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0170 | 2026-10-06 | backtest | `BuyHoldV1` | sideways-is | 1h | 0.10% | -7.1 | 21.3 | -0.48 | -1.21 | 5 | baseline | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0169 | 2026-10-06 | backtest | `TrendPullbackV2T` | bear-is | 1h | 0.10% | -0.0 | 0.8 | -0.01 | -0.02 | 8 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0168 | 2026-10-06 | backtest | `TrendPullbackV2` | bear-is | 1h | 0.10% | -3.2 | 3.4 | -2.47 | -3.62 | 21 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0167 | 2026-10-06 | backtest | `TrendPullbackV1T` | bear-is | 1h | 0.10% | -3.1 | 3.8 | -1.74 | -3.09 | 63 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0166 | 2026-10-06 | backtest | `TrendPullbackV1` | bear-is | 1h | 0.10% | -12.0 | 13.4 | -4.13 | -3.02 | 157 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0165 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | bear-is | 1h | 0.10% | -1.4 | 2.0 | -2.64 | -2.76 | 5 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0164 | 2026-10-06 | backtest | `SqueezeBreakoutV1` | bear-is | 1h | 0.10% | -6.6 | 7.4 | -3.53 | -3.25 | 31 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0163 | 2026-10-06 | backtest | `RsiBbReversionV1T` | bear-is | 1h | 0.10% | -14.7 | 15.6 | -3.39 | -3.05 | 36 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0162 | 2026-10-06 | backtest | `RsiBbReversionV1` | bear-is | 1h | 0.10% | -29.3 | 34.0 | -4.66 | -2.22 | 118 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0161 | 2026-10-06 | backtest | `MacdVolumeV2T` | bear-is | 1h | 0.10% | +0.0 | 0.0 | 0.00 | 0.00 | 0 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0160 | 2026-10-06 | backtest | `MacdVolumeV2` | bear-is | 1h | 0.10% | +1.0 | 0.5 | 2.02 | 8.40 | 3 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0159 | 2026-10-06 | backtest | `MacdVolumeV1T` | bear-is | 1h | 0.10% | +4.5 | 3.2 | 1.16 | 6.10 | 25 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0158 | 2026-10-06 | backtest | `MacdVolumeV1` | bear-is | 1h | 0.10% | +0.6 | 4.3 | 0.23 | 0.60 | 48 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0157 | 2026-10-06 | backtest | `EmaTrendV2T` | bear-is | 1h | 0.10% | -2.2 | 5.3 | -1.59 | -1.63 | 8 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0156 | 2026-10-06 | backtest | `EmaTrendV2` | bear-is | 1h | 0.10% | -7.9 | 8.6 | -4.31 | -3.31 | 8 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0155 | 2026-10-06 | backtest | `EmaTrendV1T` | bear-is | 1h | 0.10% | -8.0 | 16.8 | -1.51 | -1.70 | 53 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0154 | 2026-10-06 | backtest | `EmaTrendV1` | bear-is | 1h | 0.10% | -8.8 | 12.0 | -2.04 | -2.61 | 60 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0153 | 2026-10-06 | backtest | `DonchianBreakoutV2T` | bear-is | 1h | 0.10% | +0.4 | 2.0 | 0.46 | 0.78 | 4 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0152 | 2026-10-06 | backtest | `DonchianBreakoutV2` | bear-is | 1h | 0.10% | +0.9 | 1.5 | 0.96 | 2.33 | 4 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0151 | 2026-10-06 | backtest | `DonchianBreakoutV1T` | bear-is | 1h | 0.10% | -15.2 | 17.8 | -2.32 | -2.75 | 74 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0150 | 2026-10-06 | backtest | `DonchianBreakoutV1` | bear-is | 1h | 0.10% | -25.3 | 28.4 | -3.79 | -2.44 | 155 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0149 | 2026-10-06 | backtest | `AdxSupertrendV1T` | bear-is | 1h | 0.10% | -1.5 | 4.9 | -0.50 | -1.19 | 13 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0148 | 2026-10-06 | backtest | `AdxSupertrendV1` | bear-is | 1h | 0.10% | -5.1 | 9.5 | -1.73 | -2.03 | 29 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0147 | 2026-10-06 | backtest | `BuyHoldV1` | bear-is | 1h | 0.10% | -27.8 | 43.6 | -1.36 | -1.68 | 5 | baseline | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0146 | 2026-10-06 | backtest | `TrendPullbackV2T` | bull-is | 1h | 0.10% | +3.9 | 3.1 | 2.62 | 5.38 | 33 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0145 | 2026-10-06 | backtest | `TrendPullbackV2` | bull-is | 1h | 0.10% | +3.6 | 6.7 | 1.13 | 2.30 | 104 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0144 | 2026-10-06 | backtest | `TrendPullbackV1T` | bull-is | 1h | 0.10% | +1.5 | 5.3 | 0.62 | 1.15 | 90 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0143 | 2026-10-06 | backtest | `TrendPullbackV1` | bull-is | 1h | 0.10% | +3.0 | 8.9 | 0.93 | 1.44 | 256 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0142 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | bull-is | 1h | 0.10% | +1.0 | 1.2 | 1.54 | 3.45 | 3 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0141 | 2026-10-06 | backtest | `SqueezeBreakoutV1` | bull-is | 1h | 0.10% | +3.8 | 3.5 | 1.64 | 4.67 | 42 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0140 | 2026-10-06 | backtest | `RsiBbReversionV1T` | bull-is | 1h | 0.10% | +2.8 | 6.2 | 1.29 | 1.90 | 29 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0139 | 2026-10-06 | backtest | `RsiBbReversionV1` | bull-is | 1h | 0.10% | +3.5 | 11.4 | 1.16 | 1.31 | 77 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0138 | 2026-10-06 | backtest | `MacdVolumeV2T` | bull-is | 1h | 0.10% | -0.1 | 1.6 | -0.09 | -0.22 | 11 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0137 | 2026-10-06 | backtest | `MacdVolumeV2` | bull-is | 1h | 0.10% | -4.1 | 6.7 | -2.05 | -2.36 | 41 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0136 | 2026-10-06 | backtest | `MacdVolumeV1T` | bull-is | 1h | 0.10% | +4.5 | 3.8 | 1.47 | 5.12 | 55 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0135 | 2026-10-06 | backtest | `MacdVolumeV1` | bull-is | 1h | 0.10% | +9.7 | 4.6 | 2.40 | 9.95 | 99 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0134 | 2026-10-06 | backtest | `EmaTrendV2T` | bull-is | 1h | 0.10% | +7.3 | 6.5 | 1.80 | 5.13 | 18 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0133 | 2026-10-06 | backtest | `EmaTrendV2` | bull-is | 1h | 0.10% | +2.1 | 8.1 | 0.54 | 1.09 | 22 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0132 | 2026-10-06 | backtest | `EmaTrendV1T` | bull-is | 1h | 0.10% | -0.5 | 8.3 | -0.04 | -0.23 | 75 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0131 | 2026-10-06 | backtest | `EmaTrendV1` | bull-is | 1h | 0.10% | -8.8 | 12.6 | -2.08 | -2.49 | 91 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0130 | 2026-10-06 | backtest | `DonchianBreakoutV2T` | bull-is | 1h | 0.10% | +6.7 | 10.1 | 1.27 | 2.98 | 42 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0129 | 2026-10-06 | backtest | `DonchianBreakoutV2` | bull-is | 1h | 0.10% | +4.8 | 10.9 | 0.95 | 1.94 | 42 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0128 | 2026-10-06 | backtest | `DonchianBreakoutV1T` | bull-is | 1h | 0.10% | +27.0 | 7.0 | 4.33 | 23.36 | 103 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0127 | 2026-10-06 | backtest | `DonchianBreakoutV1` | bull-is | 1h | 0.10% | +7.7 | 9.9 | 1.16 | 3.53 | 194 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0126 | 2026-10-06 | backtest | `AdxSupertrendV1T` | bull-is | 1h | 0.10% | -1.2 | 3.5 | -0.65 | -1.40 | 12 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0125 | 2026-10-06 | backtest | `AdxSupertrendV1` | bull-is | 1h | 0.10% | -5.7 | 7.1 | -1.92 | -2.99 | 30 | pending | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0124 | 2026-10-06 | backtest | `BuyHoldV1` | bull-is | 1h | 0.10% | +134.4 | 22.5 | 5.49 | 135.83 | 5 | baseline | regime check (in-sample window), all versions | `fa623ac+dirty` |
| E0123 | 2026-10-06 | backtest | `TrendPullbackV2T` | is | 1h | 0.10% | +10.2 | 3.7 | 1.31 | 1.35 | 240 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0122 | 2026-10-06 | backtest | `TrendPullbackV2` | is | 1h | 0.10% | +3.9 | 9.2 | 0.27 | 0.21 | 675 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0121 | 2026-10-06 | backtest | `TrendPullbackV1T` | is | 1h | 0.10% | -4.1 | 12.0 | -0.29 | -0.17 | 715 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0120 | 2026-10-06 | backtest | `TrendPullbackV1` | is | 1h | 0.10% | -22.7 | 32.2 | -1.02 | -0.38 | 1941 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0119 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | is | 1h | 0.10% | +2.6 | 3.5 | 0.41 | 0.36 | 66 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0118 | 2026-10-06 | backtest | `SqueezeBreakoutV1` | is | 1h | 0.10% | -13.9 | 23.2 | -0.87 | -0.31 | 403 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0117 | 2026-10-06 | backtest | `RsiBbReversionV1T` | is | 1h | 0.10% | -0.1 | 18.2 | 0.05 | -0.00 | 254 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0116 | 2026-10-06 | backtest | `RsiBbReversionV1` | is | 1h | 0.10% | -41.9 | 53.6 | -1.28 | -0.44 | 699 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0115 | 2026-10-06 | backtest | `MacdVolumeV2T` | is | 1h | 0.10% | +7.2 | 3.4 | 1.16 | 1.05 | 81 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0114 | 2026-10-06 | backtest | `MacdVolumeV2` | is | 1h | 0.10% | -1.5 | 12.6 | -0.10 | -0.06 | 261 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0113 | 2026-10-06 | backtest | `MacdVolumeV1T` | is | 1h | 0.10% | +25.5 | 5.7 | 1.21 | 2.12 | 372 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0112 | 2026-10-06 | backtest | `MacdVolumeV1` | is | 1h | 0.10% | +18.1 | 7.6 | 0.72 | 1.15 | 695 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0111 | 2026-10-06 | backtest | `EmaTrendV2T` | is | 1h | 0.10% | +72.1 | 9.6 | 1.99 | 3.26 | 115 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0110 | 2026-10-06 | backtest | `EmaTrendV2` | is | 1h | 0.10% | +21.5 | 20.5 | 0.65 | 0.50 | 126 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0109 | 2026-10-06 | backtest | `EmaTrendV1T` | is | 1h | 0.10% | +15.8 | 25.5 | 0.51 | 0.30 | 539 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0108 | 2026-10-06 | backtest | `EmaTrendV1` | is | 1h | 0.10% | -4.2 | 26.1 | -0.03 | -0.08 | 675 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0107 | 2026-10-06 | backtest | `DonchianBreakoutV2T` | is | 1h | 0.10% | +70.4 | 13.7 | 1.45 | 2.23 | 188 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0106 | 2026-10-06 | backtest | `DonchianBreakoutV2` | is | 1h | 0.10% | +52.2 | 23.1 | 1.19 | 1.01 | 197 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0105 | 2026-10-06 | backtest | `DonchianBreakoutV1T` | is | 1h | 0.10% | +19.0 | 25.6 | 0.49 | 0.35 | 683 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0104 | 2026-10-06 | backtest | `DonchianBreakoutV1` | is | 1h | 0.10% | -27.3 | 49.6 | -0.51 | -0.30 | 1329 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0103 | 2026-10-06 | backtest | `AdxSupertrendV1T` | is | 1h | 0.10% | +14.4 | 6.5 | 0.76 | 1.06 | 118 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0102 | 2026-10-06 | backtest | `AdxSupertrendV1` | is | 1h | 0.10% | -13.9 | 20.4 | -0.69 | -0.35 | 240 | pending | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0101 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | all versions: v1, v1T, v2, v2T | `fa623ac+dirty` |
| E0100 | 2026-10-06 | backtest | `MacdVolumeV2T` | is | 1h | 0.10% | +7.2 | 3.4 | 1.16 | 1.05 | 81 | pending | hyperopt check: MacdVolumeV2 vs tuned MacdVolumeV2T | `fa623ac+dirty` |
| E0099 | 2026-10-06 | backtest | `MacdVolumeV2` | is | 1h | 0.10% | -5.8 | 14.1 | -0.40 | -0.21 | 257 | pending | hyperopt check: MacdVolumeV2 vs tuned MacdVolumeV2T | `fa623ac+dirty` |
| E0098 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hyperopt check: MacdVolumeV2 vs tuned MacdVolumeV2T | `fa623ac+dirty` |
| E0097 | 2026-10-06 | hyperopt | `MacdVolumeV2` | is | 1h | 0.10% | +7.2 | 3.0 | 0.36 | 6.35 | 81 | drop: MacdVolumeV2T: only 18 OOS trades and -2.0% (stage 1 FAIL) | CalmarHyperOptLoss, 300 epochs, seed 42, best epoch 114 (closed-trade metrics) -> MacdVolumeV2T | `fa623ac+dirty` |
| E0096 | 2026-10-06 | backtest | `DonchianBreakoutV2T` | is | 1h | 0.10% | +70.4 | 13.7 | 1.45 | 2.23 | 188 | pending | hyperopt check: DonchianBreakoutV2 vs tuned DonchianBreakoutV2T | `fa623ac+dirty` |
| E0095 | 2026-10-06 | backtest | `DonchianBreakoutV2` | is | 1h | 0.10% | +52.2 | 23.1 | 1.19 | 1.01 | 197 | pending | hyperopt check: DonchianBreakoutV2 vs tuned DonchianBreakoutV2T | `fa623ac+dirty` |
| E0094 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hyperopt check: DonchianBreakoutV2 vs tuned DonchianBreakoutV2T | `fa623ac+dirty` |
| E0093 | 2026-10-06 | hyperopt | `DonchianBreakoutV2` | is | 1h | 0.10% | +70.4 | 11.9 | 0.87 | 15.44 | 188 | drop: DonchianBreakoutV2T: IS +70% but OOS -8.2% (stage 1 FAIL) | CalmarHyperOptLoss, 300 epochs, seed 42, best epoch 259 (closed-trade metrics) -> DonchianBreakoutV2T | `fa623ac+dirty` |
| E0092 | 2026-10-06 | backtest | `EmaTrendV2T` | is | 1h | 0.10% | +72.1 | 9.6 | 1.99 | 3.26 | 115 | pending | hyperopt check: EmaTrendV2 vs tuned EmaTrendV2T | `fa623ac+dirty` |
| E0091 | 2026-10-06 | backtest | `EmaTrendV2` | is | 1h | 0.10% | +21.5 | 20.5 | 0.65 | 0.50 | 126 | pending | hyperopt check: EmaTrendV2 vs tuned EmaTrendV2T | `fa623ac+dirty` |
| E0090 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hyperopt check: EmaTrendV2 vs tuned EmaTrendV2T | `fa623ac+dirty` |
| E0089 | 2026-10-06 | hyperopt | `EmaTrendV2` | is | 1h | 0.10% | +72.1 | 8.8 | 0.86 | 21.37 | 115 | drop: EmaTrendV2T: IS +72% but OOS -1.0% (stage 1 FAIL) - tuned -3% stop at range edge overfitted | CalmarHyperOptLoss, 300 epochs, seed 42, best epoch 286 (closed-trade metrics) -> EmaTrendV2T | `fa623ac+dirty` |
| E0088 | 2026-10-06 | backtest | `TrendPullbackV2T` | is | 1h | 0.10% | +10.2 | 3.7 | 1.31 | 1.35 | 240 | pending | hyperopt check: TrendPullbackV2 vs tuned TrendPullbackV2T | `fa623ac+dirty` |
| E0087 | 2026-10-06 | backtest | `TrendPullbackV2` | is | 1h | 0.10% | +3.9 | 9.2 | 0.27 | 0.21 | 675 | pending | hyperopt check: TrendPullbackV2 vs tuned TrendPullbackV2T | `fa623ac+dirty` |
| E0086 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hyperopt check: TrendPullbackV2 vs tuned TrendPullbackV2T | `fa623ac+dirty` |
| E0085 | 2026-10-06 | hyperopt | `TrendPullbackV2` | is | 1h | 0.10% | +10.2 | 3.2 | 0.82 | 8.27 | 240 | drop: TrendPullbackV2T: IS +10.2% but OOS -1.8% (stage 1 FAIL) | CalmarHyperOptLoss, 300 epochs, seed 42, best epoch 278 (closed-trade metrics) -> TrendPullbackV2T | `fa623ac+dirty` |
| E0084 | 2026-10-06 | backtest | `RsiBbReversionV1T` | is | 1h | 0.10% | -0.0 | 18.2 | 0.05 | -0.00 | 254 | pending | hyperopt check: RsiBbReversionV1 vs tuned RsiBbReversionV1T | `fa623ac+dirty` |
| E0083 | 2026-10-06 | backtest | `RsiBbReversionV1` | is | 1h | 0.10% | -41.8 | 53.6 | -1.28 | -0.44 | 699 | pending | hyperopt check: RsiBbReversionV1 vs tuned RsiBbReversionV1T | `fa623ac+dirty` |
| E0082 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hyperopt check: RsiBbReversionV1 vs tuned RsiBbReversionV1T | `fa623ac+dirty` |
| E0081 | 2026-10-06 | hyperopt | `RsiBbReversionV1` | is | 1h | 0.10% | -0.0 | 17.3 | -0.00 | -0.00 | 254 | drop: RsiBbReversionV1T breaks even in-sample (-0.1%); idea does not work here | CalmarHyperOptLoss, 300 epochs, seed 42, best epoch 242 (closed-trade metrics) -> RsiBbReversionV1T | `fa623ac+dirty` |
| E0080 | 2026-10-06 | backtest | `AdxSupertrendV1T` | is | 1h | 0.10% | +14.4 | 6.5 | 0.76 | 1.06 | 118 | pending | hyperopt check: AdxSupertrendV1 vs tuned AdxSupertrendV1T | `fa623ac+dirty` |
| E0079 | 2026-10-06 | backtest | `AdxSupertrendV1` | is | 1h | 0.10% | -13.9 | 20.4 | -0.69 | -0.35 | 240 | pending | hyperopt check: AdxSupertrendV1 vs tuned AdxSupertrendV1T | `fa623ac+dirty` |
| E0078 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hyperopt check: AdxSupertrendV1 vs tuned AdxSupertrendV1T | `fa623ac+dirty` |
| E0077 | 2026-10-06 | hyperopt | `AdxSupertrendV1` | is | 1h | 0.10% | +14.4 | 5.1 | 0.34 | 7.41 | 118 | drop: AdxSupertrendV1T: OOS PF 1.09 and only 28% of IS Sharpe kept (stage 1 FAIL) | CalmarHyperOptLoss, 300 epochs, seed 42, best epoch 292 (closed-trade metrics) -> AdxSupertrendV1T | `fa623ac+dirty` |
| E0076 | 2026-10-06 | backtest | `SqueezeBreakoutV1T` | is | 1h | 0.10% | +2.6 | 3.5 | 0.41 | 0.36 | 66 | pending | hyperopt check: SqueezeBreakoutV1 vs tuned SqueezeBreakoutV1T | `fa623ac+dirty` |
| E0075 | 2026-10-06 | backtest | `SqueezeBreakoutV1` | is | 1h | 0.10% | -13.9 | 23.2 | -0.87 | -0.31 | 403 | pending | hyperopt check: SqueezeBreakoutV1 vs tuned SqueezeBreakoutV1T | `fa623ac+dirty` |
| E0074 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hyperopt check: SqueezeBreakoutV1 vs tuned SqueezeBreakoutV1T | `fa623ac+dirty` |
| E0073 | 2026-10-06 | hyperopt | `SqueezeBreakoutV1` | is | 1h | 0.10% | +2.6 | 3.2 | 0.13 | 2.10 | 66 | drop: SqueezeBreakoutV1T: passed stage 1 (REVIEW, ~1% exposure) but failed stage 2 (38% windows, efficiency n/a) | CalmarHyperOptLoss, 300 epochs, seed 42, best epoch 118 (closed-trade metrics) -> SqueezeBreakoutV1T | `fa623ac+dirty` |
| E0072 | 2026-10-06 | backtest | `DonchianBreakoutV1T` | is | 1h | 0.10% | +19.0 | 25.6 | 0.49 | 0.35 | 683 | pending | hyperopt check: DonchianBreakoutV1 vs tuned DonchianBreakoutV1T | `fa623ac+dirty` |
| E0071 | 2026-10-06 | backtest | `DonchianBreakoutV1` | is | 1h | 0.10% | -27.3 | 49.6 | -0.51 | -0.30 | 1329 | pending | hyperopt check: DonchianBreakoutV1 vs tuned DonchianBreakoutV1T | `fa623ac+dirty` |
| E0070 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hyperopt check: DonchianBreakoutV1 vs tuned DonchianBreakoutV1T | `fa623ac+dirty` |
| E0069 | 2026-10-06 | hyperopt | `DonchianBreakoutV1` | is | 1h | 0.10% | +19.0 | 25.0 | 0.54 | 1.98 | 683 | drop: DonchianBreakoutV1T IS +19.0% but PF 1.08 < 1.1; not a candidate | CalmarHyperOptLoss, 300 epochs, seed 42, best epoch 242 (closed-trade metrics) -> DonchianBreakoutV1T | `fa623ac+dirty` |
| E0068 | 2026-10-06 | backtest | `EmaTrendV1T` | is | 1h | 0.10% | +15.8 | 25.5 | 0.51 | 0.30 | 539 | pending | hyperopt check: EmaTrendV1 vs tuned EmaTrendV1T | `fa623ac+dirty` |
| E0067 | 2026-10-06 | backtest | `EmaTrendV1` | is | 1h | 0.10% | -4.2 | 26.1 | -0.03 | -0.08 | 675 | pending | hyperopt check: EmaTrendV1 vs tuned EmaTrendV1T | `fa623ac+dirty` |
| E0066 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hyperopt check: EmaTrendV1 vs tuned EmaTrendV1T | `fa623ac+dirty` |
| E0065 | 2026-10-06 | hyperopt | `EmaTrendV1` | is | 1h | 0.10% | +15.8 | 20.8 | 0.45 | 1.99 | 539 | drop: EmaTrendV1T IS +15.8% but PF 1.09 < 1.1; not a candidate | CalmarHyperOptLoss, 300 epochs, seed 42, best epoch 207 (closed-trade metrics) -> EmaTrendV1T | `fa623ac+dirty` |
| E0064 | 2026-10-06 | backtest | `TrendPullbackV1T` | is | 1h | 0.10% | -4.1 | 12.0 | -0.29 | -0.17 | 715 | pending | hyperopt check: TrendPullbackV1 vs tuned TrendPullbackV1T | `fa623ac+dirty` |
| E0063 | 2026-10-06 | backtest | `TrendPullbackV1` | is | 1h | 0.10% | -22.7 | 32.2 | -1.02 | -0.38 | 1941 | pending | hyperopt check: TrendPullbackV1 vs tuned TrendPullbackV1T | `fa623ac+dirty` |
| E0062 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hyperopt check: TrendPullbackV1 vs tuned TrendPullbackV1T | `fa623ac+dirty` |
| E0061 | 2026-10-06 | hyperopt | `TrendPullbackV1` | is | 1h | 0.10% | -4.1 | 11.8 | -0.39 | -0.91 | 715 | drop: TrendPullbackV1T still loses in-sample (-4.1%); not a candidate | CalmarHyperOptLoss, 300 epochs, seed 42, best epoch 151 (closed-trade metrics) -> TrendPullbackV1T | `fa623ac+dirty` |
| E0060 | 2026-10-06 | backtest | `MacdVolumeV1T` | is | 1h | 0.10% | +25.5 | 5.7 | 1.21 | 2.12 | 372 | pending | hyperopt check: MacdVolumeV1 vs tuned MacdVolumeV1T | `fa623ac+dirty` |
| E0059 | 2026-10-06 | backtest | `MacdVolumeV1` | is | 1h | 0.10% | +18.1 | 7.6 | 0.72 | 1.15 | 695 | pending | hyperopt check: MacdVolumeV1 vs tuned MacdVolumeV1T | `fa623ac+dirty` |
| E0058 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hyperopt check: MacdVolumeV1 vs tuned MacdVolumeV1T | `fa623ac+dirty` |
| E0057 | 2026-10-06 | hyperopt | `MacdVolumeV1` | is | 1h | 0.10% | +25.5 | 4.5 | 1.11 | 14.82 | 372 | drop: MacdVolumeV1T: IS +25.5% but OOS -11.0% (stage 1 FAIL) - overfitted | CalmarHyperOptLoss, 300 epochs, seed 42, best epoch 134 (closed-trade metrics) -> MacdVolumeV1T | `fa623ac+dirty` |
| E0056 | 2026-10-06 | backtest | `TrendPullbackV2` | is | 1h | 0.10% | +3.9 | 9.2 | 0.27 | 0.21 | 675 | pending | hand-designed v2s (untuned) vs v1 | `fa623ac+dirty` |
| E0055 | 2026-10-06 | backtest | `TrendPullbackV1` | is | 1h | 0.10% | -22.7 | 32.2 | -1.02 | -0.38 | 1941 | pending | hand-designed v2s (untuned) vs v1 | `fa623ac+dirty` |
| E0054 | 2026-10-06 | backtest | `SqueezeBreakoutV1` | is | 1h | 0.10% | -13.9 | 23.2 | -0.87 | -0.31 | 403 | pending | hand-designed v2s (untuned) vs v1 | `fa623ac+dirty` |
| E0053 | 2026-10-06 | backtest | `RsiBbReversionV1` | is | 1h | 0.10% | -41.9 | 53.6 | -1.28 | -0.44 | 699 | pending | hand-designed v2s (untuned) vs v1 | `fa623ac+dirty` |
| E0052 | 2026-10-06 | backtest | `MacdVolumeV2` | is | 1h | 0.10% | -5.8 | 14.1 | -0.40 | -0.21 | 257 | pending | hand-designed v2s (untuned) vs v1 | `fa623ac+dirty` |
| E0051 | 2026-10-06 | backtest | `MacdVolumeV1` | is | 1h | 0.10% | +18.1 | 7.6 | 0.72 | 1.15 | 695 | pending | hand-designed v2s (untuned) vs v1 | `fa623ac+dirty` |
| E0050 | 2026-10-06 | backtest | `EmaTrendV2` | is | 1h | 0.10% | +21.5 | 20.5 | 0.65 | 0.50 | 126 | pending | hand-designed v2s (untuned) vs v1 | `fa623ac+dirty` |
| E0049 | 2026-10-06 | backtest | `EmaTrendV1` | is | 1h | 0.10% | -4.2 | 26.1 | -0.03 | -0.08 | 675 | pending | hand-designed v2s (untuned) vs v1 | `fa623ac+dirty` |
| E0048 | 2026-10-06 | backtest | `DonchianBreakoutV2` | is | 1h | 0.10% | +52.2 | 23.1 | 1.19 | 1.01 | 197 | pending | hand-designed v2s (untuned) vs v1 | `fa623ac+dirty` |
| E0047 | 2026-10-06 | backtest | `DonchianBreakoutV1` | is | 1h | 0.10% | -27.3 | 49.6 | -0.51 | -0.30 | 1329 | pending | hand-designed v2s (untuned) vs v1 | `fa623ac+dirty` |
| E0046 | 2026-10-06 | backtest | `AdxSupertrendV1` | is | 1h | 0.10% | -13.9 | 20.4 | -0.69 | -0.35 | 240 | pending | hand-designed v2s (untuned) vs v1 | `fa623ac+dirty` |
| E0045 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hand-designed v2s (untuned) vs v1 | `fa623ac+dirty` |
| E0044 | 2026-10-06 | backtest | `MacdVolumeV1T` | is | 1h | 0.10% | +25.5 | 5.7 | 1.21 | 2.12 | 372 | pending | hyperopt check: MacdVolumeV1 vs tuned MacdVolumeV1T | `fa623ac+dirty` |
| E0043 | 2026-10-06 | backtest | `MacdVolumeV1` | is | 1h | 0.10% | +18.1 | 7.6 | 0.72 | 1.15 | 695 | pending | hyperopt check: MacdVolumeV1 vs tuned MacdVolumeV1T | `fa623ac+dirty` |
| E0042 | 2026-10-06 | backtest | `BuyHoldV1` | is | 1h | 0.10% | +428.9 | 51.3 | 1.63 | 2.53 | 5 | baseline | hyperopt check: MacdVolumeV1 vs tuned MacdVolumeV1T | `fa623ac+dirty` |
| E0041 | 2026-10-06 | hyperopt | `MacdVolumeV1` | is | 1h | 0.10% | +25.5 | 4.5 | 1.11 | 14.82 | 372 | drop: superseded by E0057: run with 11 workers (out-of-memory risk, not reproducible) | CalmarHyperOptLoss, 300 epochs, seed 42, best epoch 114 (closed-trade metrics) -> MacdVolumeV1T | `fa623ac+dirty` |
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
