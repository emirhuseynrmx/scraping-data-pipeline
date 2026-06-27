from __future__ import annotations

from datetime import datetime

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
