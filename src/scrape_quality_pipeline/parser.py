from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from scrape_quality_pipeline.models import BookRecord

PRICE_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)")
RATINGS = {"One", "Two", "Three", "Four", "Five"}


class ParseError(ValueError):
    """Raised when expected page structure is missing."""


def _required_text(node, selector: str) -> str:
    found = node.css_first(selector)
    if found is None:
        raise ParseError(f"Missing selector: {selector}")
    return found.text(strip=True)


def _parse_price(raw_price: str) -> float:
    match = PRICE_RE.search(raw_price)
    if not match:
        raise ParseError(f"Could not parse price: {raw_price!r}")
    return float(match.group(1))


def _parse_rating(classes: str) -> str:
    parts = set(classes.split())
    rating = parts & RATINGS
    if not rating:
        raise ParseError(f"Could not parse rating from classes: {classes!r}")
    return rating.pop()


def parse_books_page(
    html: str,
    *,
    source_url: str,
    scraped_at: datetime | None = None,
) -> list[BookRecord]:
    parser = HTMLParser(html)
    articles = parser.css("article.product_pod")
    if not articles:
        raise ParseError("No product cards found on page")

    timestamp = scraped_at or datetime.now(UTC)
    records: list[BookRecord] = []

    for article in articles:
        link = article.css_first("h3 a")
        rating = article.css_first("p.star-rating")
        if link is None or rating is None:
            raise ParseError("Product card missing title link or rating")

        title = link.attributes.get("title", "").strip()
        href = link.attributes.get("href", "").strip()
        rating_value = _parse_rating(rating.attributes.get("class", ""))
        price = _parse_price(_required_text(article, ".price_color"))
        availability = _required_text(article, ".availability").lower()

        if not title or not href:
            raise ParseError("Product card missing title or href")

        records.append(
            BookRecord(
                title=title,
                price_gbp=price,
                rating=rating_value,
                in_stock="in stock" in availability,
                product_url=urljoin(source_url, href),
                source_url=source_url,
                scraped_at=timestamp,
            )
        )

    return records
