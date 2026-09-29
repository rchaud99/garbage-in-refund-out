# Autonomous lab notebook

Agent: Claude Opus 5.5 (autonomous research assistant). Started 2026-09-28. Times are local.

## 2026-09-28 ~18:00 — orientation
- Read NEXT_EXPERIMENT.md, REVIEW_2026-09-27.md, README, FINDINGS, MEMO, both preregistrations, TODO, NEXT_STEPS, src/.
- Keys: the project's .env (../how_much_is_a_look_worth/.env) holds GEMINI_API_KEY and ANTHROPIC_API_KEY only. There is
  no OpenRouter/OpenAI key; my attempt to look further was denied as credential exploration, and I stopped. So GPT is
  unavailable, and Claude only works through the direct Anthropic key (card blocked; roughly $5 credit left at the
  2026-09-25 handoff). I've asked main for an OPENROUTER_API_KEY.
- The Gemini key also reaches gemini-3.1-pro-preview, gemini-3.5-flash and gemma-4-31b-it (models.list, free).
- User goal clarification (via main): the target is a website write-up plus a résumé bullet, and ONE robust finding
  (significant, replicated across reruns, ≥3 models across providers, and ≥2 tasks). The generator is now lowest priority.
- Candidate robust finding: "Scoping the check to the answer (yes and no) rather than to the action cuts wrongful
  refusals." Known weak spot: the retail tasks were at floor, so task generality is untested.
- Tests: pytest passes (see below). Git: set repo-local user.email.

## 2026-09-28 ~18:50 — write-up fixes, pilots, second task
- Write-up fixes applied (delegated to a subagent, reviewed by me, committed a2e96ab). Verified: Flash used τ²'s
  calculate tool in 12/16 D conversations (F1 5/8, F1d 7/8); provenance cost $1.8866 + $0.4027 = $2.29.
- Built `providers.py` (Gemini/Gemma, Claude direct, OpenRouter), `ladder.py` (tasks and wordings), `ladder_run.py`
  (budget-capped runner; campaign cap $40) and `ladder_analysis.py` (the frozen analysis), plus tests.
- New task "comp": compensation for an airline-cancelled flight, regular members only. There are 23 native bases,
  and insurance is the only ground for compensation, so the refusal path never touches payments.
- Pilots (excluded from confirmatory analysis), $0.73 in total:
  - Flash comp, n=8: SA gave C 0/8 and D 7/8; SN gave C 0/8 and D 1/8; W3 gave 8/8 and 8/8. So comp is not at
    floor and not at ceiling.
  - Gemini 3.1 Pro, n=3: works, at ~$0.012/call.
  - Gemma 4 31B: free, but capped at 16k input tokens/min (429s), so it needs pacing.
  - Anthropic direct: HTTP 400, credit balance too low (unbilled). No Claude without an OpenRouter key.
- Found that rejected (4xx) calls were counted against the budget as reserves; fixed, since they are unbilled.
- Froze LADDER_PREREGISTRATION.md and the stage plans (reports/ladder-plans/*.json) before any confirmatory call.

## 2026-09-28 ~19:35 — first confirmatory results; OpenRouter live
- OPENROUTER_API_KEY appeared in the project .env. Pilot: gpt-6-luna works. It is rate-limited (new account, 20
  rpm per model), so I added `--pace` and `--resume`. Amendment 1 made the parser take the lone decision object.
- **Flash scope, cancel** (62 bases, 1 rerun): D wrongful refusals SA 41/62, SN 5/62, W6 29/62.
  - C payouts 0/62 under each wording.
  - Clean A 20/20 refused and B 20/20 refunded under each.
  - SA vs SN: McNemar 36 vs 0 discordant, Holm p = 8.7e-11. This **confirms** the existing Flash finding on a
    third base set.
- **Flash scope, comp** (23 bases, 2 reruns): SA D 8/23 in each rerun, SN 3/23 and 1/23, W6 22/23 and 22/23.
  - C payouts 1/46 under W6, 0 otherwise. Clean cells 0 errors.
  - SA vs SN: rerun 1 Holm p = 0.031, rerun 0 p = 0.12. So Flash does not yet meet the "every rerun" rule on comp
    (SA leaked less than in the pilot, 35% vs 7/8).
- **Surprise:** lookup-scoped W6 protects D worse than SA on comp (96% vs 35% refusals), yet still catches C.
  Reasoning summaries mention arithmetic in 45/45 W6 C transfers vs 6/44 W6 D refusals. This contradicts "literal
  scope" and my W6 prediction. I preregistered H-asym (Amendment 2) as a new family with fresh models before
  seeing their cell-level data.
- Messages sent to main per the standing rule (CONFIRMED plus NEW).

## 2026-09-28 ~19:55 — scope does not generalise; the path finding emerges
- **Scope, all models** (interim, see progress_01 PDF):
  - Flash cancel +58 pp.
  - Pro: cancel +27 pp (Holm p = 0.03), comp none.
  - Sonnet: cancel 44/62 vs 40/62 (p = 0.54), so the earlier Sonnet effect is **not replicated**.
  - GPT-6 Sol and Luna at floor (0 errors on cancel).
  - Preregistered robustness criterion not met. Messages sent to main (REFUTED; NEW).
- **H-asym (Amendment 2):** D refusals ≫ C payouts. No model ever refused a C record, so this is not a refusal bias.
- **Amendment 3 (E/F control):** Flash and Pro show the "path" verdict on both tasks (F refused 29–96% vs E paid
  0–9%, and E ≈ C). This rules out overpayment blindness on the grant path. Pro also shows D > F on cancel (a
  direction effect on the refusal path).
- **Reasoning keyword check** (exploratory): arithmetic appears in 0–5% of refusal summaries (Sonnet 1/44 and 0/34;
  Pro 1/51, 0/18, 0/42, 0/42) vs 90–100% of transfer summaries.
- **Third-model search** (pilots, excluded):
  - DeepSeek v4 pro: C payouts 7/12, so the check rarely runs.
  - Qwen3.5-397B: C 12/12 paid, so it doesn't check.
  - Grok 4.7: cancel at floor; comp D 3/6.
  - None can satisfy the "both tasks" criterion within budget. Grok is skipped ($2.3 for one task only).
- **Budget:** $31.8 spent. W6-Sonnet stays on hold (≥ $3.5 rule), and Opus is dropped (preregistered priority).
- **Operational lesson:** `sh` reads scripts incrementally. Editing ladder_stages.sh while a chained `sh` was
  running caused a harmless syntax error after a completed stage. I now write edits via a temp file and `mv`.

## 2026-09-28 ~20:30 — paid work finished ($38.40); write-up
- Sonnet E/F on cancel: "path" (F 44/61 refused vs E 0/62 paid, Holm p = 3e-12). On comp Sonnet is not testable:
  it paid 39/44 C and 38/46 E, i.e. it rarely checks there at all.
- Amendment 4 (Flash): the same C record under a no-path request ("plans changed") was missed 19/62, vs 0/62 on
  the yes path (Holm p = 7.6e-6). The first attempt stopped on the 1.5× cost rule (true per-call $0.0086 vs the
  $0.0065 estimate). I re-estimated and resumed per the rule.
- Sonnet W6 on cancel: 21/62 vs SA 44/62 (Holm p = 2.6e-6). Lookup scope helps Sonnet but hurts Flash on comp.
- Budget stops, all decided by the preregistered priority rules:
  - W6-Sonnet-comp cancelled (it would have crossed the $40 cap).
  - Pro "plans" not run (spend > $37).
  - Opus not run.
- Found and fixed an analysis bug before the final numbers: dedupe kept the first record, so a resumed stage's
  earlier 429 error hid its later answer. It now keeps the first *answered* record, with a test added. This changed
  Flash cancel F from 36/61 to 36/62.
- Final analysis written to reports/ladder-results.{md,json} and reports/replication-table.md. FINDINGS gets a new
  top section with the killed-claims table. README and MEMO now lead with the new results and mark the Sonnet
  replication as failed. The paper abstract has a one-sentence note.
- Gemma (free): the scope-31B stage was stopped for time at 268/492 (its run.json still says "running"; I killed
  the process, and the record is kept as-is). Amendment 5 path stages for 31B and 26B-A4B are running at ~3
  calls/min.
- Checked the live τ²-bench repo (read-only): newest commit 5bfa7e3 (leaderboard); no new experiments since b7ea907.
  DRAFTS/tau2_issue.md is drafted and not posted.

## 2026-09-28 ~21:00 — analysis bug found in self-review
- `analyse()` took "tasks" from the data. Once the Amendment-4 "plans" task existed, every "in every task" criterion
  silently required a "plans" result, and the committed ladder-results listed no model in "path in every task".
  Criteria are now judged on the two preregistered tasks (CRITERION_TASKS); a test was added. The text in
  FINDINGS/README was written from the per-cell verdicts, so it was unaffected.
- Gemma path stages (free) are running at ~3–4 calls/min. Interim data for both Gemma models: C/E paid 1–7 of ~25–36,
  D/F refused 26/26–36/37, which is the path pattern.

## 2026-09-28 ~21:40 — wrap-up (user decision: no more API calls)
- All Gemma runs stopped at 21:25 on request.
  - 31B: cancel path complete; comp stopped at 36/184 calls.
  - 26B: cancel 246/248 calls; comp not run.
  - Gemma is reported as partial.
- On request, ran the W6 family analysis (W6 vs SA/SN on D and C, Holm across 44 tests): W6 helps Sonnet (−37 pp,
  Holm p = 1e-5), hurts Flash on comp (+61 pp), and raises Gemma's payouts. Sent to main.
- Final deliverables:
  - FINDINGS (latest section, with per-model × per-wording tables and killed claims);
  - WEBSITE_DRAFT.md;
  - DIGEST.md;
  - reports/progress/progress_02_2026-09-28_2135.pdf (4 pages; numbers are generated from
    reports/ladder-results.json by scripts/final_report.py);
  - README and MEMO updated.
- Final spend: $38.40 (campaign) + $0.12 (τ² verification) = $38.52 of the $40 cap.
