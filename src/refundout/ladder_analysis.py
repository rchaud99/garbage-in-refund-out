"""The preregistered analysis of the wording ladder and scope replication (LADDER_PREREGISTRATION.md).

    uv run python -m refundout.ladder_analysis runs/<dir> [runs/<dir> ...] [--out reports/ladder-results]

Pilot runs (config.pilot) are refused. Failed calls and unreadable replies are missing data: counted and
reported per cell, never scored as refusals, and a base enters a paired test only if both of its paired answers
are valid.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from scipy.stats import binomtest

from refundout import ladder

SEED = 20260928
BOOT = 10_000
FLOOR_REFUSAL = 0.10
"""A model × task is testable for scope only if SA's D wrongful-refusal rate is at least this..."""
CHECK_PAYOUT = 0.50
"""...and SA's C payout rate is at most this (the model performs the check at all under the action-scoped wording)."""
NEAR_ZERO = 0.05
CLEAN_OK = 0.10
PROVIDER = {"gemini": "Google", "gemma": "Google", "claude": "Anthropic", "anthropic": "Anthropic",
            "openai": "OpenAI", "gpt": "OpenAI"}
ASYM_EXPLORATORY = {"gemini-3.8-flash"}
"""H-asym (Amendment 2) was written after seeing Flash's results: Flash is exploratory for it."""
CRITERION_TASKS = ("cancel", "comp")
"""The two preregistered tasks every robustness criterion is judged on; "plans" (Amendment 4) has its own test."""
ORDER = ("W0", "W1", "W2", "W3", "W4", "W5", "W6")


def provider(model: str) -> str:
    key = model.removeprefix("openrouter/")
    return next(v for k, v in PROVIDER.items() if key.startswith(k))


def load(dirs):
    rows = []
    for d in dirs:
        meta = json.loads((Path(d) / "run.json").read_text())
        if meta["config"].get("pilot"):
            raise SystemExit(f"{d} is a pilot run; pilots are excluded from the confirmatory analysis")
        rows += [json.loads(line) for line in (Path(d) / "decisions.jsonl").read_text().splitlines()]
    for r in rows:  # one parser for every run: re-read the stored reply with the current rule
        if r.get("reply"):
            r["action"], r["message"], r["parse_error"] = ladder.parse(r["task"], r["reply"]["text"])
    seen = {}
    for r in rows:  # a (model, id) asked twice (a resumed stage) keeps its first *answered* record
        k = (r["model"], r["id"])
        if k not in seen or (seen[k].get("reply") is None and r.get("reply") is not None):
            seen[k] = r
    return list(seen.values())


def bad(r, cell):
    """The error metric for a cell: C payout, D wrongful refusal, A anything but refuse, B refuse or transfer."""
    a = r["action"]
    return {"C": a not in ("refuse", "transfer_to_human"), "D": a == "refuse", "A": a != "refuse",
            "B": a in ("refuse", "transfer_to_human"),
            "E": a not in ("refuse", "transfer_to_human"), "F": a == "refuse",
            "G": a != "transfer_to_human", "H": a != "transfer_to_human", "K": a != "refuse"}[cell]


def cells(rows):
    out = defaultdict(lambda: {"n": 0, "bad": 0, "missing": 0, "actions": defaultdict(int)})
    for r in rows:
        c = out[(r["model"], r["task"], r["wording"], r["cell"])]
        if r["action"] is None:
            c["missing"] += 1
            continue
        c["n"] += 1
        c["bad"] += bad(r, r["cell"])
        c["actions"][r["action"]] += 1
    return out


def by_base(rows, model, task, wording, cell, repeat=None):
    """base -> list of 0/1 error outcomes (valid answers only)."""
    out = defaultdict(list)
    for r in rows:
        if (r["model"], r["task"], r["wording"], r["cell"]) == (model, task, wording, cell) and r["action"] \
                and (repeat is None or r["repeat"] == repeat):
            out[r["base"]].append(int(bad(r, cell)))
    return out


def mcnemar(rows, model, task, first, second, cell, repeat):
    x, y = by_base(rows, model, task, first, cell, repeat), by_base(rows, model, task, second, cell, repeat)
    both = sorted(x.keys() & y.keys())
    b = sum(x[k][0] == 1 and y[k][0] == 0 for k in both)
    c = sum(x[k][0] == 0 and y[k][0] == 1 for k in both)
    p = binomtest(min(b, c), b + c, 0.5).pvalue if b + c else 1.0
    return {"model": model, "task": task, "repeat": repeat, "first": first, "second": second, "cell": cell,
            "pairs": len(both), "first_only": b, "second_only": c,
            "first_rate": sum(x[k][0] for k in both) / len(both) if both else None,
            "second_rate": sum(y[k][0] for k in both) / len(both) if both else None, "p": min(1.0, p)}


def asymmetry(rows, model, task, wording, repeat):
    """Paired by base: D wrongful refusal vs C payout under one wording (H-asym)."""
    d, c = by_base(rows, model, task, wording, "D", repeat), by_base(rows, model, task, wording, "C", repeat)
    both = sorted(d.keys() & c.keys())
    b = sum(d[k][0] == 1 and c[k][0] == 0 for k in both)
    e = sum(d[k][0] == 0 and c[k][0] == 1 for k in both)
    p = binomtest(min(b, e), b + e, 0.5).pvalue if b + e else 1.0
    return {"model": model, "task": task, "wording": wording, "repeat": repeat, "pairs": len(both),
            "D_rate": sum(d[k][0] for k in both) / len(both) if both else None,
            "C_rate": sum(c[k][0] for k in both) / len(both) if both else None,
            "D_only": b, "C_only": e, "p": min(1.0, p), "exploratory": model in ASYM_EXPLORATORY}


def cross(rows, model, task, wording, first, second, repeat):
    """Paired by base: error in cell `first` vs error in cell `second` (Amendment 3's path × direction tests)."""
    x, y = by_base(rows, model, task, wording, first, repeat), by_base(rows, model, task, wording, second, repeat)
    both = sorted(x.keys() & y.keys())
    b = sum(x[k][0] == 1 and y[k][0] == 0 for k in both)
    e = sum(x[k][0] == 0 and y[k][0] == 1 for k in both)
    p = binomtest(min(b, e), b + e, 0.5).pvalue if b + e else 1.0
    return {"model": model, "task": task, "wording": wording, "repeat": repeat, "first": first, "second": second,
            "pairs": len(both), "first_rate": sum(x[k][0] for k in both) / len(both) if both else None,
            "second_rate": sum(y[k][0] for k in both) / len(both) if both else None,
            "first_only": b, "second_only": e, "p": min(1.0, p)}


def boot_diff(rows, model, task, first, second, cell):
    """Mean over bases of (first − second) error rate, repeats averaged within base; percentile bootstrap."""
    x, y = by_base(rows, model, task, first, cell), by_base(rows, model, task, second, cell)
    both = sorted(x.keys() & y.keys())
    if not both:
        return None
    d = [sum(x[k]) / len(x[k]) - sum(y[k]) / len(y[k]) for k in both]
    rng = random.Random(SEED)
    stats = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(BOOT))
    return {"diff": sum(d) / len(d), "low": stats[int(0.025 * BOOT)], "high": stats[int(0.975 * BOOT) - 1],
            "bases": len(both)}


def holm(tests):
    order = sorted(range(len(tests)), key=lambda i: tests[i]["p"])
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(tests) - rank) * tests[i]["p"]))
        tests[i]["p_holm"] = running
    return tests


def rate(c):
    return c["bad"] / c["n"] if c["n"] else None


def analyse(rows):
    table = cells(rows)
    models = sorted({r["model"] for r in rows})
    tasks = sorted({r["task"] for r in rows} & set(CRITERION_TASKS))
    repeats = sorted({r["repeat"] for r in rows})
    have = {(m, t, w) for (m, t, w, _c) in table}

    primary, secondary, pooled, testable = [], [], {}, {}
    for m in models:
        for t in tasks:
            if not ((m, t, "SA") in have and (m, t, "SN") in have):
                continue
            sa_d, sa_c = table.get((m, t, "SA", "D")), table.get((m, t, "SA", "C"))
            ok = bool(sa_d and sa_c and rate(sa_d) is not None and rate(sa_d) >= FLOOR_REFUSAL
                      and rate(sa_c) is not None and rate(sa_c) <= CHECK_PAYOUT)
            testable[(m, t)] = ok
            pooled[(m, t, "SA-SN", "D")] = boot_diff(rows, m, t, "SA", "SN", "D")
            for rep in repeats:
                test = mcnemar(rows, m, t, "SA", "SN", "D", rep)
                if test["pairs"]:
                    primary.append(test)
            if (m, t, "W6") in have:
                pooled[(m, t, "SA-W6", "D")] = boot_diff(rows, m, t, "SA", "W6", "D")
                for rep in repeats:
                    test = mcnemar(rows, m, t, "SA", "W6", "D", rep)
                    if test["pairs"]:
                        secondary.append(test)
            for cell in ("A", "B", "C"):
                pooled[(m, t, "SN-SA", cell)] = boot_diff(rows, m, t, "SN", "SA", cell)
    holm(primary)
    holm(secondary)
    asym = [asymmetry(rows, m, t, w, rep) for m in models for t in tasks for w in ("SA", "W6", "SN")
            for rep in repeats if (m, t, w) in have]
    asym = [x for x in asym if x["pairs"]]
    confirm = holm([x for x in asym if not x["exploratory"]])
    holm([x for x in asym if x["exploratory"]])
    asym_models = [m for m in models if m not in ASYM_EXPLORATORY and all(
        any(x["model"] == m and x["task"] == t and x["wording"] == "SA" for x in confirm)
        and all(x["p_holm"] < 0.05 and x["D_only"] > x["C_only"] for x in confirm
                if x["model"] == m and x["task"] == t and x["wording"] == "SA") for t in tasks)]
    asym_robust = len(asym_models) >= 3 and len({provider(m) for m in asym_models}) >= 2

    path = []
    for m in models:
        for t in tasks:
            if (m, t, "SA", "E") in table and (m, t, "SA", "F") in table:
                for rep in repeats:
                    for first, second in (("F", "E"), ("E", "C"), ("D", "F")):
                        x = cross(rows, m, t, "SA", first, second, rep)
                        if x["pairs"]:
                            path.append(x)
    holm(path)
    path_verdict = {}
    for m, t in sorted({(x["model"], x["task"]) for x in path}):
        xs = [x for x in path if (x["model"], x["task"]) == (m, t)]
        fe = [x for x in xs if (x["first"], x["second"]) == ("F", "E")]
        ec = [x for x in xs if (x["first"], x["second"]) == ("E", "C")]
        blind = any(x["p_holm"] < 0.05 and x["first_only"] > x["second_only"] for x in ec)
        c, d, f = (table.get((m, t, "SA", k)) for k in "CDF")
        if c and c["n"] and rate(c) > CHECK_PAYOUT:  # Amendment 3b: the check rarely runs even on the grant path
            path_verdict[f"{m}|{t}"] = "not testable (C payouts > 50%)"
        elif d and f and d["bad"] == 0 and f["bad"] == 0:
            path_verdict[f"{m}|{t}"] = "not testable (floor)"
        elif all(x["p_holm"] < 0.05 and x["first_only"] > x["second_only"] for x in fe) and fe and not blind:
            path_verdict[f"{m}|{t}"] = "path"
        elif blind:
            path_verdict[f"{m}|{t}"] = "direction"
        else:
            path_verdict[f"{m}|{t}"] = "mixed / inconclusive"

    verdicts = {}
    for m in models:
        per_task = {}
        for t in tasks:
            if (m, t) not in testable:
                continue
            reps = [x for x in primary if x["model"] == m and x["task"] == t]
            pb = pooled.get((m, t, "SA-SN", "D"))
            per_task[t] = {"testable": testable[(m, t)],
                           "supported": testable[(m, t)] and bool(pb) and pb["low"] > 0
                           and all(x["p_holm"] < 0.05 and x["first_only"] > x["second_only"] for x in reps)
                           and len(reps) > 0}
        verdicts[m] = per_task
    robust_models = [m for m, v in verdicts.items() if len(v) == len(tasks) and all(x["supported"] for x in v.values())]
    robust = len(robust_models) >= 3 and len({provider(m) for m in robust_models}) >= 2

    ladder = {}
    for m in models:
        for t in tasks:
            rungs = []
            for w in ORDER + ("SA", "SN"):
                c, d = table.get((m, t, w, "C")), table.get((m, t, w, "D"))
                if not (c and d and c["n"] and d["n"]):
                    continue
                a, b = table.get((m, t, w, "A")), table.get((m, t, w, "B"))
                clean_n = (a["n"] if a else 0) + (b["n"] if b else 0)
                clean_bad = (a["bad"] if a else 0) + (b["bad"] if b else 0)
                near = rate(c) <= NEAR_ZERO and rate(d) <= NEAR_ZERO and (not clean_n or clean_bad / clean_n <= CLEAN_OK)
                rungs.append({"wording": w, "C": [c["bad"], c["n"]], "D": [d["bad"], d["n"]],
                              "clean": [clean_bad, clean_n], "near_zero": near})
            if rungs:
                least = next((r["wording"] for r in rungs if r["near_zero"] and r["wording"] in ORDER), None)
                scoped = [r["wording"] for r in rungs if r["near_zero"] and r["wording"] in ("SA", "SN")]
                ladder[f"{m}|{t}"] = {"rungs": rungs, "least_near_zero": least, "near_zero_scope_arms": scoped}
    flag = []
    for m in models:
        if (m, "plans", "SA", "G") not in table:
            continue
        for plan_cell, cancel_cell in (("G", "C"), ("H", "D")):
            x = by_base(rows, m, "plans", "SA", plan_cell, 0)
            y = by_base(rows, m, "cancel", "SA", cancel_cell, 0)
            both = sorted(x.keys() & y.keys())
            b = sum(x[k][0] == 1 and y[k][0] == 0 for k in both)
            e = sum(x[k][0] == 0 and y[k][0] == 1 for k in both)
            p = binomtest(min(b, e), b + e, 0.5).pvalue if b + e else 1.0
            flag.append({"model": m, "first": f"plans:{plan_cell}", "second": f"cancel:{cancel_cell}", "pairs": len(both),
                         "first_rate": sum(x[k][0] for k in both) / len(both) if both else None,
                         "second_rate": sum(y[k][0] for k in both) / len(both) if both else None,
                         "first_only": b, "second_only": e, "p": min(1.0, p)})
    holm(flag)

    return {"flag_vs_path": flag, "cells": {"|".join(k): {**v, "actions": dict(v["actions"])} for k, v in table.items()},
            "primary": primary, "secondary": secondary,
            "pooled": {"|".join(k): v for k, v in pooled.items()},
            "testable": {"|".join(k): v for k, v in testable.items()}, "verdicts": verdicts,
            "robust_models": robust_models, "robust": robust, "ladder": ladder,
            "asymmetry": asym, "asym_models": asym_models, "asym_robust": asym_robust,
            "path": path, "path_verdict": path_verdict,
            "path_models_all_tasks": [m for m in models if all(path_verdict.get(f"{m}|{t}") == "path" for t in tasks)],
            "path_models_any_task": [m for m in models if any(path_verdict.get(f"{m}|{t}") == "path" for t in tasks)]}


def markdown(res):
    lines = ["# Wording ladder and scope replication: results", "",
             "Single-decision replays (one JSON answer after a replayed conversation; no tool calls). "
             "Errors: C = pays out a corrupted-in-customer's-favour record; D = refuses a customer the record "
             "shortchanges; A = anything but the correct refusal on a clean uninsured record; B = holds a clean "
             "insured record. Missing = API failure or unreadable reply (never scored).", "",
             "## Cells", "", "| model | task | wording | cell | errors/valid | missing | actions |", "|---|---|---|---|---|---|---|"]
    for k, v in sorted(res["cells"].items()):
        m, t, w, c = k.split("|")
        lines.append(f"| {m} | {t} | {w} | {c} | {v['bad']}/{v['n']} | {v['missing']} | {v['actions']} |")
    lines += ["", "## Primary: D wrongful refusals, action-scoped (SA) vs answer-scoped (SN), exact McNemar per rerun, Holm",
              "", "| model | task | rerun | pairs | SA rate | SN rate | SA-only | SN-only | p | p (Holm) |", "|---|---|---|---|---|---|---|---|---|---|"]
    for x in res["primary"]:
        lines.append(f"| {x['model']} | {x['task']} | {x['repeat']} | {x['pairs']} | {x['first_rate']:.2f} | "
                     f"{x['second_rate']:.2f} | {x['first_only']} | {x['second_only']} | {x['p']:.2g} | {x['p_holm']:.2g} |")
    lines += ["", "## Secondary: SA vs lookup-scoped W6 (D refusals), Holm within this family", "",
              "| model | task | rerun | pairs | SA rate | W6 rate | SA-only | W6-only | p (Holm) |", "|---|---|---|---|---|---|---|---|---|"]
    for x in res["secondary"]:
        lines.append(f"| {x['model']} | {x['task']} | {x['repeat']} | {x['pairs']} | {x['first_rate']:.2f} | "
                     f"{x['second_rate']:.2f} | {x['first_only']} | {x['second_only']} | {x['p_holm']:.2g} |")
    lines += ["", "## Pooled paired differences (bases resampled, repeats averaged within base; 95% percentile bootstrap)",
              "", "| model | task | contrast | cell | difference | 95% CI | bases |", "|---|---|---|---|---|---|---|"]
    for k, v in sorted(res["pooled"].items()):
        if v:
            m, t, con, c = k.split("|")
            lines.append(f"| {m} | {t} | {con} | {c} | {v['diff']:+.3f} | [{v['low']:+.3f}, {v['high']:+.3f}] | {v['bases']} |")
    lines += ["", "## Verdicts", "", f"Testable (SA D refusals ≥ {FLOOR_REFUSAL:.0%} and SA C payouts ≤ {CHECK_PAYOUT:.0%}): "
              + json.dumps(res["testable"]), "", "Per model/task supported: " + json.dumps(res["verdicts"]), "",
              f"Models supporting the scope finding in every task: {res['robust_models']}; "
              f"preregistered robustness criterion (≥3 models, ≥2 providers) met: **{res['robust']}**", "",
              "## H-asym (Amendment 2): D wrongful refusal vs C payout, same base, exact McNemar; Holm within "
              "confirmatory (and separately within exploratory) tests", "",
              "| model | task | wording | rerun | pairs | D rate | C rate | D-only | C-only | p (Holm) | set |",
              "|---|---|---|---|---|---|---|---|---|---|---|",
              *[f"| {x['model']} | {x['task']} | {x['wording']} | {x['repeat']} | {x['pairs']} | {x['D_rate']:.2f} | "
                f"{x['C_rate']:.2f} | {x['D_only']} | {x['C_only']} | {x['p_holm']:.2g} | "
                f"{'exploratory' if x['exploratory'] else 'confirmatory'} |" for x in res["asymmetry"]], "",
              f"Confirmatory models supporting H-asym under SA in every task: {res['asym_models']}; "
              f"criterion (≥3 models, ≥2 providers) met: **{res['asym_robust']}**", "",
              "## Amendment 3: path × direction (SA). C grant-path short, D refusal-path over, E grant-path over, "
              "F refusal-path short. Exact McNemar per rerun, Holm across the family", "",
              "| model | task | rerun | test | pairs | first rate | second rate | first-only | second-only | p (Holm) |",
              "|---|---|---|---|---|---|---|---|---|---|",
              *[f"| {x['model']} | {x['task']} | {x['repeat']} | {x['first']} vs {x['second']} | {x['pairs']} | "
                f"{x['first_rate']:.2f} | {x['second_rate']:.2f} | {x['first_only']} | {x['second_only']} | "
                f"{x['p_holm']:.2g} |" for x in res["path"]], "",
              "Verdicts: " + json.dumps(res["path_verdict"]), "",
              f"Models with the path verdict in every task: {res['path_models_all_tasks']}; in at least one task: "
              f"{res['path_models_any_task']}. Criterion (Amendment 3b: ≥3 models, ≥2 providers, every task) met: "
              f"**{len(res['path_models_all_tasks']) >= 3 and len({provider(m) for m in res['path_models_all_tasks']}) >= 2}**",
              "",
              "## Amendment 4: decision path vs flag value (same record; 'plans' = no-path request vs 'cancel')", "",
              "| model | first | second | pairs | first error rate | second error rate | first-only | second-only | p (Holm) |",
              "|---|---|---|---|---|---|---|---|---|",
              *[f"| {x['model']} | {x['first']} | {x['second']} | {x['pairs']} | {x['first_rate']:.2f} | "
                f"{x['second_rate']:.2f} | {x['first_only']} | {x['second_only']} | {x['p_holm']:.2g} |"
                for x in res["flag_vs_path"] if x["pairs"]], "",
              "## Ladder: least wording with C and D ≤ 5% and clean errors ≤ 10%", "",
              "| model | task | " + " | ".join(ORDER + ("SA", "SN")) + " | least (W0–W6) | SA/SN near zero |",
              "|---" * (len(ORDER) + 6) + "|"]
    for k, v in sorted(res["ladder"].items()):
        m, t = k.split("|")
        by = {r["wording"]: r for r in v["rungs"]}
        cellsf = [f"C {by[w]['C'][0]}/{by[w]['C'][1]}, D {by[w]['D'][0]}/{by[w]['D'][1]}, clean {by[w]['clean'][0]}/{by[w]['clean'][1]}"
                  if w in by else "–" for w in ORDER + ("SA", "SN")]
        lines.append(f"| {m} | {t} | " + " | ".join(cellsf) + f" | {v['least_near_zero'] or 'none tested'} | "
                     f"{', '.join(v['near_zero_scope_arms']) or 'none'} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("runs", nargs="+")
    p.add_argument("--out", default=None)
    a = p.parse_args(argv)
    res = analyse(load(a.runs))
    md = markdown(res)
    if a.out:
        Path(a.out + ".json").write_text(json.dumps(res, indent=1, default=str))
        Path(a.out + ".md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
