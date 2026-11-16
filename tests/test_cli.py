from assistant.brain.base import ToolCall
from assistant.brain.fake import FakeBrain
from assistant.cli import main
from assistant.errors import BrainError


def test_cli_prints_answer(capsys):
    brain = FakeBrain(ToolCall("solve_equation", {"text": "x**2=9"}), "คำตอบคือ ±3")
    assert main(["แก้ x^2=9"], brain=brain) == 0
    assert "คำตอบคือ ±3" in capsys.readouterr().out


def test_cli_brain_error_exit_code_and_friendly_message(capsys):
    class Broken:
        def plan(self, q, t):
            raise BrainError("ติดต่อ Ollama ไม่ได้")

    assert main(["q"], brain=Broken()) == 1
    assert "ติดต่อ Ollama ไม่ได้" in capsys.readouterr().err


def test_cli_file_option_is_added_to_question():
    seen = {}

    class Spy(FakeBrain):
        def plan(self, q, t):
            seen["q"] = q
            return super().plan(q, t)

    main(["สรุป", "--file", "data.csv"], brain=Spy(ToolCall("summarize_csv", {"path": "data.csv"}), "x"))
    assert "data.csv" in seen["q"]


def test_cli_tool_failure_exits_with_1(capsys):
    brain = FakeBrain(ToolCall("solve_equation", {"text": "(((("}), "unused")
    assert main(["q"], brain=brain) == 1
    assert capsys.readouterr().out.strip() != ""
