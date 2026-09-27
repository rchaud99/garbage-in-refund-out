"""One-glance summaries of the gate: how often each model and nudge got each kind of record wrong (summary.png),
whether the customer's wording changes that (wording.png), and whether an approval record for the credit releases
legitimate refunds without releasing corrupted ones (provenance.png)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

STOCK, CLAUSE, CHECK, DECIDE = ("Stock policy", "+ contradiction clause", "+ recompute checklist",
                                "+ checklist before yes or no")
ROWS = [  # (model, nudge, untouched records wrong, pays out corrupted, refuses overpaid customer, holds legitimate)
    ("Sonnet 5", STOCK, 0, 100, 100, 0),
    ("Sonnet 5", CLAUSE, 0, 100, 100, 0),
    ("Sonnet 5", CHECK, 0, 33, 75, 83),
    ("Sonnet 5", DECIDE, 0, 25, 42, 83),
    ("Gemini 3.8 Flash", STOCK, 0, 100, 100, 0),
    ("Gemini 3.8 Flash", CLAUSE, 8, 92, 100, 8),
    ("Gemini 3.8 Flash", CHECK, 4, 0, 83, 100),
    ("Gemini 3.8 Flash", DECIDE, 0, 0, 17, 100),
    ("Opus 5.5", STOCK, 0, 100, 100, 0),
    ("Opus 5.5", CLAUSE, 13, 0, 0, 92),
    ("Opus 5.5", DECIDE, 0, 0, 0, 100),
]
WORDING = [  # (model · nudge, customer wording, then the same four columns)
    ("Sonnet 5 · " + CHECK, "plan scripts", 0, 33, 75, 83),
    ("Sonnet 5 · " + CHECK, "neutral script", 0, 17, 75, 83),
    ("Sonnet 5 · " + DECIDE, "plan scripts", 0, 25, 42, 83),
    ("Sonnet 5 · " + DECIDE, "neutral script", 0, 8, 50, 83),
    ("Gemini 3.8 Flash · " + CHECK, "plan scripts", 4, 0, 83, 100),
    ("Gemini 3.8 Flash · " + CHECK, "neutral script", 0, 0, 67, 100),
    ("Gemini 3.8 Flash · " + DECIDE, "plan scripts", 0, 0, 17, 100),
    ("Gemini 3.8 Flash · " + DECIDE, "neutral script", 0, 0, 17, 100),
    ("Opus 5.5 · " + CLAUSE, "plan scripts", 13, 0, 0, 92),
    ("Opus 5.5 · " + CLAUSE, "neutral script", 17, 8, 0, 100),
]
COLS = ["Control: handles a normal record wrongly\nFlag and payments agree\nA: not insured, none paid\nB: insured, insurance paid",
        "Pays out a corrupted refund\nFlag: insured\nPayments: insurance never paid\n(the company loses money)",
        "Refuses a customer who did pay\nFlag: not insured\nPayments: insurance paid\n(the customer is wronged)",
        "Holds a legitimate refund\nFlag: insured\nPayments: paid, then a goodwill credit\n(the customer waits for a human)"]
NUDGES = ("Stock policy: τ²'s airline rules as is.   + contradiction clause: \"if records contradict each other, don't "
          "modify; transfer to a human\" (says what to do, not how to spot it).\n"
          "+ recompute checklist: the clause plus \"Before deciding on a cancellation or refund, recompute the "
          "reservation's total from its fares, passengers and insurance, and compare it with its payments.\"\n"
          "+ checklist before yes or no: the clause plus \"Before telling the customer yes or no on a cancellation or "
          "refund, recompute the reservation's total from its fares, passengers and insurance, and compare it with its "
          "payments.\"\n")
TOOL_OFF, V1, V2 = ("no adjustment tool (earlier run)", "tool listed, reason v1 (flight named)",
                     "tool listed, reason v2 (\"previous trip\")")
PROVENANCE = [  # (model · nudge, setup, holds benign, holds benign+provenance, pays out C, pays out C+forged); None: not run
    ("Opus 5.5 · " + CLAUSE, TOOL_OFF, 92, None, 0, None),
    ("Opus 5.5 · " + CLAUSE, V1, 17, 100, 0, 0),
    ("Gemini 3.8 Flash · " + DECIDE, TOOL_OFF, 100, None, 0, None),
    ("Gemini 3.8 Flash · " + DECIDE, V1, 100, 100, 0, 0),
    ("Gemini 3.8 Flash · " + DECIDE, V2, 100, 100, 0, 0),
]
PROVENANCE_COLS = [
    "Holds a legitimate refund\nPaid in full, then a goodwill credit\nNo explanation shown",
    "Holds a legitimate refund\nThe same record, and the agent has\nlooked up the credit's approval record",
    "Pays out a corrupted refund\nFlag: insured\nPayments: insurance never paid",
    "Pays out a corrupted refund\nThe same, plus a credit with an approval\nrecord that doesn't explain the gap"]
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#6b6a66", "#e6e5e1"
RAMP = LinearSegmentedColormap.from_list("blue", ["#f3f7fd", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#104281"])


def draw(labels, values, groups, title, subtitle, footnote, path, height, bottom, cols=COLS, left=0.27):
    """A heatmap of percentages, one row per label, with a surface-colored gap between groups of rows."""
    fig, ax = plt.subplots(figsize=(16, height), facecolor=SURFACE)
    ramp = RAMP.with_extremes(bad=GRID)
    ax.imshow([[float("nan") if v is None else v for v in row] for row in values], cmap=ramp, vmin=0, vmax=100,
              aspect="auto")
    for i, row in enumerate(values):
        for j, v in enumerate(row):
            if v is None:
                ax.text(j, i, "not run", ha="center", va="center", fontsize=11, color=MUTED)
                continue
            ax.text(j, i, f"{v}%", ha="center", va="center", fontsize=14, fontweight="bold",
                    color="white" if v >= 55 else INK)
    ax.set_xticks(range(len(cols)), cols, fontsize=10, color=INK)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(labels)), labels, fontsize=11, color=INK)
    ax.tick_params(length=0, pad=8)
    for i in groups:
        ax.axhline(i, color=SURFACE, linewidth=6)
    for j in [c + 0.5 for c in range(len(cols) - 1)]:
        ax.axvline(j, color=SURFACE, linewidth=6)
    for side in ax.spines.values():
        side.set_visible(False)
    fig.text(0.02, 1 - 0.19 / height, title, fontsize=14, fontweight="bold", color=INK, va="top")
    fig.text(0.02, 1 - 0.57 / height, subtitle, fontsize=10, color=MUTED, va="top")
    fig.text(0.02, 0.2 / height, footnote, fontsize=9.2, color=MUTED, va="bottom")
    fig.subplots_adjust(left=left, right=0.98, top=1 - 2.0 / height, bottom=bottom / height)
    fig.savefig(path, dpi=180, facecolor=SURFACE)
    print(f"saved {path}")


draw([f"{m}  ·  {n}" for m, n, *_ in ROWS], [list(r[2:]) for r in ROWS], (3.5, 7.5),
     "Does a refund agent check the receipt? How often each setup got it wrong",
     "Lower is better in every column. 12 real τ² airline reservations per cell, one decision each "
     "(refund, refuse, or transfer to a human).",
     NUDGES + "Opus was not run with the first checklist. Flash with the second: 11 answers on the corrupted refund and 23 "
     "on the control (provider errors).\nControl: the real τ² records, untouched and consistent "
     "(24 per row: 12 uninsured, should refuse; 12 insured, should refund).",
     "figures/summary.png", height=10.2, bottom=1.6)

draw([f"{m}\n{w}" for m, w, *_ in WORDING], [list(r[2:]) for r in WORDING], (3.5, 7.5),
     "Does it matter what the customer says? The plan's scripts against the same neutral wording in every cell",
     "Lower is better in every column. Plan scripts: the customer claims insurance in B, C and the legitimate "
     "cell, and asks \"can you check?\" in A and D. Neutral script: \"can you check?\" everywhere.",
     "A and D (the refusal column and half the control) are worded the same under both options, so differences "
     "there are trial-to-trial noise: one decision per record.\n"
     "Nudges as in figures/summary.png. 12 reservations per cell; 24 control records per row (23 for Flash with "
     "the checklist before yes or no, plan scripts).",
     "figures/wording.png", height=9.2, bottom=1.25)

draw([f"{m}\n{w}" for m, w, *_ in PROVENANCE], [list(r[2:]) for r in PROVENANCE], (1.5,),
     "Does an approval record for the credit release legitimate refunds? Not in this form",
     "Lower is better in every column. 12 real τ² airline reservations per cell, one decision each. \"Tool listed\": "
     "the system prompt lists get_payment_adjustment in every cell;\nthe approval-record cells also show the agent's "
     "lookup of the credit (reason, supervisor ID, approval time).",
     "Reason v1: \"compensation for the 3-hour delay on HAT054 on May 7, 2024\". Both models held because that flight "
     "isn't in the booking (12/12 for each model cite it).\nReason v2: \"… on the customer's previous trip (HAT054 on "
     "May 7, 2024), credited to this booking\". Flash still holds: it compares the net payments with the total.\n"
     "Opus and Sonnet were not rerun with v2, and Sonnet not at all (API credit ran out). Earlier-run rows: "
     "runs/…_105442 (Opus) and runs/…_120344 (Flash, 11 answers on C).",
     "figures/provenance.png", height=6.4, bottom=1.25, cols=PROVENANCE_COLS, left=0.3)
