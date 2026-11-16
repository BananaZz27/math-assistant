"""The list of tools the brain may call, and a safe way to run them.

Every tool runs in a separate process so a hanging calculation can be
stopped by a timeout. The "spawn" start method is used so this works the
same on Windows and Linux.
"""

import dataclasses
import multiprocessing
import queue as queue_module
from dataclasses import dataclass
from typing import Any, Callable

from assistant.config import TOOL_TIMEOUT_S
from assistant.errors import ToolError
from assistant.tools.algebra import solve_equation
from assistant.tools.dataframe import summarize_csv


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict
    func: Callable[..., Any]


TOOLS: dict[str, ToolSpec] = {
    "solve_equation": ToolSpec(
        name="solve_equation",
        description="Solve an equation or find where an expression equals zero (real solutions).",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "e.g. 'x^2 - 5x + 6 = 0'"},
                "variable": {"type": "string", "description": "variable to solve for, default 'x'"},
            },
            "required": ["text"],
        },
        func=solve_equation,
    ),
    "summarize_csv": ToolSpec(
        name="summarize_csv",
        description="Summarize a CSV file: row count and per-column type, missing values, min, max, mean.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "path to the CSV file"}},
            "required": ["path"],
        },
        func=summarize_csv,
    ),
}


def _worker(func: Callable[..., Any], args: dict, results) -> None:
    """Runs in the child process; always puts exactly one message on the queue."""
    try:
        result = func(**args)
        if dataclasses.is_dataclass(result):
            result = dataclasses.asdict(result)
        results.put(("ok", result))
    except ToolError as exc:
        results.put(("err", str(exc)))
    except TypeError as exc:
        results.put(("err", f"bad arguments / อาร์กิวเมนต์ไม่ถูกต้อง: {exc}"))
    except Exception as exc:  # keep the parent alive whatever the tool does
        results.put(("err", f"{type(exc).__name__}: {exc}"))


def run_tool(name: str, args: dict, timeout_s: float = TOOL_TIMEOUT_S) -> dict:
    """Run tool ``name`` with ``args`` and return its result as a plain dict."""
    spec = TOOLS.get(name)
    if spec is None:
        raise ToolError(f"unknown tool / ไม่มีเครื่องมือชื่อ: {name}")

    context = multiprocessing.get_context("spawn")
    results = context.Queue()
    process = context.Process(target=_worker, args=(spec.func, args, results))
    process.start()
    try:
        kind, payload = results.get(timeout=timeout_s)
    except queue_module.Empty:
        raise ToolError(f"tool timed out after {timeout_s}s / เครื่องมือใช้เวลานานเกินไป") from None
    finally:
        if process.is_alive():
            process.terminate()
        process.join(timeout=2)

    if kind == "err":
        raise ToolError(payload)
    return payload
