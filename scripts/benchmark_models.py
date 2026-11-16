"""Compare Ollama models on the fixed question set.

Run from the repo root:  python scripts/benchmark_models.py qwen2.5:7b llama3.1:8b
Prints, per model: correct tool chosen, answers verified, average seconds per question.
Then set DEFAULT_MODEL in src/assistant/config.py to the winner.
"""

import json
import sys
import time
from pathlib import Path

from assistant.brain.local import LocalBrain
from assistant.core import answer
from assistant.errors import BrainError

QUESTIONS_FILE = Path(__file__).resolve().parent / "benchmark_questions.json"


def load_questions() -> list[dict]:
    return json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))


def score_brain(brain, questions: list[dict]) -> dict:
    tool_correct = verified = 0
    elapsed = []
    for item in questions:
        start = time.monotonic()
        try:
            result = answer(item["question"], brain)
        except BrainError:
            elapsed.append(time.monotonic() - start)
            continue
        elapsed.append(time.monotonic() - start)
        tool_correct += result.call.name == item["expected_tool"]
        verified += result.verified is True
    return {
        "total": len(questions),
        "tool_correct": tool_correct,
        "verified": verified,
        "avg_seconds": sum(elapsed) / len(elapsed) if elapsed else 0.0,
    }


def main(models: list[str]) -> int:
    if not models:
        print("usage: python scripts/benchmark_models.py MODEL [MODEL ...]", file=sys.stderr)
        return 1
    questions = load_questions()
    for model in models:
        score = score_brain(LocalBrain(model=model), questions)
        print(
            f"{model}: tool {score['tool_correct']}/{score['total']}, "
            f"verified {score['verified']}/{score['total']}, "
            f"avg {score['avg_seconds']:.1f}s"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
