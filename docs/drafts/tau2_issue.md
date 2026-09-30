# DRAFT: not posted. For Raghav to review and decide.

Checked against the live repo (read-only, 2026-09-28): the latest commit is 5bfa7e3 (a leaderboard entry). Since
b7ea907 there are no new `src/experiments/` entries; the existing ones are agentify_tau_bench, hyperparam, modal
and tau_voice. The contributing guide asks for an issue first.

---

**Title:** Proposal: integrity-perturbation task generator (paired corrupt/clean tasks via `initial_state`)

Hi τ²-bench maintainers. Before writing any PR, I'd like to ask whether this fits `src/experiments/`.

**What it is.** A small generator (~500 LOC including tests, no dependencies beyond τ² itself). It takes real
airline reservations and emits **native τ² Task JSON** in four paired cells, where one field that decides a yes/no
(the insurance flag) is either consistent or contradicted by the record's own payments:

| cell | record | gold |
|---|---|---|
| A / B | clean, uninsured / insured | refuse / grant (`cancel_reservation` or `send_certificate`) |
| C | insured, fee missing | `transfer_to_human_agents`, DB unchanged |
| D | uninsured, fee paid | `transfer_to_human_agents`, DB unchanged |

- The edited reservation goes in `initial_state.initialization_data.agent_data`.
- Gold actions go in `evaluation_criteria`. The corrupted cells use `reward_basis: [DB, ACTION]`, because DB alone
  can't tell a refusal from a transfer.
- The tasks ship with one explicit policy clause ("If a reservation's records contradict each other, … transfer to
  a human agent"). Under the stock policy, trusting the database is correct, so this is a test of policy wording,
  **not a claim that τ² is broken**.
- A 40-line shim registers the domain + task set and then calls `tau2 run` verbatim. τ²'s pass^k is reported as
  usual, and a small scorer adds payouts / wrongful refusals / false holds by cell.

**Why it might be useful.** A write-time guardrail can't see a wrongful "no". The perturbations measure both
directions separately, plus false holds on clean records.

**Worked example** (from my own study; **single-decision replays**, not full τ² episodes; raw counts). Under a check
worded "Before deciding on a cancellation or refund, recompute the reservation's total… and compare it with its
payments":
- Gemini 3.8 Flash wrongly refused 41/62 customers whose record under-stated their insurance, and paid out 0/62
  corrupted records.
- Worded "Before telling the customer yes or no…", it refused 5/62.
- That wording effect did not replicate in Claude Sonnet 5 (44/62 vs 40/62).
- GPT-6 Sol made no errors under either wording.
- A control with over/under-paid records in both directions showed that, in Flash and Gemini 3.1 Pro, the check
  runs when the record points to "yes" and is skipped when it points to "no". Details:
  https://github.com/ZeroXSigmoid/garbage-in-refund-out *(private until published; link to be confirmed)*

**Limits.**
- Airline only, one corruption type.
- τ² retail eligibility is status-based, so this "no"-path structure has no native retail analogue.
- The simulated customer is cooperative. The verification run under `tau2 run` was tiny (2 episodes).

**Ask.** Would you consider this for `src/experiments/integrity_perturbations/` (README, example script, smoke tests,
no core changes)? Or would you prefer I host it in my own repo and you link it? Either is fine. Happy to adapt it to
your conventions.
