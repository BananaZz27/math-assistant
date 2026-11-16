"""Turn user-typed math text into SymPy expressions, safely.

Safety rule: only a small whitelist of characters and names ever reaches the
SymPy parser, and the parser runs with no builtins, so text like
``__import__('os')`` is rejected before anything can execute.
"""

import re

import sympy
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from assistant.errors import ToolError

_REPLACEMENTS = {
    "²": "**2",
    "³": "**3",
    "−": "-",
    "×": "*",
    "÷": "/",
    "^": "**",
}

_FUNCTIONS = {
    "sqrt": sympy.sqrt,
    "sin": sympy.sin,
    "cos": sympy.cos,
    "tan": sympy.tan,
    "log": sympy.log,
    "exp": sympy.exp,
}
_CONSTANTS = {"pi": sympy.pi, "E": sympy.E}

_ALLOWED_CHARS = re.compile(r"^[0-9A-Za-z+\-*/().,\s]+$")
_NAME = re.compile(r"[A-Za-z]+")

_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def normalize_math_text(text: str) -> str:
    """Replace the symbols people type (², −, ×, ÷, ^) with Python-style math."""
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def parse_expression(text: str) -> sympy.Expr:
    """Parse a math expression; raise ToolError for anything else."""
    cleaned = normalize_math_text(text).strip()
    if not cleaned or not _ALLOWED_CHARS.match(cleaned):
        raise ToolError(f"ไม่ใช่นิพจน์คณิตศาสตร์ / not a math expression: {text!r}")

    local_dict: dict[str, object] = {**_FUNCTIONS, **_CONSTANTS}
    for name in set(_NAME.findall(cleaned)):
        if name in local_dict:
            continue
        if len(name) == 1:
            local_dict[name] = sympy.Symbol(name)
        else:
            raise ToolError(f"ไม่รู้จักชื่อ '{name}' / unknown name '{name}'")

    global_dict = {
        "__builtins__": {},
        "Integer": sympy.Integer,
        "Float": sympy.Float,
        "Rational": sympy.Rational,
        "Symbol": sympy.Symbol,
        "Function": sympy.Function,
    }
    try:
        return parse_expr(
            cleaned,
            local_dict=local_dict,
            global_dict=global_dict,
            transformations=_TRANSFORMATIONS,
            evaluate=True,
        )
    except Exception as exc:  # SymPy raises many different error types
        raise ToolError(f"อ่านนิพจน์ไม่ได้ / cannot parse: {text!r}") from exc
