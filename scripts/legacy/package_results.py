"""Write the final concise project narrative from the completed, audited analysis.

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
    j = json.loads((ROOT / "reports/power-results.json").read_text())
    spend = json.loads((ROOT / "reports/spend.json").read_text())
    if j["status"] != "complete":
        raise RuntimeError("Do not package a partial study as complete")
    p = j["primary"]
    ci = p["ci95"]
    cost = spend["totals_usd"]["campaign"]
    historical = spend["totals_usd"]["historical"]

    def rate(task, level, metric="wrongful_refusal"):
        return next(
            r
            for r in j["rates"]
            if r["task"] == task
            and r["level"] == level
            and r["dimension"] == "wording_type"
            and r["metric"] == metric
        )

    def label(r):
        return f"{r['k']}/{r['n']} ({100 * r['rate']:.1f}%, 95% CI {100 * r['ci95'][0]:.1f}–{100 * r['ci95'][1]:.1f})"

    headline = (
        "The prespecified cross-task rule held in these three tasks."
        if j["rule_held"]
        else "The refusal leak was task-specific; the prespecified cross-task rule did not hold."
    )
    primary = f"Action/answer odds ratio {p['odds_ratio']:.2f}, approximate 95% CI [{ci[0]:.2f}, {ci[1]:.2f}]."
    diagnostics = f"Model usable: {p['usable']}; boundary random-effect components: {p['boundary_components']} (0=base, 1=paraphrase, 2=task)."
    table = "| Task | Action-tied refusal | Answer-tied refusal | Bases per corrupted cell |\n|---|---|---|---:|\n"
    for task, name, n in [
        ("airline", "Airline cancellation", 65),
        ("retail_cancel", "Retail cancellation", 30),
        ("retail_return", "Retail return", 43),
    ]:
        table += f"| {name} | {label(rate(task, 'action'))} | {label(rate(task, 'answer'))} | {n} |\n"
    readme = f"""# Garbage In, Refund Out

![Wrongful refusals and bad payouts by wording type and task](figures/wording_tasks.png)

**{headline}** This applied-AI evaluation asks whether a support agent checks contradictory records before refusing a customer as reliably as before approving them.

{j["valid"]:,} valid Gemini 3.8 Flash decisions: three action-tied and three answer-tied instructions, two calls per item, three tasks. The check content is identical within each task; only its trigger changes. Intervals resample bases/orders, keeping repeated calls and wordings together.

{table}

Primary mixed-effects logistic model: **{primary}** Random intercepts: base/order, six paraphrases, three tasks. {j["same_direction_tasks"]}/3 tasks point in the predicted direction. {diagnostics} The pooled odds ratio is unstable in magnitude: both retail tasks have zero events and the fitted task-intercept SD is 13.52 log-odds units. Its very wide interval and common-effect assumption make it unsuitable as a portable deployment multiplier. The decision rule fails regardless because only the airline task has a positive difference. With three tasks and six paraphrases, this is limited evidence about a wider population of tasks or wordings. Both retail tasks share a status/tracking invariant. Zero-event bootstrap intervals collapse; they do not establish zero population risk.

A separate supplied-ledger test gave Flash **0/24 bad payouts, 0/24 wrongful refusals and 0/48 control errors**. The earlier 96-base airline wording follow-up gave **55/96 F1 refusals versus 8/96 F1d**, paired difference −49 percentage points [−59,−38]. In eight-base full conversations, the Flash F1/F1d refusal gap disappeared (0/8 versus 0/8); Sonnet's descriptive rates were 4/8 versus 1/8.

**Deployment lesson:** name refusal explicitly and validate both answers per model and task. Prefer a deterministic reconciliation supplied before the answer; bind enforcement to refusals as well as writes. Give legitimate adjustments approval provenance and a rule for how they count. See [the one-page memo](MEMO.md).

## Reproduce and inspect

Reproduce the primary fit from the versioned compact CSV without API keys, the benchmark clone, or the sibling library:

```sh
uv run --no-project --with numpy --with scipy python scripts/reanalyse_compact.py
```

The [statistical method note](reports/STATISTICAL_METHOD.md) explains the custom Laplace implementation and its validation. An independent lme4 check is supplied but was not run (R unavailable).

Python 3.12+, uv, the sibling `../how_much_is_a_look_worth` package, and τ²-bench at pinned commit `b7ea907` are required. This project reads the benchmark data; the new single-decision runner does not execute τ² tools. The sibling dependency is currently local, so the repository is not a standalone install.

```sh
git clone https://github.com/sierra-research/tau2-bench vendor/tau2-bench
git -C vendor/tau2-bench checkout b7ea907
uv sync
uv run pytest -q
uv run python -m refundout.power --estimate --airline 65 --cancel 30 --returns 43 --clean 5
# Paid run, only after reviewing the estimate; Gemini only, no retries:
uv run python -m refundout.power --airline 65 --cancel 30 --returns 43 --clean 5 --max-dollars 50
# Analyse a completed local run:
uv run python -m refundout.power_analysis runs/{j["run"]}
uv run python scripts/figure_power.py
cd paper
tectonic main.tex
```

The new runner enforces one shared campaign cap across its runs, reserves conservative in-flight costs and caps output at 8,192 tokens; keys load from the sibling `.env` and are never committed. Historical runners can call other models by default: inspect their `--estimate` output before use. No Claude calls were made in this continuation.

- [Preregistration](PREREGISTRATION.md): hypothesis, fixed sample, exclusions and decision rule, frozen before the study.
- [Detailed results](reports/power-results.md) and [compact decisions](reports/power-decisions.csv): exact counts, per-paraphrase results and cluster intervals.
- [Reasoning review](reports/power-review.md): 120 presampled model reasoning summaries, read and annotated by Codex; not an independent human audit.
- [Stopped-run audit](reports/stopped-audit.md) and [completed follow-ups](reports/stopped-completed.md).
- [Findings](FINDINGS.md), [paper](paper/main.pdf), [methods history](docs/original-methods.md).

New campaign spend: **${cost:.6f}**, comprising $1.457943 in completion calls and ${j["cost_usd"]:.6f} in the power study. Historical logged spend across all models: ${historical:.6f}. [Spend ledger](reports/spend.json) uses recorded tokens and list prices, not a provider invoice. Raw prompts, replies and provider payloads remain in local `runs/` (excluded from Git); compact study data, review samples, manifests and reports are versioned. No results were deleted.
"""
    readme += "\n**Commit status:** files are ready, but the first commit is blocked because `.git` write permission was not granted. See [local commit instructions](reports/COMMIT_STATUS.md).\n"
    (ROOT / "README.md").write_text(readme)
    memo = f"""# Deployment memo: check before every answer

**Decision.** Compute record reconciliation in code and supply its result before an agent grants **or refuses** a request. If using a prompt check, name both answers explicitly: “Whether you grant or refuse the request, first reconcile the record.” Validate this per model, task and conversation flow.

**Evidence and scope.** {headline} In the Flash-only study ({j["valid"]:,} decisions, six wording templates, two repeats), airline action/answer refusal rates were {label(rate("airline", "action"))} versus {label(rate("airline", "answer"))}. The mixed-model {primary[0].lower() + primary[1:]} The rule required significance plus the same direction in at least two tasks; {j["same_direction_tasks"]}/3 met the directional condition. The pooled estimate is unstable because both retail tasks have zero events; use the task rates. Both retail tasks share one benchmark-specific invariant. These are single-decision tests, not a deployment reliability estimate.

**Preferred implementation.** A required read check should return expected total, paid total, difference, evidence references and reconciliation status. Make a mismatch require a human handoff before any final eligibility answer. A guard attached only to a refund write misses a wrongful “no.” A supplied airline ledger gave 0/24 bad payouts, 0/24 wrongful refusals and 0/48 control errors; that is promising small-n evidence, not a guarantee or a test of optional tool use.

**Adjustments.** Store amount, adjustment type, reservation/order ID, approver, approval time and reason. Define the counting rule explicitly: add an authorized credit back when comparing with the original charge. An approval label alone does not reconcile a ledger. Prior tests released 36/36 approved legitimate credits across three models with the rule and held 36/36 corresponding corrupted records; validate your own exceptions and currencies.

**Release test.** Pair every “yes”-leaning contradiction with a “no”-leaning one and clean controls. Measure bad approvals, wrongful refusals, false holds and unparseable responses separately, with independent-base intervals. Repeat after model or policy changes. Review the actual customer message and successful handoff, not just a JSON label. Track unexpected invariant violations before enforcing any shipping rule in production.

**Cost and limits.** This campaign used ${cost:.2f}. The earlier small conversation sample averaged about $60 per 1,000 Flash conversations and $80 per 1,000 Sonnet conversations at recorded prices, excluding engineering and human escalation. Its Flash refusal gap disappeared (0/8 vs 0/8); do not extrapolate single-decision effects directly to live conversations.
"""
    (ROOT / "MEMO.md").write_text(memo)
    section = f"""\n## Prospective Flash wording power study (2026-09-25)\n\n**{headline}** Fixed before API calls: six trigger templates, two repeats, 65 airline bases, 30 orders per retail-cancel family, 43 per retail-return family, and five clean controls per family/task. There were {j["valid"]}/{j["planned"]} valid decisions, {j["api_errors"]} API errors and {j["unreadable"]} unreadable replies; cost ${j["cost_usd"]:.6f}. Selection and call order used seed 20260925.\n\n{table}\nPrimary: {primary} {diagnostics} The prespecified criterion requires OR CI above 1 and strictly positive action-minus-answer refusal differences in at least two tasks; **{j["same_direction_tasks"]}/3** had that direction, so **rule held = {j["rule_held"]}**. Rates and 95% cluster-bootstrap intervals for every task and paraphrase, bad payouts/return approvals, false holds, and clean-no transfers are in `reports/power-results.md`. Returns are approvals to initiate a return, not executed cash payouts.\n\nInterpretation is limited to this Flash model and setting. Repeated calls do not turn 65 airline bases into 390 independent bases. Six chosen paraphrases and three related tasks provide weak information for random-effect generality. Both retail tasks use the same explicitly supplied pending-if-and-only-if-no-tracking rule; there is no third domain or third independent checking mechanism. Zero/all-one bootstrap intervals degenerate. No equivalence margin was preregistered, so an absence of observed payout errors is not equivalence evidence.\n\nReasoning summaries were reviewed on a deterministic, outcome-independent sample of 120 replies (10 per task × wording type × corruption direction). The full sample, annotations and caveats are in `reports/power-review.md`; this is a Codex qualitative read, not an independent human coding study.\n\nNew campaign spend: ${cost:.6f} under the $50 shared cap; historical logged all-model spend ${historical:.6f}. No Claude calls, no deleted results, no post-hoc extension of the sample.\n"""
    findings = (ROOT / "FINDINGS.md").read_text()
    marker = "\n## Prospective Flash wording power study (2026-09-25)"
    findings = findings.split(marker)[0] + section
    (ROOT / "FINDINGS.md").write_text(findings)
    # LaTeX uses machine-derived counts while keeping interpretation in prose.
    tex = r"\subsection{Prospective six-wording, three-task Flash extension}" + "\n\n"
    tex += r"The analysis and decision rule were frozen before the first call in \texttt{PREREGISTRATION.md}. "
    tex += f"There were {j['valid']:,} valid decisions, two repeats per item, three action-tied and three answer-tied triggers, with identical check content within each task. The sample was reduced before collection to fit the budget: 65 airline bases, 30 orders per retail-cancel family, 43 per retail-return family and five clean controls per family/task.\n\n"
    tex += (
        r"\begin{center}\small\begin{tabular}{lccc}\toprule Task & Action refusals & Answer refusals & Bases \\\midrule"
        + "\n"
    )
    for task, name, n in [
        ("airline", "Airline cancel", 65),
        ("retail_cancel", "Retail cancel", 30),
        ("retail_return", "Retail return", 43),
    ]:
        a, b = rate(task, "action"), rate(task, "answer")
        tex += f"{name} & {a['k']}/{a['n']} & {b['k']}/{b['n']} & {n} \\\\\n"
    tex += r"\bottomrule\end{tabular}\end{center}" + "\n\n"
    tex += f"The mixed-effects logistic model used random intercepts for base/order, paraphrase and task. The action/answer odds ratio was {p['odds_ratio']:.2f}, approximate 95\\% Wald CI [{ci[0]:.2f},{ci[1]:.2f}], fitted by Laplace maximum likelihood. "
    tex += (
        f"Only {j['same_direction_tasks']}/3 tasks pointed in the predicted direction. "
        + headline
        + "\n\n"
    )
    tex += (
        r"\begin{figure}[ht]\centering\includegraphics[width=\linewidth]{fig_wording_tasks.pdf}\caption{Flash extension. Intervals resample bases/orders with repeats and wordings together. Zero-event bootstrap intervals degenerate and do not imply zero population risk. Retail return outcomes are approvals to initiate returns, not immediate payments.}\end{figure}"
        + "\n\n"
    )
    tex += (
        r"The model assumes a common wording-type coefficient despite task heterogeneity; only three tasks and six paraphrases inform their variance components. Both retail tasks share one status/tracking invariant, verified on all 1,000 source orders. A deterministic 120-summary sample was read and annotated by Codex, with full records in \texttt{reports/power-review.md}. These are model-generated summaries, not direct observations of all internal computation. "
        + "\n"
    )
    tex += "\nThe fitted task-intercept standard deviation was 13.52 log-odds units. With zero events in both retail tasks, the pooled odds-ratio magnitude is unstable and should not be treated as a portable multiplier. All four optimizer starts agreed numerically, but convergence does not resolve sparse task-level information. The paired airline refusal difference was 71.3 percentage points (95\\% cluster-bootstrap CI [64.6,77.4]); both retail differences were zero. No bad payouts or return approvals were observed (0/1,656 corrupted yes decisions), and clean-control errors were 0/360 (only five bases per clean family/task).\n\nIn the presampled qualitative review, 5/10 airline action-tied D summaries and 10/10 answer-tied D summaries showed a concrete arithmetic check. All 20 sampled airline C and all 80 retail summaries showed a concrete check. Seven of 120 summaries referred to a benchmark or test; these generated claims do not establish training contamination.\n"
    (ROOT / "paper/power_results.tex").write_text(tex)
    print(headline, primary, "Campaign", cost)


if __name__ == "__main__":
    main()
