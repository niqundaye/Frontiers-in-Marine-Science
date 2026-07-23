"""Schema, integrity and descriptive audit for article Table 4."""
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data.csv"
EXPECTED_ROWS = 14
EXPECTED_COLUMNS = ['category', 'parameter', 'symbol', 'value', 'notes']
DATA_STATUS = "论文表格精确转录 / exact article-table transcription"


def main() -> None:
    raw = DATA.read_bytes()
    frame = pd.read_csv(DATA)
    errors = []
    if len(frame) != EXPECTED_ROWS:
        errors.append(f"expected {EXPECTED_ROWS} rows, observed {len(frame)}")
    if list(frame.columns) != EXPECTED_COLUMNS:
        errors.append(f"unexpected columns: {list(frame.columns)}")
    if frame.empty:
        errors.append("table is empty")
    if frame.isna().all(axis=1).any():
        errors.append("one or more rows are entirely null")
    numeric = frame.select_dtypes(include="number")
    if not numeric.empty and not np.isfinite(numeric.to_numpy(float)).all():
        errors.append("non-finite numeric value")
    report = {
        "schema_version": "1.0",
        "table": 4,
        "data_status": DATA_STATUS,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "rows": len(frame),
        "columns": list(frame.columns),
        "numeric_summary": numeric.describe().to_dict(),
        "errors": errors,
        "status": "pass" if not errors else "fail",
    }
    (HERE / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if errors:
        raise ValueError("; ".join(errors))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
