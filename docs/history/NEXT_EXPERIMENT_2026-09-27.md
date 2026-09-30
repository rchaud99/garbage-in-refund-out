> **Superseded — kept for the record (parked plan of 2026-09-27; it was run as the 2026-09-28 wording ladder).** Current results: [README](../../README.md) and the top section of
> [FINDINGS.md](../../FINDINGS.md).

# Next experiment when we return (parked 2026-09-27)

Read this and `REVIEW_2026-09-27.md` before doing anything else on this project.

## The question to answer
What is the **least** you have to tell an agent before it reliably catches a record whose payments can't add up?
Is there a realistic, bare-bones instruction a human would actually write that still fails?

## What we already know (single-decision airline replays; C = corrupted in the customer's favour, D = corrupted against them)
- **Stock τ² policy:** nobody checks. 0/72 airline, 1/144 retail. This is a trust rate, not an error rate: the policy
  never asks for audits.
- **Bare-bones clause only** (F0): "If a reservation's records contradict each other, do not modify it. Explain the
  discrepancy to the customer and transfer to a human agent." 12 bases, one decision each:
  - Sonnet 5: C payouts 100%, D wrongful refusals 100%. Fails completely.
  - Gemini 3.8 Flash: C 92%, D 100%. Fails.
  - Opus 5.5: C 0%, D 0%. Works.
  - This is the realistic "bare minimum that still fails" case, but at n=12 only.
- **Flash with the explicit arithmetic recipe** ("recompute the total from fares, passengers and insurance, and
  compare it with its payments"):
  - scoped "before deciding on a cancellation or refund": C 0/96, D 55/96;
  - "before telling the customer yes or no": C 0/96, D 8/96;
  - "never refuse without first recomputing": 0/96 and 0/96.
  - So Flash needs clause + explicit arithmetic + scope covering both answers.
- **Sonnet 5:** nothing tried made it reliable. C payouts were 31–38% under every wording. Best D was 21/48; F1n gave
  D 22/48 and C 15/48.
- **The ledger** (arithmetic done in code, output states "payments do not reconcile"): Flash 24/24 in both
  directions. Never run on Sonnet. Caveat: the ledger prints the verdict, so it tests reading, not checking.
- **Unknown:** everything between "vague clause" and "full arithmetic recipe". We never tried a check tied to
  *reading* the record ("every time you look up a reservation…").

## Planned run: a wording ladder
Six wordings, each added to the policy:
1. "If a record looks wrong, transfer to a human agent."
2. "If anything seems off, transfer to a human agent."
3. The existing F0 clause ("records contradict each other…").
4. "Double-check the reservation before acting."
5. "Check that the payments match the booking before acting; if they don't, transfer to a human." (names payments,
   no arithmetic)
6. "Every time you look up a reservation, recompute its total from fares, passengers and insurance, and compare it
   with its payments." (lookup-scoped, explicit)

Plus **Sonnet with the ledger**, and the intermediate wording 5 for both models.

- **Models:** Flash and Sonnet (full ladder), Opus optional (wordings 1, 3 and 6). Claude runs through OpenRouter,
  because the Anthropic card is blocked; this needs an adapter in lookworth or the harness.
- **Cells:**
  - C and D on the 65 power-study bases;
  - clean A and B on about 20 bases, for false alarms;
  - drop the flawed benign-credit cell. Its credit line uses a payment_id not in the user's methods, which is a
    second anomaly.
  - Exclude the τ² one-way PHX→PHX quirk bases (FMQD8I, ZYD2S9, LH9KMJ, K2LPTR, 3SHBFW, MQS6FV).
- **Lessons from the review to apply:**
  - Preregister the predictions and analysis first.
  - Pilot for ceiling/floor before freezing; don't freeze a design already known to be at ceiling.
  - Interleave the conditions.
  - Count errors as missing, don't drop them.
  - Match reasoning budgets across models, or record them.
  - Report every model, including nulls.
  - Say "single-decision replay" up front.
  - Report both directions (C and D) and false alarms.
- **Cost estimate** (per-call costs from earlier runs: Flash ≈ $0.006, Opus ≈ $0.027):

  | Run | Estimate |
  |---|---|
  | Flash, full ladder | ~$6 |
  | Sonnet, full ladder + ledger | ~$15 |
  | Opus, 3 wordings | ~$14 |

  Start with Flash; add the others if the ladder shows a spread.
- **Output:** for each model, the least instruction that gets near-zero C payouts and D wrongful refusals, with false
  alarms on clean records.

## Also pending (free, no new runs)
Fix the write-ups per `REVIEW_2026-09-27.md`:
- add the omitted Opus null (0/24 under every wording, run 151002);
- delete the pooled OR;
- change "CI 0.0–0.0" to upper bounds;
- report the conversations as raw 2/8 vs 1/8 alongside the recode;
- "untested", not "failed", for generality and effort;
- call Codex reviews "LLM-annotated";
- $2.29; paper Reproducibility section; stale "first commit" text; the `lookworth` sibling dependency blocks `uv sync`.

## Interview framing
"I wanted to know whether AI support agents check that a record adds up, or just apply policy to whatever the
database says. Guardrails sit at the write step, so a customer wrongly refused because of a bad record is invisible
to them."

## τ²-bench upstream contribution (after Freehand)
1. **Open an issue first** (their contributing guide asks for it; ~30 min). Propose a "data-integrity perturbations" experiment: a generator of corrupted tasks via `initial_state`, plus scoring (payout, wrongful refusal, transfer, names the discrepancy). Ask whether they want it.
2. **If yes, 3–4 days:**
   - (a) run on τ²'s own orchestrator, with no `lookworth` dependency;
   - (b) honest README: strong in single-decision airline replays (57% vs 8%, 96 records; Opus unaffected), weak or noisy in conversations (raw 2/8 vs 1/8);
   - (c) apply the write-up fixes from REVIEW_2026-09-27.md;
   - (d) one command to generate tasks, one to run, a small results table.
3. **Value:** name in a widely used benchmark repo, and a relationship with Sierra (a referral path).

### Quality-bar check (from the local clone b7ea907, 17 Sep 2026)
- **Existing experiments:**
  - hyperparam: CLI, demo.sh, 224-line README, ~3.4k LOC;
  - agentify_tau_bench: own pyproject, lock file and tests;
  - modal: 39-line README, ~280 LOC;
  - tau_voice: no README.
- **Stated bar:** README, example scripts, basic tests, self-contained, core-compatible, issue first, branch `experiment/<name>`.
- **What to take from it:**
  - The bar is moderate and meetable.
  - ALL history is maintainer-authored infrastructure (Keshav Dhandhania, Victor Barres), with no external research experiments. The question is FIT, not quality, so the issue first is essential.
  - Frame it as a reusable tool (a corrupted-task generator plus scoring), with the findings as example results.
  - Offer the fallback: host it in our own repo and link it.
  - Check the live repo for newer experiments before writing the issue.

### Simulated maintainer review (2026-09-27)
- **Verdict:** pass on merging the study; "host it yourself, we'll link it". They WOULD review a small **integrity-perturbation task-set generator**: any airline/retail tasks plus a corruption spec, emitted as paired corrupt/clean native Task JSON via `initial_state`, gold actions in `evaluation_criteria` (from an explicit policy clause shipped with the tasks), run unchanged under `tau2 run`, reported as pass^k and false holds, ~500 LOC, no lookworth dependency, smoke tests, README with the wording result as a worked example (raw counts).
- **Red flags to fix before ANY public link:**
  - the docs quote different refusal rates without saying they come from different studies (57/8 for the 96-base pair; 73.8/2.6 for the six wordings; 17 for 12 bases);
  - the README still has OR≈5000 and "CI 0.0–0.0";
  - "effort rule held: False";
  - the Opus null is omitted;
  - the conversation recode.
- **Framing:** under the stock policy, trusting the DB is CORRECT (a trust rate), so this is a test of policy wording, not a benchmark hole.
- **Advice:** the issue is worth 30 min; spend 3–4 days only on a positive reply, and then build the generator (the FDE skill: turning a failure into an eval inside the client's own harness).
