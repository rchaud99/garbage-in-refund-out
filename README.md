# Garbage In, Refund Out

**Question.** When a customer-support agent looks up a record that contradicts itself, does it notice, or does it
apply policy to whatever the database says? And does it matter which way the contradiction points?

**Finding: checked before "yes", trusted before "no".** Told to reconcile a reservation's payments before deciding,
Gemini 3.8 Flash, Gemini 3.1 Pro and Claude Sonnet 5 usually ran the check when the record's insurance flag pointed
to granting the request, and usually skipped it when the flag pointed to refusing.

![Errors on corrupted records by decision path](figures/path_2026-09-28.png)

## Setup

- **Benchmark:** τ²-bench airline (commit `b7ea907`), real reservations.
- **Corruption:** one planted contradiction per record, between the insurance flag and the payments. Four
  corrupted cells: the flag says **yes** (C: fee missing, E: overpaid) or **no** (D: fee paid, F: underpaid).
  Clean controls: A (correct answer is refuse) and B (correct answer is grant).
- **Correct action on every corrupted record:** transfer to a human, per a contradiction clause added to the policy.
- **Two decisions**, each decided by insurance alone:
  - **cancel:** a sick customer cancels (62 bases);
  - **comp:** a customer asks for compensation after an airline-cancelled flight (23 bases × 2 reruns).
- **Instruction under test (SA):** "Before deciding on a cancellation or refund, recompute the reservation's total
  from its fares, passengers and insurance, and compare it with its payments."
- **Format:** single-decision replays. The model reads a replayed conversation, which ends after its own lookups,
  and returns one JSON decision. These are not full τ² episodes.
- **Preregistration:** every stage was preregistered in
  [`preregistration/LADDER_PREREGISTRATION.md`](preregistration/LADDER_PREREGISTRATION.md) and its Amendments 1–5,
  each committed before the data it governs. Every model is reported.

## Key numbers (2026-09-28 campaign)

**Scale.** 6,159 non-pilot calls (6,079 distinct items after resumed stages re-asked 80; 27 missing or unreadable),
plus 177 pilot calls. 7 models from 3 providers; the two Gemma models are free-tier and partial.
**$38.40** of API spend (logged tokens × list price, pilots included; not a provider invoice).

**1. The asymmetry (cancellation, SA wording).**

| Model | yes-path records paid out (C+E) | no-path records refused (D+F) | D only: fee paid, refused |
|---|---|---|---|
| Gemini 3.8 Flash | 0/124 (0%) | 77/124 (62%) | 41/62 (66%) |
| Gemini 3.1 Pro | 0/124 (0%) | 69/124 (56%) | 51/62 (82%) |
| Claude Sonnet 5 | 18/124 (15%) | 88/123 (72%) | 44/62 (71%) |

- Sonnet's 15% pools the C cell (18/62, 29%) with the E cell (0/62).
- "No-path refused" pools D (the fee was paid, so the customer may be owed a refund) with F (underpaid, so the
  customer is not owed anything). In both cells the correct action was to escalate, and the model refused instead.
- **Compensation:** Flash was 0/92 on the yes path vs 40/92 on the no path, and Pro 10/92 vs 84/92. Sonnet paid
  out 77/90 on the yes path, so it rarely ran the check at all. Its path test is not testable there.

**2. Swap control.**
- Test: flip which answer the over- and underpaid records point to (E: yes-path overpaid; F: no-path underpaid).
- Result: the errors follow the answer, not the arithmetic direction.
  - F refused vs E paid, cancellation: Flash 36/62 vs 0/62, Pro 18/62 vs 0/62, Sonnet 44/61 vs 0/62. Exact
    McNemar, Holm p ≤ 2.3e-4.
  - Compensation: Flash 24/46 vs 0/46 and Pro 42/46 vs 4/46 (Holm p ≤ 0.013).
- Exception: for Pro on cancellation, the direction also mattered on the no path. It refused overpaid D records
  more often than underpaid F records (51/62 vs 18/62).

**3. Same record, different answer (Flash only).**
- The yes-path record C was shown with a request whose answer is "no" whatever the flag says ("my plans changed").
- Flash missed it 19/62 times (31%), against 0/62 when the answer was "yes" (McNemar 19 vs 0, Holm p = 7.6e-6).

**4. Guardrail sentences are model-specific** (wrongful refusals of D records on cancellation, unless noted).

| Sentence | Flash | Pro | Sonnet |
|---|---|---|---|
| SA "Before deciding on…" (baseline) | 41/62 | 51/62 | 44/62 |
| SN "Before telling the customer yes or no on…" | **5/62** | 34/62 | 40/62 (no change) |
| W6 "Every time you look up a reservation, recompute…" | 29/62; **compensation: 44/46** (SA: 16/46) | not run | **21/62** |

- "If a record looks wrong, transfer to a human agent." left Flash wrong on every corrupted record in both
  directions (cancel 24/24 and 24/24; comp 23/23 and 23/23). Clean records stayed correct.
- W6 also raised Gemma 4 31B's payouts on cancellation, from 1/62 to 18/39.

**5. GPT-6 Sol checks both ways.**
- Under SA and SN it made 0 errors on all 552 decisions, corrupted and clean, on both tasks.
- Under W6 it made a few payouts (4/62 on cancellation, 2/46 on compensation) and no refusals.
- GPT-6 Luna made 0 errors on cancellation under SA and SN, and 1–5/46 on compensation.

## Limitations

- **The preregistered robustness bar was not met.** For the path finding, the bar was ≥ 3 models from ≥ 2 providers,
  on both tasks.
  - Only Gemini Flash and Gemini Pro cleared it on both tasks.
  - Sonnet showed it on cancellation only; on compensation it rarely checked at all.
  - Both Gemma models showed it on cancellation (Gemma 26B partial). Gemma adds models, not providers.
  - The scope finding (SN beats SA) also failed its bar. It was supported only for Flash and Pro on
    cancellation, with no effect in Sonnet.
- **Exploratory elements.**
  - Flash's D-vs-C asymmetry motivated the H-asym hypothesis (Amendment 2), so Flash is exploratory for it.
  - The E/F swap control was preregistered for Flash, Pro and Sonnet before their E/F data.
  - The overall path criterion (Amendment 3b) was written after the Flash and Pro E/F results, and before Sonnet's.
- **Format and scope.**
  - Single decisions, not conversations. An earlier small conversation test found smaller gaps.
  - One domain (airline), one kind of corruption (the insurance flag vs payments), two decisions.
- **Gemma data are partial.** The user stopped all runs at 21:25 on 2026-09-28. Gemma 4 31B compensation stopped
  at 36/184 calls, Gemma 26B compensation never started, and Gemma 26B cancellation reached 246/248.
- **Not run:** Opus 5.5 (budget), and Sonnet under W6 on compensation.
- **Reasoning evidence is thin.** Claims about what models "checked" rest on actions and on keyword counts in
  reasoning summaries, not on full reasoning traces.

## Reproduce

The numbers above come from the committed run records in
[`records/ladder-2026-09-28/`](records/ladder-2026-09-28/): each run's `run.json`, plus every call's prompt hash,
raw reply, reasoning summary, usage and cost (gzipped). Nothing needs an API key.

```sh
# 1. Independent recompute of every number in this README. Standard library only: no uv, no τ², no sibling package.
python3 scripts/verify_headline.py

# 2. The frozen preregistered analysis. Regenerates reports/ladder-results.{md,json} byte-for-byte.
uv sync
uv run python -m refundout.ladder_analysis records/ladder-2026-09-28/*_ladder-* --out reports/ladder-results
uv run python scripts/replication_table.py reports/ladder-results.json   # body of reports/replication-table.md
uv run python scripts/w6_family.py                                        # W6 family (Holm across 44 tests)

# 3. Tests, including checks that both paths reproduce the committed results.
uv run pytest -q
```

**Requirements for `uv sync`:**
- Python 3.12+ and uv.
- The sibling checkout `../how_much_is_a_look_worth`. It provides `lookworth`, a local path dependency used by the
  runners and model adapters.
- τ²-bench, needed only to rebuild prompts or run new calls. Some tests use it when present. Clone it into
  `vendor/`:

  ```sh
  git clone https://github.com/sierra-research/tau2-bench vendor/tau2-bench
  git -C vendor/tau2-bench checkout b7ea9074c1cba482b30687fecdb5c8425fd6f619
  ```

Paid runs go through `scripts/ladder_stages.sh`. That script refuses non-pilot stages unless the preregistration
exists and the stage's frozen plan hash matches `reports/ladder-plans/`.

## Repository layout

| Path | Contents |
|---|---|
| `FINDINGS.md` | Full results. The top section is current (2026-09-28); the sections below it are the earlier studies. |
| `preregistration/` | The three preregistrations, byte-identical to the versions hashed into each run's `run.json`. |
| `records/ladder-2026-09-28/` | Raw per-call records of the 2026-09-28 campaign, pilots included (flagged in `run.json`). |
| `reports/` | Generated results: `ladder-results.*`, `replication-table.md`, frozen stage plans, earlier-study tables and compact decision CSVs, spend ledger, progress reports. |
| `src/refundout/` | Task builders, model adapters, budget-capped runners and the frozen analyses. |
| `scripts/` | Stage launcher, figures, the independent `verify_headline.py`. `scripts/legacy/` holds superseded write-up generators. |
| `tests/` | pytest suite (123 tests). |
| `tau2_integrity/` | A τ²-native generator of paired corrupt and clean tasks, with a runner shim and scorer ([README](tau2_integrity/README.md)). |
| `figures/`, `paper/` | Figures. The paper (`paper/main.pdf`) covers the earlier 2026-09-25 Flash study only. |
| `docs/` | Deployment memo, website draft, the 2026-09-27 red-team review, the autonomous lab notebook, the draft τ² issue (not posted). |
| `docs/history/` | Superseded plans, TODOs, digests and "final results" pages, kept for the record and not current. |

## How the claims were checked

- **Preregistration.** The preregistration and each amendment were committed before the data they govern (see
  `git log -- preregistration/LADDER_PREREGISTRATION.md`). Pilots are excluded from every analysis.
- **Red-team review.** [`docs/REVIEW_2026-09-27.md`](docs/REVIEW_2026-09-27.md) records five independent reviews
  of the earlier studies. Their fixes are applied.
- **Killed claims.** [`FINDINGS.md`](FINDINGS.md) lists the killed and weakened claims, including the Sonnet
  wording-effect replication that failed.
- **Lab notebook.** [`docs/AUTONOMOUS_LOG.md`](docs/AUTONOMOUS_LOG.md) is the notebook of the 2026-09-28 session.
- **Independent recompute (2026-09-30).** Every number in this README was recomputed from the raw records by
  `scripts/verify_headline.py`, which shares no code with the analysis package.

## Earlier studies (2026-09-24 to 2026-09-25)

- **Setup:** Gemini 3.8 Flash only, 65 airline bases, a six-wording study.
- **Airline:** action-scoped checks gave 288/390 wrongful refusals, against 10/390 for answer-scoped checks.
- **Retail:** the follow-ups were at floor (0 events), so generality beyond airline was untested there.
- **Opus 5.5:** 0/24 errors under every wording, at floor.
- **Details:** [FINDINGS.md](FINDINGS.md) (earlier sections), [`reports/power-results.md`](reports/power-results.md),
  [`reports/effort-results.md`](reports/effort-results.md) and the [paper](paper/main.pdf).
- **Reproduce:** the compact decisions are in `reports/*-decisions.csv`:

  ```sh
  uv run --no-project --with numpy --with scipy python scripts/reanalyse_compact.py
  uv run --no-project --with numpy python scripts/reanalyse_effort_compact.py
  ```
- **Raw records** for these earlier runs are not committed (about 260 MB). The compact decisions and hashed
  manifests are.

## Not in the repository

- `vendor/tau2-bench`: clone it as shown above. It was used unmodified.
- `runs/` and `work/`: local raw run directories and scratch. The 2026-09-28 runs are mirrored in `records/`.
- `.venv/`, caches, LaTeX build products, and `.env` (API keys).

## License

The code and write-ups are MIT (see `LICENSE`). τ²-bench and its data keep their own license.
