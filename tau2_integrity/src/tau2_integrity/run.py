"""Run generated tasks under τ²'s own CLI, unchanged: register a domain + task set, then hand over to `tau2`.

    python -m tau2_integrity.run tasks/cancel_sick -- run --domain integrity --agent-llm ... --num-trials 4

The generated directory's policy.md becomes the domain's policy (τ²'s airline environment, tools and database are
used as-is); tasks.json becomes the task set. Everything after `--` is passed to τ²'s CLI verbatim.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

NAME = "integrity"


def register(directory: Path, name: str = NAME) -> None:
    from tau2.data_model.tasks import Task
    from tau2.domains.airline.environment import get_environment
    from tau2.registry import registry

    policy = (directory / "policy.md").read_text()
    raw = json.loads((directory / "tasks.json").read_text())

    def environment(db=None, solo_mode: bool = False):
        env = get_environment(db=db, solo_mode=solo_mode)
        env.policy = policy
        return env

    def tasks(task_split_name=None):
        return [Task.model_validate(t) for t in raw]

    registry.register_domain(environment, name)
    registry.register_tasks(tasks, name)


def main() -> None:
    args = sys.argv[1:]
    if "--" not in args or not args:
        raise SystemExit(__doc__)
    split = args.index("--")
    register(Path(args[0]))
    from tau2.cli import main as tau2_main

    sys.argv = ["tau2", *args[split + 1:]]
    tau2_main()


if __name__ == "__main__":
    main()
