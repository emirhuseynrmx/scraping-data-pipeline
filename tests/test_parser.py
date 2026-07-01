from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from scrape_quality_pipeline.configs import webscraper_laptops_config
from scrape_quality_pipeline.parser import (
    ParseError,
    _parse_html,
    parse_books_page,
    parse_product_listing,
    parse_product_page,
)

LAPTOP_HTML = """
<html>
  <body>
    <div class="card thumbnail">
      <a class="title"
         href="/test-sites/e-commerce/allinone/product/1"
         title="Lenovo ThinkPad X1">ThinkPad</a>
      <h4 class="price"><span>$1299.99</span></h4>
      <p class="description">Business ultrabook</p>
      <span class="ws-icon-star"></span><span class="ws-icon-star"></span>
      <p class="review-count"><span>12</span></p>
    </div>
    <div class="card thumbnail">
      <a class="title" href="https://example.com/laptop" title="Dell XPS 13">Dell XPS 13</a>
      <h4 class="price"><span>$999.50</span></h4>
      <p class="description">Compact laptop</p>
      <span class="ws-icon-star"></span>
      <span class="ws-icon-star"></span>
      <span class="ws-icon-star"></span>
      <p class="review-count"><span>not-a-number</span></p>
    </div>
    <div class="card thumbnail">
      <a class="title" href="/broken"></a>
      <h4 class="price"><span>$10.00</span></h4>
    </div>
    <div class="card thumbnail">
      <a class="title" href="/bad-price" title="Broken price">Broken price</a>
      <h4 class="price"><span>contact us</span></h4>
    </div>
  </body>
</html>
"""


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


def test_parse_product_listing_extracts_laptop_records() -> None:
    records = parse_product_listing(
        LAPTOP_HTML,
        source_url="https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops",
        config=webscraper_laptops_config(),
    )

    assert len(records) == 2
    assert records[0].name == "Lenovo ThinkPad X1"
    assert records[0].price_usd == 1299.99
    assert records[0].rating == 2
    assert records[0].review_count == 12
    assert str(records[0].product_url) == "https://webscraper.io/test-sites/e-commerce/allinone/product/1"
    assert records[1].review_count == 0


def test_parse_product_listing_rejects_empty_listing() -> None:
    with pytest.raises(ParseError, match="No product cards"):
        parse_product_listing(
            "<html></html>",
            source_url="https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops",
            config=webscraper_laptops_config(),
        )


def test_parse_product_page_reports_missing_required_book_fields() -> None:
    config = webscraper_laptops_config()
    bad_html = '<article class="product_pod"><h3><a href="book.html">Book</a></h3></article>'

    with pytest.raises(ParseError, match="missing title link or rating"):
        parse_product_page(
            bad_html,
            source_url="https://books.toscrape.com/index.html",
            config=config.model_copy(
                update={
                    "selectors": config.selectors.model_copy(
                        update={
                            "item": "article.product_pod",
                            "link": "h3 a",
                            "title": "h3 a",
                            "rating": "p.star-rating",
                        }
                    )
                }
            ),
        )


def test_parse_product_page_rejects_invalid_rating_and_price() -> None:
    html = """
    <article class="product_pod">
      <h3><a href="book.html" title="Book">Book</a></h3>
      <p class="star-rating Unknown"></p>
      <p class="price_color">free</p>
      <p class="availability">In stock</p>
    </article>
    """

    with pytest.raises(ParseError, match="Could not parse rating"):
        parse_books_page(html, source_url="https://books.toscrape.com/index.html")


def test_parse_html_rejects_unknown_backend() -> None:
    with pytest.raises(ParseError, match="Unsupported parser backend"):
        _parse_html("<html></html>", "unknown")
