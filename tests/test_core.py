from assistant import core
from assistant.brain.base import ToolCall
from assistant.brain.fake import FakeBrain
from assistant.core import UNVERIFIED_NOTICE, answer


def test_answer_uses_tool_result_not_brain():
    brain = FakeBrain(ToolCall("solve_equation", {"text": "x**2-5*x+6=0"}), "แยกตัวประกอบ ...")
    a = answer("แก้สมการ", brain)
    assert a.result["solutions"] == ["2", "3"] and a.verified is True
    assert a.text == "แยกตัวประกอบ ..."
    assert len(brain.explain_calls) == 1


def test_unverified_result_gets_notice(monkeypatch):
    monkeypatch.setattr(core, "run_tool", lambda n, a, **k: {"solutions": ["9"], "verified": False})
    a = answer("q", FakeBrain(ToolCall("solve_equation", {}), "ตอบ 9"))
    assert a.verified is False and a.text.startswith(UNVERIFIED_NOTICE)


def test_csv_result_has_no_verified_flag(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("v\n1\n", encoding="utf-8")
    a = answer("สรุป", FakeBrain(ToolCall("summarize_csv", {"path": str(p)}), "ok"))
    assert a.verified is None


def test_tool_error_becomes_plain_text_not_crash():
    brain = FakeBrain(ToolCall("solve_equation", {"text": "(((("}), "unused")
    a = answer("q", brain)
    assert "ToolError" not in a.text and a.verified is False
    assert a.result == {}
    assert brain.explain_calls == []
