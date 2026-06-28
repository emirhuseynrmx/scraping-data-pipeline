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
  Scrape run summary for a public listing extraction job. The report shows
  row counts, data contracts, price range, availability, and sample records.
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

#table(
  columns: (1fr, 1fr),
  inset: 5pt,
  stroke: rgb("#d0d5dd"),
  [*Rating*], [*Records*],
  [Five], [4],
  [Four], [4],
  [One], [6],
  [Three], [3],
  [Two], [3],
)

== Sample Records

#table(
  columns: (1.8fr, .8fr, .8fr, .8fr),
  inset: 5pt,
  stroke: rgb("#d0d5dd"),
  [*Title*], [*Price*], [*Rating*], [*In Stock*],
  [A Light in the Attic], [GBP 51.77], [Three], [True],
  [Tipping the Velvet], [GBP 53.74], [One], [True],
  [Soumission], [GBP 50.10], [One], [True],
  [Sharp Objects], [GBP 47.82], [Four], [True],
  [Sapiens: A Brief History of Humankind], [GBP 54.23], [Five], [True],
  [The Requiem Red], [GBP 22.65], [One], [True],
)

== Delivery Notes

- CSV output: `examples/books_sample.csv`
- Pydantic validates each parsed record before export.
- Pandera validates the final dataframe contract.
- This template is for public pages with stable selectors and respectful rate limits.
