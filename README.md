# Scrape Quality Pipeline

[![CI](https://github.com/emirhuseynrmx/scraping-data-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/emirhuseynrmx/scraping-data-pipeline/actions)
[![codecov](https://codecov.io/gh/emirhuseynrmx/scraping-data-pipeline/branch/main/graph/badge.svg)](https://codecov.io/gh/emirhuseynrmx/scraping-data-pipeline)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

A production-style Python web scraping pipeline with typed records, data validation, exports, tests, CI, and coverage reporting.

- async HTTP client with retry, timeout, and polite request pacing
- deterministic parser for `books.toscrape.com`
- Pydantic v2 models for record-level validation
- `pandera` schema validation before exporting data
- CSV and JSONL export
- offline unit tests with fixtures
- GitHub Actions + Codecov-ready coverage

This is intentionally more than a one-file scraper. The goal is to show how a small scraping project can be structured like maintainable data infrastructure: clear boundaries, reproducible tests, typed models, and validation before data leaves the pipeline.

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

Scraping is not finished when HTML is parsed. Reliable scraping needs data contracts:

- prices must be numeric and positive
- URLs must be valid HTTP(S) URLs
- ratings must be one of the expected values
- exported columns must not silently drift

`pandera` catches those issues before a bad CSV reaches a dashboard, CRM, notebook, or database.

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

This project is a technical demo. Real scraping work should include:

- robots.txt and terms review
- reasonable rate limits
- clear user-agent
- no login bypassing
- no collection of private or sensitive data
- caching where possible
