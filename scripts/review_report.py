"""Assemble the manually annotated, presampled reasoning review after collection."""

import json
from collections import Counter, defaultdict

from refundout.run import ROOT


def main():
    sample = json.loads((ROOT / "reports/power-review-sample.json").read_text())
    annotations = json.loads(
        (ROOT / "reports/power-review-annotations.json").read_text()
    )
    if len(sample) != 120 or {r["id"] for r in sample} != set(annotations):
        raise RuntimeError(
            "Every one of the 120 presampled summaries needs a manual annotation"
        )
    groups = defaultdict(list)
    for r in sample:
        groups[(r["task"], r["type"], r["cell"])].append(annotations[r["id"]])
    lines = [
        "# Presampled reasoning review",
        "",
        "120 model-generated reasoning summaries were read and annotated by Codex. Sampling used seed 20260925, 10 per task × wording type × corrupted direction, independently of outcomes. This is not an independent human audit or proof of the model’s internal computation.",
        "",
        "Explicit = actual numeric reconciliation or actual status/tracking comparison; none = no visible check; instruction-only = repeats the rule without applying it. All source summaries and messages are retained below and in power-review-sample.json.",
        "",
        "| Task | Wording type | Cell | Explicit | Instruction only | None | n |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for (task, typ, cell), values in sorted(groups.items()):
        c = Counter(a["visible_check"] for a in values)
        lines.append(
            f"| {task} | {typ} | {cell} | {c['explicit']} | {c['instruction_only']} | {c['none']} | {len(values)} |"
        )
    awareness = [r for r in sample if annotations[r["id"]].get("test_awareness")]
    lines += [
        "",
        f"**Benchmark/test references:** {len(awareness)}/120 sampled summaries explicitly mention a benchmark, evaluation dataset or a test trap. These are generated statements, not evidence of known training-set exposure. Generic mentions of prior examples or a harness are kept separately in annotations and not included in this count.",
        "",
    ]
    for r in awareness:
        lines.append("- `" + r["id"] + "`: " + annotations[r["id"]]["test_awareness"])
    for r in sample:
        a = annotations[r["id"]]
        lines += [
            "",
            "## " + r["id"],
            "",
            f"Action: `{r['action']}`. Visible check: **{a['visible_check']}**. {a['note']}",
            "",
            "**Reasoning summary:**",
            "",
            r["thoughts"] or "(No summary returned.)",
            "",
            "**Customer message:**",
            "",
            r["message"],
        ]
    (ROOT / "reports/power-review.md").write_text("\n".join(lines) + "\n")
    (ROOT / "reports/power-review-summary.json").write_text(
        json.dumps(
            {
                "n": 120,
                "test_references": len(awareness),
                "groups": [
                    {
                        "task": t,
                        "wording_type": w,
                        "cell": c,
                        "counts": dict(Counter(a["visible_check"] for a in v)),
                        "n": len(v),
                    }
                    for (t, w, c), v in sorted(groups.items())
                ],
            },
            indent=2,
        )
    )
    print("\n".join(lines[:30]))


if __name__ == "__main__":
    main()
