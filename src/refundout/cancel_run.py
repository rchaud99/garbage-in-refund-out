"""Run the retail cancel gate: does a status check fire before "no" as well as before "yes"? (see refundout.cancel)

    uv run python -m refundout.cancel_run --estimate          # the plan and its cost estimate, no calls
    uv run python -m refundout.cancel_run --dry-run           # the whole pipeline, with fakes that trust the status
    uv run python -m refundout.cancel_run --max-dollars 8     # the gate

The cells are made by scripts/make_retail_cancel.py. Each run is saved under runs/.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any

from dotenv import load_dotenv
from lookworth import models
from lookworth.costs import PRICES, Budget, cost
from lookworth.models import Model, Reply, Request, Usage, respond_with_retries
from lookworth.models.fake import FakeModel
from lookworth.runs import Run, RunWriter

from refundout import cancel
from refundout.cancel import Decision, Item, Nudge, Orders, mentions_fulfilment, parse
from refundout.gate import ask_all, fatal
from refundout.run import ENV, OUTPUT_GUESS, ROOT, _settings, estimate

MODELS = ("gemini-3.8-flash:U+E", "claude-sonnet-5:U+E")


@dataclass(frozen=True)
class Result:
    item: Item
    reply: Reply | None
    retries: tuple[str, ...]
    decision: Decision | None
    error: str | None
    fatal: bool = False

    def to_record(self, model: dict[str, Any]) -> dict[str, Any]:
        item, decision = self.item, self.decision
        order = item.order
        thoughts = None if self.reply is None else self.reply.thoughts
        return {
            "id": item.key, "model": model, "order_id": order["order_id"], "user_id": order["user_id"],
            "family": item.family, "cell": str(item.cell), "nudge": str(item.nudge),
            "true_status": order["status"], "shown_status": cancel.SHOWN_STATUS[item.cell],
            "tracking_shown": order["tracking_ids"],
            "prompt": {"system": item.request.system, "user": list(item.request.parts)},
            "reply": None if self.reply is None else self.reply.to_record(),
            "retries": list(self.retries),
            "action": None if decision is None else decision.action,
            "message": None if decision is None else decision.message,
            "unreadable": None if decision is None else decision.error,
            "correct": None if decision is None else decision.action == item.correct,
            "fulfilment_in_reasoning": None if self.reply is None else mentions_fulfilment(thoughts),
            "fulfilment_in_message": None if decision is None else mentions_fulfilment(decision.message),
            "error": self.error,
            "cost_usd": None if self.reply is None else cost(model["name"], asdict(self.reply.usage)),
        }


def ask(model: Model, item: Item) -> Result:
    try:
        reply, retries = respond_with_retries(model, item.request)
    except Exception as error:  # noqa: BLE001 - every failure is data for the log
        return Result(item, None, (), None, f"{type(error).__name__}: {error}", fatal(error))
    return Result(item, reply, tuple(retries), parse(reply.text), None)


def main(argv: list[str] | None = None) -> Any:
    parser = _parser()
    args = parser.parse_args(argv)
    plans = [_plan(spec, parser) for spec in args.models]
    orders = Orders.load()
    queues = {name: cancel.items(orders, nudges, args.corrupted, args.clean) for name, nudges in plans}
    print(f"τ² commit {orders.data['tau2_commit']}; eligible {orders.data['eligible']}; "
          f"{args.corrupted} corrupted and {args.clean} clean orders per family")
    print(estimate(queues))
    if args.estimate:
        return None
    if not args.dry_run:
        load_dotenv(ENV)
    chosen = [(fake(name) if args.dry_run else models.load(name, **_settings(name)), queues[name])
              for name, _ in plans]
    config = {
        "experiment": "retail_cancel_gate",
        "tau2_commit": orders.data["tau2_commit"],
        "cells_file": "data/retail_cancel.json",
        "corrupted_per_family": args.corrupted,
        "clean_per_family": args.clean,
        "orders": {family: [o["order_id"] for o in rows[:max(args.corrupted, args.clean)]]
                   for family, rows in orders.families.items()},
        "plan": {name: [str(n) for n in nudges] for name, nudges in plans},
        "models": [{"name": model.name, **model.settings} for model, _ in chosen],
        "prompt_version": cancel.version(tuple(n for _, ns in plans for n in ns)),
        "nudge_lines": {str(n): list(lines) for n, lines in cancel.ADDED.items()},
        "max_dollars": args.max_dollars,
        "dry_run": args.dry_run,
    }
    wordings = {str(n) for _, ns in plans for n in ns}
    tag = "" if wordings <= {"U", "E"} else "two-way_"
    name = (f"{'dry-run' if args.dry_run else 'cancel'}_{args.corrupted}+{args.clean}-orders_{tag}"
            + "+".join(m.name for m, _ in chosen))
    with RunWriter(ROOT / "runs", name, config) as run:
        print(f"run folder: {run.dir}")
        spent, stopped = 0.0, None
        for model, queue in chosen:
            described = {"name": model.name, **model.settings}
            asked = 0

            def done(result: Result, described: dict[str, Any] = described, total: int = len(queue)) -> None:
                nonlocal asked
                record = result.to_record(described)
                run.record("decisions", record)
                if result.reply is not None and result.reply.raw:
                    run.record("raw", {"id": record["id"], "model": described["name"], "response": result.reply.raw})
                run.log(f"{described['name']} {record['id']}: {result.error or record['unreadable'] or record['action']}")
                asked += 1
                print(f"\r{described['name']}: {asked}/{total}", end="", flush=True)

            budget = Budget(model.name, args.max_dollars - spent)
            stopped = ask_all(model, queue, args.workers, budget, done, ask)
            spent += budget.spent
            print()
            if stopped:
                run.log(f"stopping: {stopped}")
                print(f"stopped: {stopped}")
                break
        records = list(Run(run.dir).records("decisions"))
        summary = cancel.summarize(records)
        text = cancel.table(summary)
        (run.dir / "summary.md").write_text(text + "\n", encoding="utf-8")
        (run.dir / "review.md").write_text(cancel.review(records), encoding="utf-8")
        run.finish("stopped" if stopped else "complete",
                   summary={"metrics": summary, "cost_usd": round(spent, 4), "stopped": stopped})
        print(text)
        print(f"spent ${spent:.2f}{' (list-price equivalent of the fakes)' if args.dry_run else ''}; "
              f"hand-check {run.dir / 'review.md'}")
        return run.dir


def fake(name: str) -> FakeModel:
    """Trusts the status: offers to cancel a pending order and refuses anything else."""
    output = OUTPUT_GUESS.get(name, (2000, 6000))[0]
    usage = Usage(input_tokens=4000, output_tokens=120, reasoning_tokens=output - 120)

    def status(request: Request) -> str:
        return json.loads(request.parts[0].split("[tool: get_order_details]\n", 1)[1].split("\n", 1)[0])["status"]

    def answer(request: Request) -> str:
        action = "cancel" if status(request) == "pending" else "refuse"
        return json.dumps({"action": action, "message_to_customer": f"The order is {status(request)}."})

    return FakeModel(answer, name=name, think=lambda r: f"The order's status is {status(r)}.", usage=usage)


def _plan(spec: str, parser: argparse.ArgumentParser) -> tuple[str, tuple[Nudge, ...]]:
    name, _, nudges = spec.partition(":")
    try:
        chosen = tuple(cancel.nudge(n) for n in nudges.split("+")) if nudges else tuple(Nudge)
    except ValueError:
        parser.error(f"unknown nudge in {spec!r}; choose from {[str(n) for n in cancel.NUDGES]}")
    if name not in PRICES:
        parser.error(f"no price for {name!r}; add it to lookworth.costs.PRICES first")
    return name, chosen


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--models", nargs="+", default=list(MODELS), metavar="MODEL[:NUDGES]")
    parser.add_argument("--corrupted", type=int, default=36, help="corrupted orders per family (default 36)")
    parser.add_argument("--clean", type=int, default=12,
                        help="the first N of those orders also as clean controls (default 12)")
    parser.add_argument("--max-dollars", type=float, default=8.0)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--estimate", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


if __name__ == "__main__":
    main()
