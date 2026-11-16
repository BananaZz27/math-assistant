import pytest
from sympy import Symbol

from assistant.errors import ToolError
from assistant.tools.parse import normalize_math_text, parse_expression


def test_normalize_unicode_math():
    assert normalize_math_text("x² − 5x + 6") == "x**2 - 5x + 6"


def test_parse_implicit_multiplication():
    assert parse_expression("5x") == 5 * Symbol("x")


def test_parse_rejects_code_injection():
    with pytest.raises(ToolError):
        parse_expression("__import__('os').system('echo hi')")


def test_parse_rejects_garbage():
    with pytest.raises(ToolError):
        parse_expression("((((")
