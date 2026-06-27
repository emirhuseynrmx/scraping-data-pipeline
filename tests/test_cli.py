from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd
from typer.testing import CliRunner

import scrape_quality_pipeline.cli as cli


def test_cli_books_command(monkeypatch) -> None:
    async def fake_run_scrape(
        *,
        pages: int,
        output_path: Path,
        file_format: str,
        parser_backend: str,
        config,
    ):
        assert pages == 3
        assert output_path == Path("examples/books.csv")
        assert file_format == "csv"
        assert parser_backend == "selectolax"
        assert config is None
        return SimpleNamespace(frame=pd.DataFrame({"title": ["A", "B"]}), exported_to=output_path)

    monkeypatch.setattr(cli, "run_scrape", fake_run_scrape)

    result = CliRunner().invoke(cli.app, ["--pages", "3"])

    assert result.exit_code == 0
    assert "Scraped 2 records" in result.output
    assert "examples\\books.csv" in result.output or "examples/books.csv" in result.output
