"""Command line entry point: python -m assistant.cli "question" [--model NAME] [--file PATH]."""

import argparse
import sys

from assistant.brain.base import Brain
from assistant.brain.local import LocalBrain
from assistant.config import DEFAULT_MODEL
from assistant.core import answer
from assistant.errors import BrainError


def main(argv: list[str] | None = None, brain: Brain | None = None) -> int:
    parser = argparse.ArgumentParser(prog="assistant", description="Math and data assistant")
    parser.add_argument("question", help="the math problem or data question")
    parser.add_argument("--model", default=None, help=f"Ollama model name (default {DEFAULT_MODEL})")
    parser.add_argument("--file", default=None, help="a CSV file to analyze")
    args = parser.parse_args(argv)

    question = args.question
    if args.file:
        question += f"\nไฟล์: {args.file}"
    if brain is None:
        brain = LocalBrain(model=args.model or DEFAULT_MODEL)

    try:
        result = answer(question, brain)
    except BrainError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if result.facts:
        print(result.facts)
        print()
    print(result.text)
    return 1 if result.verified is False else 0


if __name__ == "__main__":
    sys.exit(main())
