# Next steps

**Historical roadmap, superseded 2026-09-25.** See PREREGISTRATION.md and the newest FINDINGS sections for the completed continuation. Earlier résumé claims below are drafting history, not current conclusions. Do not claim universal action/refusal asymmetry.


**Update 2026-09-24 evening:** done since this was written: F1dc on Sonnet/Opus ($2.18), the $35 insurance-fee
check ($2.93), and the retail exchange gate ($14.09; see FINDINGS.md, Retail). Remaining: steps 2–7 below.

2026-09-24. So far: single decisions on 12 real τ² reservations per cell, 3 models, ≈$17 in run logs
(per call: Flash $0.007, Sonnet $0.011, Opus $0.028). Plan = v1.2 PDF; results = `FINDINGS.md`.

## 1. Plan status

| Item | Status | Result / gap |
|---|---|---|
| Q1, H7 check unprompted? | Done (n=12) | No: stock policy, 3/3 models paid 100% of C, refused 100% of D; 0/72 named the gap to the customer (Opus saw it in 3/12 D reasonings, refused anyway) |
| Q2 what makes them check | Partly | Clause, F1, F1d, F1dc measured; cost in holds only, no $/latency, no blind reviewer |
| H1 unchecked with clause | Done | Sonnet 100%, Flash 92% paid C; **Opus 0%** (model-dependent) |
| H2 checklist halves bad writes | Supported | Sonnet 100→33%, Flash 92→0% |
| Q4, H8 decision-time check | Done, reword | D refusals: F1 75–83% → F1d Flash 17%, Sonnet 42–50%, Opus 0%; 0 extra A holds, but benign held 83–100% |
| Q5, H4 lopsided vigilance | Done, reword | Yes under checklists (Sonnet F1 neutral: C caught 83%, D 25%); not at baseline, not Opus |
| Q6 legitimate ledgers | Partly | Every checker held credits; provenance + counting rule (F1dc) fixed it for Flash; Sonnet/Opus cut off |
| Q3/H3 amounts, Q7/H6 blocks, Q8 retail, H5 blind reviewer | Not done | |
| Generator + CI eval | Partly | Single-call generator, tests, budget cap; no τ² task files, no CI thresholds, repo uncommitted |
| Check wrapper + checklist | Partly | F1d/F1dc prompts done; F3 wrapper not built |
| Memo + cost per 1,000 conversations | Not done | Memo bullets in FINDINGS only; no per-conversation cost |
| Data-quality scan | Partly | Payment rule verified 2,000/2,000 in tests; PHX quirk found by Opus, not a scan |
| Two figures | Partly | `summary.png` covers C vs B; "who does each fix protect" missing |
| Write-up, repo, demo, PR | Partly | README + FINDINGS only |

## 2. Plan changes the data justifies

- **The central finding widens.** Write-step blindness reappears *inside* the agent: "recompute before deciding"
  runs before yes, not before no. Headline: checks guard the company by default, at the gate and in the prompt;
  protecting the customer needs the check placed at the answer.
- **Model dependence is a finding.** One clause turns Opus fully on and Sonnet not at all. H1 → "for at least one
  model"; memo rule: validate every prompt fix per model.
- **Provenance needs a counting rule.** Approval record alone: 12/12 still held; plus "add approved credits back":
  12/12 released, forgeries 12/12 held (Flash). Adjustment-aware F3 is that rule in code. New H9 states it.
- **Rewording.** H4 "lopsided under checks tied to a decision"; H7 split noticed-in-reasoning from
  named-to-customer; H8 counts benign holds, not only cell A.
- **Test awareness.** Opus called the PHX quirk "the intentional trap": report how often reasoning mentions a test.
- **τ² quirks are content.** Three one-way PHX→PHX round trips cause every Opus control error: exclude them from
  bases, report them in the scan. Pool is 347, not 354.
- **Single calls replace the grid.** Plan: ~1,240 episodes/model, $1.2–3.5k. Actual: $17. Use ~100 episodes only
  to confirm and to price conversations. Sonnet costs $2/$10, not $3/$15; Opus 5.5 replaces Fable.
- **Cut or defer:** F2 demo (by construction; one line in the figure), F4/H5, pass^k repeats (neutral run is the
  replicate), soft/none detectability sets, the 50-transcript LLM judge (keep structured actions + hand read).
  Do the LedgerAgent predicate check (1 h, $0) before claiming novelty.

## 3. Roadmap (≤ 1 week, ≤ $60; top up API credit first)

| # | Step and purpose | Cost | Produces |
|---|---|---|---|
| 1 | ~~Done 2026-09-24, $2.18: 36/36 released, 36/36 forged held~~ Rerun F1dc on Sonnet and Opus (gate + provenance, 108 calls each) + Opus F0 provenance v2: complete the row | ~$6 | "Provenance + counting rule released credits for [pending]/3 models" |
| 2 | F3 integrity gate, strict vs adjustment-aware, as write wrapper and nightly scan over all 2,000 τ² reservations and every cell: the code-level comparison and data-quality artifact | $0 | "Blocks 100% of C, sees 0% of D; strict holds every credit, aware passes forgeries; flags [N] real τ² records" |
| 3 | Same reconciliation as a read tool shown before the decision, 3 models × 5 cells: can code protect both directions? | ~$3 | "Handing agents the check cut D refusals to [pending]" |
| 4 | Scale to 30 bases: 3 models × {F0, F1d, F1dc} × 5 cells (draw is prefix-stable, 18 new bases) | $13–21 | Headline chart, intervals ≈ ±15 pts |
| 5 | Full τ² episodes: pilot 6, then B/C/D × 10 bases × {F0, F1d} on Sonnet and Flash; Opus F0 on C/D if budget | ~$25 | "Episode rates within [pending] pts of single calls; $[pending]/conversation" |
| 6 | One-page memo with the cost-per-1,000 model; "who does each fix protect" figure (fixes × company / customer / legitimate / $) | $0 | The FDE deliverable |
| 7 | First commit; README led by the figure; `make eval` CI on dry-run fakes; 60 s terminal demo; τ³-bench issue | $0 | Public repo |

Total ≈ $47–55. **Step 5 needs:** a generator writing τ² task files (`initial_state` edit, per-cell script,
expected actions); a policy-variant airline domain per nudge; τ²'s own runner with one fixed user simulator
(Gemini 3.8 Flash); a database-diff scorer labelling write / transfer / refuse from final DB and tool log (τ²'s
reward cannot tell refuse from transfer); litellm costs under the existing budget cap. Stop if the pilot exceeds
~$0.40 per episode.

**Later.** H3 fare family (new write path; fare drift makes it a design job; memo doesn't need it); Q8 retail
(breadth only). H6: 10 enforced-F3 C episodes (~$3) only if step 5 works by day 4.

## 4. Résumé and pitch

**Garbage In, Refund Out | 2026** — *Do customer-service agents check the receipt, and who do guardrails protect?*
- Planted one-field corruptions in real τ²-bench airline records and tested Claude Sonnet 5, Claude Opus 5.5 and
  Gemini 3.8 Flash: on the stock policy all three paid 100% of corrupted refunds and refused 100% of customers
  the record shortchanged (12 per cell; n=30 pending).
- "Recompute before deciding" cut bad payouts to 0–33% but still refused 75–83% of shortchanged customers; tying
  the check to the yes/no cut that to 17–42% (Opus 0%). Legitimate credits were held 83–100% until they carried an
  approval record plus a counting rule (Flash: 0% held, forgeries still caught; others pending). Shipped a
  deployment memo, integrity gate and data-quality scan [pending] for ≈$[pending, ~$65] of API spend.

**30 seconds.** Support agents apply policy to whatever the database says. I planted reservations whose own
payments contradict them, like "insured" with no insurance fee paid, and tested three frontier models. On the
stock policy none checked: every bad refund paid, every customer who had paid turned away. Telling them to
recompute fixed the company's side, not the customer's: they check before saying yes, not before saying no, the
same blind spot write-time guardrails have by design. Checking at the moment of answering fixed most of it. The
deliverable is a memo: which check to ship, who it protects, and what it costs per 1,000 conversations [pending].
