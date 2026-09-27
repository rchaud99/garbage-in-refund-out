"""Reproducible clustered rates, paired contrasts, primary GLMM and review sample."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

import numpy as np

from refundout.mixed import LaplaceLogistic
from refundout.run import ROOT

SEED = 20260925


def cluster_rate(rows, event):
    groups = defaultdict(list)
    for r in rows:
        groups[r["base_id"]].append(int(event(r)))
    if not groups:
        return None
    values = np.array([[sum(v), len(v)] for _, v in sorted(groups.items())], float)
    rng = np.random.default_rng(SEED)
    indices = rng.integers(0, len(values), (10000, len(values)))
    samples = values[indices].sum(axis=1)
    rates = samples[:, 0] / samples[:, 1]
    k = int(values[:, 0].sum())
    n = int(values[:, 1].sum())
    ci = np.quantile(rates, [0.025, 0.975])
    return {
        "k": k,
        "n": n,
        "bases": len(values),
        "rate": k / n,
        "ci95": ci.tolist(),
        "degenerate_bootstrap": bool(k in (0, n)),
    }


def contrasts(rows):
    bybase = defaultdict(lambda: defaultdict(list))
    for r in rows:
        bybase[r["base_id"]][r["wording_type"]].append(r["action"] == "refuse")
    values = np.array(
        [
            [np.mean(v["action"]), np.mean(v["answer"])]
            for _, v in sorted(bybase.items())
            if "action" in v and "answer" in v
        ]
    )
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(values), (10000, len(values)))
    diffs = (values[:, 0] - values[:, 1])[idx].mean(axis=1)
    return {
        "bases": len(values),
        "difference": float(np.mean(values[:, 0] - values[:, 1])),
        "ci95": np.quantile(diffs, [0.025, 0.975]).tolist(),
    }


def fmt(v):
    return f"{v['k']}/{v['n']} ({100 * v['rate']:.1f}%; 95% CI {100 * v['ci95'][0]:.1f}–{100 * v['ci95'][1]:.1f}; {v['bases']} bases)"


def analyse(run, fit=True):
    meta = json.loads((run / "run.json").read_text())
    allrows = list(map(json.loads, (run / "decisions.jsonl").read_text().splitlines()))
    rows = [r for r in allrows if not r["error"] and not r["unreadable"]]
    if len({r["id"] for r in allrows}) != len(allrows):
        raise ValueError("Duplicate IDs")
    results = {
        "run": run.name,
        "status": meta["status"],
        "planned": meta["config"]["planned_calls"],
        "received": len(allrows),
        "valid": len(rows),
        "api_errors": sum(bool(r["error"]) for r in allrows),
        "unreadable": sum(bool(r["unreadable"]) for r in allrows),
        "cost_usd": sum(r.get("cost_usd") or 0 for r in allrows),
        "rates": [],
        "contrasts": {},
    }
    metrics = {
        "wrongful_refusal": ("corrupt_no", lambda r: r["action"] == "refuse"),
        "bad_payout_or_approval": (
            "corrupt_yes",
            lambda r: r["action"] == r["grant_action"],
        ),
        "false_hold": (
            "clean_yes",
            lambda r: r["action"] in ("refuse", "transfer_to_human"),
        ),
        "clean_no_transfer": ("clean_no", lambda r: r["action"] == "transfer_to_human"),
        "clean_no_error": ("clean_no", lambda r: r["action"] != r["correct_action"]),
    }
    for task in sorted({r["task"] for r in rows}):
        for dimension in ["wording_type", "wording"]:
            for level in sorted({r[dimension] for r in rows}):
                for metric, (cell, event) in metrics.items():
                    group = [
                        r
                        for r in rows
                        if r["task"] == task
                        and r[dimension] == level
                        and r["cell"] == cell
                    ]
                    value = cluster_rate(group, event)
                    if value:
                        results["rates"].append(
                            dict(
                                task=task,
                                dimension=dimension,
                                level=level,
                                metric=metric,
                                **value,
                            )
                        )
        results["contrasts"][task] = contrasts(
            [r for r in rows if r["task"] == task and r["cell"] == "corrupt_no"]
        )
    primary = [r for r in rows if r["cell"] == "corrupt_no"]
    if fit:
        x = np.c_[
            np.ones(len(primary)), [r["wording_type"] == "action" for r in primary]
        ]
        model = LaplaceLogistic(
            [r["action"] == "refuse" for r in primary],
            x,
            [
                [r["task"] + ":" + r["base_id"] for r in primary],
                [r["wording"] for r in primary],
                [r["task"] for r in primary],
            ],
        )
        results["primary"] = model.fit()
        results["primary"]["n"] = len(primary)
        same = sum(c["difference"] > 0 for c in results["contrasts"].values())
        results["same_direction_tasks"] = same
        results["rule_held"] = bool(
            results["primary"]["usable"]
            and results["primary"]["ci95"][0] > 1
            and same >= 2
            and meta["status"] == "complete"
        )
    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    (out / "power-results.json").write_text(json.dumps(results, indent=2))
    lines = [
        "# Flash wording power study",
        "",
        f"Run `{run.name}`: {meta['status']}; {len(rows)}/{len(allrows)} valid decisions; planned {results['planned']}; ${results['cost_usd']:.6f}.",
        "",
    ]
    if fit:
        lines += [
            "Primary model:",
            "",
            "```json",
            json.dumps(results["primary"], indent=2),
            "```",
            "",
            f"Decision rule held: **{results['rule_held']}**; {same}/3 tasks point in the predicted direction.",
            "",
        ]
    lines += [
        "Intervals below are 10,000-resample percentile cluster bootstraps over bases/orders. At all-zero/all-one outcomes they degenerate and do not bound population error.",
        "",
        "| Task | Wording | Metric | Count / n, CI, bases |",
        "|---|---|---|---|",
    ]
    for r in results["rates"]:
        lines.append(f"| {r['task']} | {r['level']} | {r['metric']} | {fmt(r)} |")
    lines += ["", "## Paired action-minus-answer refusal differences", ""]
    for task, c in results["contrasts"].items():
        lines.append(
            f"- {task}: {100 * c['difference']:.1f} percentage points [{100 * c['ci95'][0]:.1f}, {100 * c['ci95'][1]:.1f}], {c['bases']} bases."
        )
    (out / "power-results.md").write_text("\n".join(lines) + "\n")
    # Compact shareable analysis data, no raw API payloads.
    fields = [
        "id",
        "task",
        "base_id",
        "cell",
        "wording",
        "wording_type",
        "repeat",
        "action",
        "correct_action",
        "grant_action",
        "error",
        "unreadable",
        "cost_usd",
    ]
    with (out / "power-decisions.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows({k: r.get(k) for k in fields} for r in allrows)
    # Fixed independent-of-outcome review sampling. Never overwrite manual annotations.
    review = []
    rng = random.Random(SEED)
    for task in sorted({r["task"] for r in rows}):
        for typ in ["action", "answer"]:
            for cell in ["corrupt_no", "corrupt_yes"]:
                group = sorted(
                    [
                        r
                        for r in rows
                        if r["task"] == task
                        and r["wording_type"] == typ
                        and r["cell"] == cell
                    ],
                    key=lambda r: r["id"],
                )
                for r in rng.sample(group, min(10, len(group))):
                    review.append(
                        {
                            "id": r["id"],
                            "task": task,
                            "type": typ,
                            "cell": cell,
                            "action": r["action"],
                            "thoughts": r["reply"].get("thoughts"),
                            "message": r["message"],
                        }
                    )
    (out / "power-review-sample.json").write_text(json.dumps(review, indent=2))
    print(json.dumps({k: v for k, v in results.items() if k != "rates"}, indent=2))
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("run", type=Path)
    p.add_argument("--no-fit", action="store_true")
    a = p.parse_args()
    analyse(a.run, not a.no_fit)
