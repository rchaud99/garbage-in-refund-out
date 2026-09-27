"""README/paper figure from the frozen analysis artifact."""

import json

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from refundout.run import ROOT


def main():
    j = json.loads((ROOT / "reports/power-results.json").read_text())
    tasks = ["airline", "retail_cancel", "retail_return"]
    names = ["Airline cancellation", "Retail cancellation", "Retail return"]
    colors = {"action": "#7c3aed", "answer": "#087f8c"}
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), sharey=True)
    for ax, metric, title in zip(
        axes,
        ["wrongful_refusal", "bad_payout_or_approval"],
        ["Wrongful refusals", "Bad payouts / return approvals"],
    ):
        for typ, offset in [("action", -0.17), ("answer", 0.17)]:
            rs = [
                next(
                    r
                    for r in j["rates"]
                    if r["task"] == t
                    and r["dimension"] == "wording_type"
                    and r["level"] == typ
                    and r["metric"] == metric
                )
                for t in tasks
            ]
            ys = np.array([r["rate"] * 100 for r in rs])
            lo = np.array([r["ci95"][0] * 100 for r in rs])
            hi = np.array([r["ci95"][1] * 100 for r in rs])
            xs = np.arange(3) + offset
            ax.bar(
                xs,
                ys,
                width=0.29,
                color=colors[typ],
                label=typ.capitalize() + "-tied",
                zorder=3,
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
            for x, y, h, r in zip(xs, ys, hi, rs):
                ax.text(
                    x,
                    max(h, 0) + 2,
                    f"{r['k']}/{r['n']}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    rotation=0,
                )
        ax.set_title(title, loc="left", weight="bold", pad=14)
        ax.set_xticks(np.arange(3), names, rotation=15, ha="right")
        ax.set_ylim(0, 105)
        ax.grid(axis="y", alpha=0.18, zorder=0)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Error rate (%)")
    axes[0].legend(frameon=False, loc="upper right")
    fig.suptitle(
        "Does naming both answers change record checking?",
        x=0.06,
        ha="left",
        weight="bold",
        fontsize=18,
    )
    fig.text(
        0.06,
        0.875,
        "Gemini 3.8 Flash · 3 action and 3 answer wordings · 2 repeats per item",
        fontsize=11,
        color="#4b5563",
    )
    fig.text(
        0.06,
        0.035,
        "95% intervals resample bases/orders. Zero-event bootstrap intervals degenerate; they do not imply zero risk.\nAirline: 65 bases per corrupted cell; retail cancellation: 30; retail return: 43. Return approvals are not immediate payouts.",
        fontsize=9,
        color="#4b5563",
    )
    fig.subplots_adjust(left=0.075, right=0.98, top=0.79, bottom=0.23, wspace=0.12)
    (ROOT / "figures").mkdir(exist_ok=True)
    fig.savefig(ROOT / "figures/wording_tasks.png", dpi=190)
    fig.savefig(ROOT / "paper/fig_wording_tasks.pdf")


if __name__ == "__main__":
    main()
