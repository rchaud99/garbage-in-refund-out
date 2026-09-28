"""Model adapters for the wording-ladder study, all behind lookworth's Request/Reply interface.

- `gemini-*` / `gemma-*`: Google's API through google-genai (GEMINI_API_KEY). Bounded output, no SDK retries.
- `claude-*`: Anthropic directly through lookworth's Claude adapter (ANTHROPIC_API_KEY).
- `openrouter/<vendor>/<model>`: any model through OpenRouter's OpenAI-compatible API (OPENROUTER_API_KEY), with the
  provider-reported cost when OpenRouter returns one.

Reasoning settings are part of every model's `settings`, which every run records, so budgets can be compared.
Prices are list prices per million tokens (input, output); a model without a known price gets a conservative
placeholder, flagged in its settings, so the budget guard over-reserves rather than under-reserves.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Mapping
from typing import Any

from lookworth.models import Reply, Request, TransientError, Usage

MAX_OUTPUT = 8192
"""Output tokens including reasoning, for every model; as in the 2026-09-25 campaigns."""

PRICES: dict[str, tuple[float, float]] = {
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.5-flash": (1.50, 9.00),
    "gemma-4-31b-it": (0.0, 0.0),
    "gemma-4-26b-a4b-it": (0.0, 0.0),
    "gemini-3.1-pro-preview": (2.00, 12.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
    "anthropic/claude-sonnet-5": (2.00, 10.00),
    "anthropic/claude-opus-5.5": (4.00, 20.00),
    "openai/gpt-6-sol": (2.00, 10.00),
    "openai/gpt-6-luna": (0.10, 0.50),
    "deepseek/deepseek-v4-pro-0813": (0.39, 4.20),
    "qwen/qwen3.5-397b-a17b": (0.55, 3.50),
    "x-ai/grok-4.7": (2.00, 6.00),
}
# Gemma 4 on Google's API: "Free of charge" (ai.google.dev/gemini-api/docs/pricing, read 2026-09-28).
PLACEHOLDER = (2.00, 12.00)
"""Conservative stand-in for a model whose list price isn't in the table (e.g. Gemma on Google's API)."""


def price(name: str) -> tuple[tuple[float, float], bool]:
    """(input, output) dollars per million tokens, and whether that is a placeholder."""
    key = name.removeprefix("openrouter/")
    for known, value in PRICES.items():
        if key == known or key.endswith("/" + known):
            return value, False
    return PLACEHOLDER, True


def cost(name: str, usage: Mapping[str, Any], reported: float | None = None) -> float:
    """Dollars for one reply: the provider's own figure when it gives one, else tokens at list price."""
    if reported is not None:
        return float(reported)
    (p_in, p_out), _ = price(name)
    out = usage["output_tokens"] + (usage.get("reasoning_tokens") or 0)
    return (usage["input_tokens"] * p_in + out * p_out) / 1_000_000


def bound(name: str, request: Request) -> float:
    """An upper bound on one call's cost: prompt bytes as tokens (UTF-8 bytes ≥ tokens), plus the output cap."""
    tokens = len((request.system + "".join(request.parts) + json.dumps(request.json_schema)).encode()) + 4096
    (p_in, p_out), _ = price(name)
    return (tokens * p_in + MAX_OUTPUT * p_out) / 1_000_000


class GoogleModel:
    """Gemini or Gemma through google-genai. `thinking_level=None` sends no thinking config (models without one)."""

    def __init__(self, name: str, thinking_level: str | None = "medium", json_mode: bool = True) -> None:
        from google import genai
        from google.genai import types

        self.name = name
        self._types = types
        self._thinking = thinking_level
        self._json = json_mode
        placeholder = price(name)[1]
        self.settings: Mapping[str, Any] = {
            "provider": "google", "thinking_level": thinking_level, "max_output_tokens": MAX_OUTPUT,
            "temperature": "provider default", "sdk_retries": 0, "json_schema_enforced": json_mode,
            **({"price_placeholder_per_mtok": PLACEHOLDER} if placeholder else {}),
        }
        self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                                    http_options=types.HttpOptions(timeout=300_000))

    def respond(self, request: Request) -> Reply:
        from google.genai import errors
        from lookworth.models.gemini import _finish_reason, _join, _usage

        types = self._types
        config = types.GenerateContentConfig(
            system_instruction=request.system,
            thinking_config=(types.ThinkingConfig(thinking_level=types.ThinkingLevel(self._thinking.upper()),
                                                  include_thoughts=True) if self._thinking else None),
            max_output_tokens=MAX_OUTPUT,
            response_mime_type="application/json" if self._json and request.json_schema else None,
            response_json_schema=dict(request.json_schema) if self._json and request.json_schema else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        started = time.monotonic()
        try:
            response = self._client.models.generate_content(
                model=self.name, contents=[types.Content(role="user", parts=[types.Part(text=p) for p in request.parts])],
                config=config)
        except errors.APIError as error:
            if error.code in {408, 429, 500, 502, 503, 504}:
                raise TransientError(f"HTTP {error.code}: {error.message}") from error
            raise
        except Exception as error:  # transport failures from httpx
            if any(k in type(error).__name__ for k in ("Timeout", "Connect", "Protocol", "ReadError", "WriteError")):
                raise TransientError(f"{type(error).__name__}: {error}") from error
            raise
        return Reply(
            text=_join(response, False), thoughts=_join(response, True) or None,
            usage=_usage(response.usage_metadata), latency_s=round(time.monotonic() - started, 3),
            model_version=response.model_version or self.name, finish_reason=_finish_reason(response),
            raw=response.model_dump(mode="json", exclude_none=True, exclude={"sdk_http_response", "parsed"}),
        )


class ClaudeDirect:
    """lookworth's Claude adapter at the effort the earlier runs used (high), with a bounded max_tokens."""

    def __init__(self, name: str, effort: str = "high") -> None:
        from lookworth.models.claude import Claude

        self._inner = Claude(name, effort=effort, max_tokens=MAX_OUTPUT)
        self.name = name
        self.settings = {**self._inner.settings, "sdk_retries": 0}

    def respond(self, request: Request) -> Reply:
        return self._inner.respond(request)


class OpenRouter:
    """OpenRouter's chat completions API. The model is `vendor/model` after the `openrouter/` prefix.

    Structured output is requested with a strict JSON schema; reasoning with OpenRouter's unified `reasoning.effort`.
    The reply's `raw` keeps OpenRouter's whole response, including its reported cost and the serving provider.
    """

    URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, name: str, effort: str | None = "medium") -> None:
        import httpx

        self.name = name
        self._slug = name.removeprefix("openrouter/")
        self._effort = effort
        self._http = httpx.Client(timeout=300)
        self._key = os.environ["OPENROUTER_API_KEY"]
        self.settings: Mapping[str, Any] = {
            "provider": "openrouter", "model": self._slug, "reasoning_effort": effort, "max_tokens": MAX_OUTPUT,
            "temperature": "provider default", "sdk_retries": 0, "json_schema_enforced": True,
        }

    def respond(self, request: Request) -> Reply:
        import httpx

        body: dict[str, Any] = {
            "model": self._slug,
            "messages": [{"role": "system", "content": request.system},
                         {"role": "user", "content": "".join(p for p in request.parts if isinstance(p, str))}],
            "max_tokens": MAX_OUTPUT,
            "usage": {"include": True},
        }
        if self._effort:
            body["reasoning"] = {"effort": self._effort}
        if request.json_schema:
            schema = {**dict(request.json_schema), "additionalProperties": False}
            body["response_format"] = {"type": "json_schema",
                                       "json_schema": {"name": "decision", "strict": True, "schema": schema}}
        started = time.monotonic()
        try:
            response = self._http.post(self.URL, json=body, headers={"Authorization": f"Bearer {self._key}"})
        except httpx.TransportError as error:
            raise TransientError(f"{type(error).__name__}: {error}") from error
        if response.status_code in {408, 429, 500, 502, 503, 504}:
            raise TransientError(f"HTTP {response.status_code}: {response.text[:300]}")
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
        data = response.json()
        if "error" in data:
            code = data["error"].get("code")
            if code in {408, 429, 500, 502, 503, 504}:
                raise TransientError(f"OpenRouter error {code}: {data['error'].get('message')}")
            raise RuntimeError(f"OpenRouter error {code}: {data['error'].get('message')}")
        choice = data["choices"][0]
        message = choice.get("message") or {}
        usage = data.get("usage") or {}
        details = usage.get("completion_tokens_details") or {}
        reasoning = details.get("reasoning_tokens")
        return Reply(
            text=message.get("content") or "",
            thoughts=message.get("reasoning") or None,
            usage=Usage(input_tokens=usage.get("prompt_tokens", 0),
                        output_tokens=usage.get("completion_tokens", 0) - (reasoning or 0),
                        reasoning_tokens=reasoning),
            latency_s=round(time.monotonic() - started, 3),
            model_version=f"{data.get('provider', '?')}:{data.get('model', self._slug)}",
            finish_reason=choice.get("finish_reason") or "unknown",
            raw=data,
        )


def load(spec: str):
    """A model from a spec like `gemini-3.8-flash`, `gemma-4-31b-it`, `claude-sonnet-5` or
    `openrouter/openai/gpt-5.5`. Settings are fixed per family, so a spec is a full description."""
    if spec.startswith("openrouter/anthropic/"):
        return OpenRouter(spec, effort="high")  # the effort the earlier direct-API Claude runs used
    if spec.startswith("openrouter/"):
        return OpenRouter(spec, effort="medium")
    if spec.startswith("claude-"):
        return ClaudeDirect(spec)
    if spec.startswith("gemma-"):
        return GoogleModel(spec, thinking_level=None, json_mode=False)
    if spec.startswith("gemini-"):
        return GoogleModel(spec)
    raise ValueError(f"no provider for {spec!r}")


def reported_cost(reply: Reply | None) -> float | None:
    """OpenRouter's own cost for the call, when present."""
    if reply is None or not isinstance(reply.raw, Mapping):
        return None
    usage = reply.raw.get("usage")
    return usage.get("cost") if isinstance(usage, Mapping) else None
