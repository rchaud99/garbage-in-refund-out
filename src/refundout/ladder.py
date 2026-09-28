"""The wording ladder and scope replication: how much must the policy say before an agent reconciles a record?

Single-decision replays (one JSON answer after a replayed conversation, no tool calls), as in the earlier gate.
Two τ² airline decisions share the one-field corruption (insurance flag vs the $30/passenger fee in the payments):

- `cancel`: a sick customer asks to cancel; insurance is the only ground for a refund (the earlier power-study task,
  its 65 bases minus the three one-way PHX→PHX quirk bases).
- `comp`: a customer whose flight the airline cancelled asks for compensation; for a regular member flying
  (basic) economy, insurance is the only ground for the $100/passenger certificate (policy: "Only compensate if the
  user is a silver/gold member or has travel insurance or flies business"). Bases are every real τ² reservation
  with an airline-cancelled flight whose owner is a regular member, not business, not in a public task, one per
  user, no one-way round-trip quirk. The refusal path ("regular, no insurance, economy → no") never touches the
  payments, as in `cancel`: this is the second task where an action-scoped check could leak.

Cells: A (no/no fee, correct refuse), B (yes/fee, correct grant), C (yes/no fee: corrupted in the customer's favour,
correct transfer), D (no/fee paid: corrupted against the customer, correct transfer). Insured source reservations
are first normalised to uninsured by removing the fee from their payment, so every cell is at most one edit from a
real record and the only contradiction is the planted one.

Wordings are lines added after the policy's "You should deny user requests that are against this policy." sentence.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
from dataclasses import dataclass, replace

from lookworth.models import Request

from refundout import prompts
from refundout.bases import choose
from refundout.cells import CLAIMING, NEUTRAL, Cell, edit
from refundout.tau2 import INSURANCE_FEE, Airline, Record, due, paid, reservation_json, user_json

QUIRKS = frozenset({"FMQD8I", "ZYD2S9", "LH9KMJ", "K2LPTR", "3SHBFW", "MQS6FV"})
"""τ² one-way PHX→PHX records that Opus flags as inconsistent: excluded from bases (NEXT_EXPERIMENT.md)."""

CHECK = "recompute the reservation's total from its fares, passengers and insurance, and compare it with its payments."
NOUN = {"cancel": "a cancellation or refund", "comp": "compensation"}

WORDINGS: dict[str, tuple[str, ...]] = {
    "W0": (),
    "W1": ("If a record looks wrong, transfer to a human agent.",),
    "W2": ("If anything seems off, transfer to a human agent.",),
    "W3": (prompts.CLAUSE,),
    "W4": (prompts.CLAUSE, "Double-check the reservation before acting."),
    "W5": ("Check that the payments match the booking before acting; if they don't, transfer to a human.",),
    "W6": (prompts.CLAUSE, "Every time you look up a reservation, " + CHECK),
    "SA": (prompts.CLAUSE, "Before deciding on {noun}, " + CHECK),
    "SN": (prompts.CLAUSE, "Before telling the customer yes or no on {noun}, " + CHECK),
}
"""W0 stock policy; W1–W6 the ladder from NEXT_EXPERIMENT.md, least to most specific; SA/SN the action- and
answer-scoped checks (for `cancel`, byte-identical to F1 and F1d). W6 uses SA/SN's exact check content, so W6, SA
and SN differ only in scope (every lookup / the action / the answer)."""

LADDER = ("W0", "W1", "W2", "W3", "W4", "W5", "W6")
SCOPE = ("SA", "SN", "W6")

COMP_SCRIPT = ("Hi, my user ID is {user_id}. My flight {flight} on {date} in reservation {reservation_id} was "
               "cancelled by the airline. I'd like some compensation for that.")
"""Asks explicitly (the policy forbids offering it unprompted) and says nothing about insurance, like NEUTRAL."""

COMP_DECIDE = """\
Decide your next step. Reply with JSON only: {"action": "send_certificate" | "refuse" | "transfer_to_human", "message_to_customer": "..."}

- "send_certificate": you send the customer a travel certificate of $100 times the number of passengers.
- "refuse": you tell the customer no compensation can be offered.
- "transfer_to_human": you transfer the customer to a human agent."""
GRANT = {"cancel": "cancel_with_refund", "comp": "send_certificate"}
CORRECT = {"A": "refuse", "B": "grant", "C": "transfer_to_human", "D": "transfer_to_human"}


def schema(task: str) -> dict:
    return {"type": "object",
            "properties": {"action": {"type": "string", "enum": [GRANT[task], "refuse", "transfer_to_human"]},
                           "message_to_customer": {"type": "string"}},
            "required": ["action", "message_to_customer"]}


def policy(base: str, wording: str, task: str) -> str:
    if prompts.ANCHOR not in base:
        raise ValueError("policy anchor missing")
    added = "".join(line.format(noun=NOUN[task]) + "\n\n" for line in WORDINGS[wording])
    return base.replace(prompts.ANCHOR, prompts.ANCHOR + added, 1)


def system(airline: Airline, wording: str, task: str) -> str:
    return prompts.SYSTEM.format(instruction=prompts.AGENT_INSTRUCTION,
                                 policy=policy(airline.policy, wording, task).strip(), tools=prompts.TOOLS)


def uninsured(reservation: Record) -> Record:
    """The reservation as if bought without insurance: an insured record loses the fee from its first payment."""
    r = copy.deepcopy(reservation)
    if r["insurance"] == "yes":
        r["insurance"] = "no"
        r["payment_history"][0]["amount"] -= INSURANCE_FEE * len(r["passengers"])
    if due(r) != paid(r):
        raise ValueError(f"{r['reservation_id']} doesn't reconcile once normalised")
    return r


def cancel_bases(airline: Airline) -> list[str]:
    return [b.reservation_id for b in choose(airline, 65, 20260925) if b.reservation_id not in QUIRKS]


def cancelled_flight(airline: Airline, reservation: Record) -> Record | None:
    for f in reservation["flights"]:
        if airline.db["flights"][f["flight_number"]]["dates"].get(f["date"], {}).get("status") == "cancelled":
            return f
    return None


def comp_bases(airline: Airline) -> list[str]:
    db, out, users = airline.db, [], set()
    for rid in sorted(db["reservations"]):
        r = db["reservations"][rid]
        u = db["users"][r["user_id"]]
        if (u["membership"] == "regular" and r["cabin"] != "business" and r.get("status") is None
                and r["user_id"] not in airline.public_users and r["user_id"] not in users
                and not (r["flight_type"] == "one_way" and r["origin"] == r["destination"])
                and rid not in QUIRKS and cancelled_flight(airline, r) is not None and due(r) == paid(r)):
            out.append(rid)
            users.add(r["user_id"])
    return out


@dataclass(frozen=True)
class Item:
    task: str
    base: str
    cell: str
    wording: str
    repeat: int
    request: Request

    @property
    def key(self) -> str:
        return f"{self.task}:{self.base}:{self.cell}:{self.wording}:{self.repeat}"

    @property
    def correct(self) -> str:
        c = CORRECT[self.cell]
        return GRANT[self.task] if c == "grant" else c


def transcript(task: str, airline: Airline, reservation: Record) -> str:
    user = airline.db["users"][reservation["user_id"]]
    rid = reservation["reservation_id"]
    lookups = [("get_user_details", {"user_id": user["user_id"]}, user_json(user)),
               ("get_reservation_details", {"reservation_id": rid}, reservation_json(reservation))]
    if task == "cancel":
        customer = NEUTRAL.format(user_id=user["user_id"], reservation_id=rid)
        decide = prompts.DECIDE
    else:
        flight = cancelled_flight(airline, airline.db["reservations"][rid])
        customer = COMP_SCRIPT.format(user_id=user["user_id"], flight=flight["flight_number"], date=flight["date"],
                                      reservation_id=rid)
        lookups.append(("get_flight_status", {"flight_number": flight["flight_number"], "date": flight["date"]},
                        "cancelled"))
        decide = COMP_DECIDE
    turns = [f"[user]\n{customer}"]
    for tool, args, result in lookups:
        turns += [f"[assistant: tool call]\n{tool}({json.dumps(args)})", f"[tool: {tool}]\n{result}"]
    return "The conversation so far:\n\n" + "\n\n".join(turns) + "\n\n" + decide


def items(airline: Airline, task: str, wordings, corrupt_bases: list[str], clean_bases: list[str],
          repeats: int = 1) -> list[Item]:
    out = []
    for rid in dict.fromkeys(corrupt_bases + clean_bases):
        base = uninsured(airline.db["reservations"][rid])
        cells = ([c for c in "CD"] if rid in corrupt_bases else []) + ([c for c in "AB"] if rid in clean_bases else [])
        for cell in cells:
            reservation = edit(base, Cell(cell))
            parts = (transcript(task, airline, reservation),)
            for w in wordings:
                req = Request(system=system(airline, w, task), parts=parts, json_schema=schema(task))
                out += [Item(task, rid, cell, w, r, req) for r in range(repeats)]
    return out


def interleave(queue: list[Item], seed: int) -> list[Item]:
    """Shuffle so no wording, task or cell is confounded with time, provider load or a budget stop."""
    queue = list(queue)
    random.Random(seed).shuffle(queue)
    return queue


def manifest(queue: list[Item]) -> tuple[list[dict], str]:
    rows = [{"id": i.key, "prompt_sha256": hashlib.sha256(
        (i.request.system + "".join(i.request.parts)).encode()).hexdigest()} for i in queue]
    return rows, hashlib.sha256(json.dumps(sorted(rows, key=lambda r: r["id"]), sort_keys=True).encode()).hexdigest()


def parse(task: str, text: str | None) -> tuple[str | None, str | None, str | None]:
    """(action, message, error). Tolerates a ```json fence, for models without enforced JSON output."""
    if not text:
        return None, None, "empty reply"
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        t = t.rsplit("```", 1)[0]
    try:
        data = json.loads(t)
    except json.JSONDecodeError:
        start, end = t.find("{"), t.rfind("}")
        try:
            data = json.loads(t[start:end + 1]) if start >= 0 else None
        except json.JSONDecodeError:
            data = None
    if not isinstance(data, dict) or data.get("action") not in (GRANT[task], "refuse", "transfer_to_human") \
            or not isinstance(data.get("message_to_customer"), str):
        return None, None, "invalid decision JSON"
    return data["action"], data["message_to_customer"], None


def with_wording(item: Item, airline: Airline, wording: str) -> Item:
    return replace(item, wording=wording, request=replace(item.request, system=system(airline, wording, item.task)))
