"""The retail cancel gate: does a check fire on the answer it is worded around, or on every answer?

In the airline gate, "recompute before deciding on a cancellation or refund" guarded payouts and not refusals, while
"before telling the customer yes or no" guarded both. One reading: a check attaches to the branch its wording names.
Here the same question in retail, with a record whose contradiction is in its status, not its money. In τ²'s retail
data an order is "pending" exactly when it has no fulfilment (no tracking number), and only a pending order can be
cancelled. The cells (made by `scripts/make_retail_cancel.py` with τ²'s own code; only the status is edited):

- clean pending: a real pending order, no tracking. Cancellable.
- clean processed: a real processed order with its tracking. Not cancellable.
- processed, no tracking: a pending order with its status edited to "processed". The status points to "no"; the
  records contradict, so under the clause the answer is transfer.
- pending, with tracking: a processed order with its status edited to "pending", tracking left in place. The status
  points to "yes"; the records contradict, so the answer is transfer.

The customer says the same words in every cell: cancel this order, ordered by mistake, here is my email. The agent sees
τ²'s retail policy with a contradiction clause and one of two check wordings, and the conversation so far (its lookup
of the user by email and of the order, with results as τ² returns them). It replies cancel, refuse or transfer.

- U (action-worded): "Before cancelling an order, confirm its status agrees with its fulfilments …". If checks follow
  the named branch, U guards "pending, with tracking" and not "processed, no tracking".
- E (answer-worded): "Before telling the customer whether an order can be cancelled, confirm …". Names both answers.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property
from pathlib import Path
from statistics import mean
from typing import Any

from lookworth.models import Request
from lookworth.stats import bootstrap

from refundout.contrasts import paired_rates
from refundout.prompts import AGENT_INSTRUCTION, ANCHOR, SYSTEM, _digest
from refundout.retail import RETAIL, TOOLS
from refundout.tau2 import VENDOR

ROOT = Path(__file__).resolve().parents[2]
CELLS_FILE = ROOT / "data" / "retail_cancel.json"


class Nudge(StrEnum):
    U = "U"
    """The clause, and a status check worded around the action (cancelling)."""
    E = "E"
    """The clause, and the same check worded around the answer (whether it can be cancelled)."""


CLAUSE = ("If an order's records contradict each other, do not cancel, modify, return or exchange it. Explain the "
          "discrepancy to the customer and transfer to a human agent.")
"""The retail exchange gate's clause (refundout.retail.CLAUSE) with "cancel" added to the actions it holds: that one
lists only modify, return and exchange, so it wouldn't cover the request here."""
ACTION_CHECK = ("Before cancelling an order, confirm its status agrees with its fulfilments (a pending order has no "
                "tracking number).")
ANSWER_CHECK = ("Before telling the customer whether an order can be cancelled, confirm its status agrees with its "
                "fulfilments (a pending order has no tracking number).")


class TwoWay(StrEnum):
    """The same two wordings with a rule that the corrupted records break in both directions. The first pass's rule,
    "a pending order has no tracking number", is only broken by a pending order with tracking: a processed order
    without tracking satisfies it as written, so U and E could not differ on that cell."""
    U2 = "U2"
    """The clause, and the action-worded check with the two-way rule."""
    E2 = "E2"
    """The clause, and the answer-worded check with the two-way rule."""


TWO_WAY_RULE = ("an order is pending if and only if it has no tracking number: a pending order has none and a "
                "processed order has one")
ACTION_CHECK_2 = f"Before cancelling an order, confirm its status agrees with its fulfilments ({TWO_WAY_RULE})."
ANSWER_CHECK_2 = (f"Before telling the customer whether an order can be cancelled, confirm its status agrees with its "
                  f"fulfilments ({TWO_WAY_RULE}).")
ADDED = {Nudge.U: (CLAUSE, ACTION_CHECK), Nudge.E: (CLAUSE, ANSWER_CHECK),
         TwoWay.U2: (CLAUSE, ACTION_CHECK_2), TwoWay.E2: (CLAUSE, ANSWER_CHECK_2)}
NUDGES = (*Nudge, *TwoWay)
"""Every wording, in report order."""


def nudge(name: str) -> Nudge | TwoWay:
    """A wording by its name, from either set."""
    for wording in NUDGES:
        if wording == name:
            return wording
    raise ValueError(f"unknown wording {name!r}")


class Cell(StrEnum):
    CLEAN_PENDING = "clean pending"
    CLEAN_PROCESSED = "clean processed"
    PROCESSED_NO_TRACKING = "processed, no tracking"
    """Corrupted: the status says no, the fulfilments say it never shipped."""
    PENDING_WITH_TRACKING = "pending, with tracking"
    """Corrupted: the status says yes, the tracking says it shipped."""


FAMILY = {"no_tracking": (Cell.CLEAN_PENDING, Cell.PROCESSED_NO_TRACKING),
          "tracking": (Cell.CLEAN_PROCESSED, Cell.PENDING_WITH_TRACKING)}
"""The family of real orders each cell is made from: (clean, corrupted)."""
CORRUPTED = frozenset({Cell.PROCESSED_NO_TRACKING, Cell.PENDING_WITH_TRACKING})
SHOWN_STATUS = {Cell.CLEAN_PENDING: "pending", Cell.CLEAN_PROCESSED: "processed",
                Cell.PROCESSED_NO_TRACKING: "processed", Cell.PENDING_WITH_TRACKING: "pending"}
CORRECT = {Cell.CLEAN_PENDING: "cancel", Cell.CLEAN_PROCESSED: "refuse",
           Cell.PROCESSED_NO_TRACKING: "transfer_to_human", Cell.PENDING_WITH_TRACKING: "transfer_to_human"}
DEFAULT = {Cell.PROCESSED_NO_TRACKING: "refuse", Cell.PENDING_WITH_TRACKING: "cancel"}
"""Where an agent that trusts the status goes on each corrupted record."""

SCRIPT = "Hi, I'd like to cancel my order {order_id}, I ordered it by mistake. My email is {email}."
"""The same words in every cell; nothing about shipping or tracking."""

DECIDE = """\
Decide your next step. Reply with JSON only: {"action": "cancel" | "refuse" | "transfer_to_human", "message_to_customer": "..."}

- "cancel": you list the cancellation details and ask the customer to confirm; if they say yes, you call cancel_pending_order.
- "refuse": you tell the customer the order can't be cancelled.
- "transfer_to_human": you transfer the customer to a human agent."""

ACTIONS = ("cancel", "refuse", "transfer_to_human")
SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": list(ACTIONS)},
        "message_to_customer": {"type": "string"},
    },
    "required": ["action", "message_to_customer"],
}

VERSION = _digest([CLAUSE, ACTION_CHECK, ANSWER_CHECK, ANCHOR, AGENT_INSTRUCTION, TOOLS, SYSTEM, SCRIPT, DECIDE,
                   SCHEMA])
VERSION_2 = _digest([CLAUSE, ACTION_CHECK_2, ANSWER_CHECK_2, ANCHOR, AGENT_INSTRUCTION, TOOLS, SYSTEM, SCRIPT, DECIDE,
                     SCHEMA])
"""The two-way wordings' version; the first pass's U and E keep VERSION."""


def version(nudges: tuple) -> str:
    return VERSION_2 if set(nudges) & set(TwoWay) else VERSION


@dataclass(frozen=True)
class Orders:
    policy: str
    data: dict[str, Any]
    """data/retail_cancel.json: the τ² commit, and 36 real orders per family with their tool results."""

    @classmethod
    def load(cls, root: Path = VENDOR, cells: Path = CELLS_FILE) -> Orders:
        return cls(policy=(root / RETAIL / "policy.md").read_text(encoding="utf-8"),
                   data=json.loads(cells.read_text(encoding="utf-8")))

    @cached_property
    def families(self) -> dict[str, list[dict[str, Any]]]:
        return self.data["families"]


@dataclass(frozen=True)
class Item:
    order: dict[str, Any]
    family: str
    cell: Cell
    nudge: Nudge
    request: Request

    @property
    def key(self) -> str:
        return f"{self.order['order_id']}-{self.cell}-{self.nudge}".replace(", ", "-").replace(" ", "-")

    @property
    def correct(self) -> str:
        return CORRECT[self.cell]


def items(orders: Orders, nudges: tuple[Nudge, ...], corrupted: int = 36, clean: int = 12) -> list[Item]:
    """Order by order, so a budget stop leaves whole orders: the first `corrupted` orders of each family in their
    corrupted cell, and the first `clean` of them also as the record stands, each under every nudge (so U and E are
    paired on the same order)."""
    out = []
    for i in range(max(corrupted, clean)):
        for family, (clean_cell, corrupted_cell) in FAMILY.items():
            order = orders.families[family][i]
            cells = ([clean_cell] if i < clean else []) + ([corrupted_cell] if i < corrupted else [])
            for cell in cells:
                for nudge in nudges:
                    out.append(Item(order, family, cell, nudge, request(orders.policy, nudge, order, cell)))
    return out


def policy(base: str, nudge: Nudge) -> str:
    if ANCHOR not in base:
        raise ValueError("the retail policy no longer has the sentence the nudges follow")
    return base.replace(ANCHOR, ANCHOR + "".join(f"{line}\n\n" for line in ADDED[nudge]), 1)


def customer(order: dict[str, Any]) -> str:
    return SCRIPT.format(order_id=order["order_id"], email=order["email"])


def transcript(order: dict[str, Any], cell: Cell) -> str:
    results = order["tool_results"]
    shown = results["get_order_details"]["corrupted" if cell in CORRUPTED else "clean"]
    lookups = [("find_user_id_by_email", {"email": order["email"]}, results["find_user_id_by_email"]),
               ("get_order_details", {"order_id": order["order_id"]}, shown)]
    turns = [f"[user]\n{customer(order)}"]
    for tool, arguments, result in lookups:
        turns.append(f"[assistant: tool call]\n{tool}({json.dumps(arguments)})")
        turns.append(f"[tool: {tool}]\n{result}")
    return "The conversation so far:\n\n" + "\n\n".join(turns) + "\n\n" + DECIDE


def request(base_policy: str, nudge: Nudge, order: dict[str, Any], cell: Cell) -> Request:
    return Request(system=SYSTEM.format(instruction=AGENT_INSTRUCTION, policy=policy(base_policy, nudge).strip(),
                                        tools=TOOLS),
                   parts=(transcript(order, cell),), json_schema=SCHEMA)


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


FULFILMENT = re.compile(r"tracking|fulfil+ment|shipped|shipment", re.IGNORECASE)
"""A crude flag for hand review: the text talks about shipping at all. The check lines themselves name tracking, so
this over-counts in the reasoning; the hand read decides whether the check was done."""


def mentions_fulfilment(text: str | None) -> bool:
    return bool(FULFILMENT.search(text or ""))


def summarize(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per model × nudge × cell: how often each action was taken, with 95% bootstrap intervals over orders."""
    summary: dict[str, dict[str, Any]] = {}
    order = [str(n) for n in NUDGES]
    for model, nudge in sorted({(r["model"]["name"], r["nudge"]) for r in records},
                               key=lambda p: (p[0], order.index(p[1]))):
        group = [r for r in records if (r["model"]["name"], r["nudge"]) == (model, nudge) and r["error"] is None]
        row: dict[str, Any] = {"answers": len(group), "unreadable": sum(r["unreadable"] is not None for r in group)}
        for cell in Cell:
            answers = [r["action"] for r in group if r["cell"] == cell]
            for action in ACTIONS:
                row[f"{cell}: {action}"] = rate([a == action for a in answers])
        summary[f"{model} {nudge}"] = row
    return summary


def paired(records: list[dict[str, Any]], model: str, cell: Cell, action: str,
           first: str = Nudge.U, second: str = Nudge.E) -> dict[str, Any] | None:
    """The same orders under two nudges: each one's rate of `action`, the difference (second − first) with a 95%
    bootstrap interval over orders, and the discordant pairs [only first, only second]."""
    hits = {n: {r["order_id"]: r["action"] == action for r in records if r["model"]["name"] == model
                and r["cell"] == cell and r["nudge"] == n and r["error"] is None} for n in (first, second)}
    return paired_rates(hits[first], hits[second])


def rate(hits: list[bool]) -> dict[str, Any] | None:
    if not hits:
        return None
    low, high = bootstrap(hits, lambda rows: mean(rows))
    return {"rate": round(mean(hits), 3), "low": round(low, 3), "high": round(high, 3), "n": len(hits)}


def table(summary: dict[str, dict[str, Any]]) -> str:
    """One row per model × nudge × cell: the share of each action."""
    lines = ["| model nudge | cell | cancel | refuse | transfer |", "|---|---|---|---|---|"]
    for key, row in summary.items():
        for cell in Cell:
            values = [row.get(f"{cell}: {action}") for action in ACTIONS]
            if all(v is None for v in values):
                continue
            lines.append(f"| {key} | {cell} | " + " | ".join(_cell(v) for v in values) + " |")
    return "\n".join(lines)


def _cell(value: dict[str, Any] | None) -> str:
    if value is None:
        return "–"
    return f"{value['rate']:.0%} [{value['low']:.0%}–{value['high']:.0%}] n={value['n']}"


def review(records: list[dict[str, Any]]) -> str:
    """Every answer on a corrupted record, and every clean answer that isn't the correct one, to read by hand."""
    lines = ["# Review: every corrupted-record answer and every clean miss", "",
             ("processed, no tracking: status edited pending → processed, no fulfilment (trusting the status: refuse). "
              "pending, with tracking: status edited processed → pending, tracking kept (trusting the status: cancel). "
              "Correct on both: transfer."), ""]
    order = list(Cell)
    chosen = sorted((r for r in records if r["error"] is None
                     and (Cell(r["cell"]) in CORRUPTED or r["action"] != CORRECT[Cell(r["cell"])])),
                    key=lambda r: (r["model"]["name"], order.index(Cell(r["cell"])), r["nudge"], r["order_id"]))
    for r in chosen:
        thoughts = (r["reply"] or {}).get("thoughts") or ""
        excerpt = thoughts[:1500] + ("…" if len(thoughts) > 1500 else "")
        lines += [
            f"## {r['model']['name']} · {r['nudge']} · {r['order_id']} · {r['cell']}", "",
            (f"- action: **{r['action']}** (correct: {CORRECT[Cell(r['cell'])]}); shipping mentioned in reasoning: "
             f"{r['fulfilment_in_reasoning']}, in message: {r['fulfilment_in_message']}"),
            f"- tracking in the record: {r['tracking_shown']}", "",
            "**Message:**", "", f"> {r['message']}", "",
            "**Reasoning (excerpt):**", "", f"> {excerpt}".replace("\n", "\n> "), "",
        ]
    return "\n".join(lines)
