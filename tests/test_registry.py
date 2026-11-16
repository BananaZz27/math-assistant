import time

import pytest

from assistant.errors import ToolError
from assistant.tools.registry import TOOLS, ToolSpec, run_tool


def sleeper(secs):
    time.sleep(secs)


def test_run_solve_equation():
    out = run_tool("solve_equation", {"text": "x**2 - 5*x + 6 = 0"})
    assert out["solutions"] == ["2", "3"] and out["verified"] is True


def test_unknown_tool():
    with pytest.raises(ToolError, match="unknown tool"):
        run_tool("rm_rf", {})


def test_bad_arguments():
    with pytest.raises(ToolError):
        run_tool("solve_equation", {"wrong": 1})


def test_tool_error_message_is_preserved(tmp_path):
    empty = tmp_path / "e.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ToolError, match="empty"):
        run_tool("summarize_csv", {"path": str(empty)})


def test_timeout_stops_a_hanging_tool(monkeypatch):
    monkeypatch.setitem(TOOLS, "sleeper", ToolSpec("sleeper", "", {}, sleeper))
    start = time.monotonic()
    with pytest.raises(ToolError, match="timed out"):
        run_tool("sleeper", {"secs": 5}, timeout_s=0.5)
    assert time.monotonic() - start < 3


def test_registry_lists_exactly_the_two_v0_tools():
    assert set(TOOLS) == {"solve_equation", "summarize_csv"}
    assert TOOLS["solve_equation"].parameters["required"] == ["text"]
    assert TOOLS["summarize_csv"].parameters["required"] == ["path"]
