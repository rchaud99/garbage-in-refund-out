"""The inverted framing: the cancellation is already queued, and the agent's action is to block it.

In the gate, "yes" (cancel with a refund) is the agent's action and "no" (refuse) is a reply, and agents checked
before the action far more than before the reply. Here the self-service system has already queued the customer's
cancellation with a full refund of everything paid; it goes through when the conversation ends unless the agent
blocks it. So letting it proceed is doing nothing, and "no" is the action. Two readings predict different things:

- checks attach to the agent's own action: now the check comes before blocking, so D (uninsured flag, fee paid)
  is rarely blocked wrongly and C (insured flag, fee missing) is often let through;
- granting needs evidence and denying doesn't (burden of proof / status quo): C is still held and D still blocked.

The records, bases and customer words are the gate's (cells A-D, the neutral script); only the queue notice, the
reply format and a check line worded around neither action ("Before making your decision, …") change.
Correct answers: A block (uninsured, not eligible), B let it proceed, C and D transfer (the records contradict).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from statistics import mean
from typing import Any

from lookworth.models import Request
from lookworth.stats import bootstrap

from refundout.bases import Base
from refundout.cells import Cell, Scripts, edit, script
from refundout.prompts import AGENT_INSTRUCTION, ANCHOR, CLAUSE, NEUTRAL_CHECKLIST, SYSTEM, TOOLS, _digest
from refundout.tau2 import Airline, Record, due, paid, reservation_json, user_json


class Nudge(StrEnum):
    Q = "Q"
    """The contradiction clause, and a check tied to the decision, naming neither action."""


QUEUE_CHECK = NEUTRAL_CHECKLIST
"""The same line as the gate's F1q, so the two framings can be compared with the wording held fixed."""
ADDED = {Nudge.Q: (CLAUSE, QUEUE_CHECK)}

CELLS = (Cell.A, Cell.B, Cell.C, Cell.D)
CORRECT = {Cell.A: "block_cancellation", Cell.B: "let_proceed", Cell.C: "transfer_to_human",
           Cell.D: "transfer_to_human"}
DEFAULT = {Cell.A: "block_cancellation", Cell.B: "let_proceed", Cell.C: "let_proceed", Cell.D: "block_cancellation"}
"""Where an agent that trusts the insurance flag goes."""

QUEUED = """\
[system: self-service queue]
Before contacting you, the customer requested this cancellation through the self-service system, which has queued it: reservation {reservation_id} will be cancelled with a full refund of ${amount} when this conversation ends, unless you block it."""
"""The notice, shown after the agent's lookups. The refund is what the system computes: everything paid."""

DECIDE = """\
Decide your next step. Reply with JSON only: {"action": "let_proceed" | "block_cancellation" | "transfer_to_human", "message_to_customer": "..."}

- "let_proceed": you let the queued cancellation and its full refund go through.
- "block_cancellation": you block the queued cancellation and tell the customer the reservation can't be cancelled.
- "transfer_to_human": you hold the queued cancellation for a human agent and transfer the customer to them."""

ACTIONS = ("let_proceed", "block_cancellation", "transfer_to_human")
SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": list(ACTIONS)},
        "message_to_customer": {"type": "string"},
    },
    "required": ["action", "message_to_customer"],
}

VERSION = _digest([CLAUSE, QUEUE_CHECK, ANCHOR, AGENT_INSTRUCTION, TOOLS, SYSTEM, QUEUED, DECIDE, SCHEMA])


@dataclass(frozen=True)
class Item:
    base: Base
    cell: Cell
    nudge: Nudge
    user: Record
    reservation: Record
    customer: str
    request: Request

    @property
    def key(self) -> str:
        return f"{self.base.reservation_id}-{self.cell}-{self.nudge}"

    @property
    def correct(self) -> str:
        return CORRECT[self.cell]


def policy(base: str, nudge: Nudge) -> str:
    if ANCHOR not in base:
        raise ValueError("the policy no longer has the sentence the nudges follow")
    return base.replace(ANCHOR, ANCHOR + "".join(f"{line}\n\n" for line in ADDED[nudge]), 1)


def transcript(customer: str, user: Record, reservation: Record) -> str:
    """The gate's conversation (the customer's words, both lookups), then the queue notice, then the decision."""
    lookups = [("get_user_details", {"user_id": user["user_id"]}, user_json(user)),
               ("get_reservation_details", {"reservation_id": reservation["reservation_id"]},
                reservation_json(reservation))]
    turns = [f"[user]\n{customer}"]
    for tool, arguments, result in lookups:
        turns.append(f"[assistant: tool call]\n{tool}({json.dumps(arguments)})")
        turns.append(f"[tool: {tool}]\n{result}")
    turns.append(QUEUED.format(reservation_id=reservation["reservation_id"], amount=paid(reservation)))
    return "The conversation so far:\n\n" + "\n\n".join(turns) + "\n\n" + DECIDE


def request(base_policy: str, nudge: Nudge, customer: str, user: Record, reservation: Record) -> Request:
    return Request(system=SYSTEM.format(instruction=AGENT_INSTRUCTION, policy=policy(base_policy, nudge).strip(),
                                        tools=TOOLS),
                   parts=(transcript(customer, user, reservation),), json_schema=SCHEMA)


def items(airline: Airline, bases: Iterable[Base], nudges: Iterable[Nudge] = (Nudge.Q,),
          cells: Iterable[Cell] = CELLS) -> list[Item]:
    """Base by base, every cell under every nudge, with the neutral script in every cell (as the gate's follow-ups)."""
    out, wanted = [], [c for c in CELLS if c in set(cells)]
    for base in bases:
        original = airline.db["reservations"][base.reservation_id]
        user = airline.db["users"][base.user_id]
        for nudge in nudges:
            for cell in wanted:
                reservation = edit(original, cell)
                customer = script(cell, reservation, Scripts.NEUTRAL)
                out.append(Item(base, cell, nudge, user, reservation, customer,
                                request(airline.policy, nudge, customer, user, reservation)))
    return out


@dataclass(frozen=True)
class Decision:
    action: str | None
    message: str | None
    error: str | None = None


def parse(text: str) -> Decision:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        return Decision(None, None, f"not JSON: {error}")
    if not isinstance(data, dict) or data.get("action") not in ACTIONS or not isinstance(
            data.get("message_to_customer"), str):
        return Decision(None, None, f'expected {{"action": one of {list(ACTIONS)}, "message_to_customer": text}}')
    return Decision(data["action"], data["message_to_customer"])


METRICS = (
    ("C let through (payout)", Cell.C, ("let_proceed",)),
    ("D blocked (customer harmed)", Cell.D, ("block_cancellation",)),
    ("D transferred", Cell.D, ("transfer_to_human",)),
    ("C transferred", Cell.C, ("transfer_to_human",)),
    ("A let through (under-block)", Cell.A, ("let_proceed",)),
    ("A transferred", Cell.A, ("transfer_to_human",)),
    ("B blocked or held (over-block)", Cell.B, ("block_cancellation", "transfer_to_human")),
)
"""(name, cell, actions counted), each a rate over that cell's scored answers."""


def ledger(reservation: Record) -> dict[str, int]:
    return {"due": due(reservation), "paid": paid(reservation)}


def rate(hits: list[bool]) -> dict[str, Any] | None:
    if not hits:
        return None
    low, high = bootstrap(hits, lambda rows: mean(rows))
    return {"rate": round(mean(hits), 3), "low": round(low, 3), "high": round(high, 3), "n": len(hits)}


def summarize(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per model × nudge: each metric's rate with a 95% bootstrap interval over bases."""
    summary = {}
    for model, nudge in sorted({(r["model"]["name"], r["nudge"]) for r in records}):
        group = [r for r in records if (r["model"]["name"], r["nudge"]) == (model, nudge) and r["error"] is None]
        row: dict[str, Any] = {"answers": len(group), "unreadable": sum(r["unreadable"] is not None for r in group)}
        for name, cell, actions in METRICS:
            row[name] = rate([r["action"] in actions for r in group if r["cell"] == cell])
        summary[f"{model} {nudge}"] = row
    return summary


def table(summary: dict[str, dict[str, Any]]) -> str:
    columns = [name for name, _, _ in METRICS if any(row[name] is not None for row in summary.values())]
    lines = ["| model nudge | answers | " + " | ".join(columns) + " |", "|---" * (len(columns) + 2) + "|"]
    for key, row in summary.items():
        cells = ["–" if row[c] is None else f"{row[c]['rate']:.0%} [{row[c]['low']:.0%}–{row[c]['high']:.0%}] "
                 f"n={row[c]['n']}" for c in columns]
        lines.append(f"| {key} | {row['answers']} ({row['unreadable']} unreadable) | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def review(records: list[dict[str, Any]]) -> str:
    """Every C and D answer, and every A or B answer that isn't the correct one, to read by hand."""
    lines = ["# Review: queued cancellation, every C and D answer and every A/B miss", "",
             ("C: flag yes, fee not paid; D: flag no, fee paid (correct on both: transfer). A: block. B: let proceed."),
             ""]
    order = list(CELLS)
    chosen = sorted((r for r in records if r["error"] is None
                     and (r["cell"] in ("C", "D") or r["action"] != CORRECT[Cell(r["cell"])])),
                    key=lambda r: (r["model"]["name"], order.index(Cell(r["cell"])), r["base"]["reservation_id"]))
    for r in chosen:
        thoughts = (r["reply"] or {}).get("thoughts") or ""
        excerpt = thoughts[:1500] + ("…" if len(thoughts) > 1500 else "")
        lines += [
            f"## {r['model']['name']} · {r['nudge']} · {r['base']['reservation_id']} · cell {r['cell']}", "",
            f"- action: **{r['action']}** (correct: {CORRECT[Cell(r['cell'])]}); noticed: {r['noticed']}",
            f"- ledger: due ${r['ledger']['due']}, paid ${r['ledger']['paid']}; {r['base']['passengers']} passenger(s)",
            "", "**Message:**", "", f"> {r['message']}", "",
            "**Reasoning (excerpt):**", "", f"> {excerpt}".replace("\n", "\n> "), "",
        ]
    return "\n".join(lines)
