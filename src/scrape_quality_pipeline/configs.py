from __future__ import annotations

from pathlib import Path
from typing import Literal

from scrape_quality_pipeline.models import ProductSelectors, ScraperConfig


def books_to_scrape_config(
    *,
    parser_backend: Literal["selectolax", "beautifulsoup"] = "selectolax",
) -> ScraperConfig:
    return ScraperConfig(
        name="books-to-scrape",
        start_url="https://books.toscrape.com/index.html",
        page_url_template="https://books.toscrape.com/catalogue/page-{page}.html",
        parser_backend=parser_backend,
        selectors=ProductSelectors(
            item="article.product_pod",
            title="h3 a",
            link="h3 a",
            rating="p.star-rating",
            price=".price_color",
            availability=".availability",
        ),
    )


def load_scraper_config(path: Path) -> ScraperConfig:
    return ScraperConfig.model_validate_json(path.read_text(encoding="utf-8"))
