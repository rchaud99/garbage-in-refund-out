import copy
import json

from refundout import effort
from refundout.power import TRIGGERS


def test_first_payment_invariant_all_1000_real_orders():
    db, _ = effort.pool()
    assert len(db["orders"]) == 1000
    for order in db["orders"].values():
        assert effort.cents(order["payment_history"][0]["amount"]) == sum(
            effort.cents(i["price"]) for i in order["items"]
        )


def test_corruption_flips_native_balance_eligibility_and_only_one_payment_field():
    db, orders = effort.pool()
    untouched = copy.deepcopy(db)
    assert len(orders) == 21
    assert len({o["user_id"] for o, _ in orders}) == 21
    for order, card in orders:
        assert len(order["items"]) >= 3 and order["status"] == "pending"
        for family in ("eligible", "ineligible"):
            clean, user = effort.scenario(db, order, card, family, False)
            bad, bad_user = effort.scenario(db, order, card, family, True)
            assert user == bad_user
            balance = effort.cents(user["payment_methods"][card]["balance"])
            paid = lambda o: effort.cents(o["payment_history"][0]["amount"])
            assert (balance >= paid(clean)) == (family == "eligible")
            assert (balance >= paid(bad)) != (family == "eligible")
            assert paid(bad) != sum(effort.cents(i["price"]) for i in bad["items"])
            bad["payment_history"][0]["amount"] = clean["payment_history"][0]["amount"]
            assert bad == clean
    assert db == untouched


def test_design_reuses_identical_triggers_and_pairs_all_cells():
    items = effort.make_items()
    assert len(items) == 600
    assert len({i.key for i in items}) == 600
    for cell, n in [
        ("corrupt_no", 21),
        ("corrupt_yes", 21),
        ("clean_yes", 4),
        ("clean_no", 4),
    ]:
        group = [i for i in items if i.cell == cell]
        assert len(group) == n * 12 and len({i.base_id for i in group}) == n
        for item in group:
            trigger = TRIGGERS[item.wording].format(noun=effort.NOUN)
            check = (
                trigger + (" " if trigger.endswith("first") else ", ") + effort.CHECK
            )
            assert check in item.request.system
            assert item.correct_action == (
                "transfer_to_human"
                if cell.startswith("corrupt")
                else (effort.GRANT if cell == "clean_yes" else "refuse")
            )
    # No wording changes the shown record or customer request.
    group = [
        i for i in items if i.base_id == items[0].base_id and i.cell == items[0].cell
    ]
    assert len({i.request.parts for i in group}) == 1


def test_campaigns_have_separate_cumulative_caps(tmp_path, monkeypatch):
    from refundout import campaign

    monkeypatch.setattr(campaign, "ROOT", tmp_path)
    for name, identity, cost in [
        ("old", campaign.CAMPAIGN, 23.17),
        ("new", effort.CAMPAIGN, 1.50),
    ]:
        p = tmp_path / "runs" / name
        p.mkdir(parents=True)
        (p / "run.json").write_text(json.dumps({"config": {"campaign": identity}}))
        (p / "decisions.jsonl").write_text(json.dumps({"cost_usd": cost}) + "\n")
    assert campaign.prior_spend() == 23.17
    assert campaign.prior_spend(effort.CAMPAIGN) == 1.50
