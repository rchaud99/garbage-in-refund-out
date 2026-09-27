"""Build the retail exchange cells with τ²'s own code: its data models, its tools and its tool-result JSON.

Run it in a throwaway environment that can import τ² (its own dependencies, not this project's):

    PYTHONPATH=vendor/tau2-bench/src uv run --no-project --with pydantic --with loguru --with pyyaml \\
        --with python-dotenv --with pandas --with numpy --with rich --with litellm --with addict \\
        --with deepdiff --with toml --with tenacity --with fastapi --with docstring-parser --with psutil \\
        --with jinja2 python scripts/make_retail_exchange.py

It writes data/retail_exchange.json, which the harness reads; nothing else in this project runs τ²'s code.

The story each base tells. A delivered τ² order once had two of its items changed while it was pending, in one call
to τ²'s modify_pending_order_items. That tool charges the right price difference but then writes the *last* new
item's price onto every changed line (tools.py, the loop after "Modify the order"), so the first changed line keeps a
wrong price while the payments stay right. Now the customer wants to exchange that item for another variant, and τ²'s
exchange tool prices the exchange from the stored line: new price minus the wrong old one.

For each base and each of two histories, one where the bug leaves the line too high (the exchange then undercharges
or over-refunds: the company loses) and one where it leaves it too low (the customer loses), there are four cells:
clean or bugged, crossed with an upgrade (the customer pays) or a downgrade (the customer is refunded). Clean is the
same history with the line at its true price, which is what a correct tool writes. The bug also copies the last
item's options onto the line; we undo that, so the price is the only wrong field. Payment amounts are rounded to
cents (τ²'s modify tool leaves float noise such as 54.920000000000016, which a real ledger wouldn't store).
"""

from __future__ import annotations

import copy
import itertools
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
OUT = ROOT / "data" / "retail_exchange.json"

BASES, SEED = 12, 0
ERROR = (15.0, 150.0)
"""How far the bug's price may sit from the true one, in dollars: big enough to matter, small next to most items."""
MARGIN = 5.0
"""The true price difference of the exchange exceeds the error by at least this, so the error never flips a charge
into a refund (which would give it away without any arithmetic)."""


def main() -> None:
    db = RetailDB.load(str(DATA / "db.json"))
    tasks = (DATA / "tasks.json").read_text(encoding="utf-8")
    rng = random.Random(SEED)
    candidates = {}
    for order_id in sorted(db.orders):
        order = db.orders[order_id]
        user = db.users[order.user_id]
        if order.status != "delivered" or len(order.items) < 2 or _public(user, order, tasks):
            continue
        specs = {family: _specs(db, order, family) for family in ("high", "low")}
        if all(specs.values()):
            candidates[order_id] = specs
    order_ids = list(candidates)
    rng.shuffle(order_ids)
    chosen, users = [], set()
    for order_id in order_ids:
        user_id = db.orders[order_id].user_id
        if user_id not in users:
            chosen.append(order_id)
            users.add(user_id)
        if len(chosen) == BASES:
            break

    bases = []
    for order_id in chosen:
        pick = random.Random(f"{SEED}-{order_id}")
        families = {}
        for family, specs in candidates[order_id].items():
            spec = pick.choice(specs)
            families[family] = {"spec": spec, "cells": _cells(db, order_id, spec)}
        bases.append({"order_id": order_id, "user_id": db.orders[order_id].user_id, "families": families})

    commit = subprocess.run(["git", "-C", str(VENDOR), "rev-parse", "HEAD"], capture_output=True, text=True,
                            check=True).stdout.strip()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"tau2_commit": commit, "seed": SEED, "error_range": ERROR, "margin": MARGIN,
                               "eligible": len(candidates), "bases": bases}, indent=1) + "\n", encoding="utf-8")
    print(f"{len(candidates)} eligible orders; wrote {len(bases)} bases to {OUT.relative_to(ROOT)}")


def _public(user, order, tasks: str) -> bool:
    """Whether a public task names this user or order, so a model may have seen it in published transcripts."""
    name = f"{user.name.first_name} {user.name.last_name}"
    return any(key in tasks for key in (user.user_id, order.order_id, user.email, name))


def _specs(db: RetailDB, order, family: str) -> list[dict]:
    """Every (first line, second line, their new variants, upgrade and downgrade targets) that makes the bug leave the
    first line too high ("high") or too low ("low") by an amount in ERROR, with targets MARGIN clear of it. The first
    line must be the order's only item of its product, so the customer's request names it unambiguously."""
    owned = {item.item_id for item in order.items}
    specs = []
    for a, b in itertools.permutations(range(len(order.items)), 2):
        first, second = order.items[a], order.items[b]
        if sum(item.product_id == first.product_id for item in order.items) > 1:
            continue  # "the bookshelf" would be ambiguous
        for va in _available(db, first.product_id, owned):
            for vb in _available(db, second.product_id, owned | {va.item_id}):
                error = round(vb.price - va.price, 2)
                if not (ERROR[0] <= abs(error) <= ERROR[1]) or (error > 0) != (family == "high"):
                    continue
                others = _available(db, first.product_id, owned | {va.item_id, vb.item_id})
                up = [v.item_id for v in others if v.price - va.price >= abs(error) + MARGIN]
                down = [v.item_id for v in others if va.price - v.price >= abs(error) + MARGIN]
                if up and down:
                    specs.append({"first": a, "second": b, "first_new": va.item_id, "second_new": vb.item_id,
                                  "error": error, "up": sorted(up), "down": sorted(down)})
    return specs


def _available(db: RetailDB, product_id: str, exclude: set[str]) -> list:
    return [v for v in db.products[product_id].variants.values() if v.available and v.item_id not in exclude]


def _cells(db: RetailDB, order_id: str, spec: dict) -> dict:
    """The four cells of one history, each with what the agent sees and what τ²'s exchange tool would charge."""
    pick = random.Random(f"{order_id}-{spec['first_new']}-{spec['second_new']}")
    targets = {"up": pick.choice(spec["up"]), "down": pick.choice(spec["down"])}
    cells = {}
    for state in ("clean", "bugged"):
        history = _history(db, order_id, spec, bugged=state == "bugged")
        for direction, target in targets.items():
            cells[f"{state}-{direction}"] = _cell(history, order_id, spec, target)
    return cells


def _history(db: RetailDB, order_id: str, spec: dict, bugged: bool) -> RetailDB:
    """A copy of the database in which τ²'s modify tool changed the order's two items while it was pending, and the
    order then shipped and arrived."""
    db = copy.deepcopy(db)
    tools = RetailTools(db)
    order = db.orders[order_id]
    first, second = order.items[spec["first"]], order.items[spec["second"]]
    old = {first.item_id: spec["first_new"], second.item_id: spec["second_new"]}
    method_id = order.payment_history[0].payment_method_id
    method = db.users[order.user_id].payment_methods[method_id]
    balance = getattr(method, "balance", None)
    if balance is not None:
        method.balance = 1e9
    order.status = "pending"
    tools.modify_pending_order_items(order_id, [first.item_id, second.item_id],
                                     [spec["first_new"], spec["second_new"]], method_id)
    if balance is not None:
        method.balance = balance
    order = db.orders[order_id]
    line = order.items[spec["first"]]
    true_variant = db.products[line.product_id].variants[spec["first_new"]]
    assert line.item_id == spec["first_new"]
    assert round(line.price - true_variant.price, 2) == spec["error"], "τ²'s modify tool no longer has the bug"
    line.options = dict(true_variant.options)
    if not bugged:
        line.price = true_variant.price
    for payment in order.payment_history:
        payment.amount = round(payment.amount, 2)
    order.status = "delivered"
    for fulfillment in order.fulfillments:
        fulfillment.item_ids = [old.get(item_id, item_id) for item_id in fulfillment.item_ids]
    return db


def _cell(db: RetailDB, order_id: str, spec: dict, target: str) -> dict:
    order = db.orders[order_id]
    user = db.users[order.user_id]
    line = order.items[spec["first"]]
    product = db.products[line.product_id]
    true_price = product.variants[spec["first_new"]].price
    new_price = product.variants[target].price
    changed = {k: v for k, v in product.variants[target].options.items() if line.options.get(k) != v}
    tool_charge = _exchange_charge(db, order_id, line.item_id, target)
    items = round(sum(item.price for item in order.items), 2)
    net = round(sum(p.amount if p.transaction_type == "payment" else -p.amount for p in order.payment_history), 2)
    return {
        "email": user.email,
        "product": product.name,
        "product_id": product.product_id,
        "item_id": line.item_id,
        "new_item_id": target,
        "changed_options": changed,
        "payment_method_id": order.payment_history[0].payment_method_id,
        "stored_price": line.price,
        "true_price": true_price,
        "new_price": new_price,
        "true_difference": round(new_price - true_price, 2),
        "tool_difference": tool_charge,
        "items_total": items,
        "net_paid": net,
        "tool_results": {
            "find_user_id_by_email": Environment.to_json_str(RetailTools(copy.deepcopy(db)).find_user_id_by_email(
                user.email)),
            "get_order_details": Environment.to_json_str(order),
            "get_product_details": Environment.to_json_str(product),
        },
    }


def _exchange_charge(db: RetailDB, order_id: str, item_id: str, target: str) -> float:
    """What τ²'s exchange tool records as the price difference, run on a copy with any gift card topped up so a
    balance check can't stop it."""
    db = copy.deepcopy(db)
    order = db.orders[order_id]
    method_id = order.payment_history[0].payment_method_id
    method = db.users[order.user_id].payment_methods[method_id]
    if hasattr(method, "balance"):
        method.balance = 1e9
    return RetailTools(db).exchange_delivered_order_items(order_id, [item_id], [target], method_id) \
        .exchange_price_difference


if __name__ == "__main__":
    main()
