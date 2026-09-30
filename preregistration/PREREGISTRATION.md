# Wording power study — frozen before the first power-study API call

2026-09-25. Model: gemini-3.8-flash, medium thinking, provider-default temperature,
8,192 maximum output tokens including reasoning. This is a prospective extension of already observed
single-decision results, not a preregistration of the earlier experiments. No Claude calls.

Hypothesis: action-tied instructions leave more wrongful refusals than answer-tied instructions on
corrupted records whose displayed eligibility field points to no. Bad payouts differ little; no
numerical equivalence margin is specified, so absence of significance will not establish equivalence.

## Fixed design

65 airline bases; 30 orders per corrupted retail-cancel family; 43 orders per corrupted retail-return
family. Both directions of one-field corruption, six wordings, two independent calls per item.
Five bases/orders per clean family per task. Total: 3,672 calls. Selection seed and call-order seed:
20260925. No changes based on observed power-study outcomes, no optional sample-size extension.

The requested 150–200 airline and about 100 orders per retail family would exceed the cap at the high
cost estimate. Retail also has only 78 eligible processed orders after selecting one per user.
The final approximately proportional reduction (airline 150 → 65, cancel 70 → 30, return 100 → 43)
has a $29.83 typical / $44.97 high estimate, plus completion of interrupted Gemini decisions.
The $50 cap applies jointly to all new calls in this campaign; historical spend is reported separately.
All calls reserve a conservative input/output upper estimate; uncertain failures consume their reserve.
No API retries. Stop new submissions on the first API error; save already in-flight responses.

All old prompt bytes remain unchanged. New check instructions follow the contradiction clause.
Within a task only the trigger changes; check content, customer transcript, tool list and response
schema remain fixed across wordings. Three action triggers: before deciding, before processing,
when carrying out. Three answer triggers: before telling yes/no, before any eligibility answer yes/no,
whether granting or refusing. Exact strings and item/prompt hashes: `reports/power-plan.json` and
`src/refundout/power.py`.

Airline: existing insurance/payments cells A–D, neutral customer script. Selection is from the same
347 eligible reservations; some bases overlap historical runs, but no historical responses enter the
primary study. Retail cancel: pending/processed status; retail return: delivered/pending status.
Retail uses the explicit two-way rule: pending iff no tracking. Each corrupted version changes only
status. It is a benchmark-specific invariant, verified on all 1,000 source orders, not a production
claim about shipping systems. Retail tasks share this invariant and domain; they do not establish
independent mechanism or three-domain generality. Distinct selected users across retail bases.

## Outcomes and analysis

Primary outcome: action == refuse on corrupt_no. Treatment: action (1) versus answer (0).
Mixed-effects logistic model:
`refusal ~ action + (1 | base/order) + (1 | paraphrase) + (1 | task)`.
Base IDs are task-qualified. Paraphrases are the six trigger templates shared across tasks, with three
nested in each wording type. Fit by maximum likelihood using Laplace integration of normal random
intercepts. Report action/answer odds ratio and approximate 95% Wald confidence interval, with
variance estimates, optimizer diagnostics and singular/boundary fits. Check multiple starting points.
If the pooled model is unidentifiable, does not converge, or has unusable information, report the
primary criterion as not established rather than substitute a favorable analysis. Three tasks and
six paraphrases give weak information about generality beyond these selected levels.

Decision rule: claim support across these tested tasks only if the pooled 95% CI for the action/answer
OR excludes 1 in the predicted direction AND the raw action-minus-answer refusal rate is strictly
positive in at least two of the three tasks. Otherwise call the finding task-specific/not generalised.
Always identify this extension as Flash-only and single-decision evidence.

For each task × wording type and task × individual paraphrase, report exact counts, number of
independent bases/orders, and 95% percentile cluster-bootstrap intervals (10,000 resamples, fixed
seed 20260925). Resample bases with repeats and wordings together. Report paired type differences.
Bad payout/approval = grant action on corrupt_yes (return offers authorize a return, not an immediate
payment). False holds = refusal or transfer on clean_yes; separately report transfers on clean_no and
all control errors. Report unparseable and failed calls separately, excluding them from behavioral
rate denominators; report missingness by cell and do not replace failed observations.
At zero/all-one outcomes the nonparametric bootstrap degenerates; explicitly flag this and do not
interpret [0,0] as a bound on the population error probability.

Read 10 reasoning summaries per task × wording type × corrupted direction (120 total), deterministic
sample selected independently of outcomes. Classify explicit arithmetic/tracking comparison, mere
instruction repetition, or no visible check. These are model-generated summaries, not complete
internal reasoning or independent proof of mechanism. Save excerpts, IDs and manual annotations.

Sensitivity: per-paraphrase differences, paired task bootstrap, and fixed-task/wording descriptives.
No post-hoc hypothesis will be labeled preregistered. Full-conversation results remain a separate
study with a different customer script and sample size.
