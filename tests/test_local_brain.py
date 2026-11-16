import pytest
import requests

from assistant.brain.base import ToolCall
from assistant.brain.local import LocalBrain
from assistant.errors import BrainError
from assistant.tools.registry import TOOLS


class FakeResponse:
    def __init__(self, content):
        self._content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"message": {"content": self._content}}


def patch_post(monkeypatch, replies):
    """Make requests.post return the given replies in order; return the list of sent payloads."""
    sent = []
    remaining = list(replies)

    def fake_post(url, json=None, timeout=None, **kwargs):
        sent.append(json)
        return FakeResponse(remaining.pop(0))

    monkeypatch.setattr(requests, "post", fake_post)
    return sent


def raise_connection_error(*args, **kwargs):
    raise requests.ConnectionError("refused")


def test_plan_parses_json_tool_call(monkeypatch):
    patch_post(monkeypatch, ['{"tool": "solve_equation", "args": {"text": "x^2=9"}}'])
    call = LocalBrain().plan("แก้ x^2 = 9", list(TOOLS.values()))
    assert call == ToolCall("solve_equation", {"text": "x^2=9"})


def test_plan_retries_once_on_malformed_json(monkeypatch):
    posts = patch_post(monkeypatch, ["not json", '{"tool": "solve_equation", "args": {"text": "x=1"}}'])
    assert LocalBrain().plan("q", list(TOOLS.values())).name == "solve_equation"
    assert len(posts) == 2


def test_plan_gives_up_after_retry(monkeypatch):
    patch_post(monkeypatch, ["bad", "still bad"])
    with pytest.raises(BrainError):
        LocalBrain().plan("q", list(TOOLS.values()))


def test_plan_rejects_tool_not_in_list(monkeypatch):
    bad = '{"tool": "delete_everything", "args": {}}'
    patch_post(monkeypatch, [bad, bad])
    with pytest.raises(BrainError):
        LocalBrain().plan("q", list(TOOLS.values()))


def test_explain_includes_result_and_question_in_prompt(monkeypatch):
    posts = patch_post(monkeypatch, ["คำอธิบาย"])
    out = LocalBrain().explain("แก้ x^2=9", ToolCall("solve_equation", {}), {"solutions": ["-3", "3"]})
    assert out == "คำอธิบาย" and '"-3"' in posts[0]["messages"][-1]["content"]


def test_ollama_unreachable_is_friendly(monkeypatch):
    monkeypatch.setattr(requests, "post", raise_connection_error)
    with pytest.raises(BrainError, match="Ollama"):
        LocalBrain().plan("q", [])


def test_plan_rejects_args_that_are_not_an_object(monkeypatch):
    bad = '{"tool": "solve_equation", "args": "x=1"}'
    patch_post(monkeypatch, [bad, bad])
    with pytest.raises(BrainError):
        LocalBrain().plan("q", list(TOOLS.values()))


def test_plan_rejects_tool_that_is_not_a_string(monkeypatch):
    bad = '{"tool": ["solve_equation"], "args": {}}'
    patch_post(monkeypatch, [bad, bad])
    with pytest.raises(BrainError):
        LocalBrain().plan("q", list(TOOLS.values()))


def test_reply_with_null_message_is_a_brain_error(monkeypatch):
    class NullMessage(FakeResponse):
        def json(self):
            return {"message": None}

    monkeypatch.setattr(requests, "post", lambda *a, **k: NullMessage(""))
    with pytest.raises(BrainError):
        LocalBrain().explain("q", ToolCall("solve_equation", {}), {})
