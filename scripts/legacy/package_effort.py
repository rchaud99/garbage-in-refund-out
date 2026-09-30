"""Package the completed fourth task without changing either preregistration.

LEGACY (superseded 2026-09-28). This generator rewrote README.md, MEMO.md, FINDINGS.md and the paper from the
2026-09-25 study. Running it now would overwrite the current write-ups with that older text, so it refuses unless
given --overwrite-current-writeups. Kept for provenance only.
"""

import json

from refundout.run import ROOT


def main():
    import sys
    if "--overwrite-current-writeups" not in sys.argv:
        raise SystemExit("legacy generator: would overwrite README.md/FINDINGS.md with 2026-09-25 text; see its docstring")
    prior = json.loads((ROOT / "reports/power-results.json").read_text())
    new = json.loads((ROOT / "reports/effort-results.json").read_text())
    spend = json.loads((ROOT / "reports/spend.json").read_text())
    if new["status"] != "complete" or new["valid"] != new["planned"]:
        raise RuntimeError("Do not package an incomplete follow-up as complete")
    rates = prior["rates"] + new["rates"]
    tasks = [
        ("airline", "Airline arithmetic"),
        ("retail_arithmetic", "Retail arithmetic analogue"),
        ("retail_cancel", "Retail cancellation (glance)"),
        ("retail_return", "Retail return (glance)"),
    ]

    def get(task, typ, metric="wrongful_refusal"):
        return next(
            r
            for r in rates
            if r["task"] == task
            and r["level"] == typ
            and r["dimension"] == "wording_type"
            and r["metric"] == metric
        )

    def label(r):
        return f"{r['k']}/{r['n']} ({100 * r['rate']:.1f}%; CI {100 * r['ci95'][0]:.1f}–{100 * r['ci95'][1]:.1f})"

    table = "| Task | Action-tied refusals | Answer-tied refusals | Orders/bases |\n|---|---|---|---:|\n"
    for task, name in tasks:
        table += f"| {name} | {label(get(task, 'action'))} | {label(get(task, 'answer'))} | {get(task, 'action')['bases']} |\n"
    (ROOT / "reports/four-task-table.md").write_text(
        table
        + "\n95% intervals cluster by original order/base, retaining both repeats and all wordings. Zero-event bootstrap intervals do not establish zero population risk. The retail arithmetic task is a payment-switch analogue with synthetic baseline balances; it does not isolate effort.\n"
    )
    headline = (
        "The retail arithmetic analogue meets the effort-pattern rule; effort remains confounded."
        if new["effort_pattern_rule_held"]
        else "The airline wording effect is large; the retail arithmetic follow-up does not support the effort rule."
    )
    c = new["contrast"]
    contrast = f"{100 * c['difference']:.1f} percentage points (95% order-cluster CI {100 * c['ci95'][0]:.1f}–{100 * c['ci95'][1]:.1f}; {c['bases']} orders)"
    total = spend["totals_usd"]["campaign"] + spend["totals_usd"]["effort"]
    rule_text = f"The retail action-minus-answer gap is {contrast}. The frozen rule required at least +20 points with a CI above zero, while both glance tasks stayed near zero. **Effort-pattern rule held: {new['effort_pattern_rule_held']}.** The original three-task generality rule remains **False** (only 1/3 tasks had the predicted direction); it was not retroactively changed."
    caveat = "Cancellation/return eligibility is status-based, so a payment-only corruption cannot faithfully flip it. The closest native analogue switches a pending order to an existing gift card: τ²'s tool compares its balance with the first payment. We use real orders and item prices but explicitly synthetic balance scenarios. Only first-payment amount changes within a clean/corrupt pair. The arithmetic invariant holds on all 1,000 source orders. This changes the action, numeric eligibility and profile lookup as well as the check, so it cannot identify effort as the sole causal moderator."
    cost_text = f"Effort follow-up: **${new['cost_usd']:.6f} / $8**; earlier continuation: **$23.170886**; both continuations: **${total:.6f}**. No Claude calls. Costs use logged tokens at list prices, not a provider invoice; historical all-model spend is separate (${spend['totals_usd']['historical']:.6f})."
    readme = f"""# Garbage In, Refund Out

![Wrongful refusals by wording type across four tasks](figures/effort_tasks.png)

**{headline}** A support agent may trust an eligibility field and skip a consistency check before saying no. We test whether naming both answers changes that behavior.

{table}

95% percentile intervals resample independent orders/bases, preserving repeated calls and all wordings. Zero-event intervals collapse and do not establish zero risk. Six trigger templates (three action, three answer), two calls per item, Gemini 3.8 Flash with medium thinking and default temperature. The fourth task adds {new["valid"]} decisions to the 3,672-decision study; it has only 21 eligible multi-item orders, with four clean orders per family.

{rule_text}

**Why this is an analogue:** {caveat}

The airline result replicated across six Flash paraphrases and, for the original wording pair, Flash and Sonnet. The new six-wording and retail arithmetic studies are **Flash-only**. In the prior study the airline paired refusal difference was +71.3 points [64.6, 77.4]. The pooled mixed-model action/answer OR was 4999.98 [97.51, 256385.48]; its magnitude is unstable because both retail tasks had zero events and only three tasks informed the random effect. Per-task rates are more useful than that multiplier.

A supplied deterministic airline reconciliation gave **24/24 transfers in each corrupted direction**, with 0/48 clean-control errors. This small test is promising; it does not prove a code checker removes every failure. In eight-base full conversations the Flash F1/F1d refusal gap disappeared (0/8 each); Sonnet's rates were 4/8 versus 1/8. Prompt fixes must be validated in the actual workflow.

**Deployment rule:** require reconciliation before granting or refusing, name both answers in prompt checks, and prefer deterministic checks with enforcement. Give adjustments provenance and a counting rule. See [MEMO.md](MEMO.md).

## Reproduce and inspect

Compact analyses need no API keys, benchmark clone or sibling package:

```sh
uv run --no-project --with numpy --with scipy python scripts/reanalyse_compact.py
uv run --no-project --with numpy python scripts/reanalyse_effort_compact.py
```

Full tests/runners require Python 3.12+, uv, local sibling `../how_much_is_a_look_worth`, and [τ²-bench](https://github.com/sierra-research/tau2-bench) cloned into `vendor/tau2-bench` at commit `b7ea907`. The project is not yet a standalone install.

```sh
uv sync
uv run pytest -q
uv run python -m refundout.effort --estimate --orders 21 --clean 4
# Paid replay, only after inspecting the estimate. The existing campaign cap includes prior calls:
# uv run python -m refundout.effort --orders 21 --clean 4 --max-dollars 8
uv run python -m refundout.effort_analysis runs/{new["run"]}
uv run python scripts/spend_report.py
uv run python scripts/figure_effort.py
uv run python scripts/package_effort.py
cd paper
tectonic main.tex
```

The Gemini guard reserves all in-flight costs, caps output at 8,192 tokens, makes no retries, and stops submissions on an API error. The follow-up is a separate $8 campaign. Existing prompt definitions and the original preregistration remain unchanged. Every paid run retains prompts, replies, model versions, usage and hashes locally.

- [Original preregistration](PREREGISTRATION.md) and [effort preregistration](EFFORT_PREREGISTRATION.md).
- [Three-task results](reports/power-results.md), [effort results](reports/effort-results.md), and [four-task table](reports/four-task-table.md).
- Compact decisions: [original study](reports/power-decisions.csv), [follow-up](reports/effort-decisions.csv).
- Qualitative reviews: [120 original summaries](reports/power-review.md), [follow-up refusals/transfers](reports/effort-review.md). Read and annotated by Codex, not an independent human audit.
- [Statistical implementation and limitations](reports/STATISTICAL_METHOD.md); optional R/lme4 cross-check supplied but not run.
- [Stopped-run audit](reports/stopped-audit.md), [completed follow-ups](reports/stopped-completed.md), [findings](FINDINGS.md), [paper](paper/main.pdf), [original methods](docs/original-methods.md).

{cost_text} [Spend ledger](reports/spend.json). Raw run artifacts remain local and ignored by Git; compact decisions, hashed manifests and reports are ready to commit. No results were deleted.

**Git:** metadata access is blocked, as requested left unchanged. Run the [first-commit commands](reports/COMMIT_STATUS.md) locally.
"""
    (ROOT / "README.md").write_text(readme)
    memo = f"""# Deployment memo: check before every answer

**Decision.** Require deterministic reconciliation before granting or refusing a request. If checks rely on prompts, explicitly name both answers. Validate each model, task and conversation flow; a guard only on a refund write cannot catch a wrongful “no.”

**Evidence.** {headline} Wrongful refusals under Gemini 3.8 Flash:

{table}

Intervals are 95% order/base-cluster bootstraps; zero-event intervals do not prove zero risk. The original generality rule failed. The follow-up effort-pattern rule held: **{new["effort_pattern_rule_held"]}**; retail difference {contrast}. The six-wording evidence is Flash-only; the original airline pair also showed the effect in Sonnet.

**Scope.** Retail arithmetic uses a native payment-switch action and real item prices, but synthetic gift-card balances. It changes eligibility and transcript as well as checking effort. There are only 21 arithmetic retail orders and four clean orders per family. This is not a causal isolation of effort or a deployment reliability estimate.

**Implementation.** Return expected total, paid total, discrepancy, evidence references and reconciliation status. Make a mismatch require a human handoff before any final answer. A supplied airline ledger gave 24/24 correct transfers in each corrupted direction and 0/48 clean-control errors; this small result supports testing deterministic checks, not a guarantee.

**Adjustments.** Store amount, adjustment type, order/reservation ID, approver, approval time and reason. State how each adjustment counts: add an authorized credit back when comparing with the original charge. Provenance alone does not reconcile a ledger. Prior tests released 36/36 legitimate credits and held 36/36 corresponding corruptions across three models with the counting rule.

**Release test.** Pair every yes-leaning contradiction with a no-leaning one and clean controls. Measure refusals, bad approvals, false holds, invalid replies and successful handoffs separately. Repeat after model/policy changes. The earlier eight-base Flash conversation comparison had 0/8 refusals under both wordings, so single-decision gaps need workflow validation.

**Cost.** Follow-up ${new["cost_usd"]:.2f}; both new campaigns ${total:.2f}. No new Claude calls. Recorded list prices, excluding engineering and escalation.
"""
    (ROOT / "MEMO.md").write_text(memo)
    section = f"\n## Retail arithmetic effort follow-up (2026-09-25)\n\n**{headline}**\n\n{table}\n\n{rule_text}\n\n{caveat}\n\nFixed plan: 21 real multi-item orders per corrupted family, two synthetic baseline balance scenarios on those same orders, four clean counterparts per family, six identical trigger templates and two calls per item. {new['valid']}/{new['planned']} valid replies, {new['api_errors']} API errors, {new['unreadable']} invalid responses. All prompt hashes and the preregistration hash match. No post-hoc extension. Per-paraphrase refusal, approval, false-hold and clean-no error rates are in `reports/effort-results.md`; full qualitative read in `reports/effort-review.md`.\n\n{cost_text}\n"
    f = (
        (ROOT / "FINDINGS.md")
        .read_text()
        .split("\n## Retail arithmetic effort follow-up (2026-09-25)")[0]
    )
    f += section
    # Keep the historical narrative, with a prominent link to the latest follow-up.
    notice = f"\n**Latest follow-up:** {headline} See the retail arithmetic effort section below.\n"
    if "**Latest follow-up:**" not in f:
        title, rest = f.split("\n", 1)
        f = title + "\n" + notice + rest
    (ROOT / "FINDINGS.md").write_text(f)
    tex = r"\subsection{Arithmetic retail follow-up: an effort hypothesis}" + "\n\n"
    tex += "A separately preregistered follow-up used 21 real pending orders with 3--5 items, each in eligible and ineligible gift-card balance scenarios; four orders supplied clean counterparts. Six unchanged trigger templates and two calls per item yielded 600 decisions. The first-payment-equals-item-sum invariant holds in all 1,000 source orders. Within each scenario, only the first-payment amount is corrupted. Baseline gift-card balances are explicitly synthetic.\n\n"
    tex += "Cancellation/return status cannot be made arithmetic by changing payment amount. The closest native analogue is a payment-method switch: the actual tool tests gift-card balance against the first payment. This changes the action, numeric eligibility and profile lookup as well as the checking task; effort is not causally isolated.\n\n"
    tex += (
        r"\begin{table}[ht]\centering\small\begin{tabular}{llrr}\toprule Task & Wording & Refusals (\%) & 95\% CI (\%) \\\midrule"
        + "\n"
    )
    for task, name in tasks:
        for typ in ("action", "answer"):
            r = get(task, typ)
            tex += f"{name if typ == 'action' else ''} & {typ.capitalize()} & {r['k']}/{r['n']} ({100 * r['rate']:.1f}) & [{100 * r['ci95'][0]:.1f}, {100 * r['ci95'][1]:.1f}] \\\\\n"
    tex += (
        r"\bottomrule\end{tabular}\caption{Four-task Flash comparison. Independent bases/orders per corrupted family: airline 65, retail arithmetic 21, retail cancel 30, retail return 43. Intervals cluster by base/order with both repeats and all wordings together. Zero-event bootstrap intervals do not establish zero risk.}\end{table}"
        + "\n\n"
    )
    tex += f"The retail refusal gap (action minus answer) was {100 * c['difference']:.1f} percentage points, 95\\% cluster-bootstrap CI [{100 * c['ci95'][0]:.1f},{100 * c['ci95'][1]:.1f}]. The prespecified rule required at least 20 points with a positive interval and near-zero refusal rates in both earlier glance tasks. Rule held: \\textbf{{{'yes' if new['effort_pattern_rule_held'] else 'no'}}}. The original generality rule also failed. "
    tex += (
        "The result is consistent with the effort hypothesis in this analogue, with the confounds above. "
        if new["effort_pattern_rule_held"]
        else "The registered effort prediction was not supported. The airline result remains specific to that task. "
    )
    tex += f"\n\nThe follow-up cost \\${new['cost_usd']:.2f} under its separate \\$8 cap; no Claude calls were made.\n\n"
    for metric, name in [
        ("bad_payout_or_approval", "Bad payment-change approvals"),
        ("false_hold", "False holds on clean eligible orders"),
        ("clean_no_error", "Errors on clean ineligible orders"),
    ]:
        a, b = (
            get("retail_arithmetic", "action", metric),
            get("retail_arithmetic", "answer", metric),
        )
        tex += f"{name} were {a['k']}/{a['n']} under action wording and {b['k']}/{b['n']} under answer wording. "
    tex += "Clean controls cover only four independent orders per family. Per-paraphrase rates and review annotations are supplied in the accompanying reports.\n\n"
    tex += (
        r"\begin{figure}[ht]\centering\includegraphics[width=\linewidth]{fig_effort_tasks.pdf}\caption{Wrongful refusals by wording type. The arithmetic retail task is an analogue with synthetic balances, not a controlled manipulation of effort alone.}\end{figure}"
        + "\n"
    )
    review = ROOT / "reports/effort-review-summary.json"
    if review.exists():
        q = json.loads(review.read_text())
        tex += "\n" + q["paper_sentence"] + "\n"
    (ROOT / "paper/effort_results.tex").write_text(tex)
    # Replace the superseded three-task figure with the four-task figure in the follow-up section.
    p = ROOT / "paper/power_results.tex"
    text = p.read_text()
    if "\\begin{figure}" in text:
        before, rest = text.split("\\begin{figure}", 1)
        text = before + rest.split("\\end{figure}", 1)[1]
        p.write_text(text)
    p = ROOT / "paper/main.tex"
    text = p.read_text()
    if "\\input{effort_results}" not in text:
        text = text.replace(
            "\\input{power_results}", "\\input{power_results}\n\\input{effort_results}"
        )
    marker = " The practical recommendation is to validate"
    if "A further 600-call retail arithmetic analogue" not in text:
        addition = f" A further 600-call retail arithmetic analogue used synthetic gift-card balances and produced {get('retail_arithmetic', 'action')['k']}/{get('retail_arithmetic', 'action')['n']} versus {get('retail_arithmetic', 'answer')['k']}/{get('retail_arithmetic', 'answer')['n']} wrongful refusals; the preregistered effort-pattern rule {'held' if new['effort_pattern_rule_held'] else 'failed'}. The analogue does not isolate effort causally."
        text = text.replace(marker, addition + marker, 1)
    p.write_text(text)
    print(headline, contrast, cost_text, "Memo words", len(memo.split()), sep="\n")


if __name__ == "__main__":
    main()
