# Deployment memo: check before every answer

**Decision.** Require deterministic reconciliation before granting or refusing a request. If checks rely on prompts, explicitly name both answers. Validate each model, task and conversation flow; a guard only on a refund write cannot catch a wrongful “no.”

**Evidence.** The airline wording effect is large; the retail follow-ups were at floor, so they could not test whether the effect generalises. Wrongful refusals under Gemini 3.8 Flash, six-wording study (airline: 65 bases, two calls per item) and retail follow-ups:

| Task | Action-tied refusals | Answer-tied refusals | Orders/bases |
|---|---|---|---:|
| Airline arithmetic | 288/390 (73.8%; CI 66.7–80.5) | 10/390 (2.6%; CI 1.0–4.4) | 65 |
| Retail arithmetic analogue | 0/126 (0%; 95% upper bound 13.3%, 21 orders) | 0/126 (0%; 95% upper bound 13.3%, 21 orders) | 21 |
| Retail cancellation (glance) | 0/180 (0%; 95% upper bound 9.5%, 30 orders) | 0/180 (0%; 95% upper bound 9.5%, 30 orders) | 30 |
| Retail return (glance) | 0/258 (0%; 95% upper bound 6.7%, 43 orders) | 0/258 (0%; 95% upper bound 6.7%, 43 orders) | 43 |


Airline intervals are 95% base-cluster bootstraps; zero-event rows give exact one-sided 95% upper bounds computed on independent orders, not calls (repeated calls are not independent); zero events do not prove zero risk. The original generality rule was not met because both retail tasks were at floor (0 refusals under either wording); the retail tasks could not show the effect, so generality beyond this airline task is untested. Effort rule: **not testable** (retail analogue at floor; its 'no' path runs through the corrupted number); retail arithmetic had 0 events under either wording (21 orders), so the difference is not estimable (both at floor). The six-wording evidence is Flash-only; the original airline pair also showed the effect in Sonnet. Claude Opus 5.5 made 0/24 wrongful refusals and 0/24 corrupted payouts under every one of the four wordings F1, F1n, F1d, F1dp (24 fresh bases, neutral script, run runs/2026-09-25_151002_gate-24-bases-skip-12-cells-CD-neutral-script-claude-opus-5-5, $5.10): no wording effect is measurable at floor.

**Scope.** Retail arithmetic uses a native payment-switch action and real item prices, but synthetic gift-card balances. It changes eligibility and transcript as well as checking effort. There are only 21 arithmetic retail orders and four clean orders per family. This is not a causal isolation of effort or a deployment reliability estimate.

**Implementation.** Return expected total, paid total, discrepancy, evidence references and reconciliation status. Make a mismatch require a human handoff before any final answer. A supplied airline ledger gave 24/24 correct transfers in each corrupted direction and 0/48 clean-control errors; this small result supports testing deterministic checks, not a guarantee. The ledger output prints the verdict ("payments do not reconcile … insurance fee paid but insurance marked no"), so it tests whether the model acts on a stated mismatch, not whether it checks.

**Adjustments.** Store amount, adjustment type, order/reservation ID, approver, approval time and reason. State how each adjustment counts: add an authorized credit back when comparing with the original charge. Provenance alone does not reconcile a ledger. Prior tests released 36/36 legitimate credits and held 36/36 corresponding corruptions across three models with the counting rule.

**Release test.** Pair every yes-leaning contradiction with a no-leaning one and clean controls. Measure refusals, bad approvals, false holds, invalid replies and successful handoffs separately. Repeat after model/policy changes. In the earlier eight-base Flash conversation comparison, the raw harness output was 2/8 D refusals under F1 versus 1/8 under F1d; a hand recode that counts "flagged the discrepancy to the customer but didn't call the transfer tool" as held gives 0/8 under both (Sonnet: 4/8 versus 1/8). The Flash user simulator can hang up at the transfer offer, and Flash used τ²'s calculate tool in 12/16 of these episodes, which the single-decision format does not offer, so the single-decision vs conversation difference may be a format effect; treat conversations as a small stress test. Single-decision gaps need workflow validation.

**Cost.** Follow-up $4.07; both new campaigns $27.24. No new Claude calls. Recorded list prices, excluding engineering and escalation.
