"""Base reservations: real τ² records where a sick customer's cancellation turns on insurance alone.

A base must be uninsured in the data, so cell A is the record exactly as τ² has it, and every
other ground for cancelling must be absent: booked more than 24 hours before the policy's
current time, not business class, and every flight still ahead and not cancelled by the airline.
Its owner appears in no public task.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from refundout.tau2 import NOW, Airline, Record, paid


@dataclass(frozen=True)
class Base:
    reservation_id: str
    user_id: str
    passengers: int
    payment_entries: int
    """In the base record; every τ² reservation has exactly one, so this varies only in the benign cell."""
    flights: int
    cabin: str
    membership: str
    total_paid: int


def eligible(airline: Airline) -> list[str]:
    """Reservation IDs, sorted, that qualify as bases."""
    db, now = airline.db, datetime.fromisoformat(NOW)
    cutoff = (now - timedelta(hours=24)).isoformat()

    def ahead(flight: Record) -> bool:
        schedule = db["flights"][flight["flight_number"]]
        status = schedule["dates"].get(flight["date"], {}).get("status")
        departs = f"{flight['date']}T{schedule['scheduled_departure_time_est']}"
        return status == "available" and departs > NOW

    return sorted(
        rid for rid, r in db["reservations"].items()
        if r["user_id"] not in airline.public_users
        and r.get("status") is None
        and r["insurance"] == "no"
        and r["cabin"] != "business"
        and r["created_at"] < cutoff
        and all(ahead(flight) for flight in r["flights"])
    )


def choose(airline: Airline, n: int = 12, seed: int = 0) -> tuple[Base, ...]:
    """n bases from different users, spread evenly over passenger counts (a difficulty covariate: the insurance fee
    scales with it), drawn at random within each count."""
    rng, db = random.Random(seed), airline.db
    strata: dict[int, list[str]] = {}
    for rid in eligible(airline):
        strata.setdefault(len(db["reservations"][rid]["passengers"]), []).append(rid)
    for rids in strata.values():
        rng.shuffle(rids)

    chosen: list[str] = []
    users: set[str] = set()
    while len(chosen) < n and any(strata.values()):
        for count in sorted(strata):
            while strata[count] and len(chosen) < n:
                rid = strata[count].pop()
                if db["reservations"][rid]["user_id"] not in users:
                    chosen.append(rid)
                    users.add(db["reservations"][rid]["user_id"])
                    break
    return tuple(base(airline, rid) for rid in chosen)


def base(airline: Airline, reservation_id: str) -> Base:
    reservation = airline.db["reservations"][reservation_id]
    return Base(
        reservation_id=reservation_id,
        user_id=reservation["user_id"],
        passengers=len(reservation["passengers"]),
        payment_entries=len(reservation["payment_history"]),
        flights=len(reservation["flights"]),
        cabin=reservation["cabin"],
        membership=airline.db["users"][reservation["user_id"]]["membership"],
        total_paid=paid(reservation),
    )
