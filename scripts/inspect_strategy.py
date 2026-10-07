#!/usr/bin/env python3
"""Print what the robustness check needs to know about a strategy, as JSON.
Runs inside the Freqtrade container (imports the strategy):
    python scripts/inspect_strategy.py <StrategyClass>
"""

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "user_data" / "strategies"))
sys.path.insert(0, str(ROOT / "scripts"))

from freqtrade.strategy.parameters import BaseParameter  # noqa: E402
from labkit.robustness_grids import REGISTRY  # noqa: E402
import tuning  # noqa: E402


def main(name: str) -> None:
    module_file = tuning.find_strategy_file(name, ROOT / "user_data" / "strategies")
    cls = getattr(importlib.import_module(module_file.stem), name)
    entry = REGISTRY.get(name, {})
    grid = getattr(cls, "ROBUSTNESS_GRID", None) or entry.get("grid", {})
    settings = {}
    for key, values in grid.items():
        attr = getattr(cls, key)
        if isinstance(attr, BaseParameter):
            settings[key] = {"kind": "param", "space": attr.space or "buy", "default": attr.value, "values": values}
        else:
            settings[key] = {"kind": "const", "default": attr, "values": values}
    weekly = hasattr(cls, "REBALANCE_WEEKDAY") and hasattr(cls, "REBALANCE_HOUR")
    print(json.dumps({
        "strategy": name,
        "module": module_file.stem,
        "weekly": weekly,
        "rebalance": [cls.REBALANCE_WEEKDAY, cls.REBALANCE_HOUR] if weekly else None,
        "universe": list(getattr(cls, "UNIVERSE", []) or []) or None,
        "settings": settings,
        "skip": list(getattr(cls, "ROBUSTNESS_SKIP", None) or entry.get("skip", [])),
    }))


if __name__ == "__main__":
    main(sys.argv[1])
