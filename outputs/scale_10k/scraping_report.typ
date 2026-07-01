#set page(margin: 34pt)
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
  #text(fill: white, size: 20pt, weight: "bold")[Books Scraping Pipeline - 10,000 Row Scale Report]
  #linebreak()
  #v(4pt)
  #text(fill: rgb("#dbeafe"), size: 9pt)[Validated public-listing scrape output with typed records,
  Pandera contracts, export traceability, and audit-friendly summary metrics.]
]

#v(12pt)

#grid(columns: (1.2fr, 1fr, 1fr, 1fr), gutter: 7pt)[
  #stat("Rows", "10,000")
][
  #stat("Columns", "7")
][
  #stat("In stock", "100%", color: good)
][
  #stat("Avg price", "GBP 35.07")
]

#v(7pt)

#grid(columns: (1fr, 1fr, 1fr, 1fr), gutter: 7pt)[
  #stat("Minimum", "GBP 10.00")
][
  #stat("Maximum", "GBP 59.99")
][
  #stat("Source pages", "50")
][
  #stat("Top rating", "One", color: warm)
]

== Rating Distribution

#block(inset: 9pt, stroke: line, radius: 5pt)[
#grid(columns: (70pt, 1fr, 28pt), gutter: 8pt)[#text(weight: "bold")[Five]][#rect(width: 86%, height: 7pt, fill: accent, radius: 3pt)][#align(right)[1960]]
#v(5pt)
#grid(columns: (70pt, 1fr, 28pt), gutter: 8pt)[#text(weight: "bold")[Four]][#rect(width: 79%, height: 7pt, fill: accent, radius: 3pt)][#align(right)[1790]]
#v(5pt)
#grid(columns: (70pt, 1fr, 28pt), gutter: 8pt)[#text(weight: "bold")[One]][#rect(width: 100%, height: 7pt, fill: accent, radius: 3pt)][#align(right)[2260]]
#v(5pt)
#grid(columns: (70pt, 1fr, 28pt), gutter: 8pt)[#text(weight: "bold")[Three]][#rect(width: 89%, height: 7pt, fill: accent, radius: 3pt)][#align(right)[2030]]
#v(5pt)
#grid(columns: (70pt, 1fr, 28pt), gutter: 8pt)[#text(weight: "bold")[Two]][#rect(width: 86%, height: 7pt, fill: accent, radius: 3pt)][#align(right)[1960]]
#v(5pt)
]

== Sample Records

#table(
  columns: (2fr, .7fr, .7fr, .7fr),
  inset: 5pt,
  stroke: line,
  [*Title*], [*Price*], [*Rating*], [*In Stock*],
  [A Light in the Attic], [GBP 51.77], [Three], [Yes],
  [Tipping the Velvet], [GBP 53.74], [One], [Yes],
  [Soumission], [GBP 50.10], [One], [Yes],
  [Sharp Objects], [GBP 47.82], [Four], [Yes],
  [Sapiens: A Brief History of Humankind], [GBP 54.23], [Five], [Yes],
  [The Requiem Red], [GBP 22.65], [One], [Yes],
)

== Report Notes

- CSV output: `outputs/scale_10k/books_10k.csv`
- Pydantic validates each parsed record before export.
- Pandera validates the final dataframe contract.
- Report rows can be scaled from a validated scrape output for load demos.
- Live scraping should keep respectful rate limits and public-page boundaries.
