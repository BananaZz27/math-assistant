"""The main flow: question -> brain plans -> tool computes -> brain explains.

The brain never produces the final numbers; they come from the tool result.
"""

from dataclasses import dataclass

from assistant.brain.base import Brain, ToolCall
from assistant.errors import ToolError
from assistant.tools.registry import TOOLS, ToolSpec, run_tool

UNVERIFIED_NOTICE = "ยังตรวจคำตอบไม่ผ่าน / could not verify the answer"


@dataclass(frozen=True)
class Answer:
    text: str
    call: ToolCall
    result: dict
    verified: bool | None  # None when the tool has nothing to verify (e.g. CSV summary)


def answer(question: str, brain: Brain, tools: dict[str, ToolSpec] = TOOLS) -> Answer:
    call = brain.plan(question, list(tools.values()))
    try:
        result = run_tool(call.name, call.args)
    except ToolError as exc:
        text = f"ทำไม่สำเร็จ / could not do this: {exc}"
        return Answer(text=text, call=call, result={}, verified=False)

    verified = result.get("verified")
    text = brain.explain(question, call, result)
    if verified is False:
        text = f"{UNVERIFIED_NOTICE}\n{text}"
    return Answer(text=text, call=call, result=result, verified=verified)
