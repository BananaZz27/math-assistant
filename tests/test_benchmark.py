import importlib.util
from pathlib import Path

from assistant.brain.base import ToolCall
from assistant.brain.fake import FakeBrain

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "benchmark_models.py"


def load_script():
    spec = importlib.util.spec_from_file_location("benchmark_models", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_score_counts_correct_tool_and_verified():
    bench = load_script()
    brain = FakeBrain(ToolCall("solve_equation", {"text": "x**2=9"}), "ok")
    questions = [
        {"question": "q1", "expected_tool": "solve_equation"},
        {"question": "q2", "expected_tool": "summarize_csv"},
    ]
    score = bench.score_brain(brain, questions)
    assert score["total"] == 2
    assert score["tool_correct"] == 1
    assert score["verified"] == 2
    assert score["avg_seconds"] >= 0


def test_question_file_is_well_formed():
    bench = load_script()
    questions = bench.load_questions()
    assert len(questions) == 10
    assert {q["expected_tool"] for q in questions} == {"solve_equation", "summarize_csv"}


def test_score_counts_correct_solutions():
    bench = load_script()
    brain = FakeBrain(ToolCall("solve_equation", {"text": "x**2=9"}), "ok")
    questions = [
        {"question": "q1", "expected_tool": "solve_equation", "expected_solutions": ["-3", "3"]},
        {"question": "q2", "expected_tool": "solve_equation", "expected_solutions": ["1"]},
        {"question": "q3", "expected_tool": "summarize_csv", "expected_solutions": None},
    ]
    score = bench.score_brain(brain, questions)
    assert score["solutions_total"] == 2 and score["solutions_correct"] == 1


def test_every_algebra_question_has_expected_solutions():
    bench = load_script()
    for q in bench.load_questions():
        if q["expected_tool"] == "solve_equation":
            assert isinstance(q["expected_solutions"], list)
