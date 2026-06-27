from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from scrape_quality_pipeline.pipeline import run_scrape

app = typer.Typer(help="Validated scraping pipeline demo.")


@app.command()
def books(
    pages: Annotated[int, typer.Option(help="Number of catalogue pages to scrape.")] = 1,
    out: Annotated[Path, typer.Option(help="Output file path.")] = Path("examples/books.csv"),
    format: Annotated[str, typer.Option(help="Export format: csv or jsonl.")] = "csv",
) -> None:
    """Scrape books.toscrape.com and validate the resulting dataset."""
    result = asyncio.run(run_scrape(pages=pages, output_path=out, file_format=format))
    typer.echo(f"Scraped {len(result.frame)} records")
    typer.echo(f"Exported to {result.exported_to}")
