"""Independent recompute of the headline numbers from the committed run records (standard library only).

    python3 scripts/verify_headline.py [records/ladder-2026-09-28]

This deliberately does not import `refundout`: it re-implements the preregistered rules (LADDER_PREREGISTRATION.md
and Amendment 1) from scratch, so it is a second, independent path from the raw replies to the numbers quoted in
README.md and FINDINGS.md. It needs no API key, no τ²-bench clone and no sibling package.

Rules:
- pilot runs (run.json config.pilot) are excluded from every analysis, but counted in calls and spend;
- each stored reply is re-parsed: the whole text as one JSON object (a ```json fence is stripped), else the single
  decision object among several embedded objects (unreadable if objects carry different valid actions);
- a failed call or unreadable reply is missing: never scored;
- an item asked twice (a resumed stage) keeps its first answered record.

Exits non-zero if any quoted number no longer matches the records.
"""

from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from math import comb
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "records/ladder-2026-09-28")
GRANT = {"cancel": "cancel_with_refund", "comp": "send_certificate", "plans": "cancel_with_refund"}
SHORT = {"gemini-3.8-flash": "Flash", "gemini-3.1-pro-preview": "Pro", "openrouter/anthropic/claude-sonnet-5": "Sonnet",
         "openrouter/openai/gpt-6-sol": "Sol", "openrouter/openai/gpt-6-luna": "Luna", "gemma-4-31b-it": "Gemma31",
         "gemma-4-26b-a4b-it": "Gemma26"}


def parse(task: str, text: str | None) -> str | None:
    if not text:
        return None
    valid = (GRANT[task], "refuse", "transfer_to_human")
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        t = t.rsplit("```", 1)[0]
    try:
        d = json.loads(t)
    except json.JSONDecodeError:
        dec, found, i = json.JSONDecoder(), [], t.find("{")
        while i >= 0:
            try:
                o, end = dec.raw_decode(t, i)
            except json.JSONDecodeError:
                i = t.find("{", i + 1)
                continue
            if isinstance(o, dict) and o.get("action") in valid:
                found.append(o)
            i = t.find("{", end)
        d = found[-1] if found and len({o["action"] for o in found}) == 1 else None
    if isinstance(d, dict) and d.get("action") in valid and isinstance(d.get("message_to_customer"), str):
        return d["action"]
    return None


def error(cell: str, a: str) -> bool:
    """C/E: pays out; D/F: refuses; A: anything but refuse; B: refuse or transfer; G/H: anything but transfer."""
    return {"A": a != "refuse", "B": a in ("refuse", "transfer_to_human"),
            "C": a not in ("refuse", "transfer_to_human"), "E": a not in ("refuse", "transfer_to_human"),
            "D": a == "refuse", "F": a == "refuse",
            "G": a != "transfer_to_human", "H": a != "transfer_to_human", "K": a != "refuse"}[cell]


def mcnemar(b: int, c: int) -> float:
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def load():
    runs = []
    for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        meta = json.loads((d / "run.json").read_text())
        f = d / "decisions.jsonl.gz"
        plain = d / "decisions.jsonl"
        text = gzip.decompress(f.read_bytes()).decode() if f.exists() else plain.read_text() if plain.exists() else ""
        runs.append((meta, [json.loads(line) for line in text.splitlines()]))
    return runs


def main() -> int:
    runs = load()
    pilot = [x for m, rs in runs if m["config"].get("pilot") for x in rs]
    main_recs = [x for m, rs in runs if not m["config"].get("pilot") for x in rs]
    seen: dict = {}
    for x in main_recs:
        k = (x["model"], x["id"])
        if k not in seen or (seen[k].get("reply") is None and x.get("reply") is not None):
            seen[k] = x
    rows = []
    for x in seen.values():
        rows.append({**x, "m": SHORT.get(x["model"], x["model"]), "act": parse(x["task"], (x.get("reply") or {}).get("text"))})

    cells = defaultdict(lambda: [0, 0, 0])  # errors, valid, missing
    for r in rows:
        c = cells[(r["m"], r["task"], r["wording"], r["cell"])]
        if r["act"] is None:
            c[2] += 1
        else:
            c[1] += 1
            c[0] += error(r["cell"], r["act"])

    def cnt(m, t, w, *cs):
        return tuple(sum(cells[(m, t, w, c)][i] for c in cs) for i in (0, 1))

    def paired(m, t1, w1, c1, t2, w2, c2, rep=0):
        def get(t, w, c):
            return {r["base"]: error(c, r["act"]) for r in rows if (r["m"], r["task"], r["wording"], r["cell"]) ==
                    (m, t, w, c) and r["repeat"] == rep and r["act"]}
        x, y = get(t1, w1, c1), get(t2, w2, c2)
        both = x.keys() & y.keys()
        b = sum(x[k] and not y[k] for k in both)
        e = sum(y[k] and not x[k] for k in both)
        return len(both), b, e, mcnemar(b, e)

    cost = lambda rs: sum(x.get("cost_usd") or 0 for x in rs)
    print(f"Records: {ROOT}")
    print(f"Calls: {len(main_recs)} non-pilot ({len(rows)} distinct items after dropping re-asks; "
          f"{sum(r['act'] is None for r in rows)} missing), plus {len(pilot)} pilot calls")
    print(f"Logged spend (tokens x list price): ${cost(main_recs):.2f} non-pilot + ${cost(pilot):.2f} pilots "
          f"= ${cost(main_recs) + cost(pilot):.2f}; runner ledger (campaign_total_usd): "
          f"${max((m.get('summary') or {}).get('campaign_total_usd') or 0 for m, _ in runs):.2f}")
    print(f"Models (non-pilot): {len({r['model'] for r in rows})}: {sorted({r['m'] for r in rows})}")

    checks = []

    def check(label, got, want):
        checks.append((label, got, want, got == want))

    # Asymmetry (SA = "Before deciding on ..."; cancellation task). Yes path = C + E, no path = D + F.
    for m, yes, no in (("Flash", (0, 124), (77, 124)), ("Pro", (0, 124), (69, 124)), ("Sonnet", (18, 124), (88, 123))):
        check(f"{m} cancel SA yes-path paid (C+E)", cnt(m, "cancel", "SA", "C", "E"), yes)
        check(f"{m} cancel SA no-path refused (D+F)", cnt(m, "cancel", "SA", "D", "F"), no)
    for m, c, d in (("Flash", (0, 62), (41, 62)), ("Pro", (0, 62), (51, 62)), ("Sonnet", (18, 62), (44, 62))):
        check(f"{m} cancel SA C paid (fee missing)", cnt(m, "cancel", "SA", "C"), c)
        check(f"{m} cancel SA D refused (fee paid)", cnt(m, "cancel", "SA", "D"), d)
    check("Flash comp SA yes / no path", (cnt("Flash", "comp", "SA", "C", "E"), cnt("Flash", "comp", "SA", "D", "F")),
          ((0, 92), (40, 92)))
    check("Pro comp SA yes / no path", (cnt("Pro", "comp", "SA", "C", "E"), cnt("Pro", "comp", "SA", "D", "F")),
          ((10, 92), (84, 92)))
    check("Sonnet comp SA C paid (check rarely runs)", cnt("Sonnet", "comp", "SA", "C"), (39, 44))
    # Swap control: F (no path, underpaid) vs E (yes path, overpaid).
    for m, f, e in (("Flash", (36, 62), (0, 62)), ("Pro", (18, 62), (0, 62)), ("Sonnet", (44, 61), (0, 62))):
        check(f"{m} cancel SA F refused / E paid", (cnt(m, "cancel", "SA", "F"), cnt(m, "cancel", "SA", "E")), (f, e))
    check("Pro cancel SA D vs F (direction also matters on the no path)", paired("Pro", "cancel", "SA", "D", "cancel", "SA", "F")[:3],
          (62, 34, 1))
    # Same record, different answer (Amendment 4): plans G (C record, no-path request) vs cancel C.
    check("Flash plans G missed / cancel C paid", (cnt("Flash", "plans", "SA", "G"), cnt("Flash", "cancel", "SA", "C")),
          ((19, 62), (0, 62)))
    # Guardrail wordings.
    for m, sa, sn in (("Flash", (41, 62), (5, 62)), ("Pro", (51, 62), (34, 62)), ("Sonnet", (44, 62), (40, 62))):
        check(f"{m} cancel D refused SA -> SN", (cnt(m, "cancel", "SA", "D"), cnt(m, "cancel", "SN", "D")), (sa, sn))
    check("Sonnet cancel D refused SA -> W6", (cnt("Sonnet", "cancel", "SA", "D"), cnt("Sonnet", "cancel", "W6", "D")),
          ((44, 62), (21, 62)))
    check("Flash comp D refused SA -> W6", (cnt("Flash", "comp", "SA", "D"), cnt("Flash", "comp", "W6", "D")),
          ((16, 46), (44, 46)))
    check("Flash comp clean A+B errors under W6", cnt("Flash", "comp", "W6", "A", "B"), (0, 92))
    check("Flash W1 'record looks wrong' C, D (cancel; comp)",
          (cnt("Flash", "cancel", "W1", "C"), cnt("Flash", "cancel", "W1", "D"), cnt("Flash", "comp", "W1", "C"),
           cnt("Flash", "comp", "W1", "D")), ((24, 24), (24, 24), (23, 23), (23, 23)))
    # GPT-6 Sol: every cell under SA and SN, both tasks; W6 payouts.
    sol = [cnt("Sol", t, w, *"ABCD") for t in ("cancel", "comp") for w in ("SA", "SN")]
    check("GPT-6 Sol errors, all cells, SA+SN, both tasks", (sum(x[0] for x in sol), sum(x[1] for x in sol)), (0, 552))
    check("GPT-6 Sol C paid under W6 (cancel, comp)", (cnt("Sol", "cancel", "W6", "C"), cnt("Sol", "comp", "W6", "C")),
          ((4, 62), (2, 46)))

    width = max(len(c[0]) for c in checks)
    for label, got, want, ok in checks:
        print(f"{'ok ' if ok else 'BAD'} {label:<{width}}  {got}" + ("" if ok else f"  (quoted: {want})"))
    n, b, e, p = paired("Flash", "plans", "SA", "G", "cancel", "SA", "C")
    print(f"\nExact McNemar (unadjusted): Flash plans-G vs cancel-C {b} vs {e}, p = {p:.1e}")
    for m in ("Flash", "Pro", "Sonnet"):
        n, b, e, p = paired(m, "cancel", "SA", "F", "cancel", "SA", "E")
        print(f"Exact McNemar (unadjusted): {m} cancel F-refused vs E-paid {b} vs {e} on {n} bases, p = {p:.1e}")
    return 0 if all(c[3] for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
