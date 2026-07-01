from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

import scrape_quality_pipeline.pipeline as pipeline
from scrape_quality_pipeline.configs import books_to_scrape_config, webscraper_laptops_config
from scrape_quality_pipeline.exporters import export_frame
from scrape_quality_pipeline.parser import parse_books_page
from scrape_quality_pipeline.pipeline import (
    BaseScraper,
    build_scrape_manifest,
    catalog_page_url,
    run_products_scrape,
    run_scrape,
    scrape_books,
    scrape_pages,
    scrape_product_pages,
    write_manifest,
)
from scrape_quality_pipeline.schema import validate_books, validate_products

LAPTOP_HTML = """
<div class="card thumbnail">
  <a class="title"
     href="/test-sites/e-commerce/allinone/product/1"
     title="Lenovo ThinkPad X1">ThinkPad</a>
  <h4 class="price"><span>$1299.99</span></h4>
  <p class="description">Business ultrabook</p>
  <span class="ws-icon-star"></span><span class="ws-icon-star"></span>
  <p class="review-count"><span>12</span></p>
</div>
"""


class FakeClient:
    def __init__(self, html: str) -> None:
        self.html = html
        self.urls: list[str] = []

    async def fetch_text(self, url: str) -> str:
        self.urls.append(url)
        return self.html


class TimestampClient(FakeClient):
    async def fetch_text(self, url: str) -> str:
        self.urls.append(url)
        return self.html


class FailingOnceClient(FakeClient):
    async def fetch_text(self, url: str) -> str:
        self.urls.append(url)
        if len(self.urls) == 1:
            raise RuntimeError("temporary failure")
        return self.html


class FakeContextClient:
    def __init__(self, html: str) -> None:
        self.client = FakeClient(html)

    async def __aenter__(self) -> FakeClient:
        return self.client

    async def __aexit__(self, *_exc_info: object) -> None:
        return None


def test_catalog_page_url() -> None:
    assert catalog_page_url(1) == "https://books.toscrape.com/index.html"
    assert catalog_page_url(2) == "https://books.toscrape.com/catalogue/page-2.html"


def test_catalog_page_url_rejects_invalid_page() -> None:
    with pytest.raises(ValueError, match="page_number"):
        catalog_page_url(0)


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


@pytest.mark.asyncio
async def test_base_scraper_uses_config_driven_pages() -> None:
    html = Path("tests/fixtures/books_page.html").read_text(encoding="utf-8")
    client = FakeClient(html)
    scraper = BaseScraper(client, books_to_scrape_config())

    frame = await scraper.scrape(pages=1)

    assert len(frame) == 2
    assert client.urls == ["https://books.toscrape.com/index.html"]


@pytest.mark.asyncio
async def test_scrape_pages_rejects_invalid_page_count() -> None:
    with pytest.raises(ValueError, match="pages"):
        await scrape_pages(FakeClient(""), config=books_to_scrape_config(), pages=0)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_scrape_pages_skips_failed_pages() -> None:
    html = Path("tests/fixtures/books_page.html").read_text(encoding="utf-8")
    client = FailingOnceClient(html)

    frame = await scrape_pages(client, config=books_to_scrape_config(), pages=2)  # type: ignore[arg-type]

    assert len(frame) == 2
    assert len(client.urls) == 2


@pytest.mark.asyncio
async def test_scrape_product_pages_parses_laptop_listing() -> None:
    client = FakeClient(LAPTOP_HTML)

    frame = await scrape_product_pages(
        client,  # type: ignore[arg-type]
        config=webscraper_laptops_config(),
        pages=1,
    )

    assert len(frame) == 1
    assert frame.loc[0, "name"] == "Lenovo ThinkPad X1"
    assert frame.loc[0, "review_count"] == 12


@pytest.mark.asyncio
async def test_scrape_product_pages_rejects_invalid_page_count() -> None:
    with pytest.raises(ValueError, match="pages"):
        await scrape_product_pages(
            FakeClient(""),  # type: ignore[arg-type]
            config=webscraper_laptops_config(),
            pages=0,
        )


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


def test_export_frame_writes_excel_and_parquet(tmp_path: Path) -> None:
    html = Path("tests/fixtures/books_page.html").read_text(encoding="utf-8")
    frame = validate_books(
        parse_books_page(
            html,
            source_url="https://books.toscrape.com/index.html",
        )
    )

    xlsx_path = export_frame(frame, tmp_path / "books.xlsx", "xlsx")
    parquet_path = export_frame(frame, tmp_path / "books.parquet", "parquet")

    assert xlsx_path.exists()
    assert parquet_path.exists()


def test_validate_products_accepts_laptop_records() -> None:
    from scrape_quality_pipeline.parser import parse_product_listing

    frame = validate_products(
        parse_product_listing(
            LAPTOP_HTML,
            source_url="https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops",
            config=webscraper_laptops_config(),
        )
    )

    assert list(frame.columns) == [
        "name",
        "price_usd",
        "description",
        "rating",
        "review_count",
        "product_url",
        "source_url",
        "scraped_at",
    ]


def test_parse_books_page_uses_page_level_timestamp() -> None:
    html = Path("tests/fixtures/books_page.html").read_text(encoding="utf-8")
    scraped_at = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)

    records = parse_books_page(
        html,
        source_url="https://books.toscrape.com/index.html",
        scraped_at=scraped_at,
    )

    assert {record.scraped_at for record in records} == {scraped_at}


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


def test_scrape_manifest_records_schema_and_sources(tmp_path: Path) -> None:
    html = Path("tests/fixtures/books_page.html").read_text(encoding="utf-8")
    frame = validate_books(
        parse_books_page(
            html,
            source_url="https://books.toscrape.com/index.html",
        )
    )

    manifest = build_scrape_manifest(
        frame=frame,
        config=books_to_scrape_config(),
        pages=1,
        exported_to=tmp_path / "books.csv",
    )

    assert manifest.records_exported == 2
    assert manifest.source_pages == ["https://books.toscrape.com/index.html"]
    assert "price_gbp" in manifest.schema_columns


def test_write_manifest_creates_parent_directory(tmp_path: Path) -> None:
    html = Path("tests/fixtures/books_page.html").read_text(encoding="utf-8")
    frame = validate_books(parse_books_page(html, source_url="https://books.toscrape.com/index.html"))
    manifest = build_scrape_manifest(
        frame=frame,
        config=books_to_scrape_config(),
        pages=1,
        exported_to=None,
    )

    path = write_manifest(manifest, tmp_path / "nested" / "manifest.json")

    assert path.exists()
    assert "books-to-scrape" in path.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_run_scrape_exports_and_writes_manifest(monkeypatch, tmp_path: Path) -> None:
    html = Path("tests/fixtures/books_page.html").read_text(encoding="utf-8")
    monkeypatch.setattr(pipeline, "PoliteHttpClient", lambda: FakeContextClient(html))

    result = await run_scrape(
        pages=1,
        output_path=tmp_path / "books.csv",
        file_format="csv",
        show_progress=False,
    )

    assert len(result.frame) == 2
    assert result.exported_to == tmp_path / "books.csv"
    assert result.manifest_path == tmp_path / "scrape_manifest.json"


@pytest.mark.asyncio
async def test_run_products_scrape_exports_and_writes_manifest(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pipeline, "PoliteHttpClient", lambda: FakeContextClient(LAPTOP_HTML))

    result = await run_products_scrape(
        pages=1,
        output_path=tmp_path / "laptops.csv",
        file_format="csv",
        config=webscraper_laptops_config(),
        show_progress=False,
    )

    assert len(result.frame) == 1
    assert result.exported_to == tmp_path / "laptops.csv"
    assert result.manifest_path == tmp_path / "laptops_manifest.json"
