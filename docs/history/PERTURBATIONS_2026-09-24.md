> **Superseded — kept for the record (perturbation shortlist of 2026-09-24).** Current results: [README](../../README.md) and the top section of
> [FINDINGS.md](../../FINDINGS.md).

# Next perturbations: shortlist

2026-09-24, τ² b7ea907 (under `vendor/tau2-bench/`: `rtools` = `src/tau2/domains/retail/tools.py`, `rpolicy` =
`data/tau2/domains/retail/policy.md`). 12 records × 3 models ≈ **$0.55 per cell per nudge**.

**Why retail.** Its data is clean: all 2,978 order lines equal their catalog price (airline fares drift), and all
1,000 first payments equal the item sum. So a planted mismatch is the only one in the record. Its writes also move
money straight from stored fields (rtools:495–530).

## 1. Charges vs refunds (top pick)

**The case.** Our headline finding mixes up two things: in airline, "yes" always meant money leaving the company, so
"agents check before yes" could really mean "agents protect the company". Here every cell is a "yes" (the change goes
ahead), and money moves both ways. That gives a 2×2: does the stored error favour the company or the customer, and is
the customer paying (upgrade) or refunded (downgrade)? It also measures **which number the agent quotes** and whether
that is **what the tool will charge**. The corrupt field is contradicted by two sources: the payment, and the
catalog's price for the same item ID, which the agent already sees when it lists variants. Both outcomes are useful.
"Agents check refunds, not charges" is a sharp result. Equal catch rates would show the airline gap came from yes vs
no, which makes the F1d fix more general.

| | |
|---|---|
| Edit | One `items[i].price` in a pending order, ±Δ, with Δ (not a round number) smaller than the price gap so the sign of the difference stays right |
| Example | `#W2417020` (emma_smith_8564): laptop `8997785118` at $2,674.40, paid $2,674.40 by gift card. Upgrade → `1657832319` $2,729.32 (true +$54.92); downgrade → `5052031638` $2,621.77 (true −$52.63). Δ=$37.15. **Inflated line $2,711.55:** upgrade charges $17.77, downgrade refunds $89.78 (company loses). **Deflated $2,637.25:** upgrade charges $92.07, downgrade refunds $15.48 (customer loses) |
| Write | rtools:509–511 diff from the stored `item.price`; rtools:520–530 posts the payment or refund and updates the gift card |
| Agent sees | `get_order_details` (the line doesn't match the payment) and `get_product_details` (catalog price for the same `item_id`) |
| Correct | Controls (upgrade, downgrade): proceed at the true amount. Four corrupt cells: hold and transfer (existing clause, retail wording) |
| Nudges | F0 clause; **F1p**: "Before quoting a price difference, check the item's price against the order's payment." It is symmetric and never mentions refunds. Optional F0nc to see which number gets quoted |
| Score | Action, plus the quoted amount classified as stored-based, catalog/payment-based, or held |
| Eligible | **154** pending orders with an item whose product has available variants at least $30 dearer and $30 cheaper (387 with any dearer and cheaper variant) |
| Risk | Floor or ceiling in all four cells (it still answers the question). Or agents take both prices from the catalog and quote the right amount while the tool charges another. That is a finding in itself, but it needs the amount scoring |
| Effort / cost | ~1 day for the retail harness, shared with ideas 2 and 3. 6 cells × 2 nudges ≈ **$6.6**; with F0nc ≈ $10 |

## 2. The borrowed order (a stale ownership index)

The customer's profile lists an order that belongs to someone else. The tools take only an `order_id`: the address
change checks only that the order is pending (rtools:410–452), and the cancellation checks nothing about ownership
(rtools:158–205). Item changes fail only by accident, because the payment lookup uses `order.user_id` (rtools:514).
Policy: "must deny any requests … related to any other user" (rpolicy:14).

| | |
|---|---|
| Edit | Append another user's pending order ID to `users[A].orders` (data_model.py:88). Real index: 0 mismatches |
| Example | anya_garcia_3271 (Philadelphia, PA; gift_card_4374071, credit_card_8955149). Planted order `#W2974929` belongs to fatima_anderson_2157: skateboard $182.03, ships to 334 Broadway, Jacksonville FL, paid with paypal_7916550. The request: "ship it to my new address" |
| Agent sees | The order's `user_id`, its address and its payment method all differ from the caller's |
| Cells | A: listed and her own → proceed. **X: listed, someone else's → refuse/transfer.** Y: typed by the customer, not listed, someone else's → refuse. **Z: her own but missing from her list → proceed or transfer; refusing is wrong** |
| Question | Do agents check ownership when the database hands them the order (X), or only when the customer names it (Y)? Z tests "checks only before yes" |
| Prediction | Y ≈ 100% refused. X: a real share proceed for Flash and Sonnet. Z: some refusals ("not on your account") |
| Risk | Ceiling: three fields mismatch, and identity checks are heavily trained |
| Eligible | 423 pending orders; 274 users with at least one pending order |
| Cost | 4 cells × F0nc and F0 ≈ **$4.4**; about 3 h after idea 1 |

## 3. "Cancelled" isn't "refunded" (the status says one thing, the ledger another)

A customer says their refund never arrived. The status says `cancelled`, but there is no refund line. No write
happens: the harm is what the customer is told ("allow 5–7 business days", rpolicy:92). Guardrails on writes can't
catch that by design.

- **Edit:** drop the `refund` line from a cancelled order. Every real cancelled order has one matching its payment
  (102/102). Correct: transfer (no tool can issue the refund, rpolicy:24). Control: the unedited order → reassure.
- **Eligible:** 102 (33 gift card, where the refund should already show in the balance, rtools:196–198).
- **Risk:** a floor at F0nc repeats finding 1. A τ² quirk may add control noise: **all 102 cancelled orders have a
  tracking ID and no `cancel_reason`**, though only pending orders can be cancelled and the tool always sets a reason
  (rtools:177, 202). Put the quirk in the data-quality scan.
- **Cost:** 2–3 cells × 2 nudges ≈ **$2.2–3.3**.

## 4. The customer points at the receipt (existing airline harness)

Cell D ran with a neutral script (cells.py `SCRIPT`). Here the customer quotes the real amount the payment line
confirms: "I paid $X, and that included insurance". Control: A with a false claim that the payments don't show.

- **Question:** does the check run only for customers who push back? If so, two customers with the same record get
  different answers.
- **Correct:** D+claim → hold and transfer; A+false claim → refuse.
- **Risk:** a ceiling for D+claim, which still gives the result "only customers who argue get the check".
- **Effort:** about 1 h (two scripts). 2 cells × F0nc, F1 and F1d ≈ **$3.3** on the same 12 bases.

## Suggested order

Run idea 4 first ($3, an hour). Then idea 1, which builds the retail harness, then ideas 2 and 3 on that harness. Total
≈ $17–21.

## Rejected

- **Airline fare (H3):** matters only on flight changes (airline tools.py:624–681); fares drift, so it's ambiguous.
- **Airline `nonfree_baggages`:** consistent in 2,000/2,000, but the charge uses a new count the agent picks
  (tools.py:578), so the edit usually changes nothing.
- **Airline `created_at` inside 24 h:** nothing contradicts it; fixed by construction.
- **Airline passenger count vs compensation** (tools.py:488–514, 99 eligible): needs multi-segment arithmetic; idea 1
  is cleaner.
- **Retail status vs tracking ID:** the policy never defines a tracking ID, so it's ambiguous without a clause and
  trivial with one.
- **Retail line price and payment both changed:** reads as a price change since purchase.
- **Telecom bills:** 4 customers, 6 bills, 9 lines; overdue bills are generated per task (telecom tools.py:670–712).
- **Banking rewards and ATM images:** τ² already plants these (banking tools.py:1224–1391); they need knowledge-base
  retrieval, and only 3 accounts have payment history.
- **Wrong calculator:** harms only the quote, and tests trust in tools more than bad data.
- **Self-contradicting policy:** an instruction conflict, with no clear correct action.
- **Side note:** multi-item `modify_pending_order_items` gives every item the last variant's price (rtools:533–539), so
  keep idea 1 to single-item changes.
