import pytest

from assistant.errors import ToolError
from assistant.tools.dataframe import summarize_csv


def test_basic_numeric_and_text(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("name,score\nA,1\nB,3\n", encoding="utf-8")
    s = summarize_csv(str(p))
    assert s.rows == 2
    score = next(c for c in s.columns if c.name == "score")
    assert (score.minimum, score.maximum, score.mean) == (1.0, 3.0, 2.0)
    assert next(c for c in s.columns if c.name == "name").mean is None


def test_thai_headers(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("อุณหภูมิ\n30\n32\n", encoding="utf-8-sig")
    assert summarize_csv(str(p)).columns[0].name == "อุณหภูมิ"


def test_missing_values_counted(tmp_path):
    p = tmp_path / "m.csv"
    p.write_text("v,w\n1,a\n,b\n3,c\n", encoding="utf-8")
    assert summarize_csv(str(p)).columns[0].missing == 1


def test_all_missing_column_has_no_stats(tmp_path):
    p = tmp_path / "n.csv"
    p.write_text("a,b\n1,\n2,\n", encoding="utf-8")
    b = next(c for c in summarize_csv(str(p)).columns if c.name == "b")
    assert b.missing == 2 and b.mean is None


def test_empty_file_raises(tmp_path):
    p = tmp_path / "e.csv"
    p.write_text("", encoding="utf-8")
    with pytest.raises(ToolError, match="empty"):
        summarize_csv(str(p))


def test_missing_path_raises():
    with pytest.raises(ToolError):
        summarize_csv("no/such/file.csv")
