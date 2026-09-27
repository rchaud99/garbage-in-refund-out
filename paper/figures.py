"""The paper's two figures, as vector PDFs. Numbers are the hand-checked tables in FINDINGS.md (runs named there).

    uv run python paper/figures.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).parent
BLUE, VERMILLION, GREEN = "#0072B2", "#D55E00", "#009E73"
"""Okabe–Ito; checked with the dataviz palette validator (lightness, chroma, CVD and contrast all pass)."""
INK, MUTED, GRID = "#222222", "#666666", "#DDDDDD"

plt.rcParams.update({"font.family": "serif", "font.size": 8.5, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42})

# Airline, 12 reservations per cell. None: not run.
NUDGES = ["Stock", "Clause", "Check-\nlist", "Decision-\ntime"]
AIRLINE = {
    "Gemini 3.8 Flash": {"C": [100, 92, 0, 0], "D": [100, 100, 83, 17], "Benign": [0, 8, 100, 100]},
    "Claude Sonnet 5": {"C": [100, 100, 33, 25], "D": [100, 100, 75, 42], "Benign": [0, 0, 83, 83]},
    "Claude Opus 5.5": {"C": [100, 0, None, 0], "D": [100, 0, None, 0], "Benign": [0, 92, None, 100]},
}
SERIES = [("C", "Pays out a corrupted refund (company loses)", BLUE, "o"),
          ("D", "Refuses a customer who paid (customer loses)", VERMILLION, "s"),
          ("Benign", "Holds a legitimate adjusted refund", GREEN, "^")]


def airline() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4), sharey=True)
    for ax, (model, rows) in zip(axes, AIRLINE.items()):
        for key, label, color, marker in SERIES:
            xs = [i for i, v in enumerate(rows[key]) if v is not None]
            ys = [rows[key][i] for i in xs]
            ax.plot(xs, ys, color=color, marker=marker, markersize=5, linewidth=1.6, label=label,
                    markeredgecolor="white", markeredgewidth=0.8)
        ax.set_title(model, fontsize=9, color=INK)
        ax.set_xticks(range(4), NUDGES)
        ax.set_ylim(-6, 106)
        ax.set_yticks([0, 50, 100], ["0%", "50%", "100%"])
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        if model == "Claude Opus 5.5":
            ax.text(2, 50, "not run", ha="center", va="center", color=MUTED, fontsize=7.5, rotation=90)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig(OUT / "fig_airline.pdf", bbox_inches="tight")


# Retail: corrupted orders held, of 24 per family (12 orders × upgrade and downgrade).
RETAIL = [  # (row label, company-loses held, customer-loses held)
    ("Flash · stock", 0, 0), ("Sonnet · stock", 0, 0), ("Opus · stock", 0, 1),
    ("Flash · clause", 11, 8), ("Sonnet · clause", 10, 13), ("Opus · clause", 24, 24),
    ("Flash · checklist", 24, 24), ("Sonnet · checklist", 17, 24),
]


def retail() -> None:
    fig, ax = plt.subplots(figsize=(3.3, 2.6))
    for y, (label, company, customer) in enumerate(reversed(RETAIL)):
        a, b = 100 * company / 24, 100 * customer / 24
        ax.plot([a, b], [y + 0.13, y - 0.13], color=GRID, linewidth=2.2, zorder=1)
        ax.scatter([a], [y + 0.13], color=BLUE, marker="o", s=26, zorder=2, edgecolor="white", linewidth=0.8,
                   label="Company would lose" if y == 0 else None)
        ax.scatter([b], [y - 0.13], color=VERMILLION, marker="s", s=24, zorder=2, edgecolor="white", linewidth=0.8,
                   label="Customer would lose" if y == 0 else None)
    ax.set_yticks(range(len(RETAIL)), [r[0] for r in reversed(RETAIL)])
    ax.set_xlim(-5, 105)
    ax.set_xticks([0, 50, 100], ["0%", "50%", "100%"])
    ax.set_xlabel("Corrupted orders held (of 24)")
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.35, 1.0), ncol=2, frameon=False, fontsize=7.5,
              handletextpad=0.2, columnspacing=0.8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_retail.pdf", bbox_inches="tight")


if __name__ == "__main__":
    airline()
    retail()
