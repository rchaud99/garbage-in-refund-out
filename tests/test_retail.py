"""The retail exchange cells as τ² made them, the prompts built from them, reading a reply, and a dry run end to end."""

import json

import pytest

from refundout import retail
from refundout import retail_run
from refundout.retail import DIRECTIONS, FAMILIES, STATES, Nudge, Retail, items, parse, quoted
from refundout.tau2 import VENDOR


@pytest.fixture(scope="module")
def data() -> Retail:
    if not VENDOR.exists():
        pytest.skip(f"τ²-bench is not cloned into {VENDOR}")
    return Retail.load()


def _cells(data):
    for base in data.bases:
        for family in FAMILIES:
            for state in STATES:
                for direction in DIRECTIONS:
                    yield base, family, state, direction, base["families"][family]["cells"][f"{state}-{direction}"]


def test_twelve_bases_from_different_users(data):
    assert len(data.bases) == 12
    assert len({b["user_id"] for b in data.bases}) == 12


def test_only_the_bugged_line_price_is_wrong_and_the_payments_are_right(data):
    for base, family, state, direction, cell in _cells(data):
        order = json.loads(cell["tool_results"]["get_order_details"])
        line = next(i for i in order["items"] if i["item_id"] == cell["item_id"])
        variant = json.loads(cell["tool_results"]["get_product_details"])["variants"][cell["item_id"]]
        assert line["options"] == variant["options"]
        assert variant["price"] == cell["true_price"]
        assert line["price"] == cell["stored_price"]
        error = round(cell["stored_price"] - cell["true_price"], 2)
        paid = round(cell["net_paid"] - cell["items_total"], 2)
        if state == "clean":
            assert error == 0 and paid == 0
        else:
            assert error == base["families"][family]["spec"]["error"]
            assert (error > 0) == (family == "high")
            assert paid == -error  # the payments disagree with the lines by exactly the error


def test_the_tool_charges_from_the_stored_line_without_flipping_the_direction(data):
    for _, family, state, direction, cell in _cells(data):
        assert cell["tool_difference"] == round(cell["new_price"] - cell["stored_price"], 2)
        assert (cell["true_difference"] > 0) == (direction == "up") == (cell["tool_difference"] > 0)
        wrong = round(cell["tool_difference"] - cell["true_difference"], 2)
        if state == "clean":
            assert wrong == 0
        else:
            assert (wrong < 0) == (family == "high")  # high: the customer pays less or gets more back


def test_the_request_names_one_line_and_the_same_words_in_clean_and_bugged(data):
    for base in data.bases:
        for family in FAMILIES:
            for direction in DIRECTIONS:
                clean, bugged = (base["families"][family]["cells"][f"{s}-{direction}"] for s in STATES)
                assert retail.customer(base["order_id"], clean) == retail.customer(base["order_id"], bugged)
                order = json.loads(clean["tool_results"]["get_order_details"])
                assert sum(i["product_id"] == clean["product_id"] for i in order["items"]) == 1


def test_nudges_differ_only_by_their_added_lines(data):
    queue = items(data, tuple(Nudge), 1)
    systems = {i.nudge: i.request.system for i in queue}
    for nudge, lines in retail.ADDED.items():
        stripped = systems[nudge]
        for line in lines:
            assert stripped.count(line) == 1
            stripped = stripped.replace(line + "\n\n", "")
        assert stripped == systems[Nudge.F0NC]
    assert "check" not in retail.DECIDE.lower() and "discrepan" not in retail.DECIDE.lower()


def test_parse_and_quote():
    cell = {"true_difference": 44.22, "tool_difference": 15.7}
    assert parse('{"action": "offer_exchange", "price_difference": 15.7, "message_to_customer": "ok"}').action \
        == "offer_exchange"
    assert parse('{"action": "cancel", "price_difference": null, "message_to_customer": "x"}').error
    assert parse("nope").error
    assert quoted(15.7, cell) == "stored" and quoted(-44.22, cell) == "true" and quoted(20, cell) == "other"
    assert quoted(None, cell) is None


def test_a_dry_run_trusts_the_stored_line(tmp_path, monkeypatch, data):
    monkeypatch.setattr(retail_run, "ROOT", tmp_path)
    path = retail_run.main(["--dry-run", "--bases", "2", "--models", "gemini-3.8-flash:F0"])
    records = [json.loads(line) for line in (path / "decisions.jsonl").read_text().splitlines()]
    assert len(records) == 2 * 8 and all(r["error"] is None for r in records)
    assert all(r["action"] == "offer_exchange" for r in records)
    assert {r["quoted"] for r in records if r["state"] == "bugged"} == {"stored"}
    assert {r["quoted"] for r in records if r["state"] == "clean"} == {"true"}
