"""scripts/run_episodes.py's budget guard, fatal-error stop and --skip (no τ² code runs here)."""

import importlib.util
import sys
from pathlib import Path

import pytest

from refundout.bases import choose

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_episodes.py"


@pytest.fixture(scope="module")
def episodes():
    spec = importlib.util.spec_from_file_location("run_episodes", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_guard_never_starts_an_episode_that_could_pass_the_cap(episodes):
    guard = episodes.Guard(0.35, 0.10)
    assert guard.start() and guard.start() and guard.start()
    assert not guard.start() and guard.refused  # 4 × $0.10 in flight > $0.35
    guard.finish(0.02)
    assert guard.spent == 0.02 and guard.dearest == 0.10
    assert guard.start()  # 0.02 spent + 3 in flight × 0.10 = 0.32
    assert not guard.start()  # 0.02 + 4 × 0.10
    guard.finish(0.20)
    assert guard.dearest == 0.20 and not guard.start()  # 0.22 + 3 × 0.20


def test_an_unrecoverable_error_halts_and_an_ordinary_one_does_not(episodes):
    assert episodes.halt({"error": "BadRequestError: Your credit balance is too low", "termination": None})
    assert episodes.halt({"error": "AuthenticationError: invalid x-api-key", "termination": None})
    assert episodes.halt({"error": None, "termination": "TerminationReason.USER_STOP"}) is None
    assert episodes.halt({"error": "Timeout: read timed out", "termination": None}) is None


def test_skip_takes_the_prefix_stable_draw_and_the_estimate_scales(episodes, airline, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["run_episodes.py", "--models", "sonnet", "--nudges", "F1", "F1d",
                                      "--skip", "12", "--bases", "3", "--estimate"])
    episodes.main()
    out = capsys.readouterr().out
    assert "12 episodes" in out and "after skipping 12" in out
    for base in choose(airline, 15)[12:]:
        assert base.reservation_id in out
    assert choose(airline, 12)[0].reservation_id not in out
    assert "$0.96 typical, $1.20 high" in out


def test_only_an_episode_that_failed_before_any_message_is_retried(episodes):
    blip = {"error": "APIConnectionError: nodename nor servname provided", "messages": []}
    assert episodes.retryable(blip)
    assert not episodes.retryable({**blip, "messages": [{"role": "user"}]})
    assert not episodes.retryable({"error": "BadRequestError: credit balance is too low", "messages": []})
    assert not episodes.retryable({"error": None, "messages": []})
