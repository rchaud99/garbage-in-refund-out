import json

from refundout import cancel, prompts
from refundout.power import (
    CHECKS,
    TRIGGERS,
    check,
    make_items,
    retail_pools,
    retail_request,
)


def test_real_retail_invariant_and_return_corruption_both_directions():
    db, pools = retail_pools()
    assert len(db["orders"]) == 1000
    for o in db["orders"].values():
        assert (o["status"] == "pending") == (
            not any(f["tracking_id"] for f in o["fulfillments"])
        )
    for status in ["delivered", "pending"]:
        o = pools[status][0]
        a = retail_request(db, o, "retail_return", False)
        b = retail_request(db, o, "retail_return", True)

        def shown(r):
            return json.loads(
                r.parts[0].split("[tool: get_order_details]\n")[1].split("\n")[0]
            )

        clean, bad = shown(a[0]), shown(b[0])
        assert [k for k in clean if clean[k] != bad[k]] == ["status"]
        assert (bad["status"] == "pending") != (
            not any(f["tracking_id"] for f in bad["fulfillments"])
        )
        assert b[2] == "transfer_to_human"
        assert a[2] == ("offer_return" if status == "delivered" else "refuse")


def test_design_pairs_repeats_wordings_and_preserves_check_content():
    items = make_items(3, 3, 3, 1)
    assert len(items) == (18 + 6) * 12
    assert len({i.key for i in items}) == len(items)
    groups = {}
    for i in items:
        groups.setdefault((i.task, i.base_id, i.cell), []).append(i)
        clause = prompts.CLAUSE if i.task == "airline" else cancel.CLAUSE
        assert i.request.system.index(clause) < i.request.system.index(
            check(i.task, i.wording)
        )
    for values in groups.values():
        assert len(values) == 12 and len({i.request.parts for i in values}) == 1
        assert (
            len(
                {
                    i.request.system.replace(check(i.task, i.wording), "CHECK")
                    for i in values
                }
            )
            == 1
        )
    assert all(check(t, w).endswith(c) for t, c in CHECKS.items() for w in TRIGGERS)
    # No retail user appears in two distinct base/order IDs.
    byuser = {}
    for i in items:
        if i.task.startswith("retail"):
            byuser.setdefault(i.user_id, set()).add(i.base_id)
    assert all(len(v) == 1 for v in byuser.values())


def test_planned_scale_is_balanced():
    items = make_items(65, 30, 43, 5)
    assert len(items) == 3672
    for task, n in [("airline", 65), ("retail_cancel", 30), ("retail_return", 43)]:
        for cell in ["corrupt_yes", "corrupt_no"]:
            group = [i for i in items if i.task == task and i.cell == cell]
            assert len(group) == n * 12
            assert len({i.base_id for i in group}) == n
