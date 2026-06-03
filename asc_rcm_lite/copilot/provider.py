"""Swappable local copilot provider selection."""

from __future__ import annotations

import os
import warnings
from typing import Protocol

from .mock_llm import MockLLM
from .models import CopilotDraft, CopilotRequest


class CopilotProvider(Protocol):
    def generate(self, request: CopilotRequest, prompt: str) -> CopilotDraft:
        """Return a deterministic draft response."""


class MockLLMProvider:
    def __init__(self) -> None:
        self._llm = MockLLM()

    def generate(self, request: CopilotRequest, prompt: str) -> CopilotDraft:
        return self._llm.generate(request, prompt)


def get_copilot_provider() -> CopilotProvider:
    provider_name = os.getenv("ASC_RCM_COPILOT_PROVIDER", "mock").strip().lower()
    if provider_name in {"", "mock"}:
        return MockLLMProvider()
    warnings.warn(
        f"Unknown ASC_RCM_COPILOT_PROVIDER={provider_name!r}; falling back to mock provider.",
        RuntimeWarning,
        stacklevel=2,
    )
    return MockLLMProvider()
