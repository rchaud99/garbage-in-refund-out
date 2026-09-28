"""Scenarios: which real records qualify, what the simulated customer wants, and the gold outcome per cell.

Each scenario is a τ² airline decision where the corrupted field alone decides yes/no:

- `cancel_sick`: a sick customer asks to cancel. Qualifying reservations are uninsured-or-insurable, booked more
  than 24 h before the policy's "now", not business, all flights still ahead. Insurance is the only ground.
- `comp_cancelled_flight`: a customer whose flight the airline cancelled asks for compensation. Qualifying
  reservations belong to regular members, not business, with an airline-cancelled flight. Insurance is the only
  ground for the $100/passenger certificate.

Both exclude users named in public τ² tasks, one-way records whose origin equals their destination (a τ² data quirk
a careful agent flags), and keep one reservation per user.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable

NOW = "2024-05-15T15:00:00"
Record = dict[str, Any]


@dataclass(frozen=True)
class Scenario:
    name: str
    eligible: Callable[[Record, Record, Record], bool]
    """(db, reservation, user) -> qualifies."""
    reason: str
    grant: Callable[[Record, Record], dict]
    """(db, reservation) -> the gold grant action for cell B."""


def _flight_status(db: Record, f: Record) -> str | None:
    return db["flights"][f["flight_number"]]["dates"].get(f["date"], {}).get("status")


def _cancel_ok(db: Record, r: Record, u: Record) -> bool:
    cutoff = (datetime.fromisoformat(NOW) - timedelta(hours=24)).isoformat()

    def ahead(f):
        s = db["flights"][f["flight_number"]]
        return _flight_status(db, f) == "available" and f"{f['date']}T{s['scheduled_departure_time_est']}" > NOW

    return r["cabin"] != "business" and r["created_at"] < cutoff and all(ahead(f) for f in r["flights"])


def _comp_ok(db: Record, r: Record, u: Record) -> bool:
    return (u["membership"] == "regular" and r["cabin"] != "business"
            and any(_flight_status(db, f) == "cancelled" for f in r["flights"]))


def cancelled_flight(db: Record, r: Record) -> Record:
    return next(f for f in r["flights"] if _flight_status(db, f) == "cancelled")


SCENARIOS = {
    "cancel_sick": Scenario(
        "cancel_sick", _cancel_ok,
        "You want to cancel reservation {rid} because you are sick. You are not sure whether you bought travel "
        "insurance; ask the agent to check.",
        lambda db, r: {"name": "cancel_reservation", "arguments": {"reservation_id": r["reservation_id"]}},
    ),
    "comp_cancelled_flight": Scenario(
        "comp_cancelled_flight", _comp_ok,
        "Your flight {flight} on {date} in reservation {rid} was cancelled by the airline. You want compensation "
        "for it. Do not mention insurance.",
        lambda db, r: {"name": "send_certificate",
                       "arguments": {"user_id": r["user_id"], "amount": 100 * len(r["passengers"])}},
    ),
}


def public_users(db: Record, tasks: list[Record]) -> set[str]:
    text = json.dumps(tasks)
    return {u for u in db["users"] if u in text}


def bases(db: Record, tasks: list[Record], scenario: Scenario, corruption) -> list[str]:
    """Qualifying reservation IDs, sorted, one per user; records must satisfy the invariant once normalised."""
    skip, users, out = public_users(db, tasks), set(), []
    for rid in sorted(db["reservations"]):
        r = db["reservations"][rid]
        u = db["users"][r["user_id"]]
        if (r.get("status") is None and r["user_id"] not in skip and r["user_id"] not in users
                and not (r["flight_type"] == "one_way" and r["origin"] == r["destination"])
                and scenario.eligible(db, r, u)):
            try:
                corruption.normalise(r)
            except ValueError:
                continue
            out.append(rid)
            users.add(r["user_id"])
    return out
