"""Equation solving with SymPy (real solutions only in v0)."""

from dataclasses import dataclass, field
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
    approximate: list[str] = field(default_factory=list)  # decimal forms, from code, for the explanation


def _is_root(expr: sympy.Expr, symbol: sympy.Symbol, value: sympy.Expr) -> bool:
    residual = expr.subs(symbol, value)
    if residual == 0 or sympy.simplify(residual) == 0:
        return True
    return abs(sympy.N(residual, 30)) < sympy.Float("1e-15")  # roots such as CRootOf have no exact form


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
    # Decimals become exact fractions (0.5 -> 1/2) so roots stay exact and can be verified.
    expr = sympy.nsimplify(lhs - rhs, rational=True)
    other = expr.free_symbols - {symbol}
    if other:
        names = ", ".join(sorted(str(s) for s in other))
        raise ToolError(f"v0 แก้ได้ทีละตัวแปร พบตัวแปรอื่น: {names} / only one variable supported")

    solutions = sympy.solveset(expr, symbol, S.Reals)
    if solutions is S.EmptySet:
        return SolveResult(text, variable, [], "none", True)
    if solutions is S.Reals:
        return SolveResult(text, variable, [], "all", True)

    if isinstance(solutions, sympy.FiniteSet):
        roots = list(solutions)
    elif expr.is_polynomial(symbol):
        # e.g. cubics with three real roots, where solveset returns an Intersection with complex radicals
        try:
            roots = list(set(sympy.real_roots(sympy.Poly(expr, symbol))))
        except (sympy.PolynomialError, NotImplementedError) as exc:
            raise ToolError("unsupported equation") from exc
    else:
        raise ToolError("unsupported equation")

    ordered = sorted(roots, key=lambda r: float(sympy.N(r)))
    return SolveResult(
        equation=text,
        variable=variable,
        solutions=[str(r) for r in ordered],
        kind="finite",
        verified=all(_is_root(expr, symbol, r) for r in ordered),
        approximate=[str(sympy.N(r, 6)) for r in ordered],
    )
