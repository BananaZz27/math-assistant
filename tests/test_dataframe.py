import pytest

from assistant.errors import ToolError
from assistant.tools.dataframe import summarize_csv


@pytest.fixture(autouse=True)
def inside_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


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


def test_trailing_comma_does_not_shift_columns(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a,b\n1,2,\n3,4,\n", encoding="utf-8")
    cols = {c.name: c for c in summarize_csv(str(p)).columns}
    assert (cols["a"].minimum, cols["a"].maximum) == (1.0, 3.0)
    assert cols["b"].missing == 0 and cols["b"].mean == 3.0


def test_url_is_rejected():
    with pytest.raises(ToolError, match="URL"):
        summarize_csv("http://127.0.0.1:9/ok.csv")


def test_path_outside_working_folder_is_rejected(tmp_path, monkeypatch):
    work = tmp_path / "work"
    work.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text("a\n1\n", encoding="utf-8")
    monkeypatch.chdir(work)
    with pytest.raises(ToolError, match="outside"):
        summarize_csv(str(outside))


def test_relative_path_inside_working_folder_works(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "ok.csv").write_text("a\n1\n", encoding="utf-8")
    assert summarize_csv("sub/ok.csv").rows == 1


def test_thai_windows_cp874_file_is_read(tmp_path):
    p = tmp_path / "x.csv"
    p.write_bytes("อุณหภูมิ\n30\n".encode("cp874"))
    assert summarize_csv(str(p)).columns[0].name == "อุณหภูมิ"


def test_directory_path_is_a_tool_error(tmp_path):
    with pytest.raises(ToolError):
        summarize_csv(str(tmp_path))
