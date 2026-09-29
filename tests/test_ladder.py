"""The wording ladder: prompts, bases, parsing and the preregistered analysis."""

import pytest

from refundout import ladder, ladder_analysis, prompts, providers
from refundout.tau2 import Airline, due, paid


@pytest.fixture(scope="module")
def airline():
    try:
        return Airline.load()
    except FileNotFoundError:
        pytest.skip("τ² clone not present")


def test_scope_wordings_match_the_earlier_nudges(airline):
    assert ladder.policy(airline.policy, "SA", "cancel") == prompts.policy(airline.policy, prompts.Nudge.F1)
    assert ladder.policy(airline.policy, "SN", "cancel") == prompts.policy(airline.policy, prompts.Nudge.F1D)
    assert ladder.policy(airline.policy, "W3", "cancel") == prompts.policy(airline.policy, prompts.Nudge.F0)
    assert ladder.policy(airline.policy, "W0", "comp") == airline.policy


def test_w6_sa_sn_share_check_content():
    for w in ("W6", "SA", "SN"):
        assert ladder.WORDINGS[w][0] == prompts.CLAUSE and ladder.WORDINGS[w][1].endswith(ladder.CHECK)


def test_bases_exclude_quirks_and_are_distinct_users(airline):
    cancel, comp = ladder.cancel_bases(airline), ladder.comp_bases(airline)
    assert len(cancel) == 62 and not set(cancel) & ladder.QUIRKS
    users = [airline.db["reservations"][r]["user_id"] for r in comp]
    assert len(users) == len(set(users)) == 23
    for rid in comp:
        r = airline.db["reservations"][rid]
        assert airline.db["users"][r["user_id"]]["membership"] == "regular" and r["cabin"] != "business"
        assert ladder.cancelled_flight(airline, r) is not None


def test_cells_differ_only_in_flag_and_fee(airline):
    rid = ladder.comp_bases(airline)[0]
    items = {i.cell: i for i in ladder.items(airline, "comp", ["SA"], [rid], [rid])}
    assert set(items) == set("ABCD")
    assert items["A"].correct == "refuse" and items["B"].correct == "send_certificate"
    assert items["C"].correct == items["D"].correct == "transfer_to_human"
    base = ladder.uninsured(airline.db["reservations"][rid])
    assert due(base) == paid(base)
    assert len({i.request.system for i in items.values()}) == 1


def test_parse_accepts_fenced_json_and_rejects_other_actions():
    assert ladder.parse("comp", '```json\n{"action": "refuse", "message_to_customer": "no"}\n```')[0] == "refuse"
    assert ladder.parse("comp", '{"action": "cancel_with_refund", "message_to_customer": "x"}')[2]
    assert ladder.parse("cancel", "")[2] == "empty reply"


def test_prices_and_bounds():
    assert providers.price("gemma-4-31b-it") == ((0.0, 0.0), False)
    assert providers.price("some-new-model")[1] is True
    assert providers.cost("x", {"input_tokens": 1, "output_tokens": 1}, reported=0.5) == 0.5


def _rows(model, task, sa_d, sn_d, n=20, repeats=(0,)):
    rows = []
    for rep in repeats:
        for i in range(n):
            for w, refused in (("SA", i < sa_d), ("SN", i < sn_d)):
                rows.append({"model": model, "task": task, "wording": w, "cell": "D", "base": f"b{i}", "repeat": rep,
                             "action": "refuse" if refused else "transfer_to_human", "id": f"{task}:b{i}:D:{w}:{rep}"})
                rows.append({"model": model, "task": task, "wording": w, "cell": "C", "base": f"b{i}", "repeat": rep,
                             "action": "transfer_to_human", "id": f"{task}:b{i}:C:{w}:{rep}"})
    return rows


def test_analysis_verdicts():
    rows = []
    for m in ("gemini-3.8-flash", "gemma-4-31b-it", "openrouter/openai/gpt-6-sol"):
        for t in ("cancel", "comp"):
            rows += _rows(m, t, 16, 1, repeats=(0, 1))
    res = ladder_analysis.analyse(rows)
    assert res["robust"] and len(res["robust_models"]) == 3
    assert all(x["p_holm"] < 0.05 for x in res["primary"])
    # one model with no difference breaks it; Google-only never counts as ≥2 providers
    rows2 = [r for r in rows if r["model"] != "openrouter/openai/gpt-6-sol"] + _rows("gemini-3.1-pro-preview", "cancel", 16, 1) \
        + _rows("gemini-3.1-pro-preview", "comp", 16, 1)
    assert not ladder_analysis.analyse(rows2)["robust"]


def test_floor_is_not_testable():
    res = ladder_analysis.analyse(_rows("gemini-3.8-flash", "cancel", 1, 0))
    assert res["testable"]["gemini-3.8-flash|cancel"] is False


def test_missing_answers_are_not_refusals():
    rows = _rows("gemini-3.8-flash", "cancel", 10, 0)
    rows[0]["action"] = None
    table = ladder_analysis.cells(rows)
    cell = table[("gemini-3.8-flash", "cancel", "SA", "D")]
    assert cell["missing"] == 1 and cell["n"] == 19


def test_parse_takes_the_decision_object_among_several():
    text = '{"summary": "records conflict"}junk\n\n{"action":"transfer_to_human","message_to_customer":"HOLD ON."}'
    assert ladder.parse("comp", text)[0] == "transfer_to_human"
    two = '{"action":"refuse","message_to_customer":"a"} {"action":"transfer_to_human","message_to_customer":"b"}'
    assert ladder.parse("comp", two)[2]


def test_resumed_answer_replaces_earlier_failure(tmp_path):
    import json as _json
    for name, rec in (("a", {"reply": None, "error": "HTTP 429", "action": None}),
                      ("b", {"reply": {"text": '{"action":"refuse","message_to_customer":"x"}'}, "error": None})):
        d = tmp_path / name
        d.mkdir()
        (d / "run.json").write_text(_json.dumps({"config": {}}))
        base = {"model": "m", "id": "cancel:X:D:SA:0", "task": "cancel", "base": "X", "cell": "D", "wording": "SA",
                "repeat": 0}
        (d / "decisions.jsonl").write_text(_json.dumps({**base, **rec}) + "\n")
    rows = ladder_analysis.load([tmp_path / "a", tmp_path / "b"])
    assert len(rows) == 1 and rows[0]["action"] == "refuse"


def test_extra_task_does_not_change_criteria():
    rows = []
    for m in ("gemini-3.8-flash", "gemma-4-31b-it", "openrouter/openai/gpt-6-sol"):
        for t in ("cancel", "comp"):
            rows += _rows(m, t, 16, 1, repeats=(0, 1))
    rows.append({"model": "gemini-3.8-flash", "task": "plans", "wording": "SA", "cell": "G", "base": "b0", "repeat": 0,
                 "action": "refuse", "id": "plans:b0:G:SA:0"})
    assert ladder_analysis.analyse(rows)["robust"]
