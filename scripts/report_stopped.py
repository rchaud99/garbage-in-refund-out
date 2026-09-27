"""Pool original decisions with missing-only continuations; retain every source path."""

import collections
import json

from refundout.contrasts import airline, cancel, paired_rates
from refundout.resume_stopped import PREFIXES
from refundout.run import ROOT

runs = ROOT / "runs"
reports = ROOT / "reports"


def read(path):
    return list(map(json.loads, (path / "decisions.jsonl").read_text().splitlines()))


all_records = {}
sources = {}
for prefix in PREFIXES:
    old = next(runs.glob("2026-09-25_" + prefix + "*"))
    paths = [old]
    for p in sorted(runs.glob("*/run.json")):
        if json.loads(p.read_text())["config"].get("resumes") == old.name:
            paths.append(p.parent)
    rs = []
    seen = set()
    for path in paths:
        for r in read(path):
            key = (r["model"]["name"], r["id"])
            if r["error"] or key in seen:
                continue
            seen.add(key)
            rs.append(r)
    all_records[prefix] = rs
    sources[prefix] = [str(p.relative_to(ROOT)) for p in paths]
first = next(runs.glob("2026-09-25_151001*"))
pooled = read(first) + all_records["153920"]
(reports / "wording-pooled-contrasts.md").write_text(airline(pooled) + "\n")
(reports / "cancel-completed-contrasts.md").write_text(
    cancel(all_records["154345"]) + "\n"
)
rows = []
for experiment, rs in [("wording_pooled", pooled)] + list(all_records.items()):
    groups = collections.defaultdict(list)
    for r in rs:
        groups[(r["model"]["name"], r["nudge"], r["cell"])].append(r)
    for (model, nudge, cell), group in sorted(groups.items()):
        rows.append(
            {
                "experiment": experiment,
                "model": model,
                "nudge": nudge,
                "cell": cell,
                "n": len(group),
                "actions": dict(collections.Counter(r["action"] for r in group)),
            }
        )
(reports / "stopped-completed.json").write_text(
    json.dumps({"sources": sources, "rows": rows}, indent=2)
)
lines = [
    "# Completed stopped-round results",
    "",
    "Only missing Gemini calls were added; no historical answer was replaced.",
    "",
    "| Experiment | Model | Wording | Cell | n | Action counts |",
    "|---|---|---|---|---:|---|",
]
for r in rows:
    lines.append(
        "| "
        + " | ".join(
            str(r[k]) for k in ["experiment", "model", "nudge", "cell", "n", "actions"]
        )
        + " |"
    )
# Frame comparison paired across identical bases.
a = {
    r["base"]["reservation_id"]: r["action"] == "block_cancellation"
    for r in all_records["154622"]
    if r["cell"] == "D"
}
b = {
    r["base"]["reservation_id"]: r["action"] == "refuse"
    for r in all_records["154628"]
    if r["cell"] == "D"
}
contrast = paired_rates(b, a)
lines += [
    "",
    "Queued minus ordinary framing (D customer-harm rate), paired: "
    + json.dumps(contrast),
]
(reports / "stopped-completed.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
