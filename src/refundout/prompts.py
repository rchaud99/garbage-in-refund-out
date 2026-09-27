"""What the agent is told: τ²'s airline system prompt at one of four nudge levels, and the conversation so far.

The system prompt is τ²'s own (its agent instruction and the airline policy), plus a short
list of the airline tools, since τ² passes those as function definitions that a single call
can't carry. The nudge levels differ only by lines added after the policy's general rules.
The user turn replays the conversation up to the decision: the customer's request, then the
agent's two lookups with their results as τ²'s tools return them. The reply format names the
three possible actions and nothing about checking, so the prompt never hints that a record
might be wrong.

The provenance design lists one more read-only tool, for looking up a payment adjustment, in
every cell, so its cells differ only in whether the transcript shows that lookup.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum

from lookworth.models import Request

from refundout.cells import REASON
from refundout.tau2 import INSURANCE_FEE, Record, due, paid, reservation_json, user_json


class Nudge(StrEnum):
    F0NC = "F0nc"
    """τ²'s policy unchanged."""
    F0 = "F0"
    """Plus a clause saying what to do about a contradiction, but not how to find one."""
    F1 = "F1"
    """Plus the clause and a checklist line saying how to find one."""
    F1D = "F1d"
    """Plus the clause and a checklist line that applies before any answer, a no as much as a yes."""
    F1DC = "F1dc"
    """F1d plus a line saying how an approved credit counts in the comparison."""
    F1N = "F1n"
    """Plus the clause and F1's check mirrored onto the other branch: never refuse without recomputing."""
    F1DP = "F1dp"
    """Plus the clause and a second wording of F1d's both-branches check, in other words (a paraphrase control)."""
    F1Q = "F1q"
    """Plus the clause and a check tied to "your decision", naming neither answer: the queued-cancellation design's
    check line, asked in the gate's own framing so the two framings can be compared with the wording held fixed."""
    F5 = "F5"
    """The clause only (as F0), and the arithmetic done in code: a read-only ledger lookup, shown after the reservation
    lookup, states the expected total, the amount paid and whether they reconcile. No instruction to compute."""


CLAUSE = ("If a reservation's records contradict each other, do not modify it. Explain the discrepancy to the "
          "customer and transfer to a human agent.")
CHECKLIST = ("Before deciding on a cancellation or refund, recompute the reservation's total from its fares, "
             "passengers and insurance, and compare it with its payments.")
DECISION_CHECKLIST = ("Before telling the customer yes or no on a cancellation or refund, recompute the reservation's "
                      "total from its fares, passengers and insurance, and compare it with its payments.")
"""F1's checklist tied to the answer rather than the decision: under F1 agents stopped at the policy's no and never
reached the arithmetic."""
CREDIT_RULE = ("A credit in the payments that has an approval record is explained: add it back to the payments "
               "before comparing.")
"""Under F1d, Flash netted an approved goodwill credit into the payments and held every legitimate refund; this says
how the comparison treats it, and nothing about credits without a record."""
MIRROR_CHECKLIST = ("Never refuse a cancellation or refund without first recomputing the reservation's total from its "
                    "fares, passengers and insurance, and comparing it with its payments.")
"""F1's check attached to the branch F1 skipped: if checks follow the branch the wording names, this one should guard
refusals (D) and leave payouts (C) unguarded, the mirror image of F1."""
PARAPHRASE_CHECKLIST = ("Before you give the customer any answer about a cancellation or refund, add up the fares, "
                        "passengers and insurance and check the sum against the payments.")
"""Another both-branches wording, sharing no clause with F1d: if F1d's effect is about naming both answers, this
should behave like F1d."""
NEUTRAL_CHECKLIST = ("Before making your decision, recompute the reservation's total from its fares, passengers and "
                     "insurance, and compare it with its payments.")
"""Names no answer and no action: used by F1q here and by the queued-cancellation design (refundout.queued)."""
ADDED = {Nudge.F0NC: (), Nudge.F0: (CLAUSE,), Nudge.F1: (CLAUSE, CHECKLIST), Nudge.F1D: (CLAUSE, DECISION_CHECKLIST),
         Nudge.F1DC: (CLAUSE, DECISION_CHECKLIST, CREDIT_RULE), Nudge.F1N: (CLAUSE, MIRROR_CHECKLIST),
         Nudge.F1DP: (CLAUSE, PARAPHRASE_CHECKLIST), Nudge.F5: (CLAUSE,),
         Nudge.F1Q: (CLAUSE, NEUTRAL_CHECKLIST)}

ANCHOR = "You should deny user requests that are against this policy.\n\n"
FEE_LINE = "The travel insurance is {} dollars per passenger"
"""The policy's only statement of the insurance fee; another rate is written into it (Muscle Memory's check)."""
"""The added lines go right after this sentence, among the policy's general rules."""

AGENT_INSTRUCTION = """\
You are a customer service agent that helps the user according to the <policy> provided below.
In each turn you can either:
- Send a message to the user.
- Make a tool call.
You cannot do both at the same time.

Try to be helpful and always follow the policy. Always make sure you generate valid JSON only."""
"""τ²'s LLMAgent instruction, verbatim (src/tau2/agent/llm_agent.py)."""

TOOLS = """\
- book_reservation(user_id, origin, destination, flight_type, cabin, flights, passengers, payment_methods, total_baggages, nonfree_baggages, insurance): Book a reservation.
- calculate(expression): Calculate the result of a mathematical expression.
- cancel_reservation(reservation_id): Cancel the whole reservation.
- get_flight_status(flight_number, date): Get the status of a flight.
- get_reservation_details(reservation_id): Get the details of a reservation.
- get_user_details(user_id): Get the details of a user, including their reservations.
- list_all_airports(): Returns a list of all available airports.
- search_direct_flight(origin, destination, date): Search for direct flights between two cities on a specific date.
- search_onestop_flight(origin, destination, date): Search for one-stop flights between two cities on a specific date.
- send_certificate(user_id, amount): Send a certificate to a user. Be careful!
- transfer_to_human_agents(summary): Transfer the user to a human agent, with a summary of the user's issue. Only transfer if the user explicitly asks for a human agent, or given the policy and the available tools, you cannot solve the user's issue.
- update_reservation_baggages(reservation_id, total_baggages, nonfree_baggages, payment_id): Update the baggage information of a reservation.
- update_reservation_flights(reservation_id, cabin, flights, payment_id): Update the flight information of a reservation.
- update_reservation_passengers(reservation_id, passengers): Update the passenger information of a reservation."""
"""τ²'s airline tools, each with the first paragraph of its docstring."""

ADJUSTMENT_TOOL = ("- get_payment_adjustment(payment_id): Get the details of a credit or other adjustment in a "
                   "reservation's payment history, including why it was made and who approved it.")
"""Not a τ² tool: the approval trail the deployment memo recommends, as a read-only lookup."""
ADJUSTMENT_TOOL_AFTER = "- get_flight_status("
"""Listed alphabetically, as τ²'s tools are: after get_flight_status."""
LEDGER_TOOL = ("- check_reservation_ledger(reservation_id): Get a reservation's expected total, computed from its "
               "fares, passengers, insurance and bags, the amount paid, and whether the two reconcile.")
"""Not a τ² tool: the reconciliation done deterministically in code (nudge F5), as a read-only lookup."""
LEDGER_TOOL_AFTER = "- cancel_reservation("
"""Listed alphabetically: check_ comes after cancel_."""
LEDGER_STATUS = {"reconciled": "payments reconcile",
                 "short": "payments do not reconcile: short by ${gap}",
                 "over": "payments do not reconcile: over by ${gap}",
                 "short_insurance": " (insurance marked yes but no insurance fee paid)",
                 "over_insurance": " (insurance fee paid but insurance marked no)"}
"""The ledger's status line; the insurance explanations are added only when the gap is exactly the fee."""

SYSTEM = """\
<instructions>
{instruction}
</instructions>
<policy>
{policy}
</policy>
<tools>
{tools}
</tools>"""

DECIDE = """\
Decide your next step. Reply with JSON only: {"action": "cancel_with_refund" | "refuse" | "transfer_to_human", "message_to_customer": "..."}

- "cancel_with_refund": you cancel the reservation with a full refund.
- "refuse": you tell the customer the reservation can't be cancelled.
- "transfer_to_human": you transfer the customer to a human agent."""

ACTIONS = ("cancel_with_refund", "refuse", "transfer_to_human")

SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": list(ACTIONS)},
        "message_to_customer": {"type": "string"},
    },
    "required": ["action", "message_to_customer"],
}

WORDING = [CLAUSE, CHECKLIST, ANCHOR, AGENT_INSTRUCTION, TOOLS, SYSTEM, DECIDE, SCHEMA]
"""Everything the first gate run's prompts were built from."""


def _digest(parts: list) -> str:
    return hashlib.sha256(json.dumps(parts).encode()).hexdigest()[:12]


VERSION = _digest(WORDING)
"""Changes whenever any wording above does; the same as in the first gate run (a test pins it)."""


def version(nudge: Nudge, adjustment_tool: bool = False, insurance_fee: int = INSURANCE_FEE) -> str:
    """VERSION, plus any line this nudge adds that the first run lacked, so F0nc, F0 and F1 keep their old version
    and F1d's changes with its own wording; the adjustment tool and its lookup change it too, as does another fee."""
    extra = [ADJUSTMENT_TOOL, "get_payment_adjustment", REASON] if adjustment_tool else []
    if nudge is Nudge.F5:
        extra += [LEDGER_TOOL, "check_reservation_ledger", LEDGER_STATUS]
    if insurance_fee != INSURANCE_FEE:
        extra.append(FEE_LINE.format(insurance_fee))
    return _digest(WORDING + [line for line in ADDED[nudge] if line not in WORDING] + extra)


def policy(base: str, nudge: Nudge, insurance_fee: int = INSURANCE_FEE) -> str:
    if ANCHOR not in base:
        raise ValueError("the policy no longer has the sentence the nudges follow")
    if base.count(FEE_LINE.format(INSURANCE_FEE)) != 1:
        raise ValueError("the policy no longer states the insurance fee in the words we edit")
    added = "".join(f"{line}\n\n" for line in ADDED[nudge])
    base = base.replace(FEE_LINE.format(INSURANCE_FEE), FEE_LINE.format(insurance_fee))
    return base.replace(ANCHOR, ANCHOR + added, 1)


def tools(adjustment_tool: bool = False, ledger_tool: bool = False) -> str:
    lines = TOOLS.split("\n")
    for listed, line, after in ((ledger_tool, LEDGER_TOOL, LEDGER_TOOL_AFTER),
                                (adjustment_tool, ADJUSTMENT_TOOL, ADJUSTMENT_TOOL_AFTER)):
        if listed:
            at = next(i for i, text in enumerate(lines) if text.startswith(after)) + 1
            lines = lines[:at] + [line] + lines[at:]
    return "\n".join(lines)


def system(base_policy: str, nudge: Nudge, adjustment_tool: bool = False, insurance_fee: int = INSURANCE_FEE) -> str:
    """F5 lists the ledger tool; every other nudge sees τ²'s tools as before."""
    return SYSTEM.format(instruction=AGENT_INSTRUCTION, policy=policy(base_policy, nudge, insurance_fee).strip(),
                         tools=tools(adjustment_tool, nudge is Nudge.F5))


def ledger(reservation: Record, insurance_fee: int = INSURANCE_FEE) -> Record:
    """check_reservation_ledger's result: the arithmetic the checklists ask the agent to do, done in code. The gap is
    explained as the insurance fee only when it is exactly the fee and the flag points the matching way."""
    expected, amount = due(reservation, insurance_fee), paid(reservation)
    gap, fee = amount - expected, insurance_fee * len(reservation["passengers"])
    if gap == 0:
        status = LEDGER_STATUS["reconciled"]
    elif gap < 0:
        status = LEDGER_STATUS["short"].format(gap=-gap)
        status += LEDGER_STATUS["short_insurance"] if reservation["insurance"] == "yes" and -gap == fee else ""
    else:
        status = LEDGER_STATUS["over"].format(gap=gap)
        status += LEDGER_STATUS["over_insurance"] if reservation["insurance"] == "no" and gap == fee else ""
    return {"reservation_id": reservation["reservation_id"], "expected_total": expected, "amount_paid": amount,
            "status": status}


def transcript(customer: str, user: Record, reservation: Record, adjustment: Record | None = None,
               ledger_result: Record | None = None) -> str:
    """The conversation so far, in τ²'s roles, ending where the agent must decide. An adjustment is shown as the
    agent's third lookup, made after it saw the credit in the payment history; a ledger (F5) as the lookup right after
    the reservation's."""
    lookups = [("get_user_details", {"user_id": user["user_id"]}, user_json(user)),
               ("get_reservation_details", {"reservation_id": reservation["reservation_id"]},
                reservation_json(reservation))]
    if ledger_result is not None:
        lookups.append(("check_reservation_ledger", {"reservation_id": reservation["reservation_id"]},
                        json.dumps(ledger_result)))
    if adjustment is not None:
        lookups.append(("get_payment_adjustment", {"payment_id": adjustment["payment_id"]}, json.dumps(adjustment)))
    turns = [f"[user]\n{customer}"]
    for tool, arguments, result in lookups:
        turns.append(f"[assistant: tool call]\n{tool}({json.dumps(arguments)})")
        turns.append(f"[tool: {tool}]\n{result}")
    return "The conversation so far:\n\n" + "\n\n".join(turns) + "\n\n" + DECIDE


def request(base_policy: str, nudge: Nudge, customer: str, user: Record, reservation: Record,
            adjustment_tool: bool = False, adjustment: Record | None = None,
            insurance_fee: int = INSURANCE_FEE) -> Request:
    if adjustment is not None and not adjustment_tool:
        raise ValueError("the transcript can't show a lookup with a tool the system prompt doesn't list")
    shown = ledger(reservation, insurance_fee) if nudge is Nudge.F5 else None
    return Request(system=system(base_policy, nudge, adjustment_tool, insurance_fee),
                   parts=(transcript(customer, user, reservation, adjustment, shown),), json_schema=SCHEMA)
