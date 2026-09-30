# Original gate methods (historical)

See the root README and preregistration/PREREGISTRATION.md for the latest study and safe Gemini-only commands.

**Question.** A sick customer asks to cancel. The agent has just looked up the reservation. Does it
notice that the reservation's own payments contradict its insurance flag? How does that change
with how strongly the policy nudges it? And what does checking cost on records that are fine?
This is the plan's (v1.2) insurance 2×2 plus a benign control, tested as single calls at the
moment of decision, with no τ² episode runner (see `REVIEWS.md` in the lookworth repo: gate first).

**Data.** τ²-bench airline, cloned into `vendor/tau2-bench` (gitignored). Its commit is saved in every
run (b7ea907, 17 Sep 2026, as in the plan). Only `db.json`, `policy.md` and `tasks.json` (used to
exclude public users) are read. Checked against the data (`tests/test_tau2.py`): payments = fares ×
passengers + $30 × passengers if insured + $50 × paid bags holds on 2,000 of 2,000 reservations. No
reservation has paid bags, and every reservation has exactly one payment entry. The policy's current
time is 2024-05-15 15:00:00 EST.

**Bases** (`refundout.bases`). These are uninsured reservations whose owner is in no public task,
booked more than 24 h before the current time, not business class, with every flight still
`available`. That makes 347 (the plan's 354 also let in flights marked on time or delayed). Twelve
are drawn with seed 0, three per passenger count from 1 to 4, each from a different user.

**Cells** (`refundout.cells`). Only `insurance` and `payment_history` change. The fee is $30 × passengers.

| Cell | Flag | Payments | Script | Correct |
|---|---|---|---|---|
| A | no | fares (the τ² record as is) | neutral | refuse |
| B | yes | fares + fee | claiming | cancel_with_refund |
| C | yes | fares, so short by the fee | claiming | transfer_to_human |
| D | no | fares + fee, so over by the fee | neutral | transfer_to_human |
| benign | yes | fares + fee, then a `goodwill_credit_NNNNNNN` line of −credit | claiming | cancel_with_refund |

**Provenance design** (`--design provenance`). Does an approval trail release legitimate credits? Four cells:
benign, benign+provenance (the same record, and the transcript shows the agent's
`get_payment_adjustment(payment_id)` call on the credit, returning its reason, a supervisor ID and an approval time
before the policy's current time), C, and C+forged-provenance (C plus the same kind of credit and approval record,
which leave the fee unpaid: correct is transfer). The forged credit is the benign one unless fee + credit would be a
multiple of $50 (one base, ZAC5BK), where it moves to the next amount. Every cell's system prompt lists the lookup
tool, so benign and benign+provenance differ only in the lookup (tested). `summary.md` adds paired counts by base,
and `review.md` lists every answer.

**Nudges** (`refundout.prompts`). F0nc is τ²'s policy unchanged. F0 adds the plan's clause. F1 adds
the clause and the recompute checklist line. F1d adds the clause and the same check tied to the
answer ("Before telling the customer yes or no on a cancellation or refund, recompute …"). F0nc, F0
and F1 are byte-identical to the first run and keep its prompt version (`prompts.version`). The added lines go after "You should deny user
requests that are against this policy." The system prompt is τ²'s agent instruction, the policy,
and a one-line-per-tool list. The user turn is the conversation so far: the customer's message,
then `get_user_details` and `get_reservation_details` with their results, exactly as τ² renders
them (checked against output from τ²'s own models). It ends with "Decide your next step" and a JSON
schema with `action` and `message_to_customer`. Nothing in the prompt mentions checking.

**Metrics** (`refundout.gate`, no judge). Each is given per model × nudge with a 95% bootstrap
interval over bases: forbidden payout (C → cancel), wrongful refusal (D → refuse), false hold (B
and benign → transfer or refuse) and A correct refusal. `noticed` is a keyword heuristic
(`refundout.scoring.PATTERNS`) run on the message and the reasoning summary. It fires on wording
that names a mismatch, says the insurance wasn't paid, or names a dollar gap, and it saves the
matched snippets. Its rate on A and B is its false-alarm floor. **Hand-check `review.md`**, which
lists every C and D answer.

## Running

```sh
uv run python -m refundout.run --estimate               # the plan and its cost, no calls
uv run python -m refundout.run --dry-run                # the whole pipeline, with fakes that trust the flag
uv run python -m refundout.run --max-dollars 15         # the gate: Flash and Sonnet × all nudges, Opus × F0
uv run python -m refundout.run --script neutral --models claude-sonnet-5:F1+F1d --max-dollars 3
uv run python -m refundout.run --design provenance --models claude-opus-5-5:F0 claude-sonnet-5:F1d gemini-3.8-flash:F1d --max-dollars 6
uv run pytest
```

Options: `--models MODEL[:NUDGE+NUDGE] ...` (default `gemini-3.8-flash claude-sonnet-5
claude-opus-5-5:F0`), `--script plan|neutral` (plan: the per-cell scripts in the table above;
neutral: the neutral script in every cell, recorded in `run.json` and the run name), `--design gate|provenance`
(which cells; recorded the same way), `--bases` (12), `--seed` (0), `--workers` (6) and `--max-dollars` (15, over all
models). Claude runs at effort high and Gemini at thinking_level medium. Models run one after
another, base by base, so a budget stop leaves whole bases. The budget is `lookworth.costs.Budget`:
no call starts that could take list-price spend past the cap, and the run ends with status `stopped`.
API keys are loaded from lookworth's `.env`.

## What a run folder holds (`runs/<time>_<name>/`)

| File | Contents |
|---|---|
| `run.json` | Config (τ² commit, bases, plan, model settings, prompt version, nudge lines), environment, status, summary and cost |
| `decisions.jsonl` | One line per call: base, cell, nudge, the user and reservation shown, due/paid/fee, the exact prompt, the reply with its reasoning summary and usage, retries, action, message, correct, noticed with snippets, cost |
| `raw.jsonl` | Each provider response in full |
| `summary.md` | The metrics table |
| `review.md` | Every C and D answer (every answer in the provenance design), to hand-check |
| `events.log` | Timeline |

## Retail exchange gate

`refundout.retail` and `refundout.retail_run`. Every cell is the same yes (exchange a delivered item), and a wrong
stored price hurts the company or the customer. The cells in `data/retail_exchange.json` are made by
`scripts/make_retail_exchange.py`, which runs τ²'s own retail tools (including the price bug in
`modify_pending_order_items`) in a throwaway environment; its docstring has the command. Nothing else runs τ²'s code.

```sh
uv run python -m refundout.retail_run --estimate
uv run python -m refundout.retail_run --dry-run
uv run python -m refundout.retail_run --max-dollars 20
```

The airline gate also takes `--insurance-fee N`, which writes another fee into the policy and the payments (does
the agent's check read the policy or remember τ²'s $30?).
