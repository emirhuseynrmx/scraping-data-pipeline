from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from scrape_quality_pipeline.models import BookRecord
from scrape_quality_pipeline.schema import validate_books


def test_validate_books_accepts_valid_records() -> None:
    frame = validate_books(
        [
            BookRecord(
                title="Clean Architecture",
                price_gbp=42.0,
                rating="Five",
                in_stock=True,
                product_url="https://example.com/book",
                source_url="https://example.com",
                scraped_at=datetime.now(timezone.utc),
            )
        ]
    )

    assert list(frame.columns) == [
        "title",
        "price_gbp",
        "rating",
        "in_stock",
        "product_url",
        "source_url",
        "scraped_at",
    ]


def test_book_record_rejects_invalid_price() -> None:
    with pytest.raises(ValidationError):
        BookRecord(
            title="Bad Data",
            price_gbp=-1.0,
            rating="Five",
            in_stock=True,
            product_url="https://example.com/book",
            source_url="https://example.com",
            scraped_at=datetime.now(timezone.utc),
        )
