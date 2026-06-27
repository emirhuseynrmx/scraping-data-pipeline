from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from pydantic.functional_validators import field_validator


class BookRecord(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    title: str
    price_gbp: float = Field(gt=0)
    rating: str
    in_stock: bool
    product_url: HttpUrl
    source_url: HttpUrl
    scraped_at: datetime

    def to_dict(self) -> dict[str, object]:
        data = self.model_dump(mode="python")
        data["product_url"] = str(self.product_url)
        data["source_url"] = str(self.source_url)
        return data

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: str) -> str:
        allowed = {"One", "Two", "Three", "Four", "Five"}
        if value not in allowed:
            raise ValueError(f"rating must be one of {sorted(allowed)}")
        return value


class ProductSelectors(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    item: str
    title: str
    price: str
    rating: str
    availability: str
    link: str
    title_attribute: str = "title"
    link_attribute: str = "href"
    rating_attribute: str = "class"


class ScraperConfig(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    name: str
    start_url: HttpUrl
    page_url_template: str | None = None
    selectors: ProductSelectors
    parser_backend: Literal["selectolax", "beautifulsoup"] = "selectolax"
    allowed_ratings: tuple[str, ...] = ("One", "Two", "Three", "Four", "Five")

    def page_url(self, page_number: int) -> str:
        if page_number < 1:
            raise ValueError("page_number must be >= 1")
        if page_number == 1 or self.page_url_template is None:
            return str(self.start_url)
        return self.page_url_template.format(page=page_number)
