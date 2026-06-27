from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from scrape_quality_pipeline.exporters import export_frame
from scrape_quality_pipeline.http_client import PoliteHttpClient
from scrape_quality_pipeline.models import BookRecord
from scrape_quality_pipeline.parser import parse_books_page
from scrape_quality_pipeline.schema import validate_books

BASE_URL = "https://books.toscrape.com/catalogue/"


@dataclass(frozen=True)
class ScrapeResult:
    frame: pd.DataFrame
    exported_to: Path | None = None


def catalog_page_url(page_number: int) -> str:
    if page_number < 1:
        raise ValueError("page_number must be >= 1")
    if page_number == 1:
        return "https://books.toscrape.com/index.html"
    return f"{BASE_URL}page-{page_number}.html"


async def scrape_books(client: PoliteHttpClient, *, pages: int = 1) -> pd.DataFrame:
    if pages < 1:
        raise ValueError("pages must be >= 1")

    records: list[BookRecord] = []
    for page_number in range(1, pages + 1):
        source_url = catalog_page_url(page_number)
        html = await client.fetch_text(source_url)
        records.extend(parse_books_page(html, source_url=source_url))

    return validate_books(records)


async def run_scrape(
    *,
    pages: int,
    output_path: Path | None = None,
    file_format: str = "csv",
) -> ScrapeResult:
    async with PoliteHttpClient() as client:
        frame = await scrape_books(client, pages=pages)

    exported_to = export_frame(frame, output_path, file_format) if output_path else None
    return ScrapeResult(frame=frame, exported_to=exported_to)
