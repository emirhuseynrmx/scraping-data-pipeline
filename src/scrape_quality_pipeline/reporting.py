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
) -> tuple[Path, Path | None]:
    frame = pd.read_csv(csv_path)
    report = build_report(frame, title=title, csv_path=csv_path)
    output_dir.mkdir(parents=True, exist_ok=True)
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
    rating_rows = "\n".join(
        _rating_bar_row(rating, count, max(report.rating_counts.values(), default=1))
        for rating, count in report.rating_counts.items()
    )
    sample_rows = "\n".join(_sample_row(record) for record in report.sample_records)
    stock_rate = 0 if report.records == 0 else report.in_stock_count / report.records * 100
    return f"""#set page(margin: 42pt)
#set text(font: "Arial", size: 10pt)
#set heading(numbering: none)

#let accent = rgb("#1457d9")
#let good = rgb("#11845b")
#let muted = rgb("#667085")
#let panel = rgb("#f6f8fb")

#let stat(label, value, color: accent) = block[
  #rect(fill: panel, radius: 5pt, inset: 10pt, width: 100%)[
    #text(size: 8pt, fill: muted, weight: "bold")[#upper(label)]
    #linebreak()
    #text(size: 18pt, fill: color, weight: "bold")[#value]
  ]
]

= {_typ_text(report.title)}

#text(fill: muted)[
  Public listing extraction report with row counts, data contracts, price range,
  availability, rating distribution, and sample records.
]

#grid(columns: (1fr, 1fr, 1fr, 1fr), gutter: 8pt)[
  #stat("Records", "{report.records}")
][
  #stat("Columns", "{report.columns}")
][
  #stat("In stock", "{stock_rate:.0f}%", color: good)
][
  #stat("Avg price", "GBP {report.average_price:,.2f}")
]

== Price Range

#grid(columns: (1fr, 1fr, 1fr), gutter: 8pt)[
  #stat("Minimum", "GBP {report.min_price:,.2f}")
][
  #stat("Maximum", "GBP {report.max_price:,.2f}")
][
  #stat("Source pages", "{report.source_pages}")
]

== Rating Distribution

#block(inset: 8pt, stroke: rgb("#d0d5dd"), radius: 5pt)[
{rating_rows}
]

== Sample Records

#table(
  columns: (1.8fr, .8fr, .8fr, .8fr),
  inset: 5pt,
  stroke: rgb("#d0d5dd"),
  [*Title*], [*Price*], [*Rating*], [*In Stock*],
{sample_rows}
)

== Report Notes

- CSV output: `{_typ_text(report.csv_path)}`
- Pydantic validates each parsed record before export.
- Pandera validates the final dataframe contract.
- This template is for public pages with stable selectors and respectful rate limits.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the sample scraping PDF report.")
    parser.add_argument("csv", type=Path, nargs="?", default=Path("examples/books_sample.csv"))
    parser.add_argument("--out", type=Path, default=Path("outputs/sample_report"))
    parser.add_argument("--title", default="Scraping Data Quality Report")
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()
    typ_path, pdf_path = generate_sample_report(
        args.csv,
        args.out,
        title=args.title,
        compile_pdf=not args.no_pdf,
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
