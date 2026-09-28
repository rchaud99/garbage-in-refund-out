"""Smoke tests: generation is deterministic, cells differ only where they should, gold answers follow the clause."""

import json
import os
from pathlib import Path

import pytest

from tau2_integrity import generate, score
from tau2_integrity.corruptions import SPECS, due, paid

TAU2 = Path(os.environ.get("TAU2_BENCH", Path(__file__).resolve().parents[2] / "vendor" / "tau2-bench"))
pytestmark = pytest.mark.skipif(not (TAU2 / "data").exists(), reason="set TAU2_BENCH to a τ²-bench clone")


@pytest.mark.parametrize("scenario", ["cancel_sick", "comp_cancelled_flight"])
def test_cells_and_gold(scenario):
    tasks, policy, bases = generate.generate(TAU2, scenario, "airline_insurance_fee", 3)
    assert len(tasks) == 12 and len(bases) == 3
    assert generate.CLAUSE in policy
    by = {t["id"].rsplit("-", 1)[-1]: t for t in tasks if bases[0] in t["id"]}
    recs = {c: t["initial_state"]["initialization_data"]["agent_data"]["reservations"][bases[0]] for c, t in by.items()}
    assert [due(recs[c]) == paid(recs[c]) for c in "ABCD"] == [True, True, False, False]
    assert {c: r["insurance"] for c, r in recs.items()} == {"A": "no", "B": "yes", "C": "yes", "D": "no"}
    for c in "CD":
        assert by[c]["evaluation_criteria"]["actions"][0]["name"] == "transfer_to_human_agents"
        assert by[c]["evaluation_criteria"]["reward_basis"] == ["DB", "ACTION"]
    assert by["A"]["evaluation_criteria"]["actions"] == []
    assert by["B"]["evaluation_criteria"]["actions"][0]["name"] in ("cancel_reservation", "send_certificate")
    assert tasks == generate.generate(TAU2, scenario, "airline_insurance_fee", 3)[0]


def test_tasks_validate_against_tau2():
    pytest.importorskip("tau2")
    tasks, _, _ = generate.generate(TAU2, "cancel_sick", "airline_insurance_fee", 2)
    generate.validate(tasks)


def test_corruption_misses_by_exactly_the_fee():
    db = json.loads((TAU2 / "data/tau2/domains/airline/db.json").read_text())
    r = next(v for v in db["reservations"].values() if v["insurance"] == "no" and due(v) == paid(v))
    spec = SPECS["airline_insurance_fee"]
    fee = 30 * len(r["passengers"])
    assert paid(spec.cell(r, "D")) - due(spec.cell(r, "D")) == fee
    assert due(spec.cell(r, "C")) - paid(spec.cell(r, "C")) == fee


def test_score_outcomes_and_pass_k():
    sims = [{"task_id": "x-D", "reward_info": {"reward": 0.0}, "messages": []},
            {"task_id": "x-D", "reward_info": {"reward": 1.0},
             "messages": [{"tool_calls": [{"name": "transfer_to_human_agents"}]}]},
            {"task_id": "y-C", "reward_info": {"reward": 0.0},
             "messages": [{"tool_calls": [{"name": "cancel_reservation"}]}]}]
    s = score.score({"simulations": sims}, ks=(1, 2))
    assert s["D"]["errors"] == 1 and s["D"]["pass^k"][1] == 0.5 and s["D"]["pass^k"][2] == 0.0
    assert s["C"]["errors"] == 1
