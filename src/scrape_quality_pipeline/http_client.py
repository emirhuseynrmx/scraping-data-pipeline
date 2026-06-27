from __future__ import annotations

import asyncio
import time

import httpx
from pydantic import BaseModel, ConfigDict, Field


class FetchError(RuntimeError):
    """Raised after the HTTP client exhausts retries."""


class HttpClientConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_agent: str = "scrape-quality-pipeline/0.1 (+portfolio demo)"
    timeout_seconds: float = Field(default=15.0, gt=0)
    max_retries: int = Field(default=3, ge=1)
    min_delay_seconds: float = Field(default=0.5, ge=0)


class PoliteHttpClient:
    def __init__(
        self,
        config: HttpClientConfig | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.config = config or HttpClientConfig()
        self._transport = transport
        self._last_request_at = 0.0

    async def __aenter__(self) -> PoliteHttpClient:
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout_seconds,
            headers={"User-Agent": self.config.user_agent},
            follow_redirects=True,
            transport=self._transport,
        )
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self._client.aclose()

    async def fetch_text(self, url: str) -> str:
        last_error: Exception | None = None

        for attempt in range(1, self.config.max_retries + 1):
            await self._respect_delay()
            try:
                response = await self._client.get(url)
                response.raise_for_status()
                return response.text
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_error = exc
                if attempt == self.config.max_retries:
                    break
                await asyncio.sleep(0.25 * 2 ** (attempt - 1))

        raise FetchError(f"Failed to fetch {url}") from last_error

    async def _respect_delay(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait_for = self.config.min_delay_seconds - elapsed
        if wait_for > 0:
            await asyncio.sleep(wait_for)
        self._last_request_at = time.monotonic()
