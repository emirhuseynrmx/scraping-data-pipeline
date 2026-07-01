from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import scrape_quality_pipeline.reporting as reporting
from scrape_quality_pipeline.reporting import (
    build_report,
    expand_frame,
    generate_sample_report,
    render_typst,
)


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

    assert "Scrape Report" in typst
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


def test_expand_frame_repeats_to_requested_row_count() -> None:
    frame = pd.read_csv("examples/books_sample.csv")

    expanded = expand_frame(frame, 10_000)

    assert len(expanded) == 10_000
    assert expanded.iloc[0]["title"] == frame.iloc[0]["title"]


def test_expand_frame_rejects_invalid_inputs() -> None:
    frame = pd.read_csv("examples/books_sample.csv")

    for rows in (0, -1):
        with pytest.raises(ValueError, match="rows"):
            expand_frame(frame, rows)

    with pytest.raises(ValueError, match="empty"):
        expand_frame(frame.iloc[0:0], 10)


def test_generate_sample_report_writes_scaled_csv(tmp_path: Path) -> None:
    expanded_csv = tmp_path / "scale_10k" / "books_10k.csv"

    typ_path, pdf_path = generate_sample_report(
        Path("examples/books_sample.csv"),
        tmp_path / "out",
        compile_pdf=False,
        rows=100,
        expanded_csv=expanded_csv,
    )

    assert typ_path.exists()
    assert pdf_path is None
    assert len(pd.read_csv(expanded_csv)) == 100
    assert "Rows" in typ_path.read_text(encoding="utf-8")


def test_generate_sample_report_compiles_pdf_when_typst_exists(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], bool, Path]] = []

    def fake_run(command: list[str], *, check: bool, cwd: Path) -> SimpleNamespace:
        calls.append((command, check, cwd))
        (cwd / "scraping_report.pdf").write_bytes(b"%PDF-1.7\n")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(
        reporting.shutil,
        "which",
        lambda name: "typst" if name == "typst" else None,
    )
    monkeypatch.setattr(reporting.subprocess, "run", fake_run)

    typ_path, pdf_path = generate_sample_report(Path("examples/books_sample.csv"), tmp_path)

    assert typ_path.exists()
    assert pdf_path == tmp_path / "scraping_report.pdf"
    assert calls == [
        (["typst", "compile", "scraping_report.typ", "scraping_report.pdf"], True, tmp_path)
    ]


def test_reporting_main_generates_typst_without_pdf(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate-scraping-report",
            "examples/books_sample.csv",
            "--out",
            str(tmp_path),
            "--rows",
            "25",
            "--no-pdf",
        ],
    )

    reporting.main()

    captured = capsys.readouterr()
    assert "Wrote" in captured.out
    assert (tmp_path / "scraping_report.typ").exists()
