#set page(margin: 42pt)
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

= Scraping Data Quality Report

#text(fill: muted)[
  Public listing extraction report with row counts, data contracts, price range,
  availability, rating distribution, and sample records.
]

#grid(columns: (1fr, 1fr, 1fr, 1fr), gutter: 8pt)[
  #stat("Records", "20")
][
  #stat("Columns", "7")
][
  #stat("In stock", "100%", color: good)
][
  #stat("Avg price", "GBP 38.05")
]

== Price Range

#grid(columns: (1fr, 1fr, 1fr), gutter: 8pt)[
  #stat("Minimum", "GBP 13.99")
][
  #stat("Maximum", "GBP 57.25")
][
  #stat("Source pages", "1")
]

== Rating Distribution

#block(inset: 8pt, stroke: rgb("#d0d5dd"), radius: 5pt)[
#grid(columns: (70pt, 1fr, 28pt), gutter: 8pt)[#text(weight: "bold")[Five]][#rect(width: 66%, height: 7pt, fill: accent, radius: 3pt)][#align(right)[4]]
#v(5pt)
#grid(columns: (70pt, 1fr, 28pt), gutter: 8pt)[#text(weight: "bold")[Four]][#rect(width: 66%, height: 7pt, fill: accent, radius: 3pt)][#align(right)[4]]
#v(5pt)
#grid(columns: (70pt, 1fr, 28pt), gutter: 8pt)[#text(weight: "bold")[One]][#rect(width: 100%, height: 7pt, fill: accent, radius: 3pt)][#align(right)[6]]
#v(5pt)
#grid(columns: (70pt, 1fr, 28pt), gutter: 8pt)[#text(weight: "bold")[Three]][#rect(width: 50%, height: 7pt, fill: accent, radius: 3pt)][#align(right)[3]]
#v(5pt)
#grid(columns: (70pt, 1fr, 28pt), gutter: 8pt)[#text(weight: "bold")[Two]][#rect(width: 50%, height: 7pt, fill: accent, radius: 3pt)][#align(right)[3]]
#v(5pt)
]

== Sample Records

#table(
  columns: (1.8fr, .8fr, .8fr, .8fr),
  inset: 5pt,
  stroke: rgb("#d0d5dd"),
  [*Title*], [*Price*], [*Rating*], [*In Stock*],
  [A Light in the Attic], [GBP 51.77], [Three], [Yes],
  [Tipping the Velvet], [GBP 53.74], [One], [Yes],
  [Soumission], [GBP 50.10], [One], [Yes],
  [Sharp Objects], [GBP 47.82], [Four], [Yes],
  [Sapiens: A Brief History of Humankind], [GBP 54.23], [Five], [Yes],
  [The Requiem Red], [GBP 22.65], [One], [Yes],
)

== Report Notes

- CSV output: `examples/books_sample.csv`
- Pydantic validates each parsed record before export.
- Pandera validates the final dataframe contract.
- This template is for public pages with stable selectors and respectful rate limits.
