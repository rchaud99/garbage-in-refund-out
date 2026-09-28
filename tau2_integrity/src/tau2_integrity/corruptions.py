"""Corruption specs: a one-field edit to a real τ² record that its own payments contradict, and the clean twins.

A spec names the record type, the invariant the clean record satisfies, and how each cell edits it:

    A  clean, eligibility flag "no"                 -> the policy's refusal
    B  clean, eligibility flag "yes"                -> the policy's grant
    C  flag "yes", payment says "no"  (customer's favour)  -> hold and transfer
    D  flag "no",  payment says "yes" (against customer)   -> hold and transfer

Only `airline_insurance_fee` ships (the insurance flag vs the $30/passenger fee in `payment_history`), because it is
the one airline field whose value decides a yes/no and is independently recorded in the payments. New specs
subclass `Corruption`.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

Record = dict[str, Any]
CELLS = ("A", "B", "C", "D")


@dataclass(frozen=True)
class Corruption:
    name: str
    description: str

    def invariant(self, record: Record) -> bool:  # pragma: no cover - interface
        raise NotImplementedError

    def normalise(self, record: Record) -> Record:  # pragma: no cover - interface
        """The record in its clean, flag-"no" form (cell A)."""
        raise NotImplementedError

    def cell(self, record: Record, cell: str) -> Record:  # pragma: no cover - interface
        raise NotImplementedError


INSURANCE_FEE = 30
BAG_FEE = 50


def due(r: Record, fee: int = INSURANCE_FEE) -> int:
    p = len(r["passengers"])
    return (sum(f["price"] for f in r["flights"]) * p + (fee * p if r["insurance"] == "yes" else 0)
            + BAG_FEE * r["nonfree_baggages"])


def paid(r: Record) -> int:
    return sum(x["amount"] for x in r["payment_history"])


@dataclass(frozen=True)
class InsuranceFee(Corruption):
    fee: int = INSURANCE_FEE

    def invariant(self, record: Record) -> bool:
        return due(record, self.fee) == paid(record)

    def normalise(self, record: Record) -> Record:
        r = copy.deepcopy(record)
        if r["insurance"] == "yes":
            r["insurance"] = "no"
            r["payment_history"][0]["amount"] -= self.fee * len(r["passengers"])
        if not self.invariant(r):
            raise ValueError(f"{r['reservation_id']}: payments don't reconcile once normalised")
        return r

    def cell(self, record: Record, cell: str) -> Record:
        """Edit the flag and/or the first payment: C and D miss the invariant by exactly the fee."""
        if cell not in CELLS:
            raise ValueError(cell)
        r = self.normalise(record)
        r["insurance"] = "yes" if cell in ("B", "C") else "no"
        if cell in ("B", "D"):
            r["payment_history"][0]["amount"] += self.fee * len(r["passengers"])
        assert self.invariant(r) == (cell in ("A", "B"))
        return r


SPECS = {
    "airline_insurance_fee": InsuranceFee(
        "airline_insurance_fee",
        "reservation.insurance contradicted by the $30/passenger fee in payment_history"),
}
