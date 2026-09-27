"""The retail cancel cells: τ²'s status invariant, only the status edited, the prompts, and a dry run end to end."""

import json

import pytest

from refundout import cancel, cancel_run
from refundout.cancel import CORRECT, CORRUPTED, FAMILY, Cell, Nudge, Orders, items, parse
from refundout.contrasts import paired_rates
from refundout.retail import RETAIL
from refundout.tau2 import VENDOR


@pytest.fixture(scope="module")
def orders() -> Orders:
    if not VENDOR.exists():
        pytest.skip(f"τ²-bench is not cloned into {VENDOR}")
    return Orders.load()


@pytest.fixture(scope="module")
def db():
    if not VENDOR.exists():
        pytest.skip(f"τ²-bench is not cloned into {VENDOR}")
    return json.loads((VENDOR / RETAIL / "db.json").read_text())


def test_tau2_retail_status_is_pending_exactly_when_an_order_has_no_tracking(db):
    """The invariant the corrupted cells break, on all 1,000 orders."""
    assert len(db["orders"]) == 1000
    for order in db["orders"].values():
        tracked = any(f["tracking_id"] for f in order["fulfillments"])
        assert (order["status"] == "pending") == (not order["fulfillments"]) == (not tracked)


def test_only_the_status_is_edited_and_tool_results_match_the_database(orders, db):
    tasks = (VENDOR / RETAIL / "tasks.json").read_text()
    users = set()
    for family, rows in orders.families.items():
        assert len(rows) == 36
        for row in rows:
            real = db["orders"][row["order_id"]]
            clean = json.loads(row["tool_results"]["get_order_details"]["clean"])
            corrupted = json.loads(row["tool_results"]["get_order_details"]["corrupted"])
            assert {k: clean[k] for k in real} == real  # the rest are τ²'s null optional fields
            assert {k: v for k, v in corrupted.items() if k != "status"} == {k: v for k, v in clean.items()
                                                                             if k != "status"}
            assert clean["status"] == row["status"] == ("pending" if family == "no_tracking" else "processed")
            assert corrupted["status"] == row["corrupted_status"] != clean["status"]
            assert bool(clean["fulfillments"]) == (family == "tracking")
            assert row["tool_results"]["find_user_id_by_email"] == row["user_id"]
            assert db["users"][row["user_id"]]["email"] == row["email"]
            assert row["user_id"] not in tasks and row["order_id"] not in tasks and row["email"] not in tasks
            users.add(row["user_id"])
    assert len(users) == 72


def test_items_pair_u_and_e_on_the_same_orders_with_clean_controls_on_the_first(orders):
    queue = items(orders, tuple(Nudge))
    assert len(queue) == (36 * 2 + 12 * 2) * 2
    count = {cell: len({i.order["order_id"] for i in queue if i.cell == cell}) for cell in Cell}
    assert count == {Cell.CLEAN_PENDING: 12, Cell.CLEAN_PROCESSED: 12, Cell.PROCESSED_NO_TRACKING: 36,
                     Cell.PENDING_WITH_TRACKING: 36}
    for family, (clean, corrupted) in FAMILY.items():
        first = [o["order_id"] for o in orders.families[family][:12]]
        assert sorted({i.order["order_id"] for i in queue if i.cell == clean}) == sorted(first)
    for item in queue:
        shown = json.loads(item.request.parts[0].split("[tool: get_order_details]\n", 1)[1].split("\n", 1)[0])
        assert shown["status"] == cancel.SHOWN_STATUS[item.cell]
        assert (item.cell in CORRUPTED) == (shown["status"] != item.order["status"])
    assert CORRECT[Cell.PROCESSED_NO_TRACKING] == CORRECT[Cell.PENDING_WITH_TRACKING] == "transfer_to_human"


def test_u_and_e_differ_only_in_their_check_line_and_the_reply_format_never_primes_checking(orders):
    queue = items(orders, tuple(Nudge), 1, 1)
    u, e = (next(i.request for i in queue if i.nudge == n and i.cell == Cell.PENDING_WITH_TRACKING) for n in Nudge)
    assert u.parts == e.parts
    assert u.system.replace(cancel.ACTION_CHECK, cancel.ANSWER_CHECK) == e.system
    assert u.system.count(cancel.CLAUSE) == 1 and orders.policy.strip() in u.system.replace(
        "".join(f"{line}\n\n" for line in cancel.ADDED[Nudge.U]), "")
    assert cancel.ACTION_CHECK == ("Before cancelling an order, confirm its status agrees with its fulfilments (a "
                                   "pending order has no tracking number).")
    assert cancel.ANSWER_CHECK == ("Before telling the customer whether an order can be cancelled, confirm its status "
                                   "agrees with its fulfilments (a pending order has no tracking number).")
    wording = (cancel.DECIDE + json.dumps(cancel.SCHEMA) + cancel.SCRIPT).lower()
    for word in ("check", "verify", "status", "tracking", "fulfil", "discrepan", "contradict"):
        assert word not in wording


def test_parse():
    assert parse('{"action": "cancel", "message_to_customer": "ok"}').action == "cancel"
    assert parse('{"action": "cancel_with_refund", "message_to_customer": "ok"}').error
    assert parse("nope").error


def test_paired_rates_keep_pairs_together():
    first = {"a": True, "b": True, "c": False, "d": False}
    second = {"a": True, "b": False, "c": False, "d": True, "e": True}
    result = paired_rates(first, second)
    assert result["n"] == 4 and result["first"] == 0.5 and result["second"] == 0.5 and result["difference"] == 0
    assert result["discordant"] == [1, 1] and result["low"] < 0 < result["high"]
    same = paired_rates(first, first)
    assert same["difference"] == same["low"] == same["high"] == 0
    assert paired_rates({"a": True}, {"b": True}) is None


def test_a_dry_run_trusts_the_status(tmp_path, monkeypatch, orders):
    monkeypatch.setattr(cancel_run, "ROOT", tmp_path)
    path = cancel_run.main(["--dry-run", "--corrupted", "3", "--clean", "2", "--models", "gemini-3.8-flash:U+E"])
    records = [json.loads(line) for line in (path / "decisions.jsonl").read_text().splitlines()]
    assert len(records) == (3 * 2 + 2 * 2) * 2 and all(r["error"] is None for r in records)
    by_cell = {cell: {r["action"] for r in records if r["cell"] == cell} for cell in Cell}
    assert by_cell == {Cell.CLEAN_PENDING: {"cancel"}, Cell.CLEAN_PROCESSED: {"refuse"},
                       Cell.PROCESSED_NO_TRACKING: {"refuse"}, Cell.PENDING_WITH_TRACKING: {"cancel"}}
    assert all(r["correct"] == (r["cell"] not in CORRUPTED) for r in records)
    review = (path / "review.md").read_text()
    assert review.count("\n## ") == sum(r["cell"] in CORRUPTED for r in records)
    assert json.loads((path / "run.json").read_text())["config"]["prompt_version"] == cancel.VERSION


def test_the_two_way_wordings_state_the_rule_both_ways_and_differ_only_in_their_check_line(orders):
    from refundout.cancel import TwoWay

    assert cancel.TWO_WAY_RULE == ("an order is pending if and only if it has no tracking number: a pending order has "
                                   "none and a processed order has one")
    assert cancel.ACTION_CHECK_2 == cancel.ACTION_CHECK.replace("a pending order has no tracking number",
                                                                cancel.TWO_WAY_RULE)
    assert cancel.ANSWER_CHECK_2 == cancel.ANSWER_CHECK.replace("a pending order has no tracking number",
                                                                cancel.TWO_WAY_RULE)
    queue = items(orders, (TwoWay.U2, TwoWay.E2), 1, 1)
    u2, e2 = (next(i.request for i in queue if i.nudge == n and i.cell == Cell.PROCESSED_NO_TRACKING) for n in TwoWay)
    u, e = (next(i.request for i in items(orders, (n,), 1, 1) if i.cell == Cell.PROCESSED_NO_TRACKING)
            for n in (Nudge.U, Nudge.E))
    assert u2.parts == e2.parts == u.parts
    assert u2.system == u.system.replace(cancel.ACTION_CHECK, cancel.ACTION_CHECK_2)
    assert e2.system == e.system.replace(cancel.ANSWER_CHECK, cancel.ANSWER_CHECK_2)
    assert cancel.version((TwoWay.U2, TwoWay.E2)) == cancel.VERSION_2 != cancel.VERSION == cancel.version(tuple(Nudge))
    assert cancel.nudge("U2") is TwoWay.U2 and cancel.nudge("E") is Nudge.E
    with pytest.raises(ValueError):
        cancel.nudge("X")


def test_a_two_way_dry_run_says_so_and_reports_both_pairs(tmp_path, monkeypatch, orders):
    from refundout import contrasts

    monkeypatch.setattr(cancel_run, "ROOT", tmp_path)
    path = cancel_run.main(["--dry-run", "--corrupted", "2", "--clean", "1", "--models", "gemini-3.8-flash:U2+E2"])
    config = json.loads((path / "run.json").read_text())["config"]
    assert "two-way" in path.name and config["prompt_version"] == cancel.VERSION_2
    records = [json.loads(line) for line in (path / "decisions.jsonl").read_text().splitlines()]
    assert {r["nudge"] for r in records} == {"U2", "E2"}
    text = contrasts.cancel(records)
    assert "U2 → E2" in text and "U → E" not in text
