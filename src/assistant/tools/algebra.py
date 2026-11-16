"""Equation solving with SymPy (real solutions only in v0)."""

from dataclasses import dataclass
from typing import Literal

import sympy
from sympy import S

from assistant.errors import ToolError
from assistant.tools.parse import normalize_math_text, parse_expression


@dataclass(frozen=True)
class SolveResult:
    equation: str
    variable: str
    solutions: list[str]
    kind: Literal["finite", "none", "all"]
    verified: bool


def solve_equation(text: str, variable: str = "x") -> SolveResult:
    """Solve ``text`` (``lhs = rhs``, or an expression meaning ``expr = 0``) for ``variable``."""
    if len(variable) != 1 or not variable.isalpha():
        raise ToolError(f"ชื่อตัวแปรต้องเป็นตัวอักษรเดียว / bad variable: {variable!r}")

    normalized = normalize_math_text(text)
    parts = normalized.split("=")
    if len(parts) > 2:
        raise ToolError("มีเครื่องหมาย = มากกว่าหนึ่งตัว / more than one '='")
    lhs = parse_expression(parts[0])
    rhs = parse_expression(parts[1]) if len(parts) == 2 else sympy.Integer(0)

    symbol = sympy.Symbol(variable)
    other = (lhs - rhs).free_symbols - {symbol}
    if other:
        names = ", ".join(sorted(str(s) for s in other))
        raise ToolError(f"v0 แก้ได้ทีละตัวแปร พบตัวแปรอื่น: {names} / only one variable supported")

    solutions = sympy.solveset(lhs - rhs, symbol, S.Reals)
    if solutions is S.EmptySet:
        return SolveResult(text, variable, [], "none", True)
    if solutions is S.Reals:
        return SolveResult(text, variable, [], "all", True)
    if isinstance(solutions, sympy.FiniteSet):
        ordered = sorted(solutions, key=lambda s: float(s))
        verified = all(
            sympy.simplify((lhs - rhs).subs(symbol, s)) == 0 for s in ordered
        )
        return SolveResult(text, variable, [str(s) for s in ordered], "finite", verified)
    raise ToolError("unsupported equation")
