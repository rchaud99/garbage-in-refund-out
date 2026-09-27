"""Reproduce the primary fit from versioned decisions without API keys, vendor data or lookworth.

uv run --no-project --with numpy --with scipy python scripts/reanalyse_compact.py
"""

import csv
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mixed", root / "src/refundout/mixed.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with (root / "reports/power-decisions.csv").open() as f:
    rows = [
        r
        for r in csv.DictReader(f)
        if r["cell"] == "corrupt_no" and not r["error"] and not r["unreadable"]
    ]
x = np.c_[np.ones(len(rows)), [r["wording_type"] == "action" for r in rows]]
model = module.LaplaceLogistic(
    [r["action"] == "refuse" for r in rows],
    x,
    [
        [r["task"] + ":" + r["base_id"] for r in rows],
        [r["wording"] for r in rows],
        [r["task"] for r in rows],
    ],
)
counts = defaultdict(lambda: [0, 0])
for r in rows:
    value = counts[r["task"] + "/" + r["wording_type"]]
    value[0] += r["action"] == "refuse"
    value[1] += 1
print(json.dumps({"counts": dict(counts), "primary": model.fit()}, indent=2))
