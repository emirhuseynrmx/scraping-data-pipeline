from __future__ import annotations

from pathlib import Path

import pandas as pd

from scrape_quality_pipeline.reporting import build_report, generate_sample_report, render_typst


def test_build_report_summarizes_scraped_frame() -> None:
    frame = pd.read_csv("examples/books_sample.csv")

    report = build_report(frame, title="Scrape Report", csv_path=Path("examples/books_sample.csv"))

    assert report.records == len(frame)
    assert report.average_price > 0
    assert report.source_pages >= 1


def test_render_typst_contains_delivery_sections() -> None:
    frame = pd.read_csv("examples/books_sample.csv")
    report = build_report(frame, title="Scrape Report", csv_path=Path("examples/books_sample.csv"))
    typst = render_typst(report)

    assert "= Scrape Report" in typst
    assert "Rating Distribution" in typst
    assert "Sample Records" in typst


def test_generate_sample_report_writes_typst_without_pdf(tmp_path: Path) -> None:
    typ_path, pdf_path = generate_sample_report(
        Path("examples/books_sample.csv"),
        tmp_path / "out",
        compile_pdf=False,
    )

    assert typ_path.exists()
    assert pdf_path is None
    assert "Scraping Data Quality Report" in typ_path.read_text(encoding="utf-8")
