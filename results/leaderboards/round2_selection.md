# Round 2 · exam candidates (pre-registered dev rule)

Dev run `20261007-085621_dev_1h` (20231001-20261001, 1h, fee 0.10%). Rule: profit > 0, profit factor >= 1.1, >= 30 trades, bias checks passed; best 2 per idea by Calmar.

- A: fee-aware pullback: `TrendPullbackV3b` not eligible (profit factor 1.01 < 1.1)
- A: fee-aware pullback: `TrendPullbackV3` not eligible (profit -7.7% <= 0; profit factor 0.91 < 1.1)
- B: EmaTrendV2 + market filter: `EmaTrendV3` **selected** (dev Calmar 0.19, profit +14.8%, PF 1.19, 122 trades)
- B: EmaTrendV2 + market filter: `EmaTrendV3b` **selected** (dev Calmar 0.18, profit +14.2%, PF 1.18, 123 trades)
- C: momentum rotation: `MomentumRotationV1b` **selected** (dev Calmar 1.68, profit +363.1%, PF 2.70, 64 trades)
- C: momentum rotation: `MomentumRotationV1` **selected** (dev Calmar 1.51, profit +355.4%, PF 2.13, 56 trades)

**Exam candidates:** `EmaTrendV3`, `EmaTrendV3b`, `MomentumRotationV1b`, `MomentumRotationV1`
