"""Finish only missing Gemini decisions in the five interrupted single-decision experiments."""

import argparse
import json

from refundout import cancel, cancel_run, gate, prompts, queued, queued_run
from refundout.bases import choose
from refundout.campaign import MODEL, execute
from refundout.cells import Cell, Design, Scripts
from refundout.run import ROOT, estimate
from refundout.tau2 import Airline

PREFIXES = ("153920", "154341", "154345", "154622", "154628")


def plans():
    airline = Airline.load()
    out = []
    for prefix in PREFIXES:
        path = next((ROOT / "runs").glob("2026-09-25_" + prefix + "*"))
        c = json.loads((path / "run.json").read_text())["config"]
        experiment = c["experiment"]
        seen = {
            r["id"]
            for r in map(
                json.loads, (path / "decisions.jsonl").read_text().splitlines()
            )
            if r["model"]["name"] == MODEL and not r["error"]
        }
        for run in (ROOT / "runs").glob("*/run.json"):
            m = json.loads(run.read_text())
            if m["config"].get("resumes") == path.name:
                seen.update(
                    r["id"]
                    for r in map(
                        json.loads,
                        (run.parent / "decisions.jsonl").read_text().splitlines(),
                    )
                    if not r["error"]
                )
        if experiment == "retail_cancel_gate":
            items = cancel.items(
                cancel.Orders.load(),
                tuple(cancel.nudge(n) for n in c["plan"][MODEL]),
                c["corrupted_per_family"],
                c["clean_per_family"],
            )
            kind = "cancel"
        else:
            bases = choose(airline, c["skip"] + len(c["bases"]), c["seed"])[c["skip"] :]
            if experiment == "queued_cancellation":
                items = queued.items(airline, bases)
                kind = "queued"
            else:
                items = gate.items(
                    airline,
                    bases,
                    tuple(prompts.Nudge(n) for n in c["plan"][MODEL]),
                    Scripts(c["script"]),
                    Design(c["design"]),
                    c["insurance_fee"],
                    tuple(Cell(x) for x in c["cells"]),
                )
                kind = "gate"
        out.append((path, c, [i for i in items if i.key not in seen], kind))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--estimate", action="store_true")
    p.add_argument("--max-dollars", type=float, default=50)
    a = p.parse_args()
    for path, c, queue, kind in plans():
        print(path.name, len(queue))
        print(estimate({MODEL: queue}))
        if a.estimate or not queue:
            continue

        def parse(item, text, kind=kind):
            if kind == "cancel":
                return cancel.parse(text)
            if kind == "queued":
                return queued.parse(text)
            from refundout.scoring import parse as parse_gate

            return parse_gate(text)

        def record(item, reply, decision, error, kind=kind):
            from refundout.scoring import notice

            if kind == "cancel":
                r = cancel_run.Result(item, reply, (), decision, error, bool(error))
            elif kind == "queued":
                r = queued_run.Result(
                    item,
                    reply,
                    (),
                    decision,
                    notice(decision.message, reply.thoughts) if reply else None,
                    error,
                    bool(error),
                )
            else:
                r = gate.Result(
                    item,
                    reply,
                    (),
                    decision,
                    notice(decision.message, reply.thoughts) if reply else None,
                    error,
                    bool(error),
                )
            return r.to_record({"name": MODEL})

        _, stopped = execute(
            queue,
            {**c, "resumes": path.name, "plan": {MODEL: c["plan"][MODEL]}},
            record,
            parse,
            "resume-" + path.name,
            max_dollars=a.max_dollars,
        )
        if stopped:
            break


if __name__ == "__main__":
    main()
