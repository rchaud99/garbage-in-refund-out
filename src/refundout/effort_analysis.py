"""Frozen retail arithmetic decision rule and order-clustered descriptive results."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

from refundout.power_analysis import cluster_rate, contrasts, fmt
from refundout.run import ROOT


def rule(contrast, glance_rates, complete):
    return bool(
        complete
        and contrast["difference"] >= 0.20
        and contrast["ci95"][0] > 0
        and len(glance_rates) == 4
        and all(r <= 0.05 for r in glance_rates)
    )


def review_sample(rows, action):
    rng = random.Random(20260926)
    selected, seen = [], set()
    groups = {}
    for typ in ["action", "answer"]:
        group = sorted(
            [
                r
                for r in rows
                if r["cell"] == "corrupt_no"
                and r["action"] == action
                and r["wording_type"] == typ
            ],
            key=lambda r: r["id"],
        )
        rng.shuffle(group)
        groups[typ] = group
        added = 0
        for r in group:
            if r["base_id"] not in seen:
                selected.append(r)
                seen.add(r["base_id"])
                added += 1
                if added == 5:
                    break
    remaining = groups["action"] + groups["answer"]
    for prefer_distinct in [True, False]:
        for r in remaining:
            if len(selected) >= 10:
                break
            if r not in selected and (not prefer_distinct or r["base_id"] not in seen):
                selected.append(r)
                seen.add(r["base_id"])
    return [
        {
            "id": r["id"],
            "wording": r["wording"],
            "type": r["wording_type"],
            "base_id": r["base_id"],
            "action": r["action"],
            "thoughts": r["reply"].get("thoughts"),
            "message": r["message"],
        }
        for r in selected
    ]


def analyse(run):
    meta = json.loads((run / "run.json").read_text())
    allrows = list(map(json.loads, (run / "decisions.jsonl").read_text().splitlines()))
    assert len({r["id"] for r in allrows}) == len(allrows)
    rows = [r for r in allrows if not r["error"] and not r["unreadable"]]
    manifest = json.loads((ROOT / "reports/effort-plan.json").read_text())
    expected = {r["id"]: r["prompt_sha256"] for r in manifest["items"]}
    for r in allrows:
        assert (
            hashlib.sha256(
                (r["prompt"]["system"] + "".join(r["prompt"]["user"])).encode()
            ).hexdigest()
            == expected[r["id"]]
        )
    assert (
        hashlib.sha256((ROOT / "EFFORT_PREREGISTRATION.md").read_bytes()).hexdigest()
        == meta["config"]["preregistration_sha256"]
    )
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
        "prompt_hashes_verified": len(allrows),
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
        "clean_no_error": ("clean_no", lambda r: r["action"] != r["correct_action"]),
        "clean_no_transfer": ("clean_no", lambda r: r["action"] == "transfer_to_human"),
    }
    for dimension in ["wording_type", "wording"]:
        for level in sorted({r[dimension] for r in rows}):
            for metric, (cell, event) in metrics.items():
                value = cluster_rate(
                    [r for r in rows if r["cell"] == cell and r[dimension] == level],
                    event,
                )
                if value:
                    results["rates"].append(
                        dict(
                            task="retail_arithmetic",
                            dimension=dimension,
                            level=level,
                            metric=metric,
                            **value,
                        )
                    )
    contrast = contrasts([r for r in rows if r["cell"] == "corrupt_no"])
    results["contrast"] = contrast
    prior = json.loads((ROOT / "reports/power-results.json").read_text())
    glance = [
        r["rate"]
        for r in prior["rates"]
        if r["task"] in ("retail_cancel", "retail_return")
        and r["dimension"] == "wording_type"
        and r["metric"] == "wrongful_refusal"
    ]
    complete = meta["status"] == "complete" and len(rows) == results["planned"]
    results["effort_pattern_rule_held"] = rule(contrast, glance, complete)
    results["causal_effort_isolated"] = False
    results["original_generality_rule_held"] = prior["rule_held"]
    (ROOT / "reports/effort-results.json").write_text(json.dumps(results, indent=2))
    lines = [
        "# Retail arithmetic follow-up",
        "",
        f"Run `{run.name}`: {meta['status']}; {len(rows)}/{results['planned']} valid; ${results['cost_usd']:.6f}.",
        "",
        f"Effort-pattern rule held: **{results['effort_pattern_rule_held']}**. Original three-task rule remains **{prior['rule_held']}**.",
        "",
        f"Paired action-minus-answer refusal difference: {100 * contrast['difference']:.1f} percentage points, 95% order-cluster bootstrap CI [{100 * contrast['ci95'][0]:.1f}, {100 * contrast['ci95'][1]:.1f}], {contrast['bases']} orders.",
        "",
        "This analogue changes action, numeric eligibility, profile lookup and account-balance setup. It does not isolate effort causally. Real orders and prices; synthetic gift-card baseline balances; only first-payment amount changes within each clean/corrupt pair. Three to five item prices must be summed. Zero-event bootstrap intervals do not establish zero risk. Four clean orders per family provide little information about rare false holds.",
        "",
        "| Wording | Metric | Count/n, 95% cluster CI, independent orders |",
        "|---|---|---|",
    ]
    for r in results["rates"]:
        lines.append(f"| {r['level']} | {r['metric']} | {fmt(r)} |")
    (ROOT / "reports/effort-results.md").write_text("\n".join(lines) + "\n")
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
    with (ROOT / "reports/effort-decisions.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: r.get(k) for k in fields} for r in allrows)
    samples = {
        action: review_sample(rows, action)
        for action in ["refuse", "transfer_to_human"]
    }
    (ROOT / "reports/effort-review-sample.json").write_text(
        json.dumps(samples, indent=2)
    )
    print(json.dumps({k: v for k, v in results.items() if k != "rates"}, indent=2))
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("run", type=Path)
    analyse(p.parse_args().run)
