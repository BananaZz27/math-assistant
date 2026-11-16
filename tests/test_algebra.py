import pytest

from assistant.errors import ToolError
from assistant.tools.algebra import solve_equation


def test_quadratic_two_roots():
    r = solve_equation("x² − 5x + 6 = 0")
    assert r.kind == "finite" and r.solutions == ["2", "3"] and r.verified is True


def test_expression_without_equals_means_zero():
    assert solve_equation("x**2 - 5*x + 6").solutions == ["2", "3"]


def test_caret_and_implicit_multiplication():
    assert solve_equation("2x + 4 = 0").solutions == ["-2"]
    assert solve_equation("x^2 = 9").solutions == ["-3", "3"]


def test_no_real_solution():
    r = solve_equation("x**2 + 1 = 0")
    assert r.kind == "none" and r.solutions == []


def test_contradiction_has_no_solution():
    assert solve_equation("x + 1 = x + 2").kind == "none"


def test_identity_is_all_reals():
    assert solve_equation("x + 1 = x + 1").kind == "all"


def test_bad_input_raises_tool_error():
    with pytest.raises(ToolError):
        solve_equation("__import__('os').system('echo hi')")


def test_decimal_input_is_verified_and_exact():
    r = solve_equation("x^2 = 0.5")
    assert r.verified is True
    assert r.solutions == ["-sqrt(2)/2", "sqrt(2)/2"]
    assert solve_equation("1.5x^2 = 3.3").verified is True


def test_cubic_with_three_real_roots_is_solved():
    r = solve_equation("x^3 - 3x + 1 = 0")
    assert r.kind == "finite" and len(r.solutions) == 3 and r.verified is True
    assert abs(float(r.approximate[0]) - (-1.87939)) < 1e-4


def test_quintic_gives_approximate_value():
    r = solve_equation("x^5 - x - 1 = 0")
    assert len(r.solutions) == 1 and r.verified is True
    assert abs(float(r.approximate[0]) - 1.1673) < 1e-3


def test_exact_roots_also_have_approximate_values():
    assert solve_equation("x^2 = 9").approximate == ["-3.00000", "3.00000"]
