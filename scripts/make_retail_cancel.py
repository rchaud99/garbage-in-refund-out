"""Build the retail cancel cells with τ²'s own code: its data models, its tools and its tool-result JSON.

Run it in a throwaway environment that can import τ² (its own dependencies, not this project's):

    PYTHONPATH=vendor/tau2-bench/src uv run --no-project --with pydantic --with loguru --with pyyaml \\
        --with python-dotenv --with pandas --with numpy --with rich --with litellm --with addict \\
        --with deepdiff --with toml --with tenacity --with fastapi --with docstring-parser --with psutil \\
        --with jinja2 python scripts/make_retail_cancel.py

It writes data/retail_cancel.json, which the harness reads (refundout.cancel); nothing else in this project runs τ²'s
code.

In τ²'s retail data an order's status is "pending" exactly when it has no fulfilments (no tracking number): every
pending order has none, every processed, delivered or cancelled order has at least one (tests/test_cancel.py checks all
1,000). Two families of real orders, from users named in no public task, each user used once:

- family "no_tracking": pending orders. Clean, the record as τ² has it (cancellable). Corrupted, the status edited to
  "processed" with still no fulfilment: the status says no, the fulfilments say it never shipped.
- family "tracking": processed orders. Clean, the record as τ² has it (not cancellable). Corrupted, the status edited
  to "pending" with its fulfilment and tracking number left in place: the status says yes, the tracking says it shipped.

Only the status changes. Each order's get_order_details result is rendered by τ²'s own Order model and
Environment.to_json_str, for both statuses, and find_user_id_by_email's by τ²'s own tool.
"""

from __future__ import annotations

import copy
import json
import random
import subprocess
from pathlib import Path

from tau2.domains.retail.data_model import RetailDB
from tau2.domains.retail.tools import RetailTools
from tau2.environment.environment import Environment

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "tau2-bench"
DATA = VENDOR / "data" / "tau2" / "domains" / "retail"
OUT = ROOT / "data" / "retail_cancel.json"
EXCHANGE = ROOT / "data" / "retail_exchange.json"

BASES, SEED = 36, 0
FAMILIES = {"no_tracking": ("pending", "processed"), "tracking": ("processed", "pending")}
"""Family: (the status τ² gives these orders, the status the corrupted record shows)."""


def main() -> None:
    db = RetailDB.load(str(DATA / "db.json"))
    tasks = (DATA / "tasks.json").read_text(encoding="utf-8")
    exchange_users = {b["user_id"] for b in json.loads(EXCHANGE.read_text(encoding="utf-8"))["bases"]}
    rng = random.Random(SEED)
    used: set[str] = set(exchange_users)
    families, eligible = {}, {}
    # The smaller pool (processed) draws first, so the larger one gives way on a shared user.
    for family in sorted(FAMILIES, key=lambda f: FAMILIES[f][0] == "pending"):
        status, _ = FAMILIES[family]
        pool = sorted(order_id for order_id, order in db.orders.items()
                      if order.status == status and not _public(db, order, tasks))
        eligible[family] = len(pool)
        rng.shuffle(pool)
        chosen = []
        for order_id in pool:
            user_id = db.orders[order_id].user_id
            if user_id not in used:
                chosen.append(order_id)
                used.add(user_id)
            if len(chosen) == BASES:
                break
        families[family] = [_base(db, order_id, family) for order_id in chosen]

    commit = subprocess.run(["git", "-C", str(VENDOR), "rev-parse", "HEAD"], capture_output=True, text=True,
                            check=True).stdout.strip()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"tau2_commit": commit, "seed": SEED, "eligible": eligible, "families": families},
                              indent=1) + "\n", encoding="utf-8")
    print(f"eligible {eligible}; wrote {BASES} orders per family to {OUT.relative_to(ROOT)}")


def _public(db: RetailDB, order, tasks: str) -> bool:
    """Whether a public task names this user or order, so a model may have seen it in published transcripts."""
    user = db.users[order.user_id]
    name = f"{user.name.first_name} {user.name.last_name}"
    return any(key in tasks for key in (user.user_id, order.order_id, user.email, name))


def _base(db: RetailDB, order_id: str, family: str) -> dict:
    true_status, shown = FAMILIES[family]
    order = db.orders[order_id]
    assert order.status == true_status and bool(order.fulfillments) == (true_status != "pending")
    user = db.users[order.user_id]
    corrupted = copy.deepcopy(order)
    corrupted.status = shown
    return {
        "order_id": order_id,
        "user_id": order.user_id,
        "email": user.email,
        "status": true_status,
        "corrupted_status": shown,
        "items": len(order.items),
        "tracking_ids": [t for f in order.fulfillments for t in f.tracking_id],
        "tool_results": {
            "find_user_id_by_email": Environment.to_json_str(RetailTools(db).find_user_id_by_email(user.email)),
            "get_order_details": {"clean": Environment.to_json_str(order),
                                  "corrupted": Environment.to_json_str(corrupted)},
        },
    }


if __name__ == "__main__":
    main()
