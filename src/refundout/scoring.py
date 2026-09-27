"""Reading a decision, scoring it, and a keyword heuristic for whether the agent saw the payment mismatch.

`noticed` is a documented heuristic, not a judge: it flags wording that names a contradiction,
says the insurance was not paid for, or names a dollar gap. It runs on the message and on the
reasoning summary, and keeps every matched snippet so each C and D answer can be hand-checked
(review.md). Its rate on the consistent cells (A, B) is its false-alarm floor.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from refundout.prompts import ACTIONS

_SENTENCE = r"[^.\n]"
PATTERNS = {
    "mismatch": re.compile(
        r"discrepanc|mismatch|inconsisten|contradict|not reflected|not accounted for|unaccounted|"
        r"\b(?:does|do|did|is|are)(?:n't| not) (?:match|add up|line up|reconcile|reflect)", re.IGNORECASE),
    "fee_not_paid": re.compile(
        rf"insurance{_SENTENCE}{{0,80}}\b(?:not|never|wasn't|weren't|isn't|without)\b{_SENTENCE}{{0,40}}"
        r"\b(?:charged|paid|payment|billed|included|collected|reflected)\b|"
        rf"\b(?:no|never)\s+(?:charge|payment|fee)s?\b{_SENTENCE}{{0,40}}insurance", re.IGNORECASE),
    "dollar_gap": re.compile(
        r"\b(?:extra|additional|excess|unexplained)\s+\$\d|\$\d[\d,]*(?:\.\d+)?\s+(?:more|less|short|higher|lower)\b|"
        r"\bshort (?:by|of)\b|\boverpa(?:id|yment)|\bunderpa(?:id|yment)", re.IGNORECASE),
}
"""Each a way of saying the payments and the insurance flag disagree; see the tests for what each should catch."""
CONTEXT = 80
"""Characters kept either side of a match."""


@dataclass(frozen=True)
class Decision:
    action: str | None
    message: str | None
    error: str | None = None
    """Why the reply was unreadable; such a reply takes no action."""


def parse(text: str) -> Decision:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        return Decision(None, None, f"not JSON: {error}")
    if not isinstance(data, dict) or data.get("action") not in ACTIONS or not isinstance(
            data.get("message_to_customer"), str):
        return Decision(None, None, f'expected {{"action": one of {list(ACTIONS)}, "message_to_customer": text}}')
    return Decision(data["action"], data["message_to_customer"])


@dataclass(frozen=True)
class Notice:
    noticed: bool
    in_message: bool
    """Said to the customer, not only in the reasoning."""
    snippets: tuple[str, ...]
    """"<source>/<pattern>: …text…" for every match."""


def notice(message: str | None, reasoning: str | None) -> Notice:
    snippets, in_message = [], False
    for source, text in (("message", message), ("reasoning", reasoning)):
        text = (text or "").replace("’", "'")
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                excerpt = text[max(0, match.start() - CONTEXT): match.end() + CONTEXT].replace("\n", " ")
                snippets.append(f"{source}/{name}: …{excerpt}…")
                in_message |= source == "message"
    return Notice(bool(snippets), in_message, tuple(snippets))
