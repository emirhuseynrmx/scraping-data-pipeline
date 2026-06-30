from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import pandera.pandas as pa

from scrape_quality_pipeline.models import BookRecord

BOOK_SCHEMA = pa.DataFrameSchema(
    {
        "title": pa.Column(str, nullable=False),
        "price_gbp": pa.Column(float, checks=pa.Check.gt(0), nullable=False),
        "rating": pa.Column(str, checks=pa.Check.isin(["One", "Two", "Three", "Four", "Five"])),
        "in_stock": pa.Column(bool, nullable=False),
        "product_url": pa.Column(
            str,
            checks=pa.Check(
                lambda s: s.str.startswith(("http://", "https://")),
                element_wise=False,
            ),
            nullable=False,
        ),
        "source_url": pa.Column(
            str,
            checks=pa.Check(
                lambda s: s.str.startswith(("http://", "https://")),
                element_wise=False,
            ),
            nullable=False,
        ),
        "scraped_at": pa.Column(pa.DateTime, nullable=False),
    },
    coerce=True,
    strict=True,
)


def records_to_frame(records: Iterable[BookRecord]) -> pd.DataFrame:
    return pd.DataFrame([record.to_dict() for record in records])


def validate_books(records: Iterable[BookRecord]) -> pd.DataFrame:
    frame = records_to_frame(records)
    if frame.empty:
        return pd.DataFrame(columns=list(BOOK_SCHEMA.columns.keys()))
    return BOOK_SCHEMA.validate(frame, lazy=True)
