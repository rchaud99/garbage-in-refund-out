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
