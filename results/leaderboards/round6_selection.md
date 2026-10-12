# Round 6 · dev selection (pre-registered rule)

Dev run `20261012-174213_dev_1h` (20231001-20261001, 1h, fee 0.10%). Rule: max drawdown <= 30%, profit > 0, profit factor >= 1.2, >= 30 trades, Calmar above buy & hold's, bias checks passed, robustness check ROBUST; best dev Calmar wins.

Versions built (2 of max 3): `AuctionValueV1`, `AuctionValueV2`. Versions not in this run were dropped earlier (see docs/research/auction-value-preregistration.md).

Robustness reports: `20261012-174407_AuctionValueV2` (ROBUST)

- `AuctionValueV1`: not eligible (max drawdown 32.6% > 30%; profit factor 1.14 < 1.2; robustness check not run (need ROBUST); Calmar 0.29 not above buy & hold's 0.76) - dev profit +30.6%, max DD 32.6%, Calmar 0.29, PF 1.14, 437 trades
- `AuctionValueV2`: eligible - dev profit +67.5%, max DD 22.0%, Calmar 0.85, PF 1.47, 257 trades

**Exam pick:** `AuctionValueV2`
