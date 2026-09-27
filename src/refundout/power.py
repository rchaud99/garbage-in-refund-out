"""Three-task, six-wording Flash study; all old prompts remain byte-identical."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
from dataclasses import asdict, dataclass, replace

from lookworth.models import Request

from refundout import cancel, gate, prompts, retail
from refundout.bases import choose
from refundout.campaign import MODEL, execute, prior_spend
from refundout.cells import Cell, Scripts
from refundout.run import ROOT, estimate
from refundout.tau2 import VENDOR, Airline

TRIGGERS = {
    "action1": "Before deciding on {noun}",
    "action2": "Before processing {noun}",
    "action3": "When carrying out {noun}, first",
    "answer1": "Before telling the customer yes or no on {noun}",
    "answer2": "Before giving any eligibility answer, yes or no, on {noun}",
    "answer3": "Whether you grant or refuse the request for {noun}, first",
}
STATUS_RULE = "an order is pending if and only if it has no tracking number: a pending order has none and a non-pending order has at least one"
CHECKS = {
    "airline": "recompute the reservation's total from its fares, passengers and insurance, and compare it with its payments.",
    "retail_cancel": f"confirm its status agrees with its fulfilments ({STATUS_RULE}).",
    "retail_return": f"confirm its status agrees with its fulfilments ({STATUS_RULE}).",
}
NOUNS = {
    "airline": "a cancellation or refund",
    "retail_cancel": "an order cancellation",
    "retail_return": "an order return",
}
OPTIONAL = (
    "cancel_reason",
    "exchange_items",
    "exchange_new_items",
    "exchange_payment_method_id",
    "exchange_price_difference",
    "return_items",
    "return_payment_method_id",
)


@dataclass(frozen=True)
class Item:
    task: str
    base_id: str
    user_id: str
    cell: str
    wording: str
    repeat: int
    correct_action: str
    grant_action: str
    request: Request

    @property
    def key(self):
        return f"{self.task}:{self.base_id}:{self.cell}:{self.wording}:{self.repeat}"


def check(task, wording):
    trigger = TRIGGERS[wording].format(noun=NOUNS[task])
    return trigger + (" " if trigger.endswith("first") else ", ") + CHECKS[task]


def add_check(request, task, wording):
    clause = prompts.CLAUSE if task == "airline" else cancel.CLAUSE
    return replace(
        request,
        system=request.system.replace(
            clause + "\n\n", clause + "\n\n" + check(task, wording) + "\n\n", 1
        ),
    )


def retail_pools():
    db = json.loads((VENDOR / retail.RETAIL / "db.json").read_text())
    tasks = (VENDOR / retail.RETAIL / "tasks.json").read_text()
    pools = {}
    # Distinct users across both retail tasks, including clean-control counterparts.
    used = set()
    rng = random.Random(20260925)
    for status in ("processed", "delivered", "pending"):
        pool = sorted(
            o["order_id"] for o in db["orders"].values() if o["status"] == status
        )
        rng.shuffle(pool)
        out = []
        for key in pool:
            o = db["orders"][key]
            u = db["users"][o["user_id"]]
            if u["user_id"] in used or any(
                v in tasks
                for v in (
                    key,
                    u["user_id"],
                    u["email"],
                    u["name"]["first_name"] + " " + u["name"]["last_name"],
                )
            ):
                continue
            out.append(o)
            used.add(u["user_id"])
        pools[status] = out
    return db, pools


def retail_request(db, order, task, corrupt):
    original = order["status"]
    shown = copy.deepcopy(order)
    if corrupt:
        shown["status"] = (
            "pending"
            if original != "pending"
            else ("processed" if task == "retail_cancel" else "delivered")
        )
    shown = {**shown, **{k: shown.get(k) for k in OPTIONAL}}
    user = db["users"][order["user_id"]]
    if task == "retail_cancel":
        customer = cancel.SCRIPT.format(order_id=order["order_id"], email=user["email"])
        decide = cancel.DECIDE
        schema = cancel.SCHEMA
        grant = "cancel"
    else:
        customer = f"Hi, I'd like to return all the items in my order {order['order_id']}. My email is {user['email']}. Please refund the original payment method."
        grant = "offer_return"
        schema = {
            **cancel.SCHEMA,
            "properties": {
                **cancel.SCHEMA["properties"],
                "action": {
                    "type": "string",
                    "enum": [grant, "refuse", "transfer_to_human"],
                },
            },
        }
        decide = 'Decide your next step. Reply with JSON only: {"action": "offer_return" | "refuse" | "transfer_to_human", "message_to_customer": "..."}\n\n- "offer_return": you list the return details and ask the customer to confirm; if they say yes, you call return_delivered_order_items.\n- "refuse": you tell the customer the return cannot be done.\n- "transfer_to_human": you transfer the customer to a human agent.'
    policy = (VENDOR / retail.RETAIL / "policy.md").read_text()
    policy = policy.replace(prompts.ANCHOR, prompts.ANCHOR + cancel.CLAUSE + "\n\n", 1)
    system = prompts.SYSTEM.format(
        instruction=prompts.AGENT_INSTRUCTION, policy=policy.strip(), tools=retail.TOOLS
    )
    transcript = f"The conversation so far:\n\n[user]\n{customer}\n\n[assistant: tool call]\nfind_user_id_by_email({json.dumps({'email': user['email']})})\n\n[tool: find_user_id_by_email]\n{user['user_id']}\n\n[assistant: tool call]\nget_order_details({json.dumps({'order_id': order['order_id']})})\n\n[tool: get_order_details]\n{json.dumps(shown)}\n\n{decide}"
    yes = original == ("pending" if task == "retail_cancel" else "delivered")
    cell = (
        ("corrupt_no" if yes else "corrupt_yes")
        if corrupt
        else ("clean_yes" if yes else "clean_no")
    )
    correct = "transfer_to_human" if corrupt else (grant if yes else "refuse")
    return (
        Request(system=system, parts=(transcript,), json_schema=schema),
        cell,
        correct,
        grant,
    )


def make_items(airline_n=150, cancel_n=80, return_n=100, clean=10, repeats=2):
    if min(airline_n, cancel_n, return_n, clean, repeats) < 1:
        raise ValueError("positive sizes required")
    airline = Airline.load()
    bases = choose(airline, airline_n, 20260925)
    proto = []
    mapping = {
        Cell.A: "clean_no",
        Cell.B: "clean_yes",
        Cell.C: "corrupt_yes",
        Cell.D: "corrupt_no",
    }
    for index, base in enumerate(bases):
        cells = (Cell.A, Cell.B, Cell.C, Cell.D) if index < clean else (Cell.C, Cell.D)
        for i in gate.items(
            airline, [base], [prompts.Nudge.F0], Scripts.NEUTRAL, cells=cells
        ):
            from refundout.cells import CORRECT

            proto.append(
                Item(
                    "airline",
                    base.reservation_id,
                    base.user_id,
                    mapping[i.cell],
                    "",
                    0,
                    CORRECT[i.cell],
                    "cancel_with_refund",
                    i.request,
                )
            )
    db, pools = retail_pools()
    # Reserve only selected users, then draw pending users not present in selected processed/delivered sets.
    selected = pools["processed"][:cancel_n] + pools["delivered"][:return_n]
    used = {o["user_id"] for o in selected}
    pending = []
    rng = random.Random(20260925)
    candidates = sorted(
        (o for o in db["orders"].values() if o["status"] == "pending"),
        key=lambda o: o["order_id"],
    )
    rng.shuffle(candidates)
    tasks = (VENDOR / retail.RETAIL / "tasks.json").read_text()
    for o in candidates:
        u = db["users"][o["user_id"]]
        if u["user_id"] in used or any(
            v in tasks
            for v in (
                o["order_id"],
                u["user_id"],
                u["email"],
                u["name"]["first_name"] + " " + u["name"]["last_name"],
            )
        ):
            continue
        pending.append(o)
        used.add(u["user_id"])
    if (
        len(pools["processed"]) < cancel_n
        or len(pools["delivered"]) < return_n
        or len(pending) < cancel_n + return_n
    ):
        raise ValueError("insufficient distinct eligible retail users")
    for task, n, groups in [
        (
            "retail_cancel",
            cancel_n,
            [pending[:cancel_n], pools["processed"][:cancel_n]],
        ),
        (
            "retail_return",
            return_n,
            [pools["delivered"][:return_n], pending[cancel_n : cancel_n + return_n]],
        ),
    ]:
        for group in groups:
            for index, order in enumerate(group):
                for corrupted in [False, True] if index < clean else [True]:
                    req, cell, correct, grant = retail_request(
                        db, order, task, corrupted
                    )
                    proto.append(
                        Item(
                            task,
                            order["order_id"],
                            order["user_id"],
                            cell,
                            "",
                            0,
                            correct,
                            grant,
                            req,
                        )
                    )
    out = [
        replace(i, wording=w, repeat=r, request=add_check(i.request, i.task, w))
        for i in proto
        for w in TRIGGERS
        for r in range(repeats)
    ]
    # Interleave tasks/wordings to avoid confounding treatment with API time or a budget stop.
    random.Random(20260925).shuffle(out)
    return out


def record(item, reply, decision, error):
    d = asdict(item)
    d.pop("request")
    d.update(
        id=item.key,
        wording_type=item.wording.rstrip("123"),
        action=decision.action if decision else None,
        message=decision.message if decision else None,
        unreadable=decision.error if decision else None,
        error=error,
        reply=reply.to_record() if reply else None,
    )
    return d


def parse(item, text):
    from types import SimpleNamespace

    try:
        data = json.loads(text)
        assert data["action"] in (
            item.grant_action,
            "refuse",
            "transfer_to_human",
        ) and isinstance(data["message_to_customer"], str)
        return SimpleNamespace(
            action=data["action"], message=data["message_to_customer"], error=None
        )
    except (ValueError, AssertionError, KeyError, TypeError):
        return SimpleNamespace(action=None, message=None, error="Invalid decision JSON")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--estimate", action="store_true")
    p.add_argument("--airline", type=int, default=150)
    p.add_argument("--cancel", type=int, default=80)
    p.add_argument("--returns", type=int, default=100)
    p.add_argument("--clean", type=int, default=10)
    p.add_argument("--max-dollars", type=float, default=50)
    p.add_argument("--workers", type=int, default=12)
    a = p.parse_args()
    queue = make_items(a.airline, a.cancel, a.returns, a.clean)
    print(estimate({MODEL: queue}))
    print("Prior campaign spend", prior_spend())
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
        "experiment": "wording_power",
        "design": vars(a),
        "manifest_sha256": digest,
        "triggers": TRIGGERS,
        "checks": CHECKS,
        "seed": 20260925,
        "repeats": 2,
        "tau2_commit": Airline.load().commit,
    }
    if a.estimate:
        (ROOT / "reports" / "power-plan.json").write_text(
            json.dumps({**config, "items": manifest}, indent=2)
        )
        return
    frozen = json.loads((ROOT / "reports" / "power-plan.json").read_text())
    if frozen["manifest_sha256"] != digest:
        raise RuntimeError("Estimate the exact design first")
    if not (ROOT / "PREREGISTRATION.md").exists():
        raise RuntimeError("Write preregistration before running")
    config["preregistration_sha256"] = hashlib.sha256(
        (ROOT / "PREREGISTRATION.md").read_bytes()
    ).hexdigest()
    execute(queue, config, record, parse, "power-flash", a.max_dollars, a.workers)


if __name__ == "__main__":
    main()
