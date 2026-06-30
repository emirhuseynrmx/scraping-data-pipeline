from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag
from selectolax.parser import HTMLParser
from selectolax.parser import Node as SelectolaxNode

from scrape_quality_pipeline.configs import books_to_scrape_config
from scrape_quality_pipeline.models import BookRecord, ProductRecord, ScraperConfig

PRICE_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)")


class ParseError(ValueError):
    """Raised when expected page structure is missing."""


class HtmlNode(Protocol):
    def css(self, selector: str) -> list[HtmlNode]: ...

    def css_first(self, selector: str) -> HtmlNode | None: ...

    def text(self) -> str: ...

    def attr(self, name: str) -> str: ...


class SelectolaxHtmlNode:
    def __init__(self, node: HTMLParser | SelectolaxNode) -> None:
        self.node = node

    def css(self, selector: str) -> list[HtmlNode]:
        return [SelectolaxHtmlNode(node) for node in self.node.css(selector)]

    def css_first(self, selector: str) -> HtmlNode | None:
        node = self.node.css_first(selector)
        return SelectolaxHtmlNode(node) if node is not None else None

    def text(self) -> str:
        return self.node.text(strip=True)

    def attr(self, name: str) -> str:
        return self.node.attributes.get(name, "").strip()


class BeautifulSoupHtmlNode:
    def __init__(self, node: BeautifulSoup | Tag) -> None:
        self.node = node

    def css(self, selector: str) -> list[HtmlNode]:
        return [BeautifulSoupHtmlNode(node) for node in self.node.select(selector)]

    def css_first(self, selector: str) -> HtmlNode | None:
        node = self.node.select_one(selector)
        return BeautifulSoupHtmlNode(node) if node is not None else None

    def text(self) -> str:
        return self.node.get_text(strip=True)

    def attr(self, name: str) -> str:
        value = self.node.get(name, "")
        if isinstance(value, list):
            return " ".join(value).strip()
        return str(value).strip()


def _parse_html(html: str, backend: str) -> HtmlNode:
    if backend == "selectolax":
        return SelectolaxHtmlNode(HTMLParser(html))
    if backend == "beautifulsoup":
        return BeautifulSoupHtmlNode(BeautifulSoup(html, "lxml"))
    raise ParseError(f"Unsupported parser backend: {backend}")


def _required_text(node: HtmlNode, selector: str) -> str:
    found = node.css_first(selector)
    if found is None:
        raise ParseError(f"Missing selector: {selector}")
    return found.text()


def _parse_price(raw_price: str) -> float:
    match = PRICE_RE.search(raw_price)
    if not match:
        raise ParseError(f"Could not parse price: {raw_price!r}")
    return float(match.group(1))


def _parse_rating(classes: str, allowed_ratings: tuple[str, ...]) -> str:
    parts = set(classes.split())
    rating = parts & set(allowed_ratings)
    if not rating:
        raise ParseError(f"Could not parse rating from classes: {classes!r}")
    return rating.pop()


def parse_product_page(
    html: str,
    *,
    source_url: str,
    config: ScraperConfig,
    scraped_at: datetime | None = None,
) -> list[BookRecord]:
    parser = _parse_html(html, config.parser_backend)
    items = parser.css(config.selectors.item)
    if not items:
        raise ParseError(f"No product cards found with selector: {config.selectors.item}")

    timestamp = scraped_at or datetime.now(timezone.utc)
    records: list[BookRecord] = []

    for item in items:
        link = item.css_first(config.selectors.link)
        title_node = item.css_first(config.selectors.title)
        rating = item.css_first(config.selectors.rating)
        if link is None or rating is None:
            raise ParseError("Product card missing title link or rating")

        title = ""
        if title_node is not None:
            title = (
                title_node.text()
                if config.selectors.title_attribute == "text"
                else title_node.attr(config.selectors.title_attribute)
            )
        if not title and title_node is not None:
            title = title_node.text()
        href = link.attr(config.selectors.link_attribute)
        rating_value = _parse_rating(
            rating.attr(config.selectors.rating_attribute),
            config.allowed_ratings,
        )
        price = _parse_price(_required_text(item, config.selectors.price))
        availability = _required_text(item, config.selectors.availability).lower()

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


def parse_product_listing(
    html: str,
    *,
    source_url: str,
    config: ScraperConfig,
    scraped_at: datetime | None = None,
) -> list[ProductRecord]:
    parser = _parse_html(html, config.parser_backend)
    items = parser.css(config.selectors.item)
    if not items:
        raise ParseError(f"No product cards found with selector: {config.selectors.item}")

    timestamp = scraped_at or datetime.now(timezone.utc)
    records: list[ProductRecord] = []

    for item in items:
        link = item.css_first("a.title")
        if link is None:
            continue
        name = link.attr("title") or link.text()
        href = link.attr("href")
        if not name or not href:
            continue

        price_span = item.css_first("h4.price span")
        if price_span is None:
            continue
        try:
            price = _parse_price(price_span.text())
        except ParseError:
            continue

        desc_node = item.css_first("p.description")
        description = desc_node.text() if desc_node else ""

        stars = len(item.css(".ws-icon-star"))

        review_node = item.css_first(".review-count span")
        try:
            review_count = int(review_node.text()) if review_node else 0
        except (ValueError, TypeError):
            review_count = 0

        product_url = href if href.startswith("http") else f"https://webscraper.io{href}"

        records.append(
            ProductRecord(
                name=name,
                price_usd=price,
                description=description,
                rating=stars,
                review_count=review_count,
                product_url=product_url,
                source_url=source_url,
                scraped_at=timestamp,
            )
        )

    return records


def parse_books_page(
    html: str,
    *,
    source_url: str,
    scraped_at: datetime | None = None,
    parser_backend: str = "selectolax",
) -> list[BookRecord]:
    return parse_product_page(
        html,
        source_url=source_url,
        config=books_to_scrape_config(parser_backend=parser_backend),
        scraped_at=scraped_at,
    )
