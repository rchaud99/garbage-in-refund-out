"""The τ² data as we read it: the payment rule, the current time, and tool JSON exactly as τ² renders it."""

import json
from pathlib import Path

from refundout.tau2 import NOW, due, paid, reservation_json, user_json

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "tau2_tool_json.json").read_text())


def test_the_payment_rule_holds_on_every_reservation_and_none_has_paid_bags(airline):
    reservations = airline.db["reservations"].values()
    assert len(reservations) == 2000
    assert all(due(r) == paid(r) for r in reservations)
    assert not any(r["nonfree_baggages"] for r in reservations)


def test_the_policy_states_the_current_time_we_use(airline):
    assert "The current time is 2024-05-15 15:00:00 EST." in airline.policy
    assert NOW == "2024-05-15T15:00:00"


def test_tool_json_matches_what_tau2_itself_returns(airline):
    """The fixture was made by τ²'s own pydantic models; it covers all three payment-method kinds."""
    for user_id, expected in FIXTURE["users"].items():
        assert user_json(airline.db["users"][user_id]) == expected
    for reservation_id, expected in FIXTURE["reservations"].items():
        assert reservation_json(airline.db["reservations"][reservation_id]) == expected
    sources = {m["source"] for text in FIXTURE["users"].values() for m in json.loads(text)["payment_methods"].values()}
    assert sources == {"credit_card", "gift_card", "certificate"}


def test_public_task_users_are_found(airline):
    assert 0 < len(airline.public_users) < len(airline.db["users"])
    assert all(user in json.dumps(airline.tasks) for user in airline.public_users)
