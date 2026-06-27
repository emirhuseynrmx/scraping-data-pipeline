from __future__ import annotations

from pathlib import Path

import pytest

from scrape_quality_pipeline.exporters import export_frame
from scrape_quality_pipeline.parser import parse_books_page
from scrape_quality_pipeline.pipeline import catalog_page_url, scrape_books
from scrape_quality_pipeline.schema import validate_books


class FakeClient:
    def __init__(self, html: str) -> None:
        self.html = html
        self.urls: list[str] = []

    async def fetch_text(self, url: str) -> str:
        self.urls.append(url)
        return self.html


def test_catalog_page_url() -> None:
    assert catalog_page_url(1) == "https://books.toscrape.com/index.html"
    assert catalog_page_url(2) == "https://books.toscrape.com/catalogue/page-2.html"


@pytest.mark.asyncio
async def test_scrape_books_uses_client_and_validates_records() -> None:
    html = Path("tests/fixtures/books_page.html").read_text(encoding="utf-8")
    client = FakeClient(html)

    frame = await scrape_books(client, pages=2)  # type: ignore[arg-type]

    assert len(frame) == 4
    assert client.urls == [
        "https://books.toscrape.com/index.html",
        "https://books.toscrape.com/catalogue/page-2.html",
    ]


def test_export_frame_writes_csv_and_jsonl(tmp_path: Path) -> None:
    html = Path("tests/fixtures/books_page.html").read_text(encoding="utf-8")
    records = parse_books_page(
        html,
        source_url="https://books.toscrape.com/index.html",
    )
    frame = validate_books(records)

    csv_path = export_frame(frame, tmp_path / "books.csv", "csv")
    jsonl_path = export_frame(frame, tmp_path / "books.jsonl", "jsonl")

    assert csv_path.read_text(encoding="utf-8").startswith("title,price_gbp")
    assert len(jsonl_path.read_text(encoding="utf-8").splitlines()) == 2


def test_export_frame_rejects_unknown_format(tmp_path: Path) -> None:
    html = Path("tests/fixtures/books_page.html").read_text(encoding="utf-8")
    frame = validate_books(
        parse_books_page(
            html,
            source_url="https://books.toscrape.com/index.html",
        )
    )

    with pytest.raises(ValueError, match="Unsupported export format"):
        export_frame(frame, tmp_path / "books.xml", "xml")
