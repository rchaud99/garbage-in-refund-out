"""Exploratory: share of replies whose reasoning summary shows arithmetic (a sum or the word total/recompute),
by model x task x wording x cell x action. Keyword heuristic, not a judge."""
import json, re, sys
from collections import defaultdict
from refundout.ladder_analysis import load
PAT = re.compile(r"recomput|\btotal\b|\d+\s*[x×*+]\s*\d+|\$\d+.*\$\d+", re.I | re.S)
rows = load(sys.argv[1:])
t = defaultdict(lambda: [0, 0])
for r in rows:
    if r["action"] and r["cell"] in "CDEF" and r["wording"] in ("SA", "SN", "W6"):
        th = (r["reply"] or {}).get("thoughts") or ""
        k = (r["model"].split("/")[-1], r["task"], r["wording"], r["cell"], r["action"])
        t[k][0] += bool(PAT.search(th)); t[k][1] += 1
for k in sorted(t):
    if t[k][1] >= 5:
        print(*k, f"{t[k][0]}/{t[k][1]}")
