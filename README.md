# Scrape Quality Pipeline

[![CI](https://github.com/emirhuseynrmx/scrape-quality-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/emirhuseynrmx/scrape-quality-pipeline/actions)
[![codecov](https://codecov.io/gh/emirhuseynrmx/scrape-quality-pipeline/branch/main/graph/badge.svg)](https://codecov.io/gh/emirhuseynrmx/scrape-quality-pipeline)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

A production-style web scraping example built for portfolio and client work:

- async HTTP client with retry, timeout, and polite request pacing
- deterministic parser for `books.toscrape.com`
- `pandera` schema validation before exporting data
- CSV and JSONL export
- offline unit tests with fixtures
- GitHub Actions + Codecov-ready coverage

This is intentionally more than a one-file scraper. It demonstrates the kind of quality bar useful for freelance web scraping, lead generation, price monitoring, directory extraction, and data enrichment projects.

## Demo

```bash
pip install -e ".[dev]"
scrape-books --pages 2 --out examples/books.csv --format csv
```

Example output columns:

| column | meaning |
| --- | --- |
| `title` | Product title |
| `price_gbp` | Parsed numeric price |
| `rating` | Star rating text |
| `in_stock` | Availability flag |
| `product_url` | Absolute product URL |
| `source_url` | Listing page URL |
| `scraped_at` | UTC extraction timestamp |

## Why Pandera?

Scraping is not finished when HTML is parsed. Client-ready scraping needs data contracts:

- prices must be numeric and positive
- URLs must be valid HTTP(S) URLs
- ratings must be one of the expected values
- exported columns must not silently drift

`pandera` catches those issues before a bad CSV reaches a client, dashboard, CRM, or database.

## Run Tests

```bash
pytest
```

Expected coverage includes:

- parser behavior on stable fixture HTML
- schema validation success/failure
- pipeline orchestration without live network calls
- CSV and JSONL export

## Ethical Scraping Defaults

This project is a technical demo. Real client scraping should include:

- robots.txt and terms review
- reasonable rate limits
- clear user-agent
- no login bypassing
- no collection of private or sensitive data
- caching where possible

## Upwork Project Positioning

Use this repo as proof for a catalog offer like:

> I will build a validated Python web scraping and data extraction pipeline with tests, clean exports, and monitoring-ready data quality checks.

Suggested packages:

- **Starter:** one public website, CSV output, basic validation
- **Standard:** pagination, retries, schema validation, tests, JSONL/CSV
- **Advanced:** multi-source extraction, scheduling-ready pipeline, CI, Codecov, handoff docs

