"""Figure: wrongful refusals (D) and corrupted payouts (C) by model, task and check scope, with 95% base-cluster CIs.

    uv run python scripts/ladder_figure.py OUT.png runs/<dir> ...
"""

import random
import sys
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from refundout.ladder_analysis import bad, load

SERIES = [("SA", "Before deciding on … (action)", "#2a78d6"),
          ("W6", "Every time you look up … (lookup)", "#eb6834"),
          ("SN", "Before telling the customer yes or no … (answer)", "#1baf7a")]
TASKS = [("cancel", "Cancellation (62 bases)"), ("comp", "Compensation (23 bases)")]
NAMES = {"gemini-3.8-flash": "Gemini 3.8 Flash", "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
         "gemma-4-31b-it": "Gemma 4 31B", "openrouter/anthropic/claude-sonnet-5": "Claude Sonnet 5",
         "openrouter/anthropic/claude-opus-5.5": "Claude Opus 5.5", "openrouter/openai/gpt-6-sol": "GPT-6 Sol",
         "openrouter/openai/gpt-6-luna": "GPT-6 Luna"}


def rate_ci(rows, seed=20260928, boot=4000):
    per = defaultdict(list)
    for r in rows:
        per[r["base"]].append(bad(r, r["cell"]))
    vals = [sum(v) / len(v) for v in per.values()]
    if not vals:
        return None
    rng = random.Random(seed)
    st = sorted(sum(rng.choice(vals) for _ in vals) / len(vals) for _ in range(boot))
    k = sum(len(v) for v in per.values())
    return sum(vals) / len(vals), st[int(0.025 * boot)], st[int(0.975 * boot) - 1], sum(sum(v) for v in per.values()), k


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    rows = [r for r in load(dirs) if r["action"] and r["wording"] in ("SA", "SN", "W6")]
    models = [m for m in NAMES if any(r["model"] == m for r in rows)]
    fig, axes = plt.subplots(1, 2, figsize=(10, 0.55 * len(models) * 3 + 1.6), sharey=True)
    plt.rcParams.update({"font.family": "DejaVu Sans"})
    for ax, (task, title) in zip(axes, TASKS, strict=True):
        ticks, labels = [], []
        for mi, m in enumerate(models):
            for si, (w, _label, color) in enumerate(SERIES):
                y = mi * 4 + si
                sub = [r for r in rows if r["model"] == m and r["task"] == task and r["wording"] == w and r["cell"] == "D"]
                est = rate_ci(sub)
                if est is None:
                    continue
                p, lo, hi, k, n = est
                ax.plot([lo * 100, hi * 100], [y, y], color=color, lw=2, solid_capstyle="round")
                ax.plot(p * 100, y, "o", color=color, ms=8, mec="white", mew=1.5)
                ax.text(102, y, f"{k}/{n}", va="center", fontsize=8, color="#52514e")
            ticks.append(mi * 4 + 1)
            labels.append(NAMES[m])
        ax.set_yticks(ticks, labels)
        ax.set_xlim(0, 112)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_xlabel("Wrongful refusals of shortchanged customers (D), %")
        ax.set_title(title, fontsize=11, loc="left")
        ax.grid(axis="x", color="#e4e3df", lw=0.8)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.invert_yaxis()
    handles = [plt.Line2D([], [], marker="o", color=c, lw=2, ms=7, label=lab) for _w, lab, c in SERIES]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out, dpi=200)


if __name__ == "__main__":
    main()
