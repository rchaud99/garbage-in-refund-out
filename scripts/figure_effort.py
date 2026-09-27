"""Four-task refusal comparison; empirical order-cluster uncertainty."""

import json

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from refundout.run import ROOT


def main():
    prior = json.loads((ROOT / "reports/power-results.json").read_text())
    new = json.loads((ROOT / "reports/effort-results.json").read_text())
    tasks = ["airline", "retail_arithmetic", "retail_cancel", "retail_return"]
    names = [
        "Airline\narithmetic",
        "Retail payment switch\narithmetic analogue",
        "Retail cancellation\nglance-level",
        "Retail return\nglance-level",
    ]
    rates = prior["rates"] + new["rates"]
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, ax = plt.subplots(figsize=(11.5, 6.3))
    for typ, offset, color in [
        ("action", -0.18, "#7c3aed"),
        ("answer", 0.18, "#087f8c"),
    ]:
        rs = [
            next(
                r
                for r in rates
                if r["task"] == task
                and r["dimension"] == "wording_type"
                and r["level"] == typ
                and r["metric"] == "wrongful_refusal"
            )
            for task in tasks
        ]
        ys = np.array([r["rate"] * 100 for r in rs])
        lo, hi = (np.array([r["ci95"][i] * 100 for r in rs]) for i in [0, 1])
        xs = np.arange(4) + offset
        ax.bar(
            xs, ys, width=0.3, color=color, label=typ.capitalize() + "-tied", zorder=3
        )
        ax.errorbar(
            xs,
            ys,
            yerr=[ys - lo, hi - ys],
            fmt="none",
            color="#253044",
            capsize=4,
            zorder=4,
        )
        for x, h, r in zip(xs, hi, rs):
            ax.text(x, h + 2, f"{r['k']}/{r['n']}", ha="center", fontsize=10)
    ax.set_xticks(np.arange(4), names)
    ax.tick_params(axis="x", length=0, pad=10)
    ax.set_ylim(0, 102)
    ax.set_ylabel("Wrongful refusals (%)")
    ax.grid(axis="y", alpha=0.18, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper right")
    title = (
        "The retail analogue meets the effort-pattern rule"
        if new["effort_pattern_rule_held"]
        else "The retail analogue does not meet the effort-pattern rule"
    )
    fig.suptitle(title, x=0.08, ha="left", weight="bold", fontsize=17)
    fig.text(
        0.08,
        0.895,
        "Gemini 3.8 Flash · 3 action and 3 answer wordings · 2 calls per item",
        color="#4b5563",
    )
    fig.text(
        0.08,
        0.025,
        "95% bootstrap CIs cluster by order/base: airline 65; retail arithmetic 21; cancellation 30; return 43.\n"
        "Zero-event intervals do not establish zero risk. Retail arithmetic uses synthetic gift-card balances\n"
        "and a different action; this comparison does not isolate the causal effect of check effort.",
        fontsize=9,
        color="#4b5563",
    )
    fig.subplots_adjust(left=0.09, right=0.98, top=0.83, bottom=0.25)
    fig.savefig(ROOT / "figures/effort_tasks.png", dpi=190)
    fig.savefig(ROOT / "paper/fig_effort_tasks.pdf")


if __name__ == "__main__":
    main()
