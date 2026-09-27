"""τ²-bench's airline domain, read from the vendored clone: its database, policy, public tasks and tool JSON.

Only data is read; none of τ²'s code runs here. The tool JSON is rebuilt to match what τ²'s
tools return (`Environment.to_json_str`: pydantic's field order, `status: null`, float balances),
and a test checks it against output made by τ² itself.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

VENDOR = Path(__file__).resolve().parents[2] / "vendor" / "tau2-bench"
AIRLINE = Path("data/tau2/domains/airline")

NOW = "2024-05-15T15:00:00"
"""The policy's "current time" (2024-05-15 15:00:00 EST), which τ²'s tools also use for new bookings."""
INSURANCE_FEE = 30
"""Dollars per passenger."""
BAG_FEE = 50
"""Dollars per paid (non-free) bag."""

Record = dict[str, Any]


@dataclass(frozen=True)
class Airline:
    db: Record
    policy: str
    tasks: tuple[Record, ...]
    commit: str
    """The vendored clone's git commit, saved with every run."""

    @classmethod
    def load(cls, root: Path = VENDOR) -> Airline:
        if not root.exists():
            raise FileNotFoundError(f"clone https://github.com/sierra-research/tau2-bench into {root}")
        data = root / AIRLINE
        return cls(
            db=json.loads((data / "db.json").read_text(encoding="utf-8")),
            policy=(data / "policy.md").read_text(encoding="utf-8"),
            tasks=tuple(json.loads((data / "tasks.json").read_text(encoding="utf-8"))),
            commit=subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True,
                                  check=True).stdout.strip(),
        )

    @cached_property
    def public_users(self) -> frozenset[str]:
        """Users named anywhere in a public task, whose records a model may have seen in published transcripts."""
        text = json.dumps(self.tasks)
        return frozenset(user for user in self.db["users"] if user in text)


def due(reservation: Record, insurance_fee: int = INSURANCE_FEE) -> int:
    """What the reservation should have cost: fares × passengers, plus insurance and paid bags."""
    passengers = len(reservation["passengers"])
    fares = sum(flight["price"] for flight in reservation["flights"]) * passengers
    insurance = insurance_fee * passengers if reservation["insurance"] == "yes" else 0
    return fares + insurance + BAG_FEE * reservation["nonfree_baggages"]


def paid(reservation: Record) -> int:
    return sum(payment["amount"] for payment in reservation["payment_history"])


_USER = ("user_id", "name", "address", "email", "dob", "payment_methods", "saved_passengers", "membership",
         "reservations")
_ADDRESS = ("address1", "address2", "city", "country", "state", "zip")
_RESERVATION = ("reservation_id", "user_id", "origin", "destination", "flight_type", "cabin", "flights", "passengers",
                "payment_history", "created_at", "total_baggages", "nonfree_baggages", "insurance", "status")
_FLIGHT = ("flight_number", "origin", "destination", "date", "price")
_PASSENGER = ("first_name", "last_name", "dob")
_METHOD = {"credit_card": ("source", "id", "brand", "last_four"), "gift_card": ("source", "id", "amount"),
           "certificate": ("source", "id", "amount")}


def user_json(user: Record) -> str:
    """get_user_details's result, as τ² hands it to the agent."""
    methods = {key: _pick(method, _METHOD[method["source"]]) for key, method in user["payment_methods"].items()}
    for method in methods.values():
        if "amount" in method:
            method["amount"] = float(method["amount"])
    return json.dumps({
        **_pick(user, _USER),
        "name": _pick(user["name"], ("first_name", "last_name")),
        "address": _pick(user["address"], _ADDRESS),
        "payment_methods": methods,
        "saved_passengers": [_pick(p, _PASSENGER) for p in user["saved_passengers"]],
    })


def reservation_json(reservation: Record) -> str:
    """get_reservation_details's result, as τ² hands it to the agent."""
    return json.dumps({
        **_pick(reservation, _RESERVATION),
        "flights": [_pick(flight, _FLIGHT) for flight in reservation["flights"]],
        "passengers": [_pick(p, _PASSENGER) for p in reservation["passengers"]],
        "payment_history": [_pick(p, ("payment_id", "amount")) for p in reservation["payment_history"]],
    })


def _pick(record: Record, keys: tuple[str, ...]) -> Record:
    """The keys in the model's order; a field the data leaves out is null, as pydantic's default makes it."""
    return {key: record.get(key) for key in keys}
