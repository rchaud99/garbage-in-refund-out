"""Run the decision-point gate: does the agent notice that a reservation's payments contradict its insurance flag?

    uv run python -m refundout.run --estimate          # the plan and its cost estimate, no calls
    uv run python -m refundout.run --dry-run           # the whole pipeline, with fakes that trust the flag
    uv run python -m refundout.run --max-dollars 15    # the gate
    uv run python -m refundout.run --script neutral    # the same customer wording in every cell
    uv run python -m refundout.run --design provenance # does an approval trail release legitimate credits?
    uv run python -m refundout.run --skip 12 --bases 48 --cells C D   # 48 fresh bases, never the first 12

Each run is saved under runs/. See README.md.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import lookworth
from dotenv import load_dotenv
from lookworth import models
from lookworth.costs import PRICES, Budget, cost
from lookworth.models import Request, Usage
from lookworth.models.fake import FakeModel
from lookworth.runs import Run, RunWriter

from refundout import prompts
from refundout.bases import choose, eligible
from refundout.cells import CELLS, Cell, Design, Scripts
from refundout.gate import Item, Result, ask_all, items, review, summarize, table
from refundout.prompts import Nudge
from refundout.tau2 import INSURANCE_FEE, Airline

ROOT = Path(__file__).resolve().parents[2]
ENV = Path(lookworth.__file__).resolve().parents[2] / ".env"
"""The API keys live with lookworth; they are loaded, never read here."""

MODELS = ("gemini-3.8-flash:F0nc+F0+F1+F1d", "claude-sonnet-5:F0nc+F0+F1+F1d", "claude-opus-5-5:F0")
"""Flash and Sonnet at the first four nudges; Opus at the middle dose only. F1dc is for the provenance design."""
SETTINGS = {"claude-": {"effort": "high"}, "gemini-": {"thinking_level": "medium"}}

CHARS_PER_TOKEN = {"claude-": 2.6, "gemini-": 3.3}
"""For the estimate only: prompt characters per input token, the lowest seen in this project's runs (2026-09-24;
means 2.7 and 3.7), so the input side errs high. Claude's tokenizer is the denser."""
OUTPUT_GUESS = {"gemini-3.8-flash": (1400, 2500), "claude-sonnet-5": (400, 800), "claude-opus-5-5": (600, 900)}
"""Output tokens (reasoning included) per call, typical and high: rounded up from the means and 90th percentiles of
this project's single-decision runs of 2026-09-24 (Flash 1,326 / 1,818-2,434, Sonnet 369 / 563-707, Opus 550 /
661-833, airline / retail). The first guesses, from lookworth's text-only runs, came out 3-6× too high."""


def main(argv: list[str] | None = None) -> Path | None:
    parser = _parser()
    args = parser.parse_args(argv)
    plans = [_plan(spec, parser) for spec in args.models]
    airline = Airline.load()
    bases = choose(airline, args.skip + args.bases, args.seed)[args.skip:]
    cells = CELLS[args.design] if args.cells is None else tuple(c for c in CELLS[args.design] if c in args.cells)
    if args.cells is not None and set(args.cells) - set(cells):
        parser.error(f"--cells must come from the {args.design} design: {[str(c) for c in CELLS[args.design]]}")
    queues = {name: items(airline, bases, nudges, args.script, args.design, args.insurance_fee, cells)
              for name, nudges in plans}

    print(f"τ² commit {airline.commit}; {len(eligible(airline))} eligible reservations, {len(bases)} bases"
          f"{f' (after skipping the first {args.skip})' if args.skip else ''}:")
    for base in bases:
        print(f"  {base.reservation_id}  {base.passengers} passenger(s), {base.payment_entries} payment entry, "
              f"{base.flights} flight(s), {base.cabin}, {base.membership}, paid ${base.total_paid}")
    print(estimate(queues))
    if args.estimate:
        return None

    if not args.dry_run:
        load_dotenv(ENV)
    chosen = [(fake(name) if args.dry_run else models.load(name, **_settings(name)), queues[name])
              for name, _ in plans]
    listed = args.design is Design.PROVENANCE
    config = {
        "experiment": "decision_point_gate",
        "design": str(args.design),
        "cells": [str(cell) for cell in cells],
        "adjustment_tool": prompts.ADJUSTMENT_TOOL if listed else None,
        "ledger_tool": (prompts.LEDGER_TOOL if any(Nudge.F5 in nudges for _, nudges in plans) else None),
        "tau2_commit": airline.commit,
        "now": "2024-05-15T15:00:00 EST (the policy's current time)",
        "bases": [asdict(base) for base in bases],
        "seed": args.seed,
        "skip": args.skip,
        "skipped_bases": [base.reservation_id for base in choose(airline, args.skip, args.seed)] if args.skip else [],
        "plan": {name: [str(n) for n in nudges] for name, nudges in plans},
        "models": [{"name": model.name, **model.settings} for model, _ in chosen],
        "script": str(args.script),
        "prompt_version": prompts.VERSION,
        "prompt_versions": {str(n): prompts.version(n, listed, args.insurance_fee)
                            for n in dict.fromkeys(n for _, ns in plans for n in ns)},
        "insurance_fee": args.insurance_fee,
        "nudge_lines": {str(n): list(lines) for n, lines in prompts.ADDED.items()},
        "max_dollars": args.max_dollars,
        "workers": args.workers,
        "dry_run": args.dry_run,
    }
    script = "" if args.script is Scripts.PLAN else f"{args.script}-script_"
    design = "" if args.design is Design.GATE else f"{args.design}_"
    design += "" if args.insurance_fee == INSURANCE_FEE else f"fee-{args.insurance_fee}_"
    design += f"skip-{args.skip}_" if args.skip else ""
    design += "" if args.cells is None else "cells-" + "".join(str(c) for c in cells) + "_"
    name = (f"{'dry-run' if args.dry_run else 'gate'}_{len(bases)}-bases_{design}{script}"
            + "+".join(model.name for model, _ in chosen))

    with RunWriter(ROOT / "runs", name, config) as run:
        print(f"run folder: {run.dir}")
        spent, stopped = 0.0, None
        for model, queue in chosen:
            described = {"name": model.name, **model.settings}
            asked = 0

            def done(result: Result, described: dict[str, Any] = described, total: int = len(queue)) -> None:
                nonlocal asked
                save(run, described, result)
                asked += 1
                print(f"\r{described['name']}: {asked}/{total}", end="", flush=True)

            run.log(f"{model.name}: {len(queue)} items, ${args.max_dollars - spent:.2f} left")
            budget = Budget(model.name, args.max_dollars - spent)
            stopped = ask_all(model, queue, args.workers, budget, done)
            spent += budget.spent
            print()
            if stopped:
                run.log(f"stopping: {stopped}")
                print(f"stopped: {stopped}")
                break

        records = list(Run(run.dir).records("decisions"))
        summary = summarize(records)
        text = table(summary)
        (run.dir / "summary.md").write_text(text + "\n", encoding="utf-8")
        (run.dir / "review.md").write_text(review(records, args.design), encoding="utf-8")
        run.finish("stopped" if stopped else "complete",
                   summary={"metrics": summary, "cost_usd": round(spent, 4), "stopped": stopped})
        print(text)
        print(f"spent ${spent:.2f}{' (list-price equivalent of the fakes)' if args.dry_run else ''}; "
              f"hand-check {run.dir / 'review.md'}")
        return run.dir


def save(run: RunWriter, model: dict[str, Any], result: Result) -> None:
    """A line in decisions.jsonl, the raw response, and the outcome in the log."""
    record = result.to_record(model)
    run.record("decisions", record)
    if result.reply is not None and result.reply.raw:
        run.record("raw", {"id": record["id"], "model": model["name"], "response": result.reply.raw})
    outcome = result.error or record["unreadable"] or f"{record['action']} (noticed: {record['noticed']})"
    run.log(f"{model['name']} {record['id']}: {outcome}")


def estimate(queues: dict[str, list[Item]]) -> str:
    """Dollars at list price, from prompt length and a typical and a high guess at output tokens."""
    lines, typical, high = ["cost estimate (list price, no caching):"], 0.0, 0.0
    for name, queue in queues.items():
        per_token = next((c for prefix, c in CHARS_PER_TOKEN.items() if name.startswith(prefix)), 2.6)
        tokens = sum(len(i.request.system) + sum(len(p) for p in i.request.parts) for i in queue) / per_token
        low_out, high_out = OUTPUT_GUESS.get(name, (2000, 6000))
        a = _price(name, tokens, low_out * len(queue))
        b = _price(name, tokens, high_out * len(queue))
        typical, high = typical + a, high + b
        lines.append(f"  {name}: {len(queue)} calls × ~{tokens / max(len(queue), 1):,.0f} input tokens; "
                     f"${a:.2f} typical, ${b:.2f} high")
    lines.append(f"  total: ${typical:.2f} typical, ${high:.2f} high")
    return "\n".join(lines)


def _price(name: str, input_tokens: float, output_tokens: float) -> float:
    return cost(name, {"input_tokens": input_tokens, "output_tokens": output_tokens, "reasoning_tokens": 0}) or 0.0


def fake(name: str) -> FakeModel:
    """Trusts the insurance flag: cancels with a refund when it says yes, refuses when it says no. Named and priced
    as the model it stands in for, at the typical output guess, so the dry run exercises the budget guard."""
    output = OUTPUT_GUESS.get(name, (2000, 6000))[0]
    usage = Usage(input_tokens=3000, output_tokens=150, reasoning_tokens=output - 150)

    def insured(request: Request) -> bool:
        reservation = request.parts[0].split("[tool: get_reservation_details]\n", 1)[1].split("\n", 1)[0]
        return json.loads(reservation)["insurance"] == "yes"

    def answer(request: Request) -> str:
        if insured(request):
            return json.dumps({"action": "cancel_with_refund", "message_to_customer":
                               "Your reservation includes travel insurance, so I can cancel it with a full refund."})
        return json.dumps({"action": "refuse", "message_to_customer":
                           "Your reservation has no travel insurance, so I can't cancel it for a refund."})

    def think(request: Request) -> str:
        return f"The reservation's insurance field says {'yes' if insured(request) else 'no'}."

    return FakeModel(answer, name=name, think=think, usage=usage)


def _plan(spec: str, parser: argparse.ArgumentParser) -> tuple[str, tuple[Nudge, ...]]:
    """MODEL or MODEL:NUDGE+NUDGE, e.g. claude-opus-5-5:F0."""
    name, _, nudges = spec.partition(":")
    try:
        chosen = tuple(Nudge(n) for n in nudges.split("+")) if nudges else tuple(Nudge)
    except ValueError:
        parser.error(f"unknown nudge in {spec!r}; choose from {[str(n) for n in Nudge]}")
    if name not in PRICES:
        parser.error(f"no price for {name!r}; add it to lookworth.costs.PRICES first")
    return name, chosen


def _settings(name: str) -> dict[str, Any]:
    return next(settings for prefix, settings in SETTINGS.items() if name.startswith(prefix))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--models", nargs="+", default=list(MODELS), metavar="MODEL[:NUDGES]",
                        help="models, each optionally limited to nudges joined by + "
                             f"(default {' '.join(MODELS)}; nudges {'/'.join(str(n) for n in Nudge)})")
    parser.add_argument("--bases", type=int, default=12, help="base reservations (default 12)")
    parser.add_argument("--script", type=Scripts, choices=list(Scripts), default=Scripts.PLAN,
                        help="what the customer says: the plan's per-cell scripts, or the neutral one in every cell "
                             "(default plan)")
    parser.add_argument("--design", type=Design, choices=list(Design), default=Design.GATE,
                        help="which cells: the 2×2 and benign control, or benign and C with and without an approval "
                             "record for the credit (default gate)")
    parser.add_argument("--seed", type=int, default=0, help="seed for choosing bases (default 0)")
    parser.add_argument("--skip", type=int, default=0,
                        help="leave out the first N bases of the seed's draw and take the next --bases; the draw is "
                             "prefix-stable, so --skip 12 never reuses the 12 discovery bases (default 0)")
    parser.add_argument("--cells", type=Cell, nargs="+", choices=list(Cell), default=None, metavar="CELL",
                        help="ask only these cells of the design, e.g. C D (default all)")
    parser.add_argument("--insurance-fee", type=int, default=INSURANCE_FEE,
                        help="dollars per passenger, written into the policy and the payments: does the agent's check "
                             "read the policy or remember τ²'s $30? (default 30)")
    parser.add_argument("--max-dollars", type=float, default=15.0,
                        help="start no call that could take list-price spend past this, over all models (default 15)")
    parser.add_argument("--workers", type=int, default=6, help="calls at once (default 6)")
    parser.add_argument("--estimate", action="store_true", help="print the plan and its cost estimate, and stop")
    parser.add_argument("--dry-run", action="store_true", help="fakes that trust the insurance flag; no API calls")
    return parser


if __name__ == "__main__":
    main()
