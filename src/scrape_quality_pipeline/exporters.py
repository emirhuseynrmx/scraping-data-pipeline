from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_frame(frame: pd.DataFrame, output_path: Path, file_format: str) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_format = file_format.lower()

    if normalized_format == "csv":
        frame.to_csv(output_path, index=False)
    elif normalized_format == "jsonl":
        frame.to_json(output_path, orient="records", lines=True, date_format="iso")
    elif normalized_format in {"xlsx", "excel"}:
        frame.to_excel(output_path, index=False, engine="openpyxl")
    elif normalized_format == "parquet":
        frame.to_parquet(output_path, index=False, engine="pyarrow")
    else:
        raise ValueError(f"Unsupported export format: {file_format}")

    return output_path
