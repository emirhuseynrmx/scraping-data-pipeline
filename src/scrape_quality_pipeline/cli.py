from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.logging import RichHandler

from scrape_quality_pipeline.configs import load_scraper_config
from scrape_quality_pipeline.pipeline import run_scrape

app = typer.Typer(help="Validated scraping pipeline demo.")


@app.command()
def books(
    pages: Annotated[int, typer.Option(help="Number of catalogue pages to scrape.")] = 1,
    out: Annotated[Path, typer.Option(help="Output file path.")] = Path("examples/books.csv"),
    format: Annotated[
        str,
        typer.Option(help="Export format: csv, jsonl, xlsx, or parquet."),
    ] = "csv",
    parser: Annotated[
        str,
        typer.Option(help="Parser backend: selectolax or beautifulsoup."),
    ] = "selectolax",
    config: Annotated[
        Path | None,
        typer.Option(help="Optional ScraperConfig JSON path."),
    ] = None,
) -> None:
    """Scrape books.toscrape.com and validate the resulting dataset."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    scraper_config = load_scraper_config(config) if config else None
    result = asyncio.run(
        run_scrape(
            pages=pages,
            output_path=out,
            file_format=format,
            parser_backend=parser,
            config=scraper_config,
        )
    )
    typer.echo(f"Scraped {len(result.frame)} records")
    typer.echo(f"Exported to {result.exported_to}")
    typer.echo(f"Manifest: {result.manifest_path}")
