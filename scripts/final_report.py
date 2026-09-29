"""Build the final HTML report (then printed to PDF with headless Chrome) from reports/ladder-results.json.

    uv run python scripts/final_report.py reports/ladder-results.json website.md OUT.html
Numbers in the tables come from the JSON, not from hand-typed text.
"""
import html
import json
import sys

res = json.load(open(sys.argv[1]))
website = open(sys.argv[2]).read()
out = sys.argv[3]
C = res["cells"]
NAMES = {"gemini-3.8-flash": "Gemini 3.8 Flash", "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
         "gemma-4-31b-it": "Gemma 4 31B", "gemma-4-26b-a4b-it": "Gemma 4 26B-A4B",
         "openrouter/anthropic/claude-sonnet-5": "Claude Sonnet 5", "openrouter/openai/gpt-6-sol": "GPT-6 Sol",
         "openrouter/openai/gpt-6-luna": "GPT-6 Luna"}


def cnt(m, t, w, c):
    v = C.get(f"{m}|{t}|{w}|{c}")
    return f"{v['bad']}/{v['n']}" if v and v["n"] else "–"


def pj(xs):
    return "; ".join(f"{x['p_holm']:.2g}" for x in xs) or "–"


def md_to_html(md):
    import re

    def inline(t):
        t = html.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        return re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)

    parts, para, depth = [], [], 0

    def flush():
        nonlocal para
        if para:
            parts.append("<p>" + " ".join(para) + "</p>")
            para = []

    def close_to(d):
        nonlocal depth
        while depth > d:
            parts.append("</li></ul>")
            depth -= 1

    for line in md.splitlines():
        m = re.match(r"^( *)- (.*)$", line)
        if line.startswith("## "):
            flush(); close_to(0); parts.append(f"<h3>{html.escape(line[3:])}</h3>")
        elif m:
            flush()
            d = len(m.group(1)) // 2 + 1
            if d > depth:
                parts.append("<ul><li>"); depth = d
            else:
                close_to(d); parts.append("</li><li>")
            parts.append(inline(m.group(2)))
        elif not line.strip():
            flush(); close_to(0)
        elif depth:
            parts.append(" " + inline(line.strip()))
        else:
            para.append(inline(line))
    flush(); close_to(0)
    return "\n".join(parts).replace("<ul><li></li><li>", "<ul><li>")


rows = []
for m in NAMES:
    for t in ("cancel", "comp"):
        if f"{m}|{t}|SA|D" not in C:
            continue
        prim = [x for x in res["primary"] if x["model"] == m and x["task"] == t]
        path = [x for x in res["path"] if x["model"] == m and x["task"] == t and x["first"] == "F"]
        pb = res["pooled"].get(f"{m}|{t}|SA-SN|D")
        diff = f"{pb['diff'] * 100:+.0f} [{pb['low'] * 100:+.0f}, {pb['high'] * 100:+.0f}]" if pb else "–"
        scope = ("supported" if res["verdicts"].get(m, {}).get(t, {}).get("supported") else
                 ("not testable" if not res["testable"].get(f"{m}|{t}") else "not supported"))
        pv = res["path_verdict"].get(f"{m}|{t}", "not run")
        reps = max(len(prim), 1)
        rows.append(f"<tr><td>{NAMES[m]}</td><td>{t}</td><td class=n>{reps}</td><td class=n>{cnt(m,t,'SA','C')}</td>"
                    f"<td class=n>{cnt(m,t,'SA','D')}</td><td class=n>{cnt(m,t,'SN','D')}</td><td class=n>{diff}</td>"
                    f"<td>{pj(prim)}</td><td class=n>{cnt(m,t,'SA','E')}</td><td class=n>{cnt(m,t,'SA','F')}</td>"
                    f"<td>{pj(path)}</td><td>{scope}</td><td>{pv}</td></tr>")
table = "\n".join(rows)
body = open(__file__.replace("final_report.py", "final_report_body.html")).read()
open(out, "w").write(open(__file__.replace("final_report.py", "final_report_template.html")).read()
                     .replace("{{BODY}}", body).replace("{{TABLE}}", table).replace("{{WEBSITE}}", md_to_html(website))
                     .replace("{{PATH_ALL}}", ", ".join(NAMES.get(m, m) for m in res["path_models_all_tasks"]))
                     .replace("{{PATH_ANY}}", ", ".join(NAMES.get(m, m) for m in res["path_models_any_task"])))
import subprocess
wt = subprocess.run([sys.executable, __file__.replace("final_report.py", "wording_table.py"), sys.argv[1], "cancel"],
                    capture_output=True, text=True).stdout.strip().splitlines()
hdr, rows_ = wt[0], wt[2:]
cols = [c.strip() for c in hdr.strip("|").split("|")]
th = "".join(f"<th>{c}</th>" for c in cols)
trs = "".join("<tr>" + "".join(f"<td>{c.strip()}</td>" for c in r.strip("|").split("|")) + "</tr>" for r in rows_)
txt = open(out).read().replace("{{WORDTABLE}}", f"<table><tr>{th}</tr>{trs}</table>")
open(out, "w").write(txt)
print("wrote", out)
