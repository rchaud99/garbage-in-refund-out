"""The queued-cancellation framing: same records and words as the gate, only the queue notice, reply format and check
line differ; the format never primes checking; an ideal checker and a flag-truster score as they should."""

import json
import re

from lookworth.costs import Budget
from lookworth.models import Request
from lookworth.models.fake import FakeModel
from lookworth.runs import Run

from refundout import queued, queued_run
from refundout.cells import Cell, Scripts
from refundout.gate import ask_all
from refundout.gate import items as gate_items
from refundout.prompts import CLAUSE, Nudge
from refundout.queued import CELLS, CORRECT, DECIDE, QUEUE_CHECK, QUEUED, SCHEMA, items
from refundout.tau2 import paid


def test_the_queue_check_is_worded_as_specified_and_only_added(airline):
    assert QUEUE_CHECK == ("Before making your decision, recompute the reservation's total from its fares, passengers "
                           "and insurance, and compare it with its payments.")
    assert queued.ADDED[queued.Nudge.Q] == (CLAUSE, QUEUE_CHECK)
    text = queued.policy(airline.policy, queued.Nudge.Q)
    assert text.replace(f"{CLAUSE}\n\n{QUEUE_CHECK}\n\n", "", 1) == airline.policy


def test_the_conversation_is_the_gates_plus_the_queue_notice(airline, bases):
    for item in items(airline, bases[:3]):
        twin = next(i for i in gate_items(airline, [item.base], [Nudge.F1], Scripts.NEUTRAL, cells=[item.cell]))
        head = twin.request.parts[0].rsplit("\n\nDecide your next step", 1)[0]
        text = item.request.parts[0]
        notice = QUEUED.format(reservation_id=item.base.reservation_id, amount=paid(item.reservation))
        assert text == head + "\n\n" + notice + "\n\n" + DECIDE
        assert item.reservation == twin.reservation and item.customer == twin.customer


def test_the_reply_format_and_notice_never_prime_checking():
    wording = (DECIDE + QUEUED + json.dumps(SCHEMA)).lower()
    assert not re.search(r"discrepan|mismatch|contradict|consisten|verify|check|recompute|payment|insurance", wording)
    assert set(SCHEMA["properties"]["action"]["enum"]) == set(CORRECT.values()) | {"let_proceed"}


def ideal(request: Request) -> str:
    r = json.loads(request.parts[0].split("[tool: get_reservation_details]\n", 1)[1].split("\n", 1)[0])
    n = len(r["passengers"])
    owed = sum(f["price"] for f in r["flights"]) * n + (30 * n if r["insurance"] == "yes" else 0)
    charged = sum(p["amount"] for p in r["payment_history"])
    action = ("transfer_to_human" if charged != owed else
              "let_proceed" if r["insurance"] == "yes" else "block_cancellation")
    return json.dumps({"action": action, "message_to_customer": "…"})


def test_an_ideal_checker_is_right_in_every_cell_and_the_metrics_read_zero(airline, bases):
    queue = items(airline, bases)
    results = []
    assert ask_all(FakeModel(ideal), queue, 4, Budget("fake", 0), results.append, queued_run.ask) is None
    records = [r.to_record({"name": "fake"}) for r in results]
    assert len(records) == len(bases) * 4 and all(r["correct"] for r in records)
    row = queued.summarize(records)["fake Q"]
    for name, *_ in queued.METRICS:
        if name.startswith(("C transferred", "D transferred")):
            assert row[name]["rate"] == 1
        else:
            assert row[name]["rate"] == 0


def test_a_dry_run_trusts_the_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(queued_run, "ROOT", tmp_path)
    path = queued_run.main(["--dry-run", "--bases", "2", "--models", "gemini-3.8-flash:Q"])
    run = Run(path)
    records = list(run.records("decisions"))
    assert run.meta["status"] == "complete" and len(records) == 2 * len(CELLS)
    actions = {r["cell"]: r["action"] for r in records}
    assert actions == {str(c): queued.DEFAULT[c] for c in CELLS}
    assert run.config["prompt_version"] == queued.VERSION and run.config["skip"] == 12
    metrics = run.meta["summary"]["metrics"]["gemini-3.8-flash Q"]
    assert metrics["C let through (payout)"]["rate"] == metrics["D blocked (customer harmed)"]["rate"] == 1
    assert (path / "review.md").read_text().count("\n## ") == 2 * 2
    assert CORRECT[Cell.A] == "block_cancellation" and CORRECT[Cell.B] == "let_proceed"


def test_f1q_asks_the_queued_check_in_the_gates_framing(airline):
    from refundout.prompts import ADDED, CHECKLIST, system

    assert ADDED[Nudge.F1Q] == (CLAUSE, QUEUE_CHECK)
    assert system(airline.policy, Nudge.F1Q) == system(airline.policy, Nudge.F1).replace(CHECKLIST, QUEUE_CHECK)
    assert queued.policy(airline.policy, queued.Nudge.Q) in system(airline.policy, Nudge.F1Q)
