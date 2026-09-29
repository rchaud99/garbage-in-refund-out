# DIGEST: Garbage In, Refund Out (autonomous session, 2026-09-28)

**Format:** single-decision replays on τ²-bench airline. Everything was preregistered (`LADDER_PREREGISTRATION.md`
and Amendments 1–5), and every model is reported. Spend: **$38.52 of $40** (campaign $38.40, plus a $0.12 τ²-native
check). 6,159 calls. Gemma calls were free and are partial (stopped at 21:25 on request).

## Wording ladder: the least instruction per model (C payouts and D wrongful refusals both ≤ 5%)
- **Gemini 3.8 Flash:** **none of nine wordings.**
  - Stock policy, "record looks wrong", "anything seems off", the bare clause and "double-check": 100% errors both ways.
  - "Payments match before acting": C caught on cancellation only, D 47/47 refused.
  - Lookup-scoped check: D 47% (cancel) and 96% (comp).
  - Closest: "before telling the customer yes or no…" (C 0%, D 8–9%).
- **Gemini 3.1 Pro:** none tested (SN still refuses 55% / 87%).
- **Claude Sonnet 5:** none. Best: the lookup-scoped wording on cancel (D 21/62, C 16/61).
- **GPT-6 Sol:** the action-scoped arithmetic recipe already gives 0 errors.
- **GPT-6 Luna:** the same on cancel; SN on compensation.
- **Gemma 4:** none.
- **Opus:** not run (budget).

## Surviving findings
1. **Guardrail wording effects are model-specific.**
   - "Before telling the customer yes or no" vs "Before deciding on": Flash 41/62 → 5/62 (Holm p = 5e-10), Pro
     51/62 → 34/62 (p = 0.035), Sonnet 44/62 → 40/62 (p = 1).
   - The lookup-scoped check: helps Sonnet (−37 pp [−50, −26], p = 1e-5), hurts Flash on comp (16/46 → 44/46),
     and raises Gemma's payouts (1/62 → 18/39).
2. **Yes/no-path asymmetry: the check runs before "yes" and is skipped before "no".** Under the action-scoped check
   (yes-path missed vs no-path refused):

   | Model | cancel: yes / no | comp: yes / no |
   |---|---|---|
   | Flash | 0/124 / 77/124 | 0/92 / 40/92 |
   | Pro | 0/124 / 69/124 | 10/92 / 84/92 |
   | Sonnet | 18/124 / 88/123 | untestable |

   - The overpaid/underpaid control rules out overpayment blindness: E ≈ C. The F-vs-E McNemar Holm p is ≤ 0.013 in
     every "path" cell (≤ 3e-4 on cancellation).
   - Same record, different answer: Flash missed 19/62 vs 0/62 (p = 8e-6).
   - Holds in Flash and Pro on **both tasks**, and in Sonnet on cancellation. For Sonnet it disappears under the
     lookup wording.
   - Both Gemma models show it on cancellation.
   - **The preregistered bar (≥3 models over ≥2 providers on both tasks) is not met.**
3. **GPT-6 Sol and GPT-6 Luna check both ways:** 0 errors on corrupted cancellation records.

## Killed claims
- "Yes-or-no wording is a general fix."
- "Replicated in Claude Sonnet" (44/62 vs 40/62 on new bases).
- "A lookup-scoped check protects both answers", and also "it never helps".
- "Literal scope explains the leak" (weakened: Pro under SN still leaks, 34/62 vs 0/62).
- "Overpayment blindness" (on the yes path).
- "Vague transfer instructions work" (Flash).
- "All models trust corrupted records."

## Write-up fixes done
- Added the Opus null.
- Deleted the pooled OR.
- Exact upper bounds replace "CI 0.0–0.0".
- Raw conversation counts 2/8 vs 1/8 reported beside the recode.
- "Untested" instead of "failed".
- Reviews marked "LLM-annotated".
- $2.29.
- Refusal rates labelled by study.
- "Effort rule held: False" fixed.
- Paper Reproducibility section rewritten.
- Stale first-commit text removed.
- README, MEMO and FINDINGS lead with the new results; the paper abstract is annotated.

## Generator status
`tau2_integrity/` (499 LOC including tests, no lookworth dependency):
- emits paired corrupt/clean native τ² Tasks via `initial_state`, with gold actions in `evaluation_criteria` and
  the policy clause shipped with the tasks;
- a 40-line shim runs them under `tau2 run`; the scorer reports pass^k plus payouts, refusals and false holds;
- 5 smoke tests pass, and the 2-episode verification passed ($0.12);
- the issue is drafted in `DRAFTS/tau2_issue.md` and **not posted**. The live repo has no new experiments.

## Résumé bullet
Built a preregistered eval of whether LLM support agents reconcile self-contradicting records (τ²-bench; 7 models,
3 providers; ~6k decisions; $38). Agents told to "recompute before deciding" missed 0–15% of corrupted payouts but
wrongly refused 56–72% of records pointing to "no" (Holm p < 10⁻³). A published prompt fix worked for Gemini Flash
but not Claude Sonnet. Shipped a τ²-native corrupted-task generator.

## Next steps
1. Run the path test as **full τ² episodes** with `tau2_integrity`: Flash and Sonnet, 20 bases, 4 trials, a
   non-Flash simulator, about $15.
2. Find a third provider that errs on both tasks.
3. Separate path from flag value in Pro and Sonnet (about $3).
4. Publish the website text (`WEBSITE_DRAFT.md`) after your review.

Files:
- `FINDINGS.md` (latest section)
- `reports/replication-table.md`
- `reports/ladder-results.md`
- `reports/progress/progress_02_*.pdf`
- `AUTONOMOUS_LOG.md`
