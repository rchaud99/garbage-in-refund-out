> **Superseded — kept for the record (results page of the 2026-09-25 Flash study, formerly reports/FINAL_RESULTS.md).** Current results: [README](../../README.md) and the top section of
> [FINDINGS.md](../../FINDINGS.md).

# Final results — Garbage In, Refund Out

**Neither preregistered rule was met, because the retail tasks were at floor.** The airline wording effect is large; the retail follow-ups were at floor (0 refusals under either wording), so they could not test whether the effect generalises. Generality beyond this airline task is untested; the effort rule was not testable (retail analogue at floor; its 'no' path runs through the corrupted number).

| Task | Action-tied refusals | Answer-tied refusals | Orders/bases |
|---|---|---|---:|
| Airline arithmetic | 288/390 (73.8%; CI 66.7–80.5) | 10/390 (2.6%; CI 1.0–4.4) | 65 |
| Retail arithmetic analogue | 0/126 (0%; 95% upper bound 13.3%, 21 orders) | 0/126 (0%; 95% upper bound 13.3%, 21 orders) | 21 |
| Retail cancellation (glance) | 0/180 (0%; 95% upper bound 9.5%, 30 orders) | 0/180 (0%; 95% upper bound 9.5%, 30 orders) | 30 |
| Retail return (glance) | 0/258 (0%; 95% upper bound 6.7%, 43 orders) | 0/258 (0%; 95% upper bound 6.7%, 43 orders) | 43 |

Airline: Gemini 3.8 Flash six-wording study (65 bases, two calls per item); 95% intervals cluster by base, retaining both repeats and all wordings. Zero-event rows give the exact one-sided 95% (Clopper-Pearson) upper bound, 1 − 0.05^(1/n), on the n independent orders rather than calls, because repeated calls are not independent. Zero events do not establish zero population risk. The retail arithmetic task is a payment-switch analogue with synthetic baseline balances; it does not isolate effort.

The airline action-minus-answer refusal gap is 71.3 percentage points (95% CI 64.6–77.4; 65 independent bases). Retail arithmetic had 0 events under either wording across 21 independent orders, so the difference is not estimable (both at floor). Its 600 decisions were all valid: 504/504 corrupted decisions transferred, 0/252 bad approvals, 0/48 false holds on clean eligible records and 0/48 clean-ineligible errors. Four clean orders per family is small n.

The arithmetic analogue uses a native gift-card payment-switch action. A payment-only corruption cannot flip native cancellation/return status eligibility. Real item prices and orders are preserved, but baseline gift-card balances are synthetic; only first-payment amount changes within each clean/corrupt pair. The item-sum invariant passes on all 1,000 source orders. Action, eligibility and transcript also change, so this does not isolate effort causally.

No wrongful refusal summaries existed to review. In an LLM-annotated review (by Codex; not an independent human audit), all 10 selected transfer summaries (five per wording type, ten distinct orders) explicitly compared item sums with first payments; none mentioned benchmarks. These are model-generated summaries, not direct observations of internal computation. Earlier review found benchmark/test references in 7/120 summaries; these do not establish training contamination.

## What ran and spend

| Work | New Gemini calls | Logged USD |
|---|---:|---:|
| Complete interrupted experiments | 250 | 1.457943 |
| Original three-task study | 3,672 | 21.71294325 |
| Retail arithmetic follow-up | 600 | 4.07338950 |
| Both continuations total | 4,522 | 27.24427575 |

The follow-up stayed below its separate $8 cap. No new Claude calls. Historical all-model logged spend was $66.06527150; including this work the project ledger totals $93.30954725. Token/list-price accounting, not a provider invoice; unsaved historical interrupted calls may be missing.

## Deliverables and validation

- Updated project README, FINDINGS.md, MEMO.md, paper/main.tex and ten-page paper PDF.
- Four-task table and refusal figure with clustered intervals; complete per-paraphrase/metric reports and compact CSVs in the project.
- Both preregistrations and request manifests retained. All 600 new prompt hashes match the frozen manifest; all four frozen file hashes match.
- 109 tests pass, including original pinned prompts and the 1,000-order invariant. New code lint passes. The compact CSV reproduces the new contrast exactly.
- All new replies report gemini-3.8-flash, finish reason STOP; no API errors or unreadable replies. The PDF and figure were visually reviewed.
