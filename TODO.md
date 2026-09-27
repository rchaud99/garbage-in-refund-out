# TODO

Written 2026-09-24. Findings so far: `FINDINGS.md` (headline findings at the top); paper: `paper/main.pdf`. API spend
so far: $37.01 for single decisions, plus the conversation run below.

## 1. Full τ² conversations — DONE 2026-09-24 ($6.41; FINDINGS.md, last section)

Remaining: add a "Full conversations" subsection and table to the paper.

### Original notes

Validates the single-decision results when the agent runs the whole conversation and chooses its own lookups.
`scripts/run_episodes.py`: τ²'s own orchestrator, LLMAgent and user simulator (Flash as the fixed customer), the
same 8 bases as the single-decision gate, cells C and D, nudges stock (F0nc), checklist (F1) and decision-time (F1d),
Flash and Sonnet: 96 conversations, capped at $25. Run folder: `runs/2026-09-24_*_episodes-8-bases-flash+sonnet/`
(`episodes.jsonl` has every transcript; `summary.md` the table). Pilot: `runs/2026-09-24_181940_episodes-1-bases-flash`.

- [ ] Check the run finished (`run.json` status) and read `summary.md`.
- [ ] Hand-read the transcripts, especially D under F1: did the agent refuse without adding up the payments, as in
      the single decisions (Flash 83%, Sonnet 75% refused)? Check the outcome labels (not_cancelled = refused or no
      action; read the last agent message).
- [ ] Compare with the single-decision rates per cell (paired by base) and write a FINDINGS section.
- [ ] Add a short "Full conversations" subsection and table to the paper; soften the limitation it answers.

Command (from the repo root):

```sh
PYTHONPATH=vendor/tau2-bench/src uv run --with litellm --with pandas --with loguru --with pyyaml --with rich \
  --with addict --with deepdiff --with toml --with tenacity --with fastapi --with docstring-parser --with psutil \
  --with jinja2 python scripts/run_episodes.py --models flash sonnet --bases 8 --max-dollars 25
```

## 2. Test our own recommendation: the reconciliation as a tool (~$3)

The paper recommends computing the reconciliation in a tool and handing the agent the result, but there is no data
for it yet.

- [ ] Add a read-only tool `check_reservation_ledger(reservation_id)` (deterministic: expected = fares × passengers +
      fee if insured + bags; returns expected, paid, and "mismatch: insurance fee missing / paid but not flagged" or
      "consistent"; an adjustment-aware version adds back approved credits).
- [ ] Show its call and result in the transcript (like the provenance design's lookup), cells C, D, benign, A, B;
      nudges F0nc and F0; all three models; 12 bases.
- [ ] Question: handed the mismatch, do agents still refuse D customers? ~0% refusals makes the memo's main line
      ("move the check out of the prompt into a tool"); continued refusals would mean agents ignore evidence that
      points against a no, which is an even stronger finding.
- [ ] Same code as a deterministic write gate and a nightly scan over all 2,000 reservations ($0): strict vs
      adjustment-aware, catch rates by construction, plus the real τ² quirks it flags (PHX→PHX one-way records).

## 3. Scale up (only if the conversations agree with the single decisions)

- [ ] 30 bases on the headline cells: airline C and D × F1 and F1d, Flash and Sonnet (`--bases 30`; the base draw is
      prefix-stable). ~$15. Tightens intervals from about ±25 to ±15 points.

## 4. Finish Muscle Memory for frontier models (~$5)

The $35-fee check showed agents compute with the policy's number (0/36 false holds). A fee is arbitrary; memory
should pull hardest on a rule people already know.

- [ ] Single decisions with edited rules in both directions: the 24 h free-cancellation window (to 12 h and 48 h),
      the $100 certificate (to $75 and $150), one deleted rule and one added rule. Scenarios where the edited and
      original rules give different answers. Flash, Sonnet, Opus.

## 5. Packaging ($0)

- [ ] `git init`, `.gitignore` (vendor/, .env), first commit.
- [ ] README led by `paper/fig_airline.pdf` (as PNG) and the four headline findings.
- [ ] One-page deployment memo: which check to ship, who it protects, cost per 1,000 conversations (from the
      conversation run's per-episode cost).
- [ ] Publish the paper (private artifact link for the résumé).
- [ ] Rotate both API keys (they were pasted in chat); they live in `../how_much_is_a_look_worth/.env`.

## Skipped on purpose

More corruption families (fare, bags, borrowed order, cancelled-not-refunded): variations, not new findings; ideas in
`PERTURBATIONS.md`. Customer pushback in D: predictable and confounds caving with checking. Blind second-model
reviewer (H5) and post-block hand-off (H6): real, but need more machinery; future work.

## Next project: Stale Weights (fine-tuning)

Does an agent fine-tuned on one policy follow a different policy in its prompt? Runs locally on the M4 Max (128 GB)
with MLX LoRA; ~$0 of API.

- Grid: base model, fine-tuned on A, fine-tuned on B (the symmetric control for the effect of fine-tuning itself) ×
  policy A, B or a new C in the prompt. Reversion = answering by the trained policy instead of the prompted one.
- A and B differ on several rules pointing different ways (a fee, a time window, a permission, a compensation
  amount); C has a third value; none equals τ²'s original (measure pull toward τ² separately).
- Test items: single decisions where A, B and C each give a different correct answer, reusing this harness.
- Training data generated by code from the rules (no label noise, $0).
- Factors: policy text present or absent in the training prompts; dose (200 / 1,000 / 5,000 examples); full policy
  vs retrieved rule (RAG) in the prompt; 2–3 open models (~4B, ~8B, ~30B).
- Gates first: (1) the base model follows A, B and C in context; (2) the A-tuned model follows A with no policy in
  the prompt (≥ 90%).
- Predictions: reversion rises with dose and falls with size; numbers revert more than familiar norms; a stale "no"
  sticks more than a stale "yes".
- Open decisions: open models only, or also one API model that allows fine-tuning; its own repo (recommended).

## Handoff 2026-09-25 (stopped for Claude Code usage limits)

Wording study. First pass is done and analysed ($17.11): F1 vs F1d on 48 new bases (--skip 12) replicates the refusal
leak (Flash D 54→10%, Sonnet 77→44%, CIs exclude 0). The mirror F1n doesn't raise C payouts. F1dp ("any answer")
leaks more than F1d (Sonnet +21 [+4,+38], Flash +15 [0,+29], tentative). Opus is 0% everywhere. Retail first pass was
confounded (one-way rule).

The follow-up round (5 experiments) was STOPPED mid-run. These run folders may be partial; analyse them with
`uv run python -m refundout.contrasts runs/<dir>` and check run.json status:
- runs/2026-09-25_153920_gate-48-bases-skip-60-cells-CD-* (1. name-the-no, second 48 bases)
- runs/2026-09-25_154341_gate-24-bases-skip-108-cells-ABCD-* (2. compute-in-code?)
- runs/2026-09-25_154345_cancel-36-12-orders-two-way-* (3. retail two-way)
- runs/2026-09-25_154622_queued-48-bases-skip-12-* (4. inverted "queued cancellation")
- runs/2026-09-25_154628_gate-48-bases-skip-12-cells-ABCD-* (?)
- runs/2026-09-25_1543*/1545* episodes-30-bases-skip-12-sonnet-F1-F1d (5. conversations; likely stopped on Anthropic credit)

Anthropic API credit is ~$5 (card blocked). Gemini is fine.

Next, Gemini-only power study (cap $50): 3 action-tied vs 3 answer-tied paraphrases × tasks (airline insurance
cancel, retail cancel two-way, plus 1–2 new record-check decisions) × 150–200 bases × 2 runs. Fit a mixed-effects
model (random effects: base, paraphrase, task). Pre-registered claim: action-tied wordings leave more wrongful
refusals than answer-tied ones.

## Codex continuation 2026-09-25

- Audited all seven interrupted folders without rewriting original evidence.
- Completed only the five Gemini single-decision parts (250 missing calls, $1.457943).
- No Claude calls. Original conversation errors were Gemini simulator DNS/connection failures.
- Prospective Flash design frozen in PREREGISTRATION.md; 3,672 planned calls, six wordings, three tasks.
- Primary analyses, compact decisions and review sample live in reports/. Raw runs remain local.
- Existing prompt files are unchanged; new prompt definitions live in power.py.
- See the latest FINDINGS sections and reports/power-results.md for final status and decision rule.

## Final arithmetic follow-up (2026-09-25)

- Complete: 600/600 valid Flash decisions, $4.0733895 under separate $8 cap.
- 21 real multi-item orders in paired synthetic gift-card balance scenarios; no arithmetic-only status corruption is possible.
- Refusals 0/126 under each wording type; effort-pattern rule failed. Original generality rule remains failed.
- Zero wrongful refusals available for review; read ten transfers, all with explicit numeric reconciliation.
- Updated four-task table/figure, README, findings, memo and paper. No Claude calls; original prompts unchanged.
- Git metadata left untouched at user request; first commit is for the user to perform.
