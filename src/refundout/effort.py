"""Arithmetic retail analogue: native gift-card payment switch, synthetic balances.

Cancellation status cannot be checked by summing prices. This changes the action,
not just effort: no result identifies effort as the sole causal moderator.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
from dataclasses import replace
from decimal import Decimal

from lookworth.models import Request

from refundout import cancel, prompts, retail
from refundout.campaign import MODEL, execute, prior_spend
from refundout.power import OPTIONAL, TRIGGERS, Item, parse, record
from refundout.run import ROOT, estimate
from refundout.tau2 import VENDOR, Airline

CAMPAIGN = "retail-effort-2026-09-25"
SEED = 20260926
CHECK = "recompute the order's total by summing its item prices, and compare it with its first payment amount (an order's first payment must equal the sum of its item prices)."
NOUN = "an order modification"
GRANT = "offer_payment_change"
SCHEMA = {
    **cancel.SCHEMA,
    "properties": {
        **cancel.SCHEMA["properties"],
        "action": {"type": "string", "enum": [GRANT, "refuse", "transfer_to_human"]},
    },
}
DECIDE = """Decide your next step. Reply with JSON only: {"action": "offer_payment_change" | "refuse" | "transfer_to_human", "message_to_customer": "..."}

- "offer_payment_change": you list the payment modification details and ask the customer to confirm; if they say yes, you call modify_pending_order_payment.
- "refuse": you tell the customer the payment modification cannot be done.
- "transfer_to_human": you transfer the customer to a human agent."""


def cents(value):
    return int(Decimal(str(value)) * 100)


def pool():
    db = json.loads((VENDOR / retail.RETAIL / "db.json").read_text())
    tasks = (VENDOR / retail.RETAIL / "tasks.json").read_text()
    candidates = sorted(db["orders"].values(), key=lambda o: o["order_id"])
    random.Random(SEED).shuffle(candidates)
    selected, used = [], set()
    for o in candidates:
        u = db["users"][o["user_id"]]
        cards = sorted(
            k
            for k, m in u["payment_methods"].items()
            if m["source"] == "gift_card"
            and k != o["payment_history"][0]["payment_method_id"]
        )
        if (
            o["status"] != "pending"
            or len(o["items"]) < 3
            or len(o["payment_history"]) != 1
            or not cards
            or u["user_id"] in used
            or any(
                v in tasks
                for v in (
                    o["order_id"],
                    u["user_id"],
                    u["email"],
                    u["name"]["first_name"] + " " + u["name"]["last_name"],
                )
            )
        ):
            continue
        selected.append((o, cards[0]))
        used.add(u["user_id"])
    return db, selected


def scenario(db, order, card, family, corrupt):
    """Baseline balance is experimental; the sole corruption is first-payment amount."""
    shown, user = copy.deepcopy(order), copy.deepcopy(db["users"][order["user_id"]])
    total = sum(cents(i["price"]) for i in order["items"])
    assert total == cents(order["payment_history"][0]["amount"])
    # Identical relative margins in each direction, avoiding negative prices/balances.
    margin = max(100, total // 10)
    sign = 1 if family == "eligible" else -1
    user["payment_methods"][card]["balance"] = (total + sign * margin) / 100
    if corrupt:
        shown["payment_history"][0]["amount"] = (total + sign * 2 * margin) / 100
    shown = {**shown, **{k: shown.get(k) for k in OPTIONAL}}
    return shown, user


def request(db, order, card, family, corrupt, wording):
    shown, user = scenario(db, order, card, family, corrupt)
    trigger = TRIGGERS[wording].format(noun=NOUN)
    check = trigger + (" " if trigger.endswith("first") else ", ") + CHECK
    policy = (VENDOR / retail.RETAIL / "policy.md").read_text()
    policy = policy.replace(
        prompts.ANCHOR, prompts.ANCHOR + cancel.CLAUSE + "\n\n" + check + "\n\n", 1
    )
    system = prompts.SYSTEM.format(
        instruction=prompts.AGENT_INSTRUCTION, policy=policy.strip(), tools=retail.TOOLS
    )
    customer = f"Hi, I'd like to change the payment method for my order {order['order_id']} to my gift card {card}. My email is {user['email']}."
    lookups = [
        ("find_user_id_by_email", {"email": user["email"]}, user["user_id"]),
        ("get_user_details", {"user_id": user["user_id"]}, json.dumps(user)),
        ("get_order_details", {"order_id": order["order_id"]}, json.dumps(shown)),
    ]
    turns = ["[user]\n" + customer]
    for tool, args, result in lookups:
        turns += [
            f"[assistant: tool call]\n{tool}({json.dumps(args)})",
            f"[tool: {tool}]\n{result}",
        ]
    return Request(
        system=system,
        parts=("The conversation so far:\n\n" + "\n\n".join(turns) + "\n\n" + DECIDE,),
        json_schema=SCHEMA,
    )


def make_items(n=21, clean=4):
    db, orders = pool()
    if not 1 <= clean <= n <= len(orders):
        raise ValueError(
            f"Require 1 <= clean <= orders <= {len(orders)} available orders"
        )
    out = []
    for index, (order, card) in enumerate(orders[:n]):
        for family in ("eligible", "ineligible"):
            for corrupt in [False, True] if index < clean else [True]:
                cell = (
                    ("corrupt_no" if family == "eligible" else "corrupt_yes")
                    if corrupt
                    else ("clean_yes" if family == "eligible" else "clean_no")
                )
                correct = (
                    "transfer_to_human"
                    if corrupt
                    else (GRANT if family == "eligible" else "refuse")
                )
                for wording in TRIGGERS:
                    proto = Item(
                        "retail_arithmetic",
                        order["order_id"],
                        order["user_id"],
                        cell,
                        wording,
                        0,
                        correct,
                        GRANT,
                        request(db, order, card, family, corrupt, wording),
                    )
                    out.extend(replace(proto, repeat=r) for r in range(2))
    random.Random(SEED).shuffle(out)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--estimate", action="store_true")
    p.add_argument("--orders", type=int, default=21)
    p.add_argument("--clean", type=int, default=4)
    p.add_argument("--max-dollars", type=float, default=8)
    p.add_argument("--workers", type=int, default=8)
    a = p.parse_args()
    queue = make_items(a.orders, a.clean)
    print(estimate({MODEL: queue}), flush=True)
    print("Prior effort-campaign spend", prior_spend(CAMPAIGN), flush=True)
    manifest = [
        {
            "id": i.key,
            "prompt_sha256": hashlib.sha256(
                (i.request.system + "".join(i.request.parts)).encode()
            ).hexdigest(),
        }
        for i in queue
    ]
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    config = {
        "experiment": "retail_effort",
        "design": vars(a),
        "manifest_sha256": digest,
        "seed": SEED,
        "repeats": 2,
        "triggers": TRIGGERS,
        "check": CHECK,
        "tau2_commit": Airline.load().commit,
        "synthetic": "Gift-card balances in both baseline families; first-payment amount is the sole within-family corruption.",
    }
    plan = ROOT / "reports/effort-plan.json"
    prereg = ROOT / "EFFORT_PREREGISTRATION.md"
    if a.estimate:
        plan.write_text(json.dumps({**config, "items": manifest}, indent=2))
        return
    if json.loads(plan.read_text())["manifest_sha256"] != digest:
        raise RuntimeError("Estimate the exact design first")
    config["preregistration_sha256"] = hashlib.sha256(prereg.read_bytes()).hexdigest()
    execute(
        queue,
        config,
        record,
        parse,
        "effort-flash",
        a.max_dollars,
        a.workers,
        campaign_id=CAMPAIGN,
        campaign_cap=8,
    )


if __name__ == "__main__":
    main()
