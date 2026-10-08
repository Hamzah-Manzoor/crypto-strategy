# Round 4 · dev selection (pre-registered rule)

Dev run `20261008-123310_dev_1h` (20231001-20261001, 1h, fee 0.10%). Rule: max drawdown <= 30%, profit > 0, profit factor >= 1.2, >= 30 trades, bias checks passed, robustness check ROBUST; best dev Calmar wins.

Robustness reports: `20261008-123421_MomentumRotationV3` (ROBUST)

- `MomentumRotationV3`: eligible - dev profit +95.6%, max DD 29.7%, Calmar 0.84, PF 2.17, 65 trades
- `MomentumRotationV3b`: not eligible (max drawdown 42.2% > 30%; robustness check not run (need ROBUST)) - dev profit +183.3%, max DD 42.2%, Calmar 0.98, PF 2.21, 65 trades

**Exam pick:** `MomentumRotationV3`
