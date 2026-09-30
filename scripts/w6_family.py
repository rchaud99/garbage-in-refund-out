"""W6 (lookup-scoped) comparisons: W6 vs SA and W6 vs SN, on D (wrongful refusal) and C (payout), every model ×
task × rerun with W6 data. Exact McNemar, paired by base; Holm across this whole family; 95% base bootstrap CI of
the paired difference. W6-vs-SA on D was preregistered (secondary); the rest are exploratory, added on request."""
import glob, json, os, sys
from refundout.ladder_analysis import load, mcnemar, boot_diff, holm
dirs = [d for d in sorted(glob.glob("records/ladder-2026-09-28/*_ladder-*"))
        if os.path.exists(d + "/decisions.jsonl") or os.path.exists(d + "/decisions.jsonl.gz")]
rows = load(dirs)
have = {(r["model"], r["task"], r["wording"]) for r in rows}
fam, ci = [], {}
for m, t in sorted({(r["model"], r["task"]) for r in rows if r["wording"] == "W6"}):
    for other in ("SA", "SN"):
        if (m, t, other) not in have:
            continue
        for cell in ("D", "C"):
            ci[(m, t, other, cell)] = boot_diff(rows, m, t, "W6", other, cell)
            for rep in (0, 1):
                x = mcnemar(rows, m, t, "W6", other, cell, rep)
                if x["pairs"]:
                    x["prereg"] = other == "SA" and cell == "D"
                    fam.append(x)
holm(fam)
for x in fam:
    b = ci[(x["model"], x["task"], x["second"], x["cell"])]
    print(f"{x['model'].split('/')[-1]:24s} {x['task']:6s} r{x['repeat']} {x['cell']}: W6 {x['first_rate']:.2f} vs {x['second']} {x['second_rate']:.2f} "
          f"(n={x['pairs']}, W6-only {x['first_only']}, {x['second']}-only {x['second_only']}) p={x['p']:.2g} Holm={x['p_holm']:.2g} "
          f"diff {b['diff']*100:+.0f} [{b['low']*100:+.0f},{b['high']*100:+.0f}] {'prereg' if x['prereg'] else 'exploratory'}")
print("family size", len(fam))
