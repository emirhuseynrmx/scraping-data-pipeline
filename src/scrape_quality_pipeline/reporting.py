from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class ScrapeReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    records: int = Field(ge=0)
    columns: int = Field(ge=0)
    in_stock_count: int = Field(ge=0)
    average_price: float = Field(ge=0)
    min_price: float = Field(ge=0)
    max_price: float = Field(ge=0)
    rating_counts: dict[str, int]
    source_pages: int = Field(ge=0)
    sample_records: tuple[dict[str, Any], ...]
    csv_path: str


def expand_frame(frame: pd.DataFrame, rows: int) -> pd.DataFrame:
    """Repeat a validated scrape output to a larger row count."""
    if rows < 1:
        raise ValueError("rows must be >= 1")
    if frame.empty:
        raise ValueError("cannot expand an empty scrape output")

    repeats = (rows + len(frame) - 1) // len(frame)
    expanded = pd.concat([frame] * repeats, ignore_index=True).head(rows).copy()
    expanded.index = range(1, len(expanded) + 1)
    return expanded


def build_report(frame: pd.DataFrame, *, title: str, csv_path: Path) -> ScrapeReport:
    price = pd.to_numeric(frame["price_gbp"], errors="coerce")
    return ScrapeReport(
        title=title,
        records=len(frame),
        columns=len(frame.columns),
        in_stock_count=int(frame["in_stock"].astype(bool).sum()),
        average_price=round(float(price.mean()), 2),
        min_price=round(float(price.min()), 2),
        max_price=round(float(price.max()), 2),
        rating_counts={
            str(key): int(value)
            for key, value in frame["rating"].value_counts().sort_index().to_dict().items()
        },
        source_pages=int(frame["source_url"].nunique()),
        sample_records=tuple(frame.head(6).to_dict(orient="records")),
        csv_path=csv_path.as_posix(),
    )


def generate_sample_report(
    csv_path: Path,
    output_dir: Path,
    *,
    title: str = "Scraping Data Quality Report",
    compile_pdf: bool = True,
    rows: int | None = None,
    expanded_csv: Path | None = None,
) -> tuple[Path, Path | None]:
    frame = pd.read_csv(csv_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    report_csv_path = csv_path
    if rows is not None:
        frame = expand_frame(frame, rows)
        report_csv_path = expanded_csv or output_dir / f"scrape_output_{rows}.csv"
        report_csv_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(report_csv_path, index=False)

    report = build_report(frame, title=title, csv_path=report_csv_path)
    typ_path = output_dir / "scraping_report.typ"
    pdf_path = output_dir / "scraping_report.pdf"
    typ_path.write_text(render_typst(report), encoding="utf-8")
    if not compile_pdf:
        return typ_path, None
    typst = shutil.which("typst")
    if typst is None:
        return typ_path, None
    subprocess.run(
        [typst, "compile", typ_path.name, pdf_path.name],
        check=True,
        cwd=output_dir,
    )
    return typ_path, pdf_path


def render_typst(report: ScrapeReport) -> str:
    top_rating = max(report.rating_counts.items(), key=lambda item: item[1], default=("n/a", 0))[0]
    rating_rows = "\n".join(
        _rating_bar_row(rating, count, max(report.rating_counts.values(), default=1))
        for rating, count in report.rating_counts.items()
    )
    sample_rows = "\n".join(_sample_row(record) for record in report.sample_records)
    stock_rate = 0 if report.records == 0 else report.in_stock_count / report.records * 100
    return f"""#set page(margin: 34pt)
#set text(font: "Arial", size: 9.6pt)
#set heading(numbering: none)

#let ink = rgb("#101828")
#let muted = rgb("#667085")
#let accent = rgb("#1457d9")
#let good = rgb("#11845b")
#let warm = rgb("#b54708")
#let panel = rgb("#f7f9fc")
#let line = rgb("#d0d5dd")

#let stat(label, value, color: accent) = block[
  #rect(fill: panel, stroke: line, radius: 4pt, inset: 9pt, width: 100%)[
    #text(size: 7pt, fill: muted, weight: "bold")[#upper(label)]
    #linebreak()
    #text(size: 16pt, fill: color, weight: "bold")[#value]
  ]
]

#rect(fill: rgb("#0b1220"), radius: 6pt, inset: 18pt, width: 100%)[
  #text(fill: white, size: 20pt, weight: "bold")[{_typ_text(report.title)}]
  #linebreak()
  #v(4pt)
  #text(fill: rgb("#dbeafe"), size: 9pt)[Validated public-listing scrape output with typed records,
  Pandera contracts, export traceability, and audit-friendly summary metrics.]
]

#v(12pt)

#grid(columns: (1.2fr, 1fr, 1fr, 1fr), gutter: 7pt)[
  #stat("Rows", "{report.records:,}")
][
  #stat("Columns", "{report.columns}")
][
  #stat("In stock", "{stock_rate:.0f}%", color: good)
][
  #stat("Avg price", "GBP {report.average_price:,.2f}")
]

#v(7pt)

#grid(columns: (1fr, 1fr, 1fr, 1fr), gutter: 7pt)[
  #stat("Minimum", "GBP {report.min_price:,.2f}")
][
  #stat("Maximum", "GBP {report.max_price:,.2f}")
][
  #stat("Source pages", "{report.source_pages}")
][
  #stat("Top rating", "{_typ_text(top_rating)}", color: warm)
]

== Rating Distribution

#block(inset: 9pt, stroke: line, radius: 5pt)[
{rating_rows}
]

== Sample Records

#table(
  columns: (2fr, .7fr, .7fr, .7fr),
  inset: 5pt,
  stroke: line,
  [*Title*], [*Price*], [*Rating*], [*In Stock*],
{sample_rows}
)

== Report Notes

- CSV output: `{_typ_text(report.csv_path)}`
- Pydantic validates each parsed record before export.
- Pandera validates the final dataframe contract.
- Report rows can be scaled from a validated scrape output for load demos.
- Live scraping should keep respectful rate limits and public-page boundaries.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the sample scraping PDF report.")
    parser.add_argument("csv", type=Path, nargs="?", default=Path("examples/books_sample.csv"))
    parser.add_argument("--out", type=Path, default=Path("outputs/sample_report"))
    parser.add_argument("--title", default="Scraping Data Quality Report")
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        help="Scale the report dataset to N rows.",
    )
    parser.add_argument(
        "--expanded-csv",
        type=Path,
        default=None,
        help="Optional path for scaled CSV.",
    )
    args = parser.parse_args()
    typ_path, pdf_path = generate_sample_report(
        args.csv,
        args.out,
        title=args.title,
        compile_pdf=not args.no_pdf,
        rows=args.rows,
        expanded_csv=args.expanded_csv,
    )
    print(f"Wrote {typ_path}")
    if pdf_path is not None:
        print(f"Wrote {pdf_path}")


def _sample_row(record: dict[str, Any]) -> str:
    title = str(record.get("title", ""))
    if len(title) > 42:
        title = f"{title[:39]}..."
    return (
        f"  [{_typ_text(title)}],"
        f" [GBP {float(record.get('price_gbp', 0)):,.2f}],"
        f" [{_typ_text(record.get('rating'))}],"
        f" [{_typ_text(_yes_no(record.get('in_stock')))}],"
    )


def _typ_text(value: Any) -> str:
    text = "" if value is None else str(value)
    replacements = {
        "\\": "\\\\",
        "[": "\\[",
        "]": "\\]",
        "#": "\\#",
        "$": "\\$",
        "@": "\\@",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _yes_no(value: Any) -> str:
    if isinstance(value, str):
        return "Yes" if value.strip().lower() in {"true", "1", "yes"} else "No"
    return "Yes" if bool(value) else "No"


def _rating_bar_row(rating: str, count: int, max_count: int) -> str:
    width = 5 if max_count == 0 else max(5, int(count / max_count * 100))
    return (
        f"#grid(columns: (70pt, 1fr, 28pt), gutter: 8pt)["
        f"#text(weight: \"bold\")[{_typ_text(rating)}]"
        f"][#rect(width: {width}%, height: 7pt, fill: accent, radius: 3pt)]"
        f"[#align(right)[{count}]]\n#v(5pt)"
    )
