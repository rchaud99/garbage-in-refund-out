# Retail arithmetic follow-up — frozen before API calls

2026-09-25. Gemini 3.8 Flash only, medium thinking, provider-default temperature,
8,192 maximum output tokens including reasoning, no retries. Separate campaign
`retail-effort-2026-09-25`, hard cumulative cap $8 including any failed-call reserves.
This is a prospective follow-up motivated by the known three-task results, not a
preregistration of those earlier results. The original preregistration is unchanged.

## Claim and identification limit

Prediction: action-tied checks leak refusals when reconciliation needs arithmetic,
whereas the previously tested glance-level checks did not. The new task tests the
predicted pattern; it cannot establish effort as the sole causal moderator.

A faithful arithmetic-only change to cancellation/return is impossible under the
native policy: their eligibility depends on status, and corrupting payment amount
does not flip status. The closest native analogue is modifying a pending order's
payment method to an existing gift card. The real tool uses first-payment amount
as the charge and refuses if gift-card balance is smaller (`tools.py`, function
`modify_pending_order_payment`). A corrupted first-payment amount can thus wrongly
block or allow the switch; the sum of item prices exposes the contradiction.

The original-payment-equals-item-sum invariant is verified in a test on all 1,000
source orders. Eligibility pool: pending orders, one payment, at least three items,
an existing alternate gift card, distinct users, and no order/user identity in
public tasks. There are only 21 such orders (3–5 items each). Native balances give
only one eligible pending order even before these exclusions, so balance scenarios
are explicitly synthetic. This changes the customer action, numeric eligibility,
profile lookup and balance setup relative to the glance tasks; effort is not isolated.

## Fixed design

Use all 21 eligible real orders, each in two balance scenarios. Let T be the original
item sum in cents and d = max(100, floor(T/10)). Eligible baseline: existing gift-card
balance T+d. Ineligible baseline: balance T-d. Those balances are experimentally set,
not claimed to be the original τ² account balances. All item prices and order statuses
remain real and unchanged. Within each baseline, corrupt only the first payment amount:
T+2d (heads to no) or T-2d (heads to yes). Both require human transfer under the clause.
Clean counterparts keep amount T: offer payment change / refuse, respectively.

The first four selected orders supply clean counterparts in both scenarios. Six
wordings, two calls per item: (21×2 + 4×2)×6×2 = 600 decisions. Same orders in both
families; uncertainty clusters by original order. Three action and three answer
trigger templates are imported byte-for-byte from `power.TRIGGERS`, with the task
noun “an order modification”. Only the common check content changes to item-sum
versus first payment. Existing prompt definitions are untouched. Exact prompts and
IDs are hashed in `reports/effort-plan.json`. Selection and call-order seed 20260926.

The estimate is $5.02 typical / $7.50 high before calls. The dataset limit and $8
budget prevent the requested 40–60 orders per family. Fixed sample; no extensions,
resampling or prompt edits after outcomes. Conservative in-flight input/output
reserves and failed-call accounting use the previous guard, scoped to the separate
$8 campaign. Stop submissions on the first API error and save in-flight replies.
A budget stop or incomplete data cannot count as a successful confirmatory result.

## Outcomes, decision rule, and review

Report count/n and 95% percentile cluster-bootstrap intervals (10,000 resamples,
seed 20260925 for consistency with the prior analysis) for each wording type and
paraphrase: refusal on corrupt_no, offer_payment_change on corrupt_yes, false hold
(refuse or transfer) on clean_yes, and clean_no errors/transfers. Invalid responses
and API errors are separate, never scored as refusals. The primary contrast is
paired action-minus-answer refusal rate on corrupt_no, clustered by original order,
keeping all six wordings and both repeats together. Zero-event bootstrap intervals
degenerate and do not prove zero population risk. Four clean orders is very small n.

Prespecified operational rule: the predicted effort pattern is supported if the
new arithmetic retail contrast is at least +20 percentage points, its two-sided
95% bootstrap interval excludes zero in the positive direction, the run completes,
and both previously completed glance tasks remain near zero under both types.
For an explicit operational definition, near zero means observed refusal rate ≤5%;
their already observed rates are exactly zero. Otherwise retain a task-specific
airline conclusion. Even if the numerical rule passes, report “consistent with an
effort hypothesis in this analogue,” not causal identification of effort. Do not
refit/redefine the original three-task generality rule, which already failed.

Create the four-task table from the frozen previous results plus this study; do not
pool repetitions as independent orders. No cross-task mixed model is required here.
Read up to ten corrupt_no refusal summaries, deterministically sampled after grouping
by wording type (five per type where available, remaining slots filled from the other),
prefer distinct orders. If fewer than ten refusals exist, read all and say so. Also
read ten matched/selected corrupt_no transfers to assess reported arithmetic checks.
Record explicit item addition/comparison, skipped arithmetic, unclear evidence, and
benchmark references without inferring hidden internal reasoning or contamination.
