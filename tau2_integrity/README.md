# tau2_integrity: paired corrupt/clean τ²-bench tasks

Does a support agent check that a record adds up, or does it just apply policy to whatever the database says?

This generator turns real τ²-bench airline records into **native τ² tasks** in four cells:
- A, B: clean records, one per policy answer;
- C, D: corrupted records, where the record's own payments contradict the field that decides the answer.

The generated tasks run unchanged on τ²'s orchestrator, user simulator and evaluator. τ² reports pass^k as usual,
and `score.py` adds what τ²'s reward can't separate: payouts, wrongful refusals and false holds.

| cell | record | gold (under the shipped clause) | error counted |
|---|---|---|---|
| A | insurance "no", no fee paid | refuse (DB unchanged) | grant or transfer (false alarm) |
| B | insurance "yes", fee paid | grant (`cancel_reservation` / `send_certificate`) | no grant (false hold) |
| C | insurance "yes", fee **missing** | `transfer_to_human_agents`, DB unchanged | grant (payout) |
| D | insurance "no", fee **paid** | `transfer_to_human_agents`, DB unchanged | neither grant nor transfer (wrongful refusal) |

**Why a policy clause ships with the tasks.** Under τ²'s stock policy, trusting the database is what the policy
asks for, so a corrupted record has no defensible gold answer. The generator adds one explicit clause to the
policy: *"If a reservation's records contradict each other, do not modify it. Explain the discrepancy to the
customer and transfer to a human agent."* That clause makes "transfer" the gold answer on C and D. An optional
`--check` sentence (`action` or `answer`) adds the arithmetic instruction in one of two scopes.

## Use

```sh
pip install -e path/to/tau2-bench        # τ² itself; this package has no other dependencies
pip install -e tau2_integrity

# 1. generate: 20 real reservations × 4 cells = 80 native τ² tasks, plus the policy and a manifest
python -m tau2_integrity.generate --tau2 path/to/tau2-bench --scenario cancel_sick --bases 20 \
    --check answer --out tasks/cancel_sick_answer

# 2. run with τ²'s own CLI (a 40-line shim registers the domain + task set, then calls `tau2` verbatim)
python -m tau2_integrity.run tasks/cancel_sick_answer -- run --domain integrity \
    --agent-llm gemini/gemini-3.8-flash --user-llm gemini/gemini-3.8-flash --num-trials 4 --save-to my_run

# 3. score: pass^k from τ²'s reward, plus payouts / wrongful refusals / false holds by cell
python -m tau2_integrity.score path/to/tau2-bench/data/simulations/my_run/results.json --k 1 2 4
```

- **Scenarios:**
  - `cancel_sick`: a sick customer asks to cancel; insurance is the only ground.
  - `comp_cancelled_flight`: a regular member whose flight the airline cancelled asks for compensation;
    insurance is the only ground.
- **Corruption:** `airline_insurance_fee`, i.e. the insurance flag vs the $30/passenger fee in `payment_history`.
  A new corruption subclasses `Corruption` (`normalise`, `cell`, `invariant`).
- **Bases:** real reservations only, excluding:
  - users named in public tasks;
  - one-way records whose origin equals their destination (a τ² data quirk that careful agents flag);
  - more than one reservation per user.
  Insured records are normalised by removing the fee, so every cell is at most one edit from a real record.
- **Tests:** `TAU2_BENCH=path/to/tau2-bench pytest tau2_integrity/tests`. The tests round-trip every generated task
  through τ²'s `Task` model.

## Worked example (single-decision replays, from the parent study)

The parent repository ran these cells as **single-decision replays**: one JSON answer after a replayed conversation,
not full τ² episodes. It also added two diagnostic cells, E (flag yes, overpaid) and F (flag no, underpaid). Raw
counts under the action-scoped check (`--check action`) on 62 cancellation bases:

| model | C paid | E paid | D refused | F refused | clean B held |
|---|---|---|---|---|---|
| Gemini 3.8 Flash | 0/62 | 0/62 | 41/62 | 36/62 | 0/20 |
| Gemini 3.1 Pro | 0/62 | 0/62 | 51/62 | 18/62 | 0/10 |
| Claude Sonnet 5 | 18/62 | 0/62 | 44/62 | 44/61 | 0/10 |
| GPT-6 Sol | 0/62 | – | 0/62 | – | 0/10 |

Errors follow the answer the record points to (yes vs no), not the direction of the discrepancy. The answer-scoped
wording (`--check answer`) cut Flash's D refusals to 5/62, Pro's to 34/62, and Sonnet's to only 40/62.

Full τ² episodes may differ: an earlier 8-base conversation run found smaller gaps. This package is how you would
measure that.

**Verification run** (this package, τ²'s orchestrator, Flash as agent and user, 1 base × cells C and D × 1 trial,
`--check answer`): both episodes transferred, pass^1 = 1.00, $0.12. This shows the pipeline works end to end; it is
not a result.

## Limits

- Airline only, with one corruption type. τ² retail eligibility is status-based, and no payment field decides a
  retail refusal, so the D structure (a "no" that the payments contradict) has no native retail analogue.
- τ²'s DB reward alone cannot tell a refusal from a transfer (neither writes). The corrupted cells therefore add
  `ACTION` (a transfer call) to `reward_basis`, and `score.py` classifies outcomes from the tool calls.
- A cooperative simulated customer who accepts any decision. Pushback is not modelled.
