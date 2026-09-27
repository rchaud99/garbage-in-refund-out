from lookworth.models import Request

from refundout.campaign import MAX_OUTPUT, HardBudget, bound


def test_budget_reserves_every_in_flight_call_at_bound():
    b = HardBudget(0.10, 0.04)
    assert b.allows(2) and not b.allows(3)
    b.spent = 0.03
    assert b.allows(1) and not b.allows(2)
    b.spent = 0.08
    assert not b.allows(1)


def test_bound_includes_utf8_schema_and_output():
    req = Request(system="policy", parts=("é" * 100,), json_schema={"type": "object"})
    assert bound(req) > MAX_OUTPUT * 3.75 / 1e6
    assert bound(req) > bound(
        Request(system="policy", parts=("a",), json_schema={"type": "object"})
    )


def test_campaign_failure_stops_further_calls_and_reserves_uncertain_cost(
    tmp_path, monkeypatch
):
    import json
    from types import SimpleNamespace

    from refundout import campaign

    calls = []

    class FailedModel:
        def __init__(self):
            self.settings = {}

        def respond(self, request):
            calls.append(request)
            raise RuntimeError("simulated unrecoverable API failure")

    monkeypatch.setattr(campaign, "ROOT", tmp_path)
    monkeypatch.setattr(campaign, "BoundedGemini", FailedModel)
    monkeypatch.setattr(campaign, "load_dotenv", lambda _: None)
    request = Request(system="test", parts=("test",), json_schema={"type": "object"})
    queue = [SimpleNamespace(request=request, key=str(i)) for i in range(5)]

    def record(i, reply, decision, error):
        return {"id": i.key, "error": error, "reply": None}

    path, stopped = campaign.execute(
        queue, {}, record, lambda *_: None, "fake-error", workers=1
    )
    records = list(map(json.loads, (path / "decisions.jsonl").read_text().splitlines()))
    assert len(calls) == len(records) == 1
    assert stopped.startswith("API error:")
    assert records[0]["uncertain_cost_reserve_usd"] == bound(request)
    assert campaign.prior_spend() == bound(request)
    assert json.loads((path / "run.json").read_text())["status"] == "stopped"
