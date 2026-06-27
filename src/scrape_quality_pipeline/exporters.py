from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_frame(frame: pd.DataFrame, output_path: Path, file_format: str) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if file_format == "csv":
        frame.to_csv(output_path, index=False)
    elif file_format == "jsonl":
        frame.to_json(output_path, orient="records", lines=True, date_format="iso")
    else:
        raise ValueError(f"Unsupported export format: {file_format}")

    return output_path
