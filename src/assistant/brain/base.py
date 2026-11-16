"""The contract every brain (LLM adapter) must follow."""

from dataclasses import dataclass
from typing import Protocol

from assistant.tools.registry import ToolSpec


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict


class Brain(Protocol):
    def plan(self, question: str, tools: list[ToolSpec]) -> ToolCall:
        """Pick which tool to call (and its arguments) for the question."""
        ...

    def explain(self, question: str, call: ToolCall, result: dict) -> str:
        """Explain the tool's verified result to the user, in their language."""
        ...
