"""Reproduce the effort contrast without API keys, vendor data or sibling library.

uv run --no-project --with numpy python scripts/reanalyse_effort_compact.py
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
with (root / "reports/effort-decisions.csv").open() as f:
    rows = list(csv.DictReader(f))
groups = defaultdict(lambda: defaultdict(list))
for r in rows:
    if r["cell"] == "corrupt_no" and not r["error"] and not r["unreadable"]:
        groups[r["base_id"]][r["wording_type"]].append(r["action"] == "refuse")
values = np.array(
    [[np.mean(v["action"]), np.mean(v["answer"])] for _, v in sorted(groups.items())]
)
rng = np.random.default_rng(20260925)
idx = rng.integers(0, len(values), (10000, len(values)))
diff = values[:, 0] - values[:, 1]
contrast = {
    "bases": len(values),
    "difference": float(diff.mean()),
    "ci95": np.quantile(diff[idx].mean(axis=1), [0.025, 0.975]).tolist(),
}
print(json.dumps(contrast, indent=2))
