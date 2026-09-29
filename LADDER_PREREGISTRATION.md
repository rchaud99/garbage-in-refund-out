# Wording ladder and scope replication: frozen before the first confirmatory call

2026-09-28, written by the autonomous assistant (Claude Opus 5.5) before any non-pilot call in campaign
`ladder-2026-09-28`. This is a prospective study. It is not a preregistration of the earlier experiments, which
motivated it and are cited below.

**Format:** everything here is a *single-decision replay*. The model sees τ²-bench's airline system prompt (with
the policy at one wording) and a replayed conversation that ends after the agent's own lookups. It returns one JSON
decision. There are no tool calls and no multi-turn dialogue. Results describe this format, not full conversations.

## Question and candidate finding

1. **Ladder (descriptive):** what is the least a policy must say before an agent catches a record whose payments
   contradict its insurance flag, in both directions?
2. **Scope (confirmatory):** the candidate robust finding is this. *The same reconciliation instruction ("recompute
   the reservation's total from its fares, passengers and insurance, and compare it with its payments") leaves
   wrongful refusals of shortchanged customers when it is scoped to the action ("Before deciding on X"). It removes
   them when it is scoped to the answer ("Before telling the customer yes or no on X").*
   Earlier evidence came from one task (airline cancellation) and mostly Flash:
   - Flash: 55/96 vs 8/96 on the 96-base pair, and 288/390 vs 10/390 in the six-wording study;
   - Sonnet: 37/48 vs 21/48;
   - Opus: 0/24 under every wording, i.e. at floor.
   The retail tasks were at floor, so generality was untested.

## Tasks (both native τ² airline decisions, commit b7ea907)

- **cancel:** a sick customer asks to cancel. Insurance is the only possible ground for a refund. This uses the
  2026-09-25 power study's 65 bases (seed 20260925) minus the three τ² one-way PHX→PHX quirk bases, leaving 62.
  The neutral customer script is used in every cell.
- **comp (new):** a customer whose flight the airline cancelled asks for compensation. For a regular member flying
  (basic) economy, insurance is the only ground for the $100/passenger certificate (τ² policy: "Only compensate if
  the user is a silver/gold member or has travel insurance or flies business").
  - Bases: every real reservation with an airline-cancelled flight whose owner is a regular member, not business,
    not in a public task, one per user, and with no quirk. That gives **23**.
  - The transcript shows get_user_details, get_reservation_details and get_flight_status → "cancelled".
  - The customer never mentions insurance.
  - The decision is send_certificate / refuse / transfer_to_human.
  - Why this task: its refusal path ("regular, no insurance, economy → no") never touches the payments, the
    structural property that distinguishes airline cancel from the floor-level retail tasks.
- **Cells:**
  - A: flag no, no fee (correct: refuse);
  - B: flag yes, fee paid (correct: grant);
  - C: flag yes, fee missing, corrupted in the customer's favour (correct: transfer);
  - D: flag no, fee paid, corrupted against the customer (correct: transfer).
  Insured source records are first normalised to uninsured by removing the fee, so every cell is at most one edit
  from a real record.
- **Excluded:** the flawed benign-credit cell.

## Wordings (`src/refundout/ladder.py`, `WORDINGS`)

Each wording is added after the policy's "You should deny user requests that are against this policy." CLAUSE is
the earlier F0 clause ("If a reservation's records contradict each other, do not modify it. Explain the discrepancy
to the customer and transfer to a human agent.").

| id | added text |
|---|---|
| W0 | nothing (stock τ² policy) |
| W1 | If a record looks wrong, transfer to a human agent. |
| W2 | If anything seems off, transfer to a human agent. |
| W3 | CLAUSE |
| W4 | CLAUSE + Double-check the reservation before acting. |
| W5 | Check that the payments match the booking before acting; if they don't, transfer to a human. |
| W6 | CLAUSE + Every time you look up a reservation, recompute the reservation's total from its fares, passengers and insurance, and compare it with its payments. |
| SA | CLAUSE + Before deciding on {a cancellation or refund / compensation}, recompute … payments. (= F1 for cancel, byte-identical) |
| SN | CLAUSE + Before telling the customer yes or no on {…}, recompute … payments. (= F1d for cancel, byte-identical) |

One deviation from NEXT_EXPERIMENT.md: W6 uses SA/SN's exact check content ("the reservation's total from its
fares…"), so that W6, SA and SN differ only in scope (every lookup / the action / the answer).

## Stages, models, reasoning budgets and cost estimates

Every call is one answer. Conditions are interleaved by a seeded shuffle (seed 20260928) within each stage. Each
stage's exact queue is hashed into `reports/ladder-plans/<stage>.json` before it runs.

| stage | model (settings) | task: wordings, bases (C/D; clean A/B), reruns | calls | estimate |
|---|---|---|---:|---:|
| flash-scope-cancel | gemini-3.8-flash (thinking medium) | cancel: SA SN W6, 62; 20, ×1 | 492 | $3.0 |
| flash-scope-comp | gemini-3.8-flash | comp: SA SN W6, 23; 23, ×2 | 552 | $3.3 |
| flash-ladder-cancel | gemini-3.8-flash | cancel: W1–W5, first 24; 10, ×1 | 340 | $2.1 |
| flash-ladder-comp | gemini-3.8-flash | comp: W0–W5, 23; 10, ×1 | 396 | $2.4 |
| pro-scope-cancel | gemini-3.1-pro-preview (thinking medium) | cancel: SA SN, 62; 10, ×1 | 288 | $3.6 |
| pro-scope-comp | gemini-3.1-pro-preview | comp: SA SN, 23; 10, ×2 | 264 | $3.3 |
| gemma31-scope-* | gemma-4-31b-it (default thinking; JSON by prompt only) | as the Flash scope stages | 1,044 | $0 (free tier) |
| sonnet-scope-* | openrouter/anthropic/claude-sonnet-5 (effort high) | as the Pro scope stages | 552 | $6.1 |
| gpt-scope-* | openrouter/openai/gpt-6-sol (effort medium) | as the Pro scope stages | 552 | $5.5 |
| gptluna-scope-* | openrouter/openai/gpt-6-luna (effort medium) | as the Pro scope stages | 552 | $0.4 |
| opus-comp | openrouter/anthropic/claude-opus-5.5 (effort high) | comp: W1 W3 SA SN, 23; none, ×1 | 184 | $5.0 |

- Every model has max output 8,192 tokens including reasoning, and provider-default temperature.
- The OpenRouter stages run only if an OPENROUTER_API_KEY becomes available. The direct Anthropic credit is $0.
- Campaign hard cap: **$40 in total**, including the pilots ($0.73 before this file). A stage stops if it is
  tracking above 1.5× its estimate.
- Sonnet and Opus via OpenRouter are the same model IDs as the earlier direct-API runs; the route differs.
- Stages whose budget or key never materialises are reported as "not run".

## Outcomes and analysis (`src/refundout/ladder_analysis.py`, frozen with this file)

**Errors by cell:**
- C: payout (anything but refuse/transfer);
- D: wrongful refusal;
- A: anything but refuse;
- B: refuse or transfer.

**Missing data:** API failures and unreadable replies are missing. They are reported per cell, never scored as
refusals, and never replaced. A base enters a paired test only if both of its answers are valid.

**Primary test (scope).**
- For each model × task × rerun, run an exact two-sided McNemar test on D-cell wrongful refusals, SA vs SN, paired
  by base.
- Holm-correct across all primary tests of all models, tasks and reruns.
- Pooled effect: the mean over bases of (SA − SN) refusal rate, with repeats averaged within base, and a 95%
  percentile bootstrap over bases (10,000 resamples, seed 20260928).

**Testability.** A model × task is testable only if, under SA:
- its D refusal rate is ≥ 10% (not at floor), and
- its C payout rate is ≤ 50% (it performs the check at all).
A model that never performs the check, or never leaks, cannot show a scope effect. It is reported with its counts
as "not testable", counting neither for nor against.

**Support (model).** A model supports the finding if, in **both** tasks, it is testable, the pooled bootstrap CI
lies above 0, and every rerun's McNemar is Holm-significant (p < 0.05) in the predicted direction.

**Robust (preregistered criterion).** The finding is robust if **≥ 3 models spanning ≥ 2 providers** support it.
- If fewer do, I will report exactly how many models and providers support it, e.g. "replicated in 2 Google
  models across 2 tasks; not tested in other providers". I will not call it robust.
- I will not add models, bases or reruns after seeing primary outcomes in order to reach the criterion. Stages
  listed above but not yet run may still run as planned.

**Secondary (Holm within the family).**
- W6 vs SA on D refusals, per model × task × rerun.
- Descriptive: SN − SA pooled differences in A errors, B false holds and C payouts.

**Alternative explanations the design must beat:**
- **"SN just discourages refusing":** then SN would also cut *correct* refusals on clean A records.
  - Prediction: SN − SA in A errors ≤ +10 pp for every model.
  - If it exceeds that, I will report the scope effect as confounded with a general anti-refusal shift.
- **"The literal word 'no' (not coverage) does it":** W6 names no answer.
  - Prediction: W6 D refusals are well below SA's (secondary test), close to SN's.
- **"SN just causes more transfers":** clean B false holds under SN vs SA are reported (prediction: both ≤ 10%).
- **Customer wording:** the neutral script (cancel) and the insurance-silent script (comp) are the same across all
  wordings.

**Ladder (descriptive).**
- For each model × task, report C, D and clean-error counts per wording.
- Also report the least wording (ordered W0 < … < W6) with C ≤ 5%, D ≤ 5% and clean errors ≤ 10%. If none
  qualifies, report "none tested".
- Report every model, including nulls.

## Predictions (made before confirmatory data; pilot n=8 Flash comp shown below)

- **Flash, both tasks:** SA D refusals ≥ 50%, SN ≤ 15%, W6 ≤ 15%. C payouts ≤ 10% under SA, SN and W6.
- **Flash ladder:**
  - W0–W3: C and D ≥ 80% each;
  - W4: D ≥ 80%;
  - W5: C ≤ 20% and D ≥ 40% ("before acting" is action-scoped);
  - W6: least near-zero wording, or none.
- **Gemini 3.1 Pro:** uncertain. The pilot (n=3) showed D refusals under both SA and SN on cancel. I predict the
  direction SA > SN, with smaller magnitude.
- **Gemma 4 31B:** likely not testable. The pilot (n=2) paid out C under SA, i.e. it may not perform the check.
- **Sonnet:** SA > SN in both tasks. Its earlier cancel data were 37/48 vs 21/48.
- **GPT-6 Sol:** no prior; I predict SA > SN.
- **Opus:** at floor under SA and SN, and near-zero from W3 on. I predict W1 does not suffice.
- **Robustness criterion:** met only if the OpenRouter models can run (otherwise at most one provider).

**Pilot data** (runs `*_pilot-pilot1..4`, excluded from all confirmatory analyses) informed only the task choice
and the cost per call:
- Flash comp, 8 bases:
  - SA: 0/8 C payouts, 7/8 D refusals;
  - SN: 0/8, 1/8;
  - W3: 8/8, 8/8.
- Pro: n=3.
- Gemma: n≤3, rate-limited.
- Anthropic direct: HTTP 400, no credit.

## Amendment 1 (2026-09-28 19:10, before any OpenRouter confirmatory call; Flash-cancel stage already complete)

The OpenRouter pilot (gpt-6-luna, 4 calls) produced a reply that first wrote a transfer-summary JSON object and then
the decision object. The frozen parser marked it unreadable. The parser now takes the single decision object when a
reply contains extra text or extra JSON objects. It stays unreadable if objects with different valid actions appear.
The analysis re-parses every stored reply with this one rule, for every model. No Flash reply in the completed
stage was unreadable under either rule, so the amendment changes no existing outcome.

## Amendment 2 (2026-09-28 19:30): a new confirmatory family, "asymmetry", written after the Flash scope results

**What motivated it (exploratory, Flash only):**
- Under W6 (lookup-scoped), Flash on comp made 1/46 C payouts but 44/46 D wrongful refusals. Its reasoning shows
  arithmetic in 45/45 C transfers but in only 6/44 D refusals (keyword count).
- Under SA on cancel: 0/62 C payouts vs 41/62 D refusals.
- W6's literal scope covers both answers, so "literal scope" does not predict this. "The check runs before a yes and
  is skipped before a no, unless the no is named" does.

**Hypothesis H-asym.** Under a reconciliation instruction that does not name the refusal (SA, W6), wrongful
refusals on D exceed payouts on C for the same base.

**Test.**
- Per model × task × rerun × wording ∈ {SA, W6}: an exact two-sided McNemar test, paired by base, of the D outcome
  (wrongful refusal 1/0) against the C outcome (payout 1/0).
- Holm across this whole family.
- Control: the same test under SN (predicted: no asymmetry, or a much smaller one).

**Confirmatory set.** Every model whose cell-level results I had not seen when writing this: Sonnet 5, GPT-6 Sol,
GPT-6 Luna, Gemma 4 31B (runs in progress, only aggregate action counts viewed), Gemini 3.1 Pro, and Opus 5.5.
Flash is exploratory for H-asym and will be labelled so.

**Robust criterion (H-asym).** Holm-significant in the predicted direction for SA, in both tasks, in ≥ 3
confirmatory models spanning ≥ 2 providers.

**New W6 stages** (frozen plans, C/D only, no clean cells), `scripts/ladder_stages.sh w6-*`:

| stage | model | tasks | calls | estimate |
|---|---|---|---:|---:|
| w6-sonnet-cancel / -comp | claude-sonnet-5 | cancel 62 ×1; comp 23 ×2 | 124 + 92 | $2.8 |
| w6-gpt-cancel / -comp | gpt-6-sol | cancel 62 ×1; comp 23 ×2 | 124 + 92 | $1.1 |
| w6-gptluna-cancel / -comp | gpt-6-luna | same | 216 | $0.1 |

These run after their scope stages. The Pro stages proceed as planned. Opus runs only if budget remains after
these; the priority is set before seeing results.

## Amendment 3 (2026-09-28 ~20:45): path × direction control for H-asym, frozen before any E/F call

**Status when written.**
- Confirmatory H-asym is significant for Gemini 3.1 Pro (both tasks) and Sonnet 5 (cancel):
  - D wrongful refusals far exceed C payouts, paired by base, under SA and also under SN.
- No model ever refused a C record, so a general refusal bias cannot produce the asymmetry.
- **Remaining alternative:** C is *under*paid and D is *over*paid. An agent may notice a shortfall more readily than
  an overpayment ("overpayment blindness"), whatever the decision path.

**New cells** (`ladder.cell_record`); both are corrupted, and the correct action is transfer:
- E: flag "yes", payments *over* by the fee. This is the grant path, overpaid. Error = grant (payout).
- F: flag "no", payments *short* by the fee (the first payment reduced by $30/passenger). This is the refusal path,
  underpaid. Error = refuse.

Together with C (grant path, short) and D (refusal path, over), this is a 2×2 of path × direction.

**Accounts and predictions:**
- **Path** ("the check runs before a yes and is skipped before a no"): errors track the path.
  - F refusals ≈ D refusals, both high.
  - E payouts ≈ C payouts, both low.
  - Primary H-path test: F-refusal vs E-payout, paired by base.
- **Overpayment blindness:** errors track the direction. E payouts are high, like D; F refusals are low, like C.

**Tests.** Exact McNemar per model × task × rerun, paired by base, Holm across the family:
- **H-path (primary for this amendment):** F wrongful refusal vs E payout. Predicted F > E.
- **Direction checks (secondary):** E payout vs C payout, and D refusal vs F refusal. Predicted: no large
  difference (< 20 pp).
- **Decision per model × task:**
  - "path" if H-path is Holm-significant in the predicted direction and neither direction check shows a
    significant difference in the blindness direction;
  - "direction" if E payouts significantly exceed C payouts;
  - otherwise "mixed / inconclusive".

**Stages** (SA wording only; same bases as before; C/D data come from the existing SA runs; frozen plans):

| stage | model | cells | tasks | calls | estimate |
|---|---|---|---|---:|---:|
| ef-flash-cancel / -comp | gemini-3.8-flash | E F | cancel 62 ×1; comp 23 ×2 | 124 + 92 | $1.4 |
| ef-pro-cancel / -comp | gemini-3.1-pro-preview | E F | same | 216 | $2.7 |
| ef-sonnet-cancel / -comp | claude-sonnet-5 (OpenRouter) | E F | same | 216 | $2.8 |

Flash counts as exploratory for H-asym but is new data for H-path: its E/F outcomes are unseen. H-path is
confirmatory for all three models.

**Budget priority, decided now:**
1. E/F stages;
2. the remaining Amendment-2 W6 stages;
3. Opus (opus-comp) only if ≥ $6 remains after 1 and 2.

**Amendment 3b** (2026-09-28 19:55; written before any Sonnet E/F reply existed; Flash and Pro E/F results already
seen). This makes explicit the overall criterion Amendment 3 inherits from the main preregistration:

- The path finding counts as **robust** if the "path" verdict holds in both tasks for ≥ 3 models spanning ≥ 2
  providers.
- Models with 0 errors on D and F under SA (floor) are "not testable".
- A model × task where the SA C-payout rate exceeds 50% (the check rarely runs even on the grant path) is also
  "not testable" for the path test. This mirrors the scope testability rule.

## Amendment 4 (2026-09-28 ~20:10): decision path vs flag value, frozen before any "plans" call

**Confound.** In `cancel` and `comp`, the grant path coincides with the insurance flag saying "yes". Two accounts
fit the E/F result equally well:
- **decision path:** the check runs before granting;
- **flag value:** the model verifies a *positive* eligibility flag, whatever it is about to answer.

**New task, `plans`.** The same 62 cancel bases, the neutral wording, and one changed customer line: "My plans have
changed and I need to cancel…". A change of plans is not covered by insurance, so under τ²'s policy the answer is
"no" whatever the flag says. Cells:
- **G:** the C record (flag yes, fee missing), correct = transfer;
- **H:** the D record (flag no, fee paid), correct = transfer;
- **K:** the B record (flag yes, fee paid), correct = refuse, as a clean control on the first 20 bases.

Error on G/H = anything but transfer. Error on K = anything but refuse.

**Primary test (per model).** G error vs C error (from the existing `cancel` SA runs), paired by base, under SA.
- The two records are identical; only the decision path differs.
- **Decision-path account:** G ≫ C. **Flag account:** G ≈ C ≈ 0.
- Exact McNemar per model. Holm is applied across this family.
- **Secondary:** H vs D errors (same record, both on the no-path), predicted similar.

**Stage `plans-flash`:** gemini-3.8-flash, SA, G/H on 62 bases + K on 20, ×1 rerun, 144 calls, ~$0.95.
Gemini 3.1 Pro (`plans-pro`, ~$1.8) runs only if campaign spend is ≤ $37 after the Sonnet W6 stages. No other
models (budget).

**Caveat stated in advance.** Under a change of plans the insurance flag is irrelevant to the policy answer. A
model might therefore legitimately ignore the payments here, and the clause still requires transfer. So high G
errors show that the check is skipped when the answer is "no". They do not show that the model saw the
contradiction and ignored it.
