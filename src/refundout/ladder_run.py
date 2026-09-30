"""Run the wording ladder / scope replication for one model: estimate, pilot, or a frozen stage.

    uv run python -m refundout.ladder_run --model gemini-3.8-flash --tasks cancel comp --wordings SA SN \
        --corrupt 8 --clean 2 --pilot --max-dollars 1              # pilot: not preregistered, labelled as such
    uv run python -m refundout.ladder_run --stage flash-ladder --model gemini-3.8-flash ... --estimate
    uv run python -m refundout.ladder_run --stage flash-ladder --model gemini-3.8-flash ... --max-dollars 8

A non-pilot stage refuses to run unless `preregistration/LADDER_PREREGISTRATION.md` exists and the exact queue's manifest hash was
written by `--estimate` into reports/ladder-plans/<stage>.json first. Every call is recorded, failures included; a
failed call is missing data, never a refusal. Spend across the whole campaign is capped (CAMPAIGN_CAP).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import asdict

from dotenv import load_dotenv
from lookworth.models import TransientError, respond_with_retries
from lookworth.runs import RunWriter

from refundout import ladder, providers
from refundout.run import ENV, ROOT
from refundout.tau2 import Airline

CAMPAIGN = "ladder-2026-09-28"
CAMPAIGN_CAP = 40.0
"""Hard cap in dollars across every run in this campaign (all models), including pilots and failed-call reserves."""
PREREG = ROOT / "preregistration" / "LADDER_PREREGISTRATION.md"
PLANS = ROOT / "reports" / "ladder-plans"
LOCAL_ENV = ROOT / ".env"
"""Optional project-local keys (e.g. OPENROUTER_API_KEY); loaded after lookworth's .env, never overriding it."""


def unbilled(error: str | None) -> bool:
    """A request the provider rejected with a 4xx (quota, rate limit, no credit, bad request) is never billed."""
    return bool(error) and re.search(r"(HTTP|Error code:|OpenRouter error) 4\d\d", error) is not None


def campaign_spend() -> float:
    total = 0.0
    for meta_path in (ROOT / "runs").glob("*/run.json"):
        meta = json.loads(meta_path.read_text())
        if meta["config"].get("campaign") != CAMPAIGN:
            continue
        f = meta_path.parent / "decisions.jsonl"
        if f.exists():
            for line in f.read_text().splitlines():
                r = json.loads(line)
                total += (r.get("cost_usd") or 0) + (0 if unbilled(r.get("error")) else (r.get("reserve_usd") or 0))
    return total


def build(args, airline):
    queue = []
    for task in args.tasks:
        bases = ladder.comp_bases(airline) if task == "comp" else ladder.cancel_bases(airline)
        corrupt = bases[: args.corrupt] if args.corrupt else bases
        clean = bases[: args.clean]
        queue += ladder.items(airline, task, args.wordings, corrupt, clean, args.repeats, args.corrupt_cells,
                              args.clean_cells)
    return ladder.interleave(queue, args.seed)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--stage", default=None)
    p.add_argument("--model", required=True)
    p.add_argument("--tasks", nargs="+", default=["cancel"], choices=["cancel", "comp", "plans"])
    p.add_argument("--wordings", nargs="+", default=list(ladder.LADDER), choices=list(ladder.WORDINGS))
    p.add_argument("--corrupt", type=int, default=0, help="first N bases per task get C and D (0 = all)")
    p.add_argument("--clean", type=int, default=20, help="first N bases per task also get A and B")
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--corrupt-cells", default="CD", help="which corrupted cells (C D E F G H) the corrupt bases get")
    p.add_argument("--clean-cells", default="AB", help="which clean cells (A B K) the clean bases get")
    p.add_argument("--seed", type=int, default=20260928)
    p.add_argument("--max-dollars", type=float, required=False, default=0)
    p.add_argument("--estimate-per-call", type=float, default=None,
                   help="typical $/call from the pilot; the run stops if tracking above 1.5× this")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--pace", type=float, default=0.0, help="minimum seconds between call starts (rate-limited APIs)")
    p.add_argument("--pilot", action="store_true")
    p.add_argument("--resume", nargs="*", default=[],
                   help="earlier (stopped) run folders of this stage: items they answered are not asked again")
    p.add_argument("--estimate", action="store_true")
    a = p.parse_args(argv)

    airline = Airline.load()
    queue = build(a, airline)
    rows, digest = ladder.manifest(queue)
    bound = max(providers.bound(a.model, i.request) for i in queue)
    manifest_rows = rows
    prior = campaign_spend()
    typical = a.estimate_per_call
    print(f"{len(queue)} calls for {a.model}; worst-case reserve ${bound:.4f}/call; campaign spend so far ${prior:.4f}")
    if typical:
        print(f"typical estimate ${typical * len(queue):.2f}; stop threshold 1.5× = ${1.5 * typical * len(queue):.2f}")
    config = {"experiment": "wording_ladder", "campaign": CAMPAIGN, "stage": a.stage, "pilot": a.pilot,
              "design": {k: v for k, v in vars(a).items() if k not in ("estimate",)},
              "wording_lines": {w: list(ladder.WORDINGS[w]) for w in a.wordings},
              "manifest_sha256": digest, "tau2_commit": airline.commit, "single_decision_replay": True}
    if a.estimate:
        if not a.stage:
            raise SystemExit("--estimate needs --stage")
        PLANS.mkdir(parents=True, exist_ok=True)
        (PLANS / f"{a.stage}.json").write_text(json.dumps({**config, "items": rows}, indent=1))
        print("plan written", PLANS / f"{a.stage}.json", digest)
        return None
    if not a.pilot:
        plan = PLANS / f"{a.stage}.json"
        if not plan.exists() or json.loads(plan.read_text())["manifest_sha256"] != digest:
            raise SystemExit("estimate this exact stage first (manifest hash mismatch)")
        if not PREREG.exists():
            raise SystemExit("write preregistration/LADDER_PREREGISTRATION.md before a non-pilot stage")
        config["preregistration_sha256"] = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    done_ids = set()
    for d in a.resume:
        meta = json.loads((ROOT / d / "run.json").read_text() if not d.startswith("/") else open(d + "/run.json").read())
        if meta["config"].get("manifest_sha256") != digest:
            raise SystemExit(f"{d} is not this stage")
        path = (ROOT / d if not d.startswith("/") else __import__("pathlib").Path(d)) / "decisions.jsonl"
        done_ids |= {r["id"] for r in map(json.loads, path.read_text().splitlines()) if r.get("reply")}
    if done_ids:
        queue = [i for i in queue if i.key not in done_ids]
        config["resumes"] = a.resume
        print(f"resuming: {len(done_ids)} answered earlier, {len(queue)} to ask")
    limit = min(a.max_dollars, CAMPAIGN_CAP - prior)
    if limit <= 0:
        raise SystemExit(f"no budget: stage cap ${a.max_dollars}, campaign left ${CAMPAIGN_CAP - prior:.2f}")

    load_dotenv(ENV)
    load_dotenv(LOCAL_ENV)
    model = providers.load(a.model)
    config.update(model={"name": model.name, **model.settings}, limit_usd=limit, prior_campaign_usd=prior,
                  reserve_per_call_usd=bound, planned_calls=len(queue))
    name = f"{'pilot' if a.pilot else 'ladder'}-{a.stage or 'adhoc'}-{a.model.replace('/', '_')}"

    spent, count, stopped, streak = 0.0, 0, None, 0
    with RunWriter(ROOT / "runs", name, config) as run:
        print("RUN", run.dir, flush=True)
        prompts_seen = {}
        for i in queue:
            prompts_seen.setdefault(f"system:{i.task}:{i.wording}", i.request.system)
            prompts_seen.setdefault(f"transcript:{i.task}:{i.base}:{i.cell}", i.request.parts[0])
        (run.dir / "prompts.json").write_text(json.dumps(prompts_seen, indent=1))

        import threading
        import time

        gate = threading.Lock()
        last = [0.0]

        def call(item):
            if a.pace:
                with gate:
                    wait_s = last[0] + a.pace - time.monotonic()
                    if wait_s > 0:
                        time.sleep(wait_s)
                    last[0] = time.monotonic()
            try:
                reply, retries = respond_with_retries(model, item.request, attempts=4 if a.pace else 3,
                                                     first_delay_s=30 if a.pace else 4)
                return item, reply, retries, None, False
            except Exception as e:  # noqa: BLE001 - saved as missing data
                return item, None, [], f"{type(e).__name__}: {e}", not isinstance(e, TransientError)

        pending, running = iter(queue), set()
        exhausted = False
        with ThreadPoolExecutor(a.workers) as pool:
            while True:
                while (not stopped and not exhausted and len(running) < a.workers
                       and spent + (len(running) + 1) * bound <= limit):
                    item = next(pending, None)
                    if item is None:
                        exhausted = True
                        break
                    running.add(pool.submit(call, item))
                if not running:
                    if not exhausted and not stopped:
                        stopped = f"budget: ${spent:.4f} spent of ${limit:.2f}"
                    break
                done, running = wait(running, return_when=FIRST_COMPLETED)
                for fut in done:
                    item, reply, retries, error, fatal = fut.result()
                    action, message, bad = ladder.parse(item.task, reply.text) if reply else (None, None, None)
                    usage = asdict(reply.usage) if reply else None
                    c = providers.cost(a.model, usage, providers.reported_cost(reply)) if reply else None
                    # A rejected request (HTTP 429 quota/rate limit, 4xx) is never billed; anything else that failed
                    # (timeouts, 5xx) may have been, so it consumes a worst-case reserve.
                    rejected = unbilled(error)
                    reserve = 0 if reply or rejected else bound
                    spent += c if c is not None else reserve
                    rec = {"id": item.key, "task": item.task, "base": item.base, "cell": item.cell,
                           "wording": item.wording, "repeat": item.repeat, "correct_action": item.correct,
                           "action": action, "message": message, "parse_error": bad, "error": error,
                           "retries": retries, "cost_usd": c, "reserve_usd": reserve,
                           "model": model.name,
                           "prompt_sha256": hashlib.sha256((item.request.system + item.request.parts[0]).encode()
                                                           ).hexdigest(),
                           "reply": reply.to_record() if reply else None}
                    run.record("decisions", rec)
                    count += 1
                    streak = streak + 1 if error else 0
                    if error and not stopped and (fatal or streak >= 5):
                        stopped = f"API error: {error[:300]}"
                    if typical and count >= 50 and spent > 1.5 * typical * count:
                        stopped = stopped or f"tracking above 1.5× estimate: ${spent:.3f} after {count} calls"
                    if count % 50 == 0 or error:
                        print(f"{count}/{len(queue)} ${spent:.4f} {error or ''}", flush=True)
        status = "stopped" if stopped else "complete"
        run.finish(status, {"cost_usd": spent, "records": count, "planned": len(queue), "stopped": stopped,
                            "campaign_total_usd": prior + spent})
        print("FINISHED", run.dir, status, stopped, f"${spent:.4f}", flush=True)
    return run.dir


if __name__ == "__main__":
    main()
