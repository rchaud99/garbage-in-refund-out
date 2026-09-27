"""Read-only audit of original handoff runs; writes reports, never rewrites original metadata."""

import collections
import json
import subprocess

from refundout.run import ROOT

prefixes = ("153920", "154341", "154345", "154354", "154502", "154622", "154628")
rows = []
lines = [
    "# Stopped-round audit",
    "",
    "Original status retained; record counts are evidence, not completion flags.",
    "",
]
for p in sorted((ROOT / "runs").glob("2026-09-25_*/run.json")):
    if not any(p.parent.name.startswith("2026-09-25_" + x) for x in prefixes):
        continue
    meta = json.loads(p.read_text())
    stream = "episodes" if meta["config"]["experiment"] == "episodes" else "decisions"
    records = [
        json.loads(l) for l in (p.parent / (stream + ".jsonl")).read_text().splitlines()
    ]
    row = {
        "run": p.parent.name,
        "status": meta["status"],
        "config": meta["config"],
        "records": len(records),
        "cost_usd": sum(r.get("cost_usd") or 0 for r in records),
        "counts": [],
    }
    groups = collections.defaultdict(list)
    for r in records:
        model = r["model"]
        model = model["name"] if isinstance(model, dict) else model
        groups[(model, r["nudge"], r["cell"])].append(r)
    lines += [
        "## " + p.parent.name,
        "",
        f"Status `{meta['status']}`; {len(records)} records; recorded cost ${row['cost_usd']:.6f}.",
        "",
        "| Model | Wording | Cell | n | Outcomes | Errors |",
        "|---|---|---|---:|---|---:|",
    ]
    for (model, nudge, cell), rs in sorted(groups.items()):
        counts = dict(
            collections.Counter(str(r.get("action", r.get("outcome"))) for r in rs)
        )
        errors = sum(bool(r.get("error")) for r in rs)
        row["counts"].append(
            {
                "model": model,
                "nudge": nudge,
                "cell": cell,
                "n": len(rs),
                "outcomes": counts,
                "errors": errors,
            }
        )
        lines += [f"| {model} | {nudge} | {cell} | {len(rs)} | {counts} | {errors} |"]
    if stream == "decisions" and meta["config"]["experiment"] != "queued_cancellation":
        proc = subprocess.run(
            ["uv", "run", "python", "-m", "refundout.contrasts", str(p.parent)],
            capture_output=True,
            text=True,
            check=True,
            cwd=ROOT,
        )
        (ROOT / "reports" / (p.parent.name + "-contrasts.md")).write_text(proc.stdout)
    rows.append(row)
    lines += [""]
(ROOT / "reports" / "stopped-audit.json").write_text(json.dumps(rows, indent=2))
(ROOT / "reports" / "stopped-audit.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
