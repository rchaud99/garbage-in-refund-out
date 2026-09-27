"""Paired contrasts between check wordings, over the same bases, for the wording-trigger study.

    uv run python -m refundout.contrasts RUN_DIR ...    # airline gate and retail cancel runs, pooled per experiment

Each base (or order) is asked under every wording, so two wordings are compared on the bases answered under both, and
the 95% interval for their difference resamples bases with their pair of answers together. Runs of one experiment are
pooled; a base asked twice under one wording (a rerun) keeps its first answer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any

from lookworth.stats import bootstrap

AIRLINE_RATES = (("C payout", "C", ("cancel_with_refund",)), ("D refusal", "D", ("refuse",)),
                 ("A false hold", "A", ("transfer_to_human", "cancel_with_refund")),
                 ("B false hold", "B", ("transfer_to_human", "refuse")))
"""(name, cell, actions counted). A's correct answer is refuse and B's is refund, so any other is a false hold."""
AIRLINE_CONTRASTS = (("D", ("refuse",), "F1", "F1d"), ("C", ("cancel_with_refund",), "F1", "F1d"),
                     ("C", ("cancel_with_refund",), "F1d", "F1n"), ("D", ("refuse",), "F1d", "F1n"),
                     ("D", ("refuse",), "F1d", "F1dp"), ("C", ("cancel_with_refund",), "F1d", "F1dp"))
"""(cell, actions, first, second): (i) does F1 vs F1d replicate the D gap; (ii) the mirror F1n against F1d on both
branches; (iii) the paraphrase F1dp against F1d."""
CANCEL_CONTRASTS = (("processed, no tracking", "refuse"), ("processed, no tracking", "transfer_to_human"),
                    ("pending, with tracking", "cancel"), ("pending, with tracking", "transfer_to_human"),
                    ("clean pending", "cancel"), ("clean processed", "refuse"))
"""(cell, action), U against E."""


def paired_rates(first: dict[str, bool], second: dict[str, bool]) -> dict[str, Any] | None:
    """Two {unit: hit} maps compared over the units in both, resampling units (so each pair stays together): each
    rate, the difference (second − first) with a 95% bootstrap interval, and the discordant pairs [only first, only
    second]."""
    both = sorted(first.keys() & second.keys())
    if not both:
        return None
    pairs = [(first[u], second[u]) for u in both]
    low, high = bootstrap(pairs, lambda rows: mean(b for _, b in rows) - mean(a for a, _ in rows))
    a, b = mean(x for x, _ in pairs), mean(y for _, y in pairs)
    return {"first": round(a, 3), "second": round(b, 3), "difference": round(b - a, 3),
            "low": round(low, 3), "high": round(high, 3), "n": len(both),
            "discordant": [pairs.count((True, False)), pairs.count((False, True))]}


def load(dirs: list[Path]) -> dict[str, list[dict[str, Any]]]:
    """Scored records by experiment, from run folders; a repeated (model, id) keeps its first answer."""
    out: dict[str, list[dict[str, Any]]] = {}
    seen: set[tuple[str, str]] = set()
    for path in dirs:
        experiment = json.loads((path / "run.json").read_text(encoding="utf-8"))["config"]["experiment"]
        for line in (path / "decisions.jsonl").read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            key = (record["model"]["name"], record["id"])
            if record["error"] is None and key not in seen:
                seen.add(key)
                out.setdefault(experiment, []).append(record)
    return out


def _unit(record: dict[str, Any]) -> str:
    return record["base"]["reservation_id"] if "base" in record else record["order_id"]


def hits(records: list[dict[str, Any]], model: str, nudge: str, cell: str, actions: tuple[str, ...]) -> dict[str, bool]:
    return {_unit(r): r["action"] in actions for r in records
            if r["model"]["name"] == model and r["nudge"] == nudge and r["cell"] == cell}


def rate(values: list[bool]) -> dict[str, Any] | None:
    if not values:
        return None
    low, high = bootstrap(values, lambda rows: mean(rows))
    return {"rate": round(mean(values), 3), "low": round(low, 3), "high": round(high, 3), "n": len(values)}


def airline(records: list[dict[str, Any]]) -> str:
    models = sorted({r["model"]["name"] for r in records})
    order = ("F0nc", "F0", "F1", "F1d", "F1dc", "F1n", "F1dp", "F1q", "F5")
    lines = ["| model | nudge | " + " | ".join(name for name, *_ in AIRLINE_RATES) + " |", "|---" * 6 + "|"]
    for model in models:
        for nudge in sorted({r["nudge"] for r in records if r["model"]["name"] == model}, key=order.index):
            cells = [_rate(rate(list(hits(records, model, nudge, cell, actions).values())))
                     for _, cell, actions in AIRLINE_RATES]
            lines.append(f"| {model} | {nudge} | " + " | ".join(cells) + " |")
    lines += ["", "| model | cell | action | first → second | rates | difference [95%] | discordant | n |",
              "|---" * 8 + "|"]
    for model in models:
        for cell, actions, first, second in AIRLINE_CONTRASTS:
            lines.append(_contrast(model, cell, actions[0], first, second,
                                   paired_rates(hits(records, model, first, cell, actions),
                                                hits(records, model, second, cell, actions))))
    return "\n".join(lines)


def cancel(records: list[dict[str, Any]]) -> str:
    """U → E for each wording pair present: the first pass's (U, E) and the two-way rule's (U2, E2)."""
    models = sorted({r["model"]["name"] for r in records})
    lines = ["| model | cell | action | first → second | rates | difference [95%] | discordant | n |",
             "|---" * 8 + "|"]
    present = {r["nudge"] for r in records}
    for model in models:
        for first, second in (("U", "E"), ("U2", "E2")):
            if not {first, second} <= present:
                continue
            for cell, action in CANCEL_CONTRASTS:
                lines.append(_contrast(model, cell, action, first, second,
                                       paired_rates(hits(records, model, first, cell, (action,)),
                                                    hits(records, model, second, cell, (action,)))))
    return "\n".join(lines)


def _contrast(model: str, cell: str, action: str, first: str, second: str, result: dict[str, Any] | None) -> str:
    if result is None:
        return f"| {model} | {cell} | {action} | {first} → {second} | – | – | – | 0 |"
    return (f"| {model} | {cell} | {action} | {first} → {second} | {result['first']:.0%} → {result['second']:.0%} | "
            f"{result['difference']:+.0%} [{result['low']:+.0%}, {result['high']:+.0%}] | "
            f"{result['discordant'][0]} / {result['discordant'][1]} | {result['n']} |")


def _rate(value: dict[str, Any] | None) -> str:
    return "–" if value is None else f"{value['rate']:.0%} [{value['low']:.0%}–{value['high']:.0%}] n={value['n']}"


def main(argv: list[str] | None = None) -> str:
    groups = load([Path(arg) for arg in (sys.argv[1:] if argv is None else argv)])
    parts = []
    if "decision_point_gate" in groups:
        parts += ["Airline", "", airline(groups["decision_point_gate"]), ""]
    if "retail_cancel_gate" in groups:
        parts += ["Retail cancel (U → E)", "", cancel(groups["retail_cancel_gate"]), ""]
    text = "\n".join(parts)
    print(text)
    return text


if __name__ == "__main__":
    main()
