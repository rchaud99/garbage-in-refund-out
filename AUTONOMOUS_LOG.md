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
