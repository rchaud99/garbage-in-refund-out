"""Figure: under the action-scoped check (SA), errors on the grant path (C, E) vs the refusal path (D, F).

    uv run python scripts/path_figure.py OUT.png runs/<dir> ...
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ladder_figure import NAMES, rate_ci
from refundout.ladder_analysis import load

CELLS = [("C", "yes-path, underpaid → paid out", "#2a78d6", "o"),
         ("E", "yes-path, overpaid → paid out", "#2a78d6", "s"),
         ("D", "no-path, overpaid → refused", "#eb6834", "o"),
         ("F", "no-path, underpaid → refused", "#eb6834", "s")]
TASKS = [("cancel", "Cancellation (62 bases)"), ("comp", "Compensation (23 bases × 2 reruns)")]


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    rows = [r for r in load(dirs) if r["action"] and r["wording"] == "SA"]
    models = [m for m in NAMES if any(r["model"] == m and r["cell"] in "EF" for r in rows)]
    fig, axes = plt.subplots(1, 2, figsize=(10, 1.1 * len(models) + 1.9), sharey=True)
    for ax, (task, title) in zip(axes, TASKS, strict=True):
        ticks = []
        for mi, m in enumerate(models):
            for ci, (cell, _lab, color, marker) in enumerate(CELLS):
                y = mi * 5 + ci
                est = rate_ci([r for r in rows if r["model"] == m and r["task"] == task and r["cell"] == cell])
                if est is None:
                    continue
                p, lo, hi, k, n = est
                ax.plot([lo * 100, hi * 100], [y, y], color=color, lw=2, solid_capstyle="round")
                ax.plot(p * 100, y, marker, color=color, ms=7, mec="white", mew=1.2)
                ax.text(102, y, f"{k}/{n}", va="center", fontsize=7.5, color="#52514e")
            ticks.append(mi * 5 + 1.5)
        ax.set_yticks(ticks, [NAMES[m] for m in models])
        ax.set_xlim(0, 114)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_xlabel("Error rate on corrupted records, % (95% base-cluster CI)")
        ax.set_title(title, fontsize=11, loc="left")
        ax.grid(axis="x", color="#e4e3df", lw=0.8)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.invert_yaxis()
    handles = [plt.Line2D([], [], marker=mk, color=c, lw=2, ms=7, label=lab) for _c, lab, c, mk in CELLS]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(out, dpi=200)


if __name__ == "__main__":
    main()
