from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class BookRecord:
    title: str
    price_gbp: float
    rating: str
    in_stock: bool
    product_url: str
    source_url: str
    scraped_at: datetime

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
