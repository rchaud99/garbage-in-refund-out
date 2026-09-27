"""Run the inverted framing: the cancellation is already queued and the agent may block it (see refundout.queued).

    uv run python -m refundout.queued_run --estimate                     # the plan and its cost, no calls
    uv run python -m refundout.queued_run --dry-run                      # fakes that trust the flag
    uv run python -m refundout.queued_run --skip 12 --bases 48 --max-dollars 12

Each run is saved under runs/.
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

from refundout import queued
from refundout.bases import choose
from refundout.gate import ask_all, fatal
from refundout.queued import Decision, Item, Nudge, parse
from refundout.run import ENV, OUTPUT_GUESS, ROOT, _settings, estimate
from refundout.scoring import Notice, notice
from refundout.tau2 import Airline

MODELS = ("gemini-3.8-flash:Q", "claude-sonnet-5:Q")


@dataclass(frozen=True)
class Result:
    item: Item
    reply: Reply | None
    retries: tuple[str, ...]
    decision: Decision | None
    notice: Notice | None
    error: str | None
    fatal: bool = False

    def to_record(self, model: dict[str, Any]) -> dict[str, Any]:
        item, decision = self.item, self.decision
        return {
            "id": item.key, "model": model, "base": asdict(item.base), "cell": str(item.cell),
            "nudge": str(item.nudge), "records": {"user": item.user, "reservation": item.reservation},
            "ledger": queued.ledger(item.reservation),
            "prompt": {"system": item.request.system, "user": list(item.request.parts)},
            "reply": None if self.reply is None else self.reply.to_record(),
            "retries": list(self.retries),
            "action": None if decision is None else decision.action,
            "message": None if decision is None else decision.message,
            "unreadable": None if decision is None else decision.error,
            "correct": None if decision is None else decision.action == item.correct,
            "noticed": None if self.notice is None else self.notice.noticed,
            "snippets": [] if self.notice is None else list(self.notice.snippets),
            "error": self.error,
            "cost_usd": None if self.reply is None else cost(model["name"], asdict(self.reply.usage)),
        }


def ask(model: Model, item: Item) -> Result:
    try:
        reply, retries = respond_with_retries(model, item.request)
    except Exception as error:  # noqa: BLE001 - every failure is data for the log
        return Result(item, None, (), None, None, f"{type(error).__name__}: {error}", fatal(error))
    decision = parse(reply.text)
    return Result(item, reply, tuple(retries), decision, notice(decision.message, reply.thoughts), None)


def main(argv: list[str] | None = None) -> Any:
    parser = _parser()
    args = parser.parse_args(argv)
    plans = [_plan(spec, parser) for spec in args.models]
    airline = Airline.load()
    bases = choose(airline, args.skip + args.bases, args.seed)[args.skip:]
    queues = {name: queued.items(airline, bases, nudges) for name, nudges in plans}
    print(f"τ² commit {airline.commit}; {len(bases)} bases after skipping {args.skip}")
    print(estimate(queues))
    if args.estimate:
        return None
    if not args.dry_run:
        load_dotenv(ENV)
    chosen = [(fake(name) if args.dry_run else models.load(name, **_settings(name)), queues[name])
              for name, _ in plans]
    config = {
        "experiment": "queued_cancellation",
        "tau2_commit": airline.commit,
        "bases": [asdict(base) for base in bases],
        "seed": args.seed, "skip": args.skip,
        "cells": [str(c) for c in queued.CELLS],
        "script": "neutral",
        "plan": {name: [str(n) for n in nudges] for name, nudges in plans},
        "models": [{"name": model.name, **model.settings} for model, _ in chosen],
        "prompt_version": queued.VERSION,
        "nudge_lines": {str(n): list(lines) for n, lines in queued.ADDED.items()},
        "correct": {str(c): a for c, a in queued.CORRECT.items()},
        "max_dollars": args.max_dollars,
        "dry_run": args.dry_run,
    }
    name = (f"{'dry-run' if args.dry_run else 'queued'}_{len(bases)}-bases_skip-{args.skip}_"
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
        summary = queued.summarize(records)
        text = queued.table(summary)
        (run.dir / "summary.md").write_text(text + "\n", encoding="utf-8")
        (run.dir / "review.md").write_text(queued.review(records), encoding="utf-8")
        run.finish("stopped" if stopped else "complete",
                   summary={"metrics": summary, "cost_usd": round(spent, 4), "stopped": stopped})
        print(text)
        print(f"spent ${spent:.2f}{' (list-price equivalent of the fakes)' if args.dry_run else ''}; "
              f"hand-check {run.dir / 'review.md'}")
        return run.dir


def fake(name: str) -> FakeModel:
    """Trusts the insurance flag: lets an insured cancellation proceed and blocks an uninsured one."""
    output = OUTPUT_GUESS.get(name, (2000, 6000))[0]
    usage = Usage(input_tokens=3000, output_tokens=150, reasoning_tokens=output - 150)

    def insured(request: Request) -> bool:
        text = request.parts[0].split("[tool: get_reservation_details]\n", 1)[1].split("\n", 1)[0]
        return json.loads(text)["insurance"] == "yes"

    def answer(request: Request) -> str:
        action = "let_proceed" if insured(request) else "block_cancellation"
        return json.dumps({"action": action, "message_to_customer": "…"})

    return FakeModel(answer, name=name, think=lambda r: "The insurance field decides it.", usage=usage)


def _plan(spec: str, parser: argparse.ArgumentParser) -> tuple[str, tuple[Nudge, ...]]:
    name, _, nudges = spec.partition(":")
    try:
        chosen = tuple(Nudge(n) for n in nudges.split("+")) if nudges else tuple(Nudge)
    except ValueError:
        parser.error(f"unknown nudge in {spec!r}; choose from {[str(n) for n in Nudge]}")
    if name not in PRICES:
        parser.error(f"no price for {name!r}; add it to lookworth.costs.PRICES first")
    return name, chosen


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--models", nargs="+", default=list(MODELS), metavar="MODEL[:NUDGES]")
    parser.add_argument("--bases", type=int, default=48)
    parser.add_argument("--skip", type=int, default=12,
                        help="leave out the first N bases (default 12: the first follow-up pass's bases)")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-dollars", type=float, default=12.0)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--estimate", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


if __name__ == "__main__":
    main()
