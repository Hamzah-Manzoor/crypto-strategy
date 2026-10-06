# Stage 2 · walk-forward and market regimes · 1h

Walk-forward = 8 rolling 3-month test windows. An untuned strategy is scored with its fixed settings; a tuned `…T` version through its parent re-tuned on the 12 months before each window. Regime cells: profit / max drawdown.

| Status | Strategy | WF windows profitable | WF efficiency | WF stitched profit | B&H same windows | bull-is | bear-is | sideways-is | bull-oos | bear-oos | sideways-oos |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **FAIL** | `EmaTrendV2` | 38% | 0.88 | +11.2 | +41.9 | +2.1% / 8.1% | -7.9% / 8.6% | -10.0% / 13.2% | +12.6% / 5.2% | -0.1% / 2.7% | -1.0% / 5.0% |
| **FAIL** | `SqueezeBreakoutV1T` | 38% | n/a | -5.9 | +41.9 | +1.0% / 1.2% | -1.4% / 2.0% | -0.1% / 1.1% | +1.3% / 1.4% | +0.9% / 1.7% | -0.7% / 1.2% |

## Why

**EmaTrendV2 - FAIL** (walk-forward, fixed: `20261006-081742_EmaTrendV2_fixed`)
- ❌ 38% of 8 walk-forward test windows profitable (>= 60%)
- ✅ walk-forward efficiency 0.88 (>= 0.5)
- ✅ worst regime drawdown 13.2% in sideways-is (<= 30%)

**SqueezeBreakoutV1T - FAIL** (walk-forward, retuned: `20261006-081923_SqueezeBreakoutV1_retuned`)
- ❌ 38% of 8 walk-forward test windows profitable (>= 60%)
- ❌ walk-forward efficiency n/a (training was not profitable) (>= 0.5)
- ✅ worst regime drawdown 2.0% in bear-is (<= 30%)

Rules: docs/TESTING_METHODOLOGY.md (thresholds in scripts/rules.py).
