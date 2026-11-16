"""Summarize a CSV file with pandas."""

from dataclasses import dataclass

import pandas as pd
from pandas.api.types import is_numeric_dtype

from assistant.errors import ToolError


@dataclass(frozen=True)
class ColumnSummary:
    name: str
    dtype: str
    missing: int
    minimum: float | None
    maximum: float | None
    mean: float | None


@dataclass(frozen=True)
class CsvSummary:
    rows: int
    columns: list[ColumnSummary]


def summarize_csv(path: str) -> CsvSummary:
    """Read ``path`` (UTF-8 or UTF-8 with BOM) and describe each column."""
    try:
        frame = pd.read_csv(path, encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise ToolError(f"ไม่พบไฟล์ / file not found: {path}") from exc
    except pd.errors.EmptyDataError as exc:
        raise ToolError(f"ไฟล์ว่าง / the file is empty: {path}") from exc
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise ToolError(f"อ่าน CSV ไม่ได้ / cannot read CSV: {path}") from exc

    columns = []
    for name in frame.columns:
        series = frame[name]
        has_stats = is_numeric_dtype(series) and series.notna().any()
        columns.append(
            ColumnSummary(
                name=str(name),
                dtype=str(series.dtype),
                missing=int(series.isna().sum()),
                minimum=float(series.min()) if has_stats else None,
                maximum=float(series.max()) if has_stats else None,
                mean=float(series.mean()) if has_stats else None,
            )
        )
    return CsvSummary(rows=len(frame), columns=columns)
