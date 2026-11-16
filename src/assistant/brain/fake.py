"""A brain with canned replies, for tests. No LLM involved."""

from assistant.brain.base import ToolCall
from assistant.tools.registry import ToolSpec


class FakeBrain:
    def __init__(self, call: ToolCall, explanation: str):
        self.call = call
        self.explanation = explanation
        self.explain_calls: list[tuple[str, ToolCall, dict]] = []

    def plan(self, question: str, tools: list[ToolSpec]) -> ToolCall:
        return self.call

    def explain(self, question: str, call: ToolCall, result: dict) -> str:
        self.explain_calls.append((question, call, result))
        return self.explanation
