from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from scrape_quality_pipeline.configs import books_to_scrape_config
from scrape_quality_pipeline.exporters import export_frame
from scrape_quality_pipeline.http_client import PoliteHttpClient
from scrape_quality_pipeline.models import BookRecord, ScrapeManifest, ScraperConfig
from scrape_quality_pipeline.parser import parse_product_page
from scrape_quality_pipeline.schema import validate_books

BASE_URL = "https://books.toscrape.com/catalogue/"
LOGGER = logging.getLogger(__name__)
CONSOLE = Console()


@dataclass(frozen=True)
class ScrapeResult:
    frame: pd.DataFrame
    exported_to: Path | None = None
    manifest_path: Path | None = None


class BaseScraper:
    def __init__(self, client: PoliteHttpClient, config: ScraperConfig) -> None:
        self.client = client
        self.config = config

    async def scrape(self, *, pages: int = 1, show_progress: bool = False) -> pd.DataFrame:
        return await scrape_pages(
            self.client,
            config=self.config,
            pages=pages,
            show_progress=show_progress,
        )


def catalog_page_url(page_number: int) -> str:
    if page_number < 1:
        raise ValueError("page_number must be >= 1")
    if page_number == 1:
        return "https://books.toscrape.com/index.html"
    return f"{BASE_URL}page-{page_number}.html"


async def scrape_books(client: PoliteHttpClient, *, pages: int = 1) -> pd.DataFrame:
    return await scrape_pages(
        client,
        config=books_to_scrape_config(),
        pages=pages,
        show_progress=False,
    )


async def scrape_pages(
    client: PoliteHttpClient,
    *,
    config: ScraperConfig,
    pages: int = 1,
    show_progress: bool = False,
) -> pd.DataFrame:
    if pages < 1:
        raise ValueError("pages must be >= 1")

    records: list[BookRecord] = []
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=CONSOLE,
        disable=not show_progress,
    )
    with progress:
        task_id = progress.add_task(f"Scraping {config.name}", total=pages)
        for page_number in range(1, pages + 1):
            source_url = config.page_url(page_number)
            try:
                html = await client.fetch_text(source_url)
                scraped_at = datetime.now(timezone.utc)
                records.extend(
                    parse_product_page(
                        html,
                        source_url=source_url,
                        config=config,
                        scraped_at=scraped_at,
                    )
                )
                progress.advance(task_id)
            except Exception:
                LOGGER.exception("Failed to scrape page %s: %s", page_number, source_url)
                progress.advance(task_id)
                continue

    return validate_books(records)


async def run_scrape(
    *,
    pages: int,
    output_path: Path | None = None,
    file_format: str = "csv",
    parser_backend: Literal["selectolax", "beautifulsoup"] = "selectolax",
    config: ScraperConfig | None = None,
    show_progress: bool = True,
) -> ScrapeResult:
    scraper_config = config or books_to_scrape_config(parser_backend=parser_backend)
    async with PoliteHttpClient() as client:
        frame = await scrape_pages(
            client,
            config=scraper_config,
            pages=pages,
            show_progress=show_progress,
        )

    exported_to = export_frame(frame, output_path, file_format) if output_path else None
    manifest_path = None
    if exported_to is not None:
        manifest_path = write_manifest(
            build_scrape_manifest(
                frame=frame,
                config=scraper_config,
                pages=pages,
                exported_to=exported_to,
            ),
            exported_to.parent / "scrape_manifest.json",
        )
    return ScrapeResult(frame=frame, exported_to=exported_to, manifest_path=manifest_path)


def build_scrape_manifest(
    *,
    frame: pd.DataFrame,
    config: ScraperConfig,
    pages: int,
    exported_to: Path | None,
) -> ScrapeManifest:
    return ScrapeManifest(
        run_id=uuid4().hex,
        generated_at=datetime.now(timezone.utc),
        scraper_name=config.name,
        parser_backend=config.parser_backend,
        pages_requested=pages,
        records_exported=len(frame),
        source_pages=sorted(str(url) for url in frame["source_url"].unique()),
        output_file=exported_to.as_posix() if exported_to else None,
        schema_columns=[str(column) for column in frame.columns],
        notes=[
            "Only public listing pages are used.",
            "Selectors come from the configured scraper contract.",
            "Exports are validated with Pandera before handoff.",
        ],
    )


def write_manifest(manifest: ScrapeManifest, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return path
