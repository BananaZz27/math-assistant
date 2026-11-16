"""Summarize a CSV file with pandas.

Safety: the tool only reads local files inside the working folder (or the
folder named by the ASSISTANT_DATA_DIR environment variable). URLs are rejected,
because the file path can come from an LLM.
"""

import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from pandas.api.types import is_numeric_dtype

from assistant.errors import ToolError

# utf-8 first; cp874 is what Excel on Thai-locale Windows writes for "CSV (Comma delimited)".
_ENCODINGS = ("utf-8-sig", "cp874")


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


def _resolve_inside_base(path: str, base_dir: Path | None) -> Path:
    if "://" in path:
        raise ToolError(f"ไม่รองรับ URL / URLs are not allowed, use a local file: {path}")
    base = Path(base_dir or os.environ.get("ASSISTANT_DATA_DIR") or Path.cwd()).resolve()
    candidate = Path(path)
    resolved = (candidate if candidate.is_absolute() else base / candidate).resolve()
    if not resolved.is_relative_to(base):
        raise ToolError(f"ไฟล์อยู่นอกโฟลเดอร์ทำงาน / file is outside the working folder: {path}")
    return resolved


def summarize_csv(path: str, base_dir: Path | None = None) -> CsvSummary:
    """Read a local CSV (UTF-8, UTF-8 with BOM or cp874) and describe each column."""
    resolved = _resolve_inside_base(path, base_dir)
    if not resolved.exists():
        raise ToolError(f"ไม่พบไฟล์ / file not found: {path}")
    if not resolved.is_file():
        raise ToolError(f"ไม่ใช่ไฟล์ / not a file: {path}")

    frame = None
    for encoding in _ENCODINGS:
        try:
            with open(resolved, encoding=encoding, newline="") as handle:
                # index_col=False: a trailing comma must not shift the columns.
                frame = pd.read_csv(handle, index_col=False)
            break
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError as exc:
            raise ToolError(f"ไฟล์ว่าง / the file is empty: {path}") from exc
        except pd.errors.ParserError as exc:
            raise ToolError(f"อ่าน CSV ไม่ได้ / cannot read CSV: {path}") from exc
    if frame is None:
        raise ToolError(
            f"ถอดรหัสตัวอักษรไม่ได้ (ลอง UTF-8 และ cp874) / cannot decode the file as UTF-8 or cp874: {path}"
        )

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
