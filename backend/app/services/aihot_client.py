from dataclasses import dataclass
from typing import Any
import asyncio

import httpx

from app.core.config import settings
from app.core.errors import (
    ErrorCode,
    QueryServiceError,
    upstream_bad_response,
    upstream_forbidden,
    upstream_not_found,
    upstream_rate_limited,
    upstream_timeout,
    upstream_unavailable,
)
from app.services.cache import InMemoryCacheStore
from app.services.planner import QueryPlan, request_headers


@dataclass(frozen=True)
class UpstreamResult:
    data: Any | None
    status_code: int
    etag: str | None = None
    not_modified: bool = False
    cached: bool = False


class AihotClient:
    def __init__(
        self,
        *,
        base_url: str = settings.aihot_base_url,
        timeout_seconds: float = settings.request_timeout_seconds,
        retry_count: int = settings.retry_count,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count

    async def fetch_json(
        self,
        plan: QueryPlan,
        cache: InMemoryCacheStore,
    ) -> UpstreamResult:
        etag = cache.get_etag(plan.cache_key)
        url = f"{self.base_url}{plan.upstream_path}"
        attempts = self.retry_count + 1
        last_error: QueryServiceError | None = None

        for attempt in range(attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.get(
                        url,
                        params=plan.params,
                        headers=request_headers(etag),
                    )
            except httpx.TimeoutException:
                last_error = upstream_timeout()
            except httpx.HTTPError:
                last_error = upstream_unavailable()
            else:
                try:
                    result = self._handle_response(
                        response,
                        cache=cache,
                        cache_key=plan.cache_key,
                    )
                except QueryServiceError as exc:
                    last_error = exc
                    if not _should_retry(exc):
                        raise
                else:
                    cache.set_etag(plan.cache_key, result.etag)
                    if not result.not_modified:
                        cache.set_response(plan.cache_key, result.data)
                    return result

            if last_error and attempt < attempts - 1 and _should_retry(last_error):
                await asyncio.sleep(0.2 * (2**attempt))
                continue
            if last_error:
                raise last_error

        raise last_error or upstream_unavailable()

    def _handle_response(
        self,
        response: httpx.Response,
        *,
        cache: InMemoryCacheStore,
        cache_key: str,
    ) -> UpstreamResult:
        if response.status_code == 304:
            cached_payload = cache.get_response(cache_key)
            return UpstreamResult(
                data=cached_payload,
                status_code=304,
                etag=response.headers.get("etag"),
                not_modified=True,
                cached=cached_payload is not None,
            )
        if response.status_code == 403:
            raise upstream_forbidden()
        if response.status_code == 404:
            raise upstream_not_found()
        if response.status_code == 429:
            raise upstream_rate_limited()
        if response.status_code >= 500:
            raise upstream_unavailable(response.status_code)
        if response.status_code >= 400:
            raise upstream_bad_response({"upstreamStatus": response.status_code})

        try:
            data = response.json()
        except ValueError as exc:
            snippet = response.text[:300]
            raise upstream_bad_response(
                {"upstreamStatus": response.status_code, "snippet": snippet}
            ) from exc
        return UpstreamResult(
            data=data,
            status_code=response.status_code,
            etag=response.headers.get("etag"),
        )


def _should_retry(exc: QueryServiceError) -> bool:
    return exc.code in {
        ErrorCode.UPSTREAM_RATE_LIMITED,
        ErrorCode.UPSTREAM_UNAVAILABLE,
        ErrorCode.UPSTREAM_TIMEOUT,
    }
