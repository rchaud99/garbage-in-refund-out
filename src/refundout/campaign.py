"""Shared Gemini-only campaign guard. No retries; reserve a bounded response for failed calls."""

from __future__ import annotations

import json
import time
from dataclasses import asdict

from dotenv import load_dotenv
from lookworth.costs import Budget, cost
from lookworth.models import Reply
from lookworth.models.gemini import Gemini, _finish_reason, _join, _usage
from lookworth.runs import RunWriter

from refundout.run import ENV, ROOT

MODEL = "gemini-3.8-flash"
CAMPAIGN = "wording-power-2026-09-25"
MAX_OUTPUT = 8192


class BoundedGemini(Gemini):
    def __init__(self):
        super().__init__(name=MODEL, thinking_level="medium")
        self.settings = {
            **self.settings,
            "max_output_tokens": MAX_OUTPUT,
            "temperature": "provider default",
            "retries": 0,
        }

    def respond(self, request):
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=request.system,
            thinking_config=types.ThinkingConfig(
                thinking_level=self._thinking_level, include_thoughts=True
            ),
            max_output_tokens=MAX_OUTPUT,
            response_mime_type="application/json",
            response_json_schema=dict(request.json_schema),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )
        started = time.monotonic()
        response = self._client.models.generate_content(
            model=self.name,
            contents=[
                types.Content(role="user", parts=[self._part(p) for p in request.parts])
            ],
            config=config,
        )
        return Reply(
            text=_join(response, False),
            thoughts=_join(response, True) or None,
            usage=_usage(response.usage_metadata),
            latency_s=round(time.monotonic() - started, 3),
            model_version=response.model_version or self.name,
            finish_reason=_finish_reason(response),
            raw=response.model_dump(
                mode="json", exclude_none=True, exclude={"sdk_http_response", "parsed"}
            ),
        )


def prior_spend(campaign_id=CAMPAIGN):
    total = 0.0
    for p in (ROOT / "runs").glob("*/run.json"):
        meta = json.loads(p.read_text())
        if meta["config"].get("campaign") != campaign_id or meta["config"].get(
            "dry_run"
        ):
            continue
        f = p.parent / "decisions.jsonl"
        if f.exists():
            total += sum(
                (r.get("cost_usd") or 0) + (r.get("uncertain_cost_reserve_usd") or 0)
                for r in map(json.loads, f.read_text().splitlines())
            )
    return total


def bound(request):
    # UTF-8 bytes dominate text token count; extra 4096 covers schema/message framing.
    tokens = (
        len(
            (
                request.system
                + "".join(request.parts)
                + json.dumps(request.json_schema)
            ).encode()
        )
        + 4096
    )
    return cost(
        MODEL,
        {"input_tokens": tokens, "output_tokens": MAX_OUTPUT, "reasoning_tokens": 0},
    )


class HardBudget(Budget):
    def __init__(self, limit, maximum):
        super().__init__(MODEL, limit)
        self.maximum = maximum

    def allows(self, calls):
        return self.spent + calls * self.maximum <= self.limit


def execute(
    queue,
    config,
    record_result,
    parse,
    name,
    max_dollars=50,
    workers=8,
    *,
    campaign_id=CAMPAIGN,
    campaign_cap=50,
):
    """One campaign lock; bounded concurrent requests, stop submissions on any API failure."""
    import fcntl
    from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

    (ROOT / "work").mkdir(exist_ok=True)
    lock = open(ROOT / "work" / "campaign.lock", "w")  # noqa: SIM115 - held for the whole campaign run
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    prior = prior_spend(campaign_id)
    budget = HardBudget(
        min(max_dollars, campaign_cap) - prior,
        max((bound(i.request) for i in queue), default=0),
    )
    if budget.limit <= 0:
        raise RuntimeError("Campaign budget exhausted")
    load_dotenv(ENV)
    model = BoundedGemini()
    config = {
        **config,
        "campaign": campaign_id,
        "prior_campaign_spend_usd": prior,
        "max_dollars": min(max_dollars, campaign_cap),
        "model": {"name": MODEL, **model.settings},
        "maximum_reserved_per_call": budget.maximum,
        "planned_calls": len(queue),
    }
    stopped = None
    with RunWriter(ROOT / "runs", name, config) as run:
        print("RUN", run.dir, flush=True)

        def call(item):
            try:
                return item, model.respond(item.request), None
            except Exception as e:  # noqa: BLE001 - every API failure is saved and stops submission
                return item, None, f"{type(e).__name__}: {e}"

        pending = iter(queue)
        exhausted = False
        running = set()
        count = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            while True:
                while (
                    not stopped
                    and not exhausted
                    and len(running) < workers
                    and budget.allows(len(running) + 1)
                ):
                    item = next(pending, None)
                    if item is None:
                        exhausted = True
                        break
                    running.add(pool.submit(call, item))
                if not running:
                    if not exhausted and not stopped:
                        stopped = budget.stop()
                    break
                done, running = wait(running, return_when=FIRST_COMPLETED)
                for future in done:
                    item, reply, error = future.result()
                    decision = parse(item, reply.text) if reply else None
                    record = record_result(item, reply, decision, error)
                    record.update(
                        model={"name": MODEL, **model.settings},
                        cost_usd=cost(MODEL, asdict(reply.usage)) if reply else None,
                        uncertain_cost_reserve_usd=budget.maximum if error else 0,
                        prompt={
                            "system": item.request.system,
                            "user": list(item.request.parts),
                        },
                    )
                    if reply:
                        budget.pay(asdict(reply.usage))
                    else:
                        budget.spent += budget.maximum
                        stopped = "API error: " + error
                    run.record("decisions", record)
                    if reply and reply.raw:
                        run.record("raw", {"id": record["id"], "response": reply.raw})
                    count += 1
                    if count % 24 == 0 or error:
                        print(
                            f"{count}/{len(queue)} campaign ${prior + budget.spent:.4f} {error or ''}",
                            flush=True,
                        )
        run.finish(
            "stopped" if stopped else "complete",
            {
                "cost_usd": budget.spent,
                "campaign_total_usd": prior + budget.spent,
                "stopped": stopped,
                "records": count,
            },
        )
        print("FINISHED", run.dir, stopped, prior + budget.spent, flush=True)
    lock.close()
    return run.dir, stopped
