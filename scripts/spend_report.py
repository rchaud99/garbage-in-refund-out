"""Sum logged list-price spend, keeping paid requests, failures and dry runs separate."""

import json
from collections import defaultdict

from refundout.campaign import CAMPAIGN
from refundout.effort import CAMPAIGN as EFFORT_CAMPAIGN
from refundout.run import ROOT

rows = []
totals = defaultdict(float)
counts = defaultdict(int)
gemini_decision_total = 0.0
all_conversation_total = 0.0
for p in sorted((ROOT / "runs").glob("*/run.json")):
    m = json.loads(p.read_text())
    c = m["config"]
    if c.get("dry_run") or "dry-run" in p.parent.name:
        continue
    stream = "episodes" if (p.parent / "episodes.jsonl").exists() else "decisions"
    f = p.parent / (stream + ".jsonl")
    if not f.exists():
        continue
    rs = list(map(json.loads, f.read_text().splitlines()))
    if stream == "episodes":
        all_conversation_total += sum(r.get("cost_usd") or 0 for r in rs)
    else:
        gemini_decision_total += sum(
            (r.get("cost_usd") or 0)
            for r in rs
            if r.get("model", {}).get("name", "").startswith("gemini")
        )
    amount = sum(r.get("cost_usd") or 0 for r in rs)
    reserve = sum(r.get("uncertain_cost_reserve_usd") or 0 for r in rs)
    category = (
        "campaign"
        if c.get("campaign") == CAMPAIGN
        else "effort"
        if c.get("campaign") == EFFORT_CAMPAIGN
        else "historical"
    )
    rows.append(
        {
            "run": p.parent.name,
            "category": category,
            "records": len(rs),
            "cost_usd": amount,
            "uncertain_reserve_usd": reserve,
            "status": m["status"],
        }
    )
    totals[category] += amount
    totals[category + "_uncertain_reserve"] += reserve
    counts[category] += len(rs)
result = {
    "totals_usd": dict(totals),
    "cumulative_gemini_logged_cost_bound_usd": {
        "single_decisions": gemini_decision_total,
        "all_conversations_including_non_gemini": all_conversation_total,
        "conservative_total": gemini_decision_total + all_conversation_total,
    },
    "record_counts": dict(counts),
    "runs": rows,
    "basis": "Logged tokens at lookworth list prices; not a provider invoice. Historical interrupted calls without a saved usage record may be missing.",
}
(ROOT / "reports/spend.json").write_text(json.dumps(result, indent=2))
print(json.dumps({k: v for k, v in result.items() if k != "runs"}, indent=2))
