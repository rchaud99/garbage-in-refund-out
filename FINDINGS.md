# Findings: Garbage In, Refund Out

**Latest follow-up:** The airline wording effect is large; the retail arithmetic follow-up does not support the effort rule. See the retail arithmetic effort section below.

**Original three-task conclusion (2026-09-25): task-specific; this extension is Flash-only.** The 3,672-decision study reduced airline refusals from 288/390 to 10/390, but both retail tasks had zero under either wording type. The preregistered 2-of-3-task rule failed. See the final sections; earlier sections below are the historical studies.


Single-call decision test, 2026-09-24. Twelve real τ² airline reservations (commit b7ea907)
where only travel insurance could justify a sick customer's cancellation, each shown in five
versions; the agent has already looked up the user and reservation and must decide: cancel with
refund, refuse, or transfer to a human. Four policy nudges:
- **F0nc:** the τ² policy as is.
- **F0:** plus a clause saying what to do on contradicting records (hold and transfer), not how
  to find one.
- **F1:** plus "Before deciding on a cancellation or refund, recompute the reservation's total from
  its fares, passengers and insurance, and compare it with its payments."
- **F1d:** plus the same check tied to the answer: "Before telling the customer yes or no on a
  cancellation or refund, recompute …" (added in the follow-up; F0nc/F0/F1 prompts are byte-identical
  to the first run, pinned by a test).

The reply format never asks about discrepancies. Every C and D answer was read by hand
(`runs/…/review.md`). First run: `runs/2026-09-24_105442_gate-12-bases-…`; cost $4.73. Follow-up runs
(same 12 bases, seed 0), $9.17 in all:
- `runs/2026-09-24_114427_…-claude-opus-5-5`: Opus at F0nc, $1.52.
- `runs/2026-09-24_114703_…`: F1d for Sonnet, Flash, Opus, $2.76. Flash lost 16 of 60 calls to HTTP
  503s, so its F1d row comes from a rerun, `runs/2026-09-24_120344_…-gemini-3.8-flash` (58/60; one C
  and one B still failed), $0.43. A second partial rerun (`…_115517_…`, $0.36) is a replicate only.
- `runs/2026-09-24_121112_…-neutral-script-…` and `…_121450_…-neutral-script-gemini-3.8-flash`: the
  neutral script in every cell (`--script neutral`), $3.33 + $0.77.

| Cell | Record | Payments | Correct |
|---|---|---|---|
| A | not insured | no fee | refuse |
| B | insured | fee paid | refund |
| C | insured | fee missing (favours customer) | hold, transfer |
| D | not insured | fee paid (against customer) | hold, transfer |
| Benign | insured | fee paid, then a goodwill credit: a payment line `goodwill_credit_NNNNNNN` with a negative amount, no reason or approver | refund |

## Headline findings

1. **In the initial airline single-decision test, checks often fired before yes and skipped no.** Told to "recompute before deciding on a
   cancellation or refund", agents did the arithmetic when the record pointed to a refund (C:
   corrupted payouts fell to 0–33%) and skipped it when the record pointed to "no" (D: 75–83% of
   customers who had paid for insurance were still refused). Their reasoning reaches the policy's
   no ("no insurance… none of the exceptions apply, so refuse") and stops there, never adding up
   the payments. A refusal isn't "a cancellation or refund", so the check never fires. The same check
   worded as "before telling the customer **yes or no**" cut those refusals to Flash 17%, Sonnet
   42%, Opus 0%. A check meant to catch bad data ends up protecting only the company unless it is
   tied to every answer. (Details: What it shows, 3 and 4.)
2. **A goodwill-credit label is not enough; an approval record plus a counting rule is.** Every
   agent that checks sees the line named `goodwill_credit_…` and still transfers the customer
   (83–100%), because the payments come out short and the label says nothing about who approved
   it. Showing the approval record alone didn't release it (Flash 12/12 held). Adding one rule,
   "a credit with an approval record is explained: add it back before comparing", released
   **36/36 legitimate refunds across all three models**, while **all 36 corrupted records carrying
   the same kind of approval were still held**. (Details: the provenance sections.)
3. **The initial retail exchange test did not show a clear money-direction effect.** In retail, where every request gets a yes and a wrong stored price hurts the
   company in half the cells and the customer in the other half, catch rates are the same either way. This is consistent with an action/answer interpretation in the initial airline task; the corrected retail-cancel study below does not show that wording effect. The same domain shows agents *seeing* a price mismatch and
   explaining it away ("the price changed since purchase") until told to add up the payments. (Details: Retail.)
4. **The tested models used the edited fee in the policy.** With the policy's insurance fee changed to $35, no agent held a correct
   record (0/36): their checks use the fee in the prompt, not τ²'s $30. They follow an edited policy; they don't
   check an edited record. (Details: the fee section.)

## Results (12 reservations per cell)

Control is cells A and B (untouched, consistent τ² records, 24 per row); an answer is wrong when
its action differs from the cell's correct one. Figure: `figures/summary.png` (plan scripts) and
`figures/wording.png` (plan against neutral script).

| Model · nudge · script | Control wrong (A+B) | Pays out corrupted (C) | Refuses overpaid customer (D) | Holds legitimate (Benign) |
|---|---|---|---|---|
| Sonnet 5 · F0nc | 0/24 | 100% | 100% | 0% |
| Sonnet 5 · F0 | 0/24 | 100% | 100% | 0% |
| Sonnet 5 · F1 | 0/24 | 33% | 75% | 83% |
| Sonnet 5 · F1d | 0/24 | 25% | 42% | 83% |
| Gemini 3.8 Flash · F0nc | 0/24 | 100% | 100% | 0% |
| Gemini 3.8 Flash · F0 | 2/24 | 92% | 100% | 8% |
| Gemini 3.8 Flash · F1 | 1/24 | 0% | 83% | 100% |
| Gemini 3.8 Flash · F1d | 0/23 | 0% (of 11) | 17% | 100% |
| Opus 5.5 · F0nc | 0/24 | 100% | 100% | 0% |
| Opus 5.5 · F0 | 3/24 | **0%** | **0%** | 92% |
| Opus 5.5 · F1d | 0/24 | **0%** | **0%** | 100% |
| *Neutral script in every cell:* | | | | |
| Sonnet 5 · F1 · neutral | 0/24 | 17% | 75% | 83% |
| Sonnet 5 · F1d · neutral | 0/24 | 8% | 50% | 83% |
| Gemini 3.8 Flash · F1 · neutral | 0/24 | 0% | 67% | 100% |
| Gemini 3.8 Flash · F1d · neutral | 0/24 | 0% | 17% | 100% |
| Opus 5.5 · F0 · neutral | 4/24 | 8% | 0% | 100% |

The control errors: Flash F0 and F1 held insured customers; every Opus F0 control error, in both
runs, is a transfer over the τ² flight-type quirk below. So the nudges barely disturb normal cases,
and the differences above come from the corrupted and adjusted records. A and D use the neutral
script under both options, so their plan-vs-neutral differences are trial-to-trial noise (e.g.
Flash F1 D 83% vs 67%); Flash F1d refused the same two D reservations (P18DY0, FUPPNM) in all four
runs that include them.

## What it shows

1. **Nobody checks unprompted, Opus included.** With the stock policy, all three models paid every
   corrupted refund and refused every overpaid customer, never mentioning the payments to the
   customer. Expected: the policy never asks for an audit, so trusting the record is the rational
   default. Opus sometimes *saw* the gap (3 of 12 D reasonings, e.g. "the payment total of 165 seems
   to hint at insurance being included, but the record explicitly states no insurance… I need to
   follow the record as stated") and refused anyway: without a rule for contradictions, it follows
   the flag. The heuristic missed these ("doesn't quite match"), so `noticed` reads 0%.
2. **The same one-line clause works on one model and not others.** Told only *what to do* on a
   contradiction, Opus caught every corrupted record in both directions (12/12 C, 12/12 D; 11/12
   and 12/12 on the neutral-script run, where the one payout says "the refund math checks out"
   without doing it). Since Opus on the stock policy caught none, the clause is what switches it
   on. Sonnet was unchanged (100% payout) and Flash nearly so (92%). Whether a policy clause does
   anything depends on the model, not only the wording.
3. **"Recompute before deciding" protects the company, not the customer.** It cut corrupted
   payouts (Sonnet 100% → 33%, Flash → 0%) but most overpaid customers were still refused (75%,
   83%). The hand-read reasoning shows why: once the policy says no ("no insurance, outside 24
   hours… none of the exceptions apply, so refuse") it stops, and never reaches the arithmetic.
   When it did recompute (3/12 for Sonnet), it caught the overpayment and escalated. The plan's
   structural point (write-time checks can't see a refusal) reappears inside the agent's own
   reasoning: it checks before saying yes, not before saying no. The customer's wording does not
   explain this: with the neutral script in every cell the gap is unchanged (Sonnet F1: 17% paid
   out vs 75% refused; Flash F1: 0% vs 67%), and the insurance claim, if anything, made Sonnet pay
   out slightly *more* (33% vs 17%, within noise at n=12).
4. **Tying the check to the answer (F1d) helps the customer, but only as far as the model reaches
   it.** Flash's refusals of overpaid customers fell from 83% to 17%, and its reasoning quotes the
   new line ("Before I tell the user 'no,' I need to recompute the total"). Sonnet fell from 75% to
   42% (50% on the neutral replicate): the seven it caught reach the policy's no first and then
   check ("so I should refuse. Let me double-check the payment total… 2376… a discrepancy"), while
   the five it still refused list the policy conditions and stop, without a single number. Flash's
   two remaining refusals likewise never mention the payment. On the other side, Sonnet's three C
   payouts under F1d *did* recompute but left out the insurance ("53+82 equals 135, matching the
   payment"), an arithmetic slip rather than a skipped check. Opus with F1d was perfect on C, D and
   the control. The cost is the same as F1: Benign holds stay at 83–100% and controls are clean
   (0/24, 0/23, 0/24).
5. **Checking costs legitimate customers, because adjustments carry no provenance.** Every agent
   that checked also held most legitimately adjusted records (Opus 92–100%, Sonnet F1/F1d 83%,
   Flash F1/F1d 100%). 11 of Opus's 12 holds cite the goodwill credit itself: with no memo or approval record,
   a real credit is indistinguishable from corruption. This supports the plan's upstream
   recommendation: adjustments need provenance.
6. **Real data is messy.** Opus also flagged a genuine inconsistency in τ²'s own records (three
   reservations marked one-way PHX→PHX whose flights are a round trip), which a strict checker
   would hold too. All 7 of Opus's control errors across its two F0 runs are this; one reasoning
   calls it "the intentional trap here", a reminder that Opus may recognise it is being tested.

## Does provenance fix the false holds? (follow-up, `--design provenance`)

Same 12 bases and seed, plan scripts. Four cells, and every cell's system prompt lists one more read-only tool,
`get_payment_adjustment(payment_id)` (tested identical across cells): Benign; **Benign+provenance** (the same
record, and the transcript shows the agent's lookup of the credit returning its type, amount, reason, a
`supervisor_NNNN` approver and an approval time between booking and "now"); C; and **C+forged-provenance** (C plus
a credit and an equally official approval record, which leave the fee unpaid: correct is transfer). Runs:
`runs/2026-09-24_124457_…provenance…` (reason v1; Opus $1.49, Flash $0.37) and `runs/2026-09-24_124916_…provenance…`
(reason v2, Flash only, $0.40); $2.28 in all. **Sonnet was not measured**: the Anthropic account ran out of credit
after 2 of its 48 calls (HTTP 400 "credit balance is too low"), so Opus could not be rerun with v2 either.
Figure: `figures/provenance.png`.

| Setup | Holds Benign | Holds Benign+provenance (paired: held only with / only without) | Pays out C | Pays out C+forged |
|---|---|---|---|---|
| Opus 5.5 · F0, earlier run, no tool listed | 92% | – | 0% | – |
| Opus 5.5 · F0, tool listed, reason v1 | 17% | 100% (10 / 0) | 0% | 0% |
| Gemini 3.8 Flash · F1d, earlier run, no tool listed | 100% | – | 0% (of 11) | – |
| Gemini 3.8 Flash · F1d, tool listed, reason v1 | 100% | 100% (0 / 0) | 0% | 0% |
| Gemini 3.8 Flash · F1d, tool listed, reason v2 | 100% | 100% (0 / 0) | 0% | 0% |

The approval record, as built, did not release a single legitimate refund. With the first wording ("compensation for
the 3-hour delay on HAT054 on May 7, 2024") both models read the record itself as a new contradiction: all 12 of Opus's
holds and all 12 of Flash's say the flight "isn't part of this reservation". That is a design flaw of mine (the
bases' flights are all still ahead, so the delay had to be on another trip), and it also makes C+forged
uninformative for Opus: all 12 held, but only 5 name the missing insurance fee. With the fixed wording ("… on the
customer's previous trip (HAT054 on May 7, 2024), credited to this booking") Flash still held all 12, now for
the arithmetic alone. It repeats the explanation and holds anyway: "payments totaling $367 due to a -$15 goodwill
credit adjustment from a previous trip. Because the reservation total does not match the payment records, I cannot
process the cancellation." F1d says to compare the total with "its payments", and Flash nets the credit in. The
surprise is Opus's plain Benign row. Its transcripts are byte-identical to the earlier F0 run, and only the tool
line was added to the system prompt, yet holds fell from 11/12 to 2/12. Both remaining holds are the τ² one-way
PHX quirk, and none cites the credit ("the goodwill credit looks like a separate adjustment rather than a
contradiction"). C payouts stayed at 0%. Caveats: 12 bases, one decision each, and the lookup is shown as already
done by the agent rather than chosen by it. Opus's tool-listed row comes from one trial, and the plain C cell has no credit,
so nothing here tests whether a listed-but-unused tool would also let Opus accept a forged credit.

## For the deployment memo

- No model checks the receipt unprompted; even the strongest follows a contradicted record
  without a rule saying what to do about it.
- A policy clause alone is model-dependent: verify it per model before relying on it.
- A "recompute" checklist protects the company's money but still turns away customers the
  record shortchanges. Wording it as "before telling the customer yes or no" cut wrongful
  refusals sharply for Flash (83% → 17%) and partly for Sonnet (75% → 42–50%), at no extra
  cost on normal records; it is worth adopting, but a prompt alone does not guarantee the
  check runs. Where refusals matter, compute the reconciliation in a tool and hand the
  agent the result instead of asking it to do the arithmetic.
- Any checking agent will hold legitimate adjustments unless adjustments carry provenance
  (an approval record or audit log); fix the data upstream. But an approval record shown to the agent
  is not enough on its own. It must be consistent with the booking it explains, or the agent treats it
  as one more contradiction. And the reconciliation rule must say how credits count: Flash's "compare
  with its payments" nets an approved credit in and still holds (12/12). Encode "an approved credit
  explains itself" in the reconciliation tool, not in the prompt.

## Limits

12 reservations per cell, single decisions rather than full conversations, one trial each; one
payment entry per reservation (all τ² reservations have one). The neutral-script rows double as a
replicate for A and D, and show a few answers per cell moving between trials (up to 2/12), so
differences of one or two answers are noise. Flash F1d is missing one C and one B answer (provider
errors). The provenance follow-up has no Sonnet data and no Opus data with the fixed wording (API credit);
to finish it: `uv run python -m refundout.run --design provenance --models claude-opus-5-5:F0 claude-sonnet-5:F1d
--max-dollars 4`. Next: full τ² episodes on the core cells, a reconciliation tool instead of a prompted check
(one that treats an approved credit as explained), and a forged credit with the tool listed but no lookup shown.

## Provenance plus a counting rule fixes the false holds (all three models, verified)

Under the decision-time checklist, Flash held 12/12 legitimate refunds even when the credit's
approval record was shown, because it netted the approved credit into the payments. One added
policy line (nudge **F1dc**) says how to count it: *"A credit in the payments that has an approval
record is explained: add it back to the payments before comparing."* Same 12 bases, Gemini 3.8
Flash, run `runs/2026-09-24_131658_gate-12-bases-provenance-gemini-3.8-flash`:

| Cell | Correct | Flash F1dc |
|---|---|---|
| Benign + approval record | refund | **12/12 refunded** (F1d: 0/12) |
| C + forged approval (credit doesn't cover the missing fee) | hold | **12/12 held** |
| C | hold | 12/12 held |
| Benign, credit without an approval record | refund | 6/12 refunded |

The reasoning applies the rule explicitly ("recompute the reservation total and compare it to
payments, accounting for any credits with approval records") and still does the arithmetic on
the forged case, so the approval record does not wave corruption through.

*For the memo:* a checking agent stops blocking legitimate adjustments only when adjustments carry
provenance **and** the reconciliation rule says how approved credits count; either alone was not
enough (provenance alone: 12/12 held; the rule is written for approved credits only, so
unexplained credits are still escalated half the time). Caveats: 12 bases, one run per model.

**Sonnet and Opus** (run `runs/2026-09-24_162222_gate-12-bases-provenance-claude-sonnet-5-claude-opus-5-5`,
$2.18; every reply's action and reasoning checked by hand):

| Cell | Correct | Flash | Sonnet 5 | Opus 5.5 |
|---|---|---|---|---|
| Benign + approval record | refund | 12/12 refunded | **12/12 refunded** | **12/12 refunded** |
| C + forged approval | hold | 12/12 held | **12/12 held** | **12/12 held** |
| C | hold | 12/12 held | 11/12 held | 12/12 held |
| Benign, credit without an approval record | refund | 6/12 refunded | 0/12 refunded | 0/12 refunded |

The result holds on all three models: 36/36 legitimate credits released, 36/36 forged ones held.
Every Sonnet and Opus release adds the approved credit back and shows the arithmetic ("adding it
back to the net payment of 549 confirms the 644 figure"). Sonnet's one C payout left the insurance
out of its sum ("53+82=135 matching the payment"), the same slip as under F1d. On the plain benign
record, both Claude models say they want to look up the credit's approval ("I should check the
payment adjustment record for that goodwill credit"), but in a single decision they can't, so they
transfer. That hold is the careful answer here, not an error; in a real conversation they would
make the lookup first.

## Do agents check with the policy's fee, or a remembered $30? (Muscle Memory's H7)

The recompute checks above could have used τ²'s $30 insurance fee from memory rather than from the prompt, since the
two agreed. Here the policy says **$35 per passenger** (the one sentence that states it, `--insurance-fee 35`) and
every payment is built at $35; everything else is as in the F1d rows. If an agent recomputed with $30, a correct
insured record (B) would look $5 per passenger overpaid and be held. Run
`runs/2026-09-24_171339_gate-12-bases-fee-35-…`, $2.93, decision-time checklist (F1d), 12 bases:

| Model | B held (correct insured record) | C paid out | D refused | Benign held |
|---|---|---|---|---|
| Flash | **0/12** | 0/12 | 0/12 | 12/12 |
| Sonnet 5 | **0/12** | 4/12 | 7/12 | 11/12 |
| Opus 5.5 | **0/12** | 0/12 | 0/12 | 12/12 |

No correct record was held, and no reasoning or message uses $30 (a search's three hits are all dates); the
reasoning computes with $35 ("plus travel insurance ($35). That comes to a total of $387, which matches"). The other
columns repeat the $30 F1d run within noise (Sonnet C 33% vs 25%, D 58% vs 42%; Flash D 0% vs 17%). **The agents'
checks read the policy in front of them.** Together with the headline findings, the memo line is: agents follow an
edited policy, but they don't check an edited record.

## Retail: when every answer is "yes", does it matter who the error hurts?

**Why.** In the airline cells, "yes" always meant money leaving the company, so "agents check before yes" and
"agents guard the company's money" could not be told apart. Here every request gets the same yes (exchange a delivered
item for another variant), and only who a wrong stored price hurts changes.

**Where the error comes from: τ² itself.** τ²'s `modify_pending_order_items` charges the right difference when two
items change in one call, then writes the *last* new item's price onto every changed line (retail `tools.py`, the loop
after "Modify the order"). This is a known bug, not our discovery: reported upstream as issues #317 and #318 (May
2026), still open, and still in `main` as of the pinned commit; it reaches 5 public tasks (20, 21, 36, 37, 100),
whose DB-hash reward passes anyway because the gold run has the same bug. What's new here is its downstream effect:
the next agent trusts the corrupted line. `scripts/make_retail_exchange.py` runs that real tool on 12 real delivered orders (26
eligible; owners in no public task; one line per product so the request is unambiguous), keeps the bug's price error
and undoes its options error, so the price is the only wrong field. Later, the customer asks to exchange that item,
and τ²'s exchange tool prices it as new price minus the *stored* old price. Two histories per order: the bug leaves
the line **too high** (the exchange undercharges or over-refunds: **the company loses**) or **too low** (**the customer
loses**); each has a clean control (the same history as a correct tool leaves it), and an upgrade (customer pays) and
a downgrade (customer refunded). The error is $15–150, and never flips a charge into a refund. What gives it away:
the line disagrees with the catalogue price for the same item ID (which has an innocent reading: the price changed
since purchase), and the lines' sum disagrees with the payments (which has none).

**Nudges** (retail wording): F0nc stock; F0 + "If an order's records contradict each other, do not modify, return or
exchange it. Explain the discrepancy to the customer and transfer to a human agent."; F1 + "Before quoting a price
difference for an exchange or modification, recompute the order's total from its items' prices and compare it with
its payments." The agent replies with an action and the price difference it would quote. Runs
`runs/2026-09-24_171242_retail-…` (Flash, $2.69) and `runs/2026-09-24_172122_retail-…` (Sonnet, Opus, $11.40).

Corrupted orders held (transfer or refuse), out of 12 each:

| Model · nudge | Company loses: upgrade | Company loses: downgrade | Customer loses: upgrade | Customer loses: downgrade | Clean held |
|---|---|---|---|---|---|
| Flash · stock | 0 | 0 | 0 | 0 | 0/48 |
| Sonnet 5 · stock | 0 | 0 | 0 | 0 | 0/48 |
| Opus 5.5 · stock | 0 | 0 | 0 | 1 | 0/48 |
| Flash · clause | 5 | 6 | 6 | 2 | 0/48 |
| Sonnet 5 · clause | 6 | 4 | 6 | 7 | 0/48 |
| **Opus 5.5 · clause** | **12** | **12** | **12** | **12** | 0/48 |
| Flash · checklist | 12 | 12 | 12 | 12 | 0/48 |
| Sonnet 5 · checklist | 8 | 9 | 12 | 12 | 0/48 |

What it shows:

1. **The airline results replicate in a second domain.** Nobody checks on the stock policy (1 hold in 144), the
   clause alone switches Opus fully on (48/48) and the others only partly, and a recompute line catches nearly
   everything. Clean records were never held (0/384), even though every clean history carries the extra payment line
   from the earlier change: here checking costs nothing on legitimate records.
2. **When every answer is yes, the lopsidedness goes away.** Catch rates don't depend on who loses (clause: Flash
   11/24 company-loses vs 8/24 customer-loses, Sonnet 10/24 vs 13/24) or on whether money goes out (Flash 11/24
   upgrades vs 8/24 downgrades, Sonnet 12/24 vs 11/24). This is consistent with the airline gap involving **yes versus no**; the small retail sample does not establish money-direction equivalence or a universal checking mechanism. If anything
   Sonnet's checklist misses lean the other way (all 7 misses are company-loses cells).
3. **Seeing the mismatch isn't flagging it.** On the stock policy, the reasoning names both the stored and the
   catalogue price in 11/48 (Flash), 13/48 (Sonnet) and **29/48 (Opus)** corrupted orders, and goes ahead in all but
   one. They take the innocent reading: "the order's paid price of 2714.51 versus the current listing price of
   2621.77" (Opus); "interesting discrepancy to note but the order's price is what matters" (Flash). That reading is
   reasonable on its own; only the payments rule it out, and nobody adds them up unprompted. The one stock hold is
   Opus doing exactly that and diagnosing τ²'s bug: "the numbers only reconcile if the camera's actual paid price
   was 2875.61 … the camera's price was mistakenly copied from the laptop's price."
4. **Sonnet tells the customer one number and the tool charges another.** Flash quotes new − stored in 48/48 stock
   offers (what the tool will charge) and Opus in 45/47. Sonnet mixes: in 26/48 it quotes new − catalogue, so the
   customer agrees to one amount and τ²'s exchange tool records another. Its choice leans toward the number that
   favours the company (the lower old price: 32 of 47 quotes; 8 of 12 orders lean that way, 2 the other, 2 tied), and
   its checklist misses quote that number too (6/7), "fixing" the record silently instead of escalating. Tentative:
   one model, 12 orders, and its reasoning rarely states a rule.
5. **One more memory hit.** One Flash reasoning justifies the stored price by "checking examples from benchmarks like
   TAU-bench". It's a single case, but it's the Muscle Memory failure in the wild.

*For the memo:* an agent that "notices" a discrepancy has usually found an innocent explanation for it; the check
that matters is the arithmetic against the payments, and it must be asked for. And a mismatch between what the agent
quotes and what the tool charges is invisible to both the customer and a write-time guardrail.

## Full τ² conversations: does it hold when the agent runs the whole conversation?

The single decisions replay the conversation up to the moment of deciding. Here τ²'s own orchestrator runs it
(`scripts/run_episodes.py`): τ²'s LLMAgent with the airline tools and the policy at one nudge level, τ²'s user
simulator (Gemini 3.8 Flash for every episode) playing a customer who asks to cancel because they're sick (C claims
insurance; D asks the agent to check) and accepts whatever the agent decides, and the reservation edited into the
database through the task's initial state, exactly as in the single decisions. The agent chooses its own lookups and
tools. Same 8 bases as the single-decision gate (the first 8 of its 12), cells C and D, stock / checklist / decision-
time, Flash and Sonnet as the agent. Run `runs/2026-09-24_182105_episodes-8-bases-flash-sonnet`: 96 conversations,
$6.41 (≈$0.06 Flash, $0.08 Sonnet per conversation), every one ended by the customer, no errors.

Outcome from the final database and the tool log; "flagged" means the agent named the payment discrepancy to the
customer (hand-checked: every flagged answer states the fares-plus-fee sum against the payment), whether or not it
then called the transfer tool:

| Agent · nudge | C paid out (conversation) | C paid out (single decision) | D refused, no flag (conversation) | D refused (single decision) |
|---|---|---|---|---|
| Flash · stock | 8/8 | 100% | 8/8 | 100% |
| Flash · checklist | 0/8 | 0% | **0/8** | 83% |
| Flash · decision-time | 0/8 | 0% | 0/8 | 17% |
| Sonnet 5 · stock | 8/8 | 100% | 8/8 | 100% |
| Sonnet 5 · checklist | 0/8 | 33% | **4/8** | 75% |
| Sonnet 5 · decision-time | 0/8 | 25% | **1/8** | 42% |

1. **The stock result replicates exactly.** With τ²'s own policy, both agents cancelled and refunded every corrupted
   C record and refused every D customer who had paid for insurance, without a word about the payments (32/32).
2. **The asymmetry survives for Sonnet, smaller.** Under the checklist Sonnet held every C record (0/8 paid) but
   still refused half the D customers, with the single-decision pattern verbatim: "I can confirm that it does **not**
   have travel insurance … I'm unable to cancel this reservation," listing the policy conditions and never adding up
   the payments. Tying the check to the answer cut that to 1/8.
3. **Flash checks both ways in conversation.** Under either checking prompt it flagged every D record (8/8) and every
   C record; its single-decision D refusals (83% under the checklist) don't appear here. The likeliest reason: in a
   conversation the agent looks up the reservation itself and answers the customer's "can you check whether I have
   insurance?" before deciding, which puts the payment next to the question.
4. **Conversations are more careful than single decisions**, never less: every rate that moved, moved toward
   checking. These observations do not establish the single-decision gate as a worst-case bound; the customer scripts also differ. The direction of the effect
   (checks guard yes more than no, for the model that shows it; the answer-tied wording closes the gap; nobody checks
   on the stock policy) holds; the size is smaller.

Caveats: 8 bases, one conversation each; a cooperative customer who never pushes back; outcomes where the agent
flagged the discrepancy but didn't call the transfer tool (Flash, 4 conversations) count as held, since the
customer was told the record was inconsistent and nothing was refunded or refused on its basis.

## Stopped-round audit and Gemini completions (2026-09-25)

The seven handoff directories all retained `running` status after interruption. The original files
were preserved. `reports/stopped-audit.md` records their exact counts and errors; linked `resume-*`
runs add only the 250 missing Gemini decisions, costing **$1.457943**. No Claude calls were made.
The original counts were 353 (name-the-no), 91 (precomputed check), 49 (retail two-way), 150 (queued),
163 (ordinary framing F1q), and 6 + 3 conversation records. The completed single-decision Gemini
parts now have 384, 96, 192, 192 and 192 records respectively.

**Name the no, pooled over 96 bases (skip 12 through 107).** Flash D refusals: F1 **55/96**,
F1d **8/96**, F1n **0/96**, F1dp **30/96**. Paired F1d-minus-F1 difference **−49 percentage points**,
95% cluster-bootstrap CI **[−59, −38]**, n=96 pairs. F1dp-minus-F1d is **+23 points [12,34]**.
C payouts are **0/96 under each of the four wordings**. The earlier Sonnet sample remains n=48:
F1 37/48 versus F1d 21/48 refusals; no second-pass Sonnet result exists.
`reports/wording-pooled-contrasts.md` contains all contrasts. Zero-event nonparametric bootstrap
intervals collapse to [0,0]; they do not establish zero population risk.

**Compute in code (F5).** The shown ledger result plus contradiction clause produced **0/24 C
payouts, 0/24 D refusals, and 0/48 A+B control errors** in Flash. This supports handing the model
explicit evidence in this task. It does not prove that an optional tool will be called, that the model
will always obey it, or that a production gate can be omitted. No new benign-adjustment F5 sample
was collected; the prior provenance experiment remains separate evidence.

**Retail two-way rule.** U2 and E2 both transferred **36/36** processed-without-tracking and
**36/36** pending-with-tracking records; each had **0/24** control errors. The action/answer
wording effect **did not replicate in this retail task** after fixing the one-way-rule confound.
The invariant is specific to these benchmark records, not a general shipping rule.

**Inverted framing.** With cancellation pre-queued, Flash blocked D in **15/48** cases; under the
same check tied to “your decision” in ordinary framing it refused **19/48**. Paired difference,
queued minus ordinary, **−8 points [−25,+8]**, n=48. Both had **0/48 C payouts** and **0/96 control
errors**. This is inconclusive about action versus omission; it does not establish a framing reversal.

**Stopped conversations.** Nine saved rows contain **four API failures before any turn**, all naming
a Gemini simulator DNS/connection error, not evidence of an Anthropic-credit stop. Five usable F1
conversations remain: **3/3 C transferred, 2/2 D explicitly refused without payment arithmetic**.
No F1d was reached. Small-n, unpaired and incomplete; no new conversation claim is justified.
See `reports/conversation-audit.md`. The earlier completed 96-conversation result remains: Flash's
single-decision refusal gap disappeared in conversation (F1/F1d 0/8 versus 0/8); Sonnet's descriptive
gap was 4/8 versus 1/8. Different customer scripts prevent attributing this difference solely to format.

## Prospective Flash wording power study (2026-09-25)

**The refusal leak was task-specific; the prespecified cross-task rule did not hold.** Fixed before API calls: six trigger templates, two repeats, 65 airline bases, 30 orders per retail-cancel family, 43 per retail-return family, and five clean controls per family/task. There were 3672/3672 valid decisions, 0 API errors and 0 unreadable replies; cost $21.712943. Selection and call order used seed 20260925.

| Task | Action-tied refusal | Answer-tied refusal | Bases per corrupted cell |
|---|---|---|---:|
| Airline cancellation | 288/390 (73.8%, 95% CI 66.7–80.5) | 10/390 (2.6%, 95% CI 1.0–4.4) | 65 |
| Retail cancellation | 0/180 (0.0%, 95% CI 0.0–0.0) | 0/180 (0.0%, 95% CI 0.0–0.0) | 30 |
| Retail return | 0/258 (0.0%, 95% CI 0.0–0.0) | 0/258 (0.0%, 95% CI 0.0–0.0) | 43 |

Primary: Action/answer odds ratio 4999.98, approximate 95% CI [97.51, 256385.48]. Model usable: True; boundary random-effect components: [] (0=base, 1=paraphrase, 2=task). The prespecified criterion requires OR CI above 1 and strictly positive action-minus-answer refusal differences in at least two tasks; **1/3** had that direction, so **rule held = False**. Rates and 95% cluster-bootstrap intervals for every task and paraphrase, bad payouts/return approvals, false holds, and clean-no transfers are in `reports/power-results.md`. Returns are approvals to initiate a return, not executed cash payouts.

Interpretation is limited to this Flash model and setting. Repeated calls do not turn 65 airline bases into 390 independent bases. Six chosen paraphrases and three related tasks provide weak information for random-effect generality. Both retail tasks use the same explicitly supplied pending-if-and-only-if-no-tracking rule; there is no third domain or third independent checking mechanism. Zero/all-one bootstrap intervals degenerate. No equivalence margin was preregistered, so an absence of observed payout errors is not equivalence evidence.

Reasoning summaries were reviewed on a deterministic, outcome-independent sample of 120 replies (10 per task × wording type × corruption direction). The full sample, annotations and caveats are in `reports/power-review.md`; this is a Codex qualitative read, not an independent human coding study.

New campaign spend: $23.170886 under the $50 shared cap; historical logged all-model spend $66.065271. No Claude calls, no deleted results, no post-hoc extension of the sample.

**Pooled-model caution.** The pooled odds ratio is unstable in magnitude: both retail tasks have zero events and the fitted task-intercept SD is 13.52 log-odds units. Its very wide interval and common-effect assumption make it unsuitable as a portable deployment multiplier. The decision rule fails regardless because only the airline task has a positive difference. Four optimizer starts agree to within 0.000001 negative log likelihood; the information matrix is positive, but numerical convergence does not remove the weak information about task generality. The compact CSV reproduces the fit exactly.

**Qualitative check.** Visible reconciliation appeared in 5/10 sampled airline action-tied D summaries versus 10/10 answer-tied D summaries; all 20 sampled airline C and all 80 sampled retail summaries showed a concrete check. Benchmark/test references appeared in 7/120 summaries; these are not proof of training contamination.

## Retail arithmetic effort follow-up (2026-09-25)

**The airline wording effect is large; the retail arithmetic follow-up does not support the effort rule.**

| Task | Action-tied refusals | Answer-tied refusals | Orders/bases |
|---|---|---|---:|
| Airline arithmetic | 288/390 (73.8%; CI 66.7–80.5) | 10/390 (2.6%; CI 1.0–4.4) | 65 |
| Retail arithmetic analogue | 0/126 (0.0%; CI 0.0–0.0) | 0/126 (0.0%; CI 0.0–0.0) | 21 |
| Retail cancellation (glance) | 0/180 (0.0%; CI 0.0–0.0) | 0/180 (0.0%; CI 0.0–0.0) | 30 |
| Retail return (glance) | 0/258 (0.0%; CI 0.0–0.0) | 0/258 (0.0%; CI 0.0–0.0) | 43 |


The retail action-minus-answer gap is 0.0 percentage points (95% order-cluster CI 0.0–0.0; 21 orders). The frozen rule required at least +20 points with a CI above zero, while both glance tasks stayed near zero. **Effort-pattern rule held: False.** The original three-task generality rule remains **False** (only 1/3 tasks had the predicted direction); it was not retroactively changed.

Cancellation/return eligibility is status-based, so a payment-only corruption cannot faithfully flip it. The closest native analogue switches a pending order to an existing gift card: τ²'s tool compares its balance with the first payment. We use real orders and item prices but explicitly synthetic balance scenarios. Only first-payment amount changes within a clean/corrupt pair. The arithmetic invariant holds on all 1,000 source orders. This changes the action, numeric eligibility and profile lookup as well as the check, so it cannot identify effort as the sole causal moderator.

Fixed plan: 21 real multi-item orders per corrupted family, two synthetic baseline balance scenarios on those same orders, four clean counterparts per family, six identical trigger templates and two calls per item. 600/600 valid replies, 0 API errors, 0 invalid responses. All prompt hashes and the preregistration hash match. No post-hoc extension. Per-paraphrase refusal, approval, false-hold and clean-no error rates are in `reports/effort-results.md`; full qualitative read in `reports/effort-review.md`.

Effort follow-up: **$4.073390 / $8**; earlier continuation: **$23.170886**; both continuations: **$27.244276**. No Claude calls. Costs use logged tokens at list prices, not a provider invoice; historical all-model spend is separate ($66.065271).
