from __future__ import annotations

import httpx
import pytest

from scrape_quality_pipeline.http_client import FetchError, HttpClientConfig, PoliteHttpClient


@pytest.mark.asyncio
async def test_polite_http_client_fetches_text_with_user_agent() -> None:
    seen_user_agents: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_user_agents.append(request.headers["user-agent"])
        return httpx.Response(200, text="ok")

    transport = httpx.MockTransport(handler)
    config = HttpClientConfig(user_agent="pipeline-test", min_delay_seconds=0, max_retries=1)

    async with PoliteHttpClient(config=config, transport=transport) as client:
        text = await client.fetch_text("https://example.com")

    assert text == "ok"
    assert seen_user_agents == ["pipeline-test"]


@pytest.mark.asyncio
async def test_polite_http_client_retries_then_succeeds() -> None:
    attempts = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, text="temporarily unavailable")
        return httpx.Response(200, text="recovered")

    transport = httpx.MockTransport(handler)
    config = HttpClientConfig(min_delay_seconds=0, max_retries=2)

    async with PoliteHttpClient(config=config, transport=transport) as client:
        text = await client.fetch_text("https://example.com")

    assert text == "recovered"
    assert attempts == 2


@pytest.mark.asyncio
async def test_polite_http_client_raises_after_retries() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="still broken")

    transport = httpx.MockTransport(handler)
    config = HttpClientConfig(min_delay_seconds=0, max_retries=2)

    async with PoliteHttpClient(config=config, transport=transport) as client:
        with pytest.raises(FetchError):
            await client.fetch_text("https://example.com")
