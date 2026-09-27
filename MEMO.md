# Deployment memo: check before every answer

**Decision.** Require deterministic reconciliation before granting or refusing a request. If checks rely on prompts, explicitly name both answers. Validate each model, task and conversation flow; a guard only on a refund write cannot catch a wrongful “no.”

**Evidence.** The airline wording effect is large; the retail arithmetic follow-up does not support the effort rule. Wrongful refusals under Gemini 3.8 Flash:

| Task | Action-tied refusals | Answer-tied refusals | Orders/bases |
|---|---|---|---:|
| Airline arithmetic | 288/390 (73.8%; CI 66.7–80.5) | 10/390 (2.6%; CI 1.0–4.4) | 65 |
| Retail arithmetic analogue | 0/126 (0.0%; CI 0.0–0.0) | 0/126 (0.0%; CI 0.0–0.0) | 21 |
| Retail cancellation (glance) | 0/180 (0.0%; CI 0.0–0.0) | 0/180 (0.0%; CI 0.0–0.0) | 30 |
| Retail return (glance) | 0/258 (0.0%; CI 0.0–0.0) | 0/258 (0.0%; CI 0.0–0.0) | 43 |


Intervals are 95% order/base-cluster bootstraps; zero-event intervals do not prove zero risk. The original generality rule failed. The follow-up effort-pattern rule held: **False**; retail difference 0.0 percentage points (95% order-cluster CI 0.0–0.0; 21 orders). The six-wording evidence is Flash-only; the original airline pair also showed the effect in Sonnet.

**Scope.** Retail arithmetic uses a native payment-switch action and real item prices, but synthetic gift-card balances. It changes eligibility and transcript as well as checking effort. There are only 21 arithmetic retail orders and four clean orders per family. This is not a causal isolation of effort or a deployment reliability estimate.

**Implementation.** Return expected total, paid total, discrepancy, evidence references and reconciliation status. Make a mismatch require a human handoff before any final answer. A supplied airline ledger gave 24/24 correct transfers in each corrupted direction and 0/48 clean-control errors; this small result supports testing deterministic checks, not a guarantee.

**Adjustments.** Store amount, adjustment type, order/reservation ID, approver, approval time and reason. State how each adjustment counts: add an authorized credit back when comparing with the original charge. Provenance alone does not reconcile a ledger. Prior tests released 36/36 legitimate credits and held 36/36 corresponding corruptions across three models with the counting rule.

**Release test.** Pair every yes-leaning contradiction with a no-leaning one and clean controls. Measure refusals, bad approvals, false holds, invalid replies and successful handoffs separately. Repeat after model/policy changes. The earlier eight-base Flash conversation comparison had 0/8 refusals under both wordings, so single-decision gaps need workflow validation.

**Cost.** Follow-up $4.07; both new campaigns $27.24. No new Claude calls. Recorded list prices, excluding engineering and escalation.
