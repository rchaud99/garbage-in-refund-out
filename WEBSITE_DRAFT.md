# Checked before yes, trusted before no

*Draft for the personal website (~550 words). Every number comes from preregistered single-decision replays on
τ²-bench. Chart: `figures/path_2026-09-28.png`.*

AI support agents apply policy to whatever the database says. I asked a narrow question: if a record contradicts
itself, does the agent notice? And does it matter which way the error cuts?

**Setup.**
- **The corrupted records.** I took real reservations from τ²-bench, Sierra's customer-service benchmark, and
  planted one-field contradictions:
  - an insurance flag that says "yes" when no insurance fee was paid (trusting it pays out wrongly);
  - an insurance flag that says "no" when the fee *was* paid (trusting it turns away a customer who is owed a
    refund).
- **The decisions.** Two of them: a sick customer cancelling, and a customer asking for compensation after the
  airline cancelled their flight. In both, insurance alone decides the answer.
- **The instructions.** The policy told the agent to hand contradictory records to a human, and to "recompute the
  reservation's total from its fares, passengers and insurance, and compare it with its payments."
- **Method.** Each test is a single decision: the model reads the conversation so far and answers. Every test was
  preregistered, and every model is reported.

**1. The check guards the "yes".**
- Gemini 3.8 Flash, Gemini 3.1 Pro and Claude Sonnet 5 missed 0%, 0% and 15% of corrupted records that would have
  paid out.
- The same models refused 56–72% of corrupted records that pointed to "no".
- A control ruled out the idea that overpayments are just harder to spot. I swapped which answer the over- and
  underpaid records pointed to, and the errors followed the answer, not the arithmetic.
- Shown the *same* corrupted record under a request whose answer was "no", Flash missed it 31% of the time, against
  0% when the answer was "yes".
- The refusals read like this: *"There's no insurance, it's not a business flight, it wasn't booked within 24
  hours… None of the policy exceptions apply."* The model never reaches the payments.

This held for Flash and Pro on both decisions. It held for Sonnet on cancellations; on compensation, Sonnet rarely
checked at all.

**2. Prompt fixes are model-specific.**
- **"Before telling the customer yes or no…"** cut Flash's wrongful refusals from 41/62 to 5/62, replicating my
  earlier result. It barely helped Sonnet (44/62 → 40/62): my earlier Sonnet result did not replicate.
- **"Every time you look up a reservation, recompute…"** halved Sonnet's refusals and closed its gap. The same
  sentence made Flash refuse 44/46 compensation cases, and made an open-weights Gemma model pay out more.
- **Vague instructions** ("If a record looks wrong, transfer to a human") left Flash wrong 100% of the time.

A guardrail sentence that works on one model can backfire on the next.

**3. Some models check both ways.** GPT-6 Sol made no errors in either direction.

**Why it matters.**
- Guardrails usually sit at the write step: check before issuing a refund. A wrongful "no" writes nothing, so the
  guard never sees it.
- Here the same blind spot appears inside the model: it verifies on the way to an action and skips verification
  on the way to a refusal.
- What I'd ship: compute the reconciliation in code, show it before *any* answer, and test both directions on
  every model you deploy.

**Limits.**
- These are single decisions, not full conversations; an earlier small conversation test found smaller gaps.
- One domain, one kind of corruption, two decisions.
- The robustness bar I set in advance (three models from two providers, on both decisions) was not met. Only two
  Gemini models cleared it on both.
- About 6,000 decisions, for $38 of API spend.
