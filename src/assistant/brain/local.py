"""Brain that talks to a local Ollama server (offline, no API key)."""

import json

import requests

from assistant.brain.base import ToolCall
from assistant.config import DEFAULT_MODEL, OLLAMA_HOST
from assistant.errors import BrainError
from assistant.tools.registry import ToolSpec

_PLAN_SYSTEM = (
    "You choose which tool answers the user's question. "
    'Reply with JSON only: {{"tool": "<tool name>", "args": {{...}}}}.\n'
    "Available tools:\n{tools}"
)

_EXPLAIN_SYSTEM = (
    "You explain a verified result to a student, step by step, in the same language as the "
    "question (Thai or English). Use ONLY the numbers that appear in the result. "
    "Never calculate new numbers yourself."
)


class LocalBrain:
    def __init__(self, model: str = DEFAULT_MODEL, host: str = OLLAMA_HOST, timeout_s: float = 60.0):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout_s = timeout_s

    def plan(self, question: str, tools: list[ToolSpec]) -> ToolCall:
        listing = "\n".join(
            f"- {t.name}: {t.description} parameters={json.dumps(t.parameters)}" for t in tools
        )
        messages = [
            {"role": "system", "content": _PLAN_SYSTEM.format(tools=listing)},
            {"role": "user", "content": question},
        ]
        allowed = {t.name for t in tools}
        reply = self._chat(messages, json_format=True)
        try:
            return self._parse_call(reply, allowed)
        except ValueError as first_error:
            messages += [
                {"role": "assistant", "content": reply},
                {"role": "user", "content": f"That reply was invalid ({first_error}). Reply with valid JSON only."},
            ]
        reply = self._chat(messages, json_format=True)
        try:
            return self._parse_call(reply, allowed)
        except ValueError as exc:
            raise BrainError(f"โมเดลตอบรูปแบบไม่ถูกต้อง / model gave an invalid plan: {exc}") from exc

    def explain(self, question: str, call: ToolCall, result: dict) -> str:
        messages = [
            {"role": "system", "content": _EXPLAIN_SYSTEM},
            {
                "role": "user",
                "content": f"Question: {question}\nTool: {call.name}\n"
                f"Result: {json.dumps(result, ensure_ascii=False)}",
            },
        ]
        return self._chat(messages, json_format=False)

    @staticmethod
    def _parse_call(reply: str, allowed: set[str]) -> ToolCall:
        try:
            data = json.loads(reply)
        except json.JSONDecodeError as exc:
            raise ValueError("not valid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON is not an object")
        name, args = data.get("tool"), data.get("args", {})
        if not isinstance(name, str) or name not in allowed:
            raise ValueError(f"unknown tool {name!r}")
        if not isinstance(args, dict):
            raise ValueError("'args' must be an object")
        return ToolCall(name, args)

    def _chat(self, messages: list[dict], json_format: bool) -> str:
        payload = {"model": self.model, "messages": messages, "stream": False}
        if json_format:
            payload["format"] = "json"
        try:
            response = requests.post(f"{self.host}/api/chat", json=payload, timeout=self.timeout_s)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise BrainError(
                f"ติดต่อ Ollama ไม่ได้ ({self.host}) ลองเปิดโปรแกรม Ollama ก่อน / "
                f"cannot reach Ollama at {self.host}"
            ) from exc
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            raise BrainError(f"Ollama ตอบกลับผิดปกติ / unexpected reply from Ollama: {exc}") from exc
