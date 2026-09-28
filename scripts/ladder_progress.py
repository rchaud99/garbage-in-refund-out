"""Progress of ladder runs: records, action counts, errors, mean $/call."""
import json, sys
from collections import Counter
for d in sys.argv[1:]:
    try:
        rs = [json.loads(l) for l in open(f"{d}/decisions.jsonl")]
    except FileNotFoundError:
        continue
    c = Counter((r["action"] or ("ERR:" + (r["error"] or "")[:50] if r["error"] else "BAD")) for r in rs)
    print(d.split("/")[-1][-55:], len(rs), dict(c), round(sum(r["cost_usd"] or 0 for r in rs) / max(1, len(rs)), 5))
