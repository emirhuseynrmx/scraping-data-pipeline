from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from scrape_quality_pipeline.parser import parse_books_page


def test_parse_books_page_extracts_expected_records() -> None:
    html = Path("tests/fixtures/books_page.html").read_text(encoding="utf-8")
    source_url = "https://books.toscrape.com/index.html"
    scraped_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

    records = parse_books_page(html, source_url=source_url, scraped_at=scraped_at)

    assert len(records) == 2
    assert records[0].title == "A Light in the Attic"
    assert records[0].price_gbp == 51.77
    assert records[0].rating == "Three"
    assert records[0].in_stock is True
    assert str(records[0].product_url) == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    assert records[0].scraped_at == scraped_at


def test_parse_books_page_supports_beautifulsoup_backend() -> None:
    html = Path("tests/fixtures/books_page.html").read_text(encoding="utf-8")

    records = parse_books_page(
        html,
        source_url="https://books.toscrape.com/index.html",
        parser_backend="beautifulsoup",
    )

    assert len(records) == 2
    assert records[1].title == "Tipping the Velvet"
