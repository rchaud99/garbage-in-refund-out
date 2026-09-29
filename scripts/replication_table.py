"""Replication table (models × tasks × reruns) from a ladder_analysis JSON: scope (SA vs SN) and path (F vs E).

    uv run python scripts/replication_table.py reports/ladder-results.json > reports/replication-table.md
"""

import json
import sys

NAMES = {"gemini-3.8-flash": "Gemini 3.8 Flash", "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
         "gemma-4-31b-it": "Gemma 4 31B", "openrouter/anthropic/claude-sonnet-5": "Claude Sonnet 5",
         "openrouter/openai/gpt-6-sol": "GPT-6 Sol", "openrouter/openai/gpt-6-luna": "GPT-6 Luna"}


def cell(res, m, t, w, c):
    v = res["cells"].get(f"{m}|{t}|{w}|{c}")
    return f"{v['bad']}/{v['n']}" if v and v["n"] else "–"


def main():
    res = json.load(open(sys.argv[1]))
    out = ["| model | task | reruns | C paid SA | D refused SA | D refused SN | SA−SN [95% CI] | McNemar SA vs SN, Holm p per rerun "
           "| E paid SA | F refused SA | McNemar F vs E, Holm p per rerun | scope | path |",
           "|---" * 13 + "|"]
    for m in NAMES:
        for t in ("cancel", "comp"):
            if f"{m}|{t}|SA|D" not in res["cells"]:
                continue
            prim = [x for x in res["primary"] if x["model"] == m and x["task"] == t]
            path = [x for x in res["path"] if x["model"] == m and x["task"] == t and x["first"] == "F"]
            pb = res["pooled"].get(f"{m}|{t}|SA-SN|D")
            diff = f"{pb['diff'] * 100:+.0f} pp [{pb['low'] * 100:+.0f}, {pb['high'] * 100:+.0f}]" if pb else "–"
            scope = ("supported" if res["verdicts"].get(m, {}).get(t, {}).get("supported") else
                     ("not testable" if not res["testable"].get(f"{m}|{t}") else "not supported"))
            out.append(
                f"| {NAMES[m]} | {t} | {max(len(prim), 1)} | {cell(res, m, t, 'SA', 'C')} | {cell(res, m, t, 'SA', 'D')} | "
                f"{cell(res, m, t, 'SN', 'D')} | {diff} | {'; '.join(f'{x['p_holm']:.2g}' for x in prim) or '–'} | "
                f"{cell(res, m, t, 'SA', 'E')} | {cell(res, m, t, 'SA', 'F')} | "
                f"{'; '.join(f'{x['p_holm']:.2g}' for x in path) or '–'} | {scope} | "
                f"{res['path_verdict'].get(f'{m}|{t}', 'not run')} |")
    print("\n".join(out))


if __name__ == "__main__":
    main()
