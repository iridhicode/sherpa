"""LLM provider abstraction.

The :class:`Provider` protocol keeps the rest of the codebase independent of
any particular vendor SDK. Tests inject a fake; production uses
:class:`AnthropicProvider`. Adding another vendor is a single new class.
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

from agent_skills.errors import ProviderError

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 4096


@runtime_checkable
class Provider(Protocol):
    """Anything that can turn (system prompt, user prompt) into text."""

    def complete(self, *, system: str, prompt: str) -> str:
        """Return the model's text completion."""
        ...


class AnthropicProvider:
    """Provider backed by the official Anthropic Python SDK.

    The API key is read from the ``ANTHROPIC_API_KEY`` environment variable
    (handled by the SDK). The model can be overridden with the
    ``ANTHROPIC_MODEL`` environment variable or the ``model`` argument.
    """

    def __init__(self, model: str | None = None, max_tokens: int = DEFAULT_MAX_TOKENS) -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - dependency is declared
            raise ProviderError(
                "The 'anthropic' package is required. Install with: pip install anthropic"
            ) from exc

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ProviderError(
                "ANTHROPIC_API_KEY is not set. Get a key at https://console.anthropic.com/ "
                "and export it: export ANTHROPIC_API_KEY=sk-ant-..."
            )

        self._anthropic = anthropic
        self._client = anthropic.Anthropic()
        self._model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self._max_tokens = max_tokens

    def complete(self, *, system: str, prompt: str) -> str:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            raise ProviderError(f"Anthropic API request failed: {exc}") from exc

        text = "".join(
            block.text
            for block in response.content
            if isinstance(block, self._anthropic.types.TextBlock)
        )
        if not text:
            raise ProviderError("Provider returned an empty completion")
        return text
