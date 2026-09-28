"""Quick tabulation of ladder run(s): counts of actions per task x wording x cell."""
import json, sys
from collections import Counter, defaultdict
rows = []
for d in sys.argv[1:]:
    rows += [json.loads(l) for l in open(f"{d}/decisions.jsonl")]
t = defaultdict(Counter)
for r in rows:
    t[(r["model"], r["task"], r["wording"], r["cell"])][r["action"] or ("ERR" if r["error"] else "BAD")] += 1
for k in sorted(t):
    print(*k, dict(t[k]))
print("n", len(rows), "cost", round(sum(r["cost_usd"] or 0 for r in rows), 4))
