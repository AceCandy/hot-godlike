from typing import Any

import httpx
import pytest

from app.services import aihot_client as client_module
from app.services.aihot_client import AihotClient
from app.services.cache import InMemoryCacheStore
from app.services.planner import plan_items


class SequenceAsyncClient:
    responses: list[httpx.Response] = []
    calls: list[dict[str, Any]] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self) -> "SequenceAsyncClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str],
    ) -> httpx.Response:
        self.calls.append({"url": url, "params": params, "headers": headers})
        return self.responses.pop(0)


async def no_sleep(_: float) -> None:
    return None


@pytest.fixture(autouse=True)
def reset_sequence_client(monkeypatch: pytest.MonkeyPatch) -> None:
    SequenceAsyncClient.responses = []
    SequenceAsyncClient.calls = []
    monkeypatch.setattr(client_module.httpx, "AsyncClient", SequenceAsyncClient)
    monkeypatch.setattr(client_module.asyncio, "sleep", no_sleep)


@pytest.mark.asyncio
async def test_fetch_json_returns_cached_payload_on_not_modified() -> None:
    plan = plan_items()
    cache = InMemoryCacheStore()
    cached_payload = {
        "items": [
            {
                "id": "cached-1",
                "title": "缓存条目",
                "url": "https://example.com/cached",
                "source": "AI HOT",
            }
        ],
        "take": 50,
    }
    cache.set_etag(plan.cache_key, "etag-1")
    cache.set_response(plan.cache_key, cached_payload)
    SequenceAsyncClient.responses = [httpx.Response(304, headers={"etag": "etag-1"})]

    result = await AihotClient(
        base_url="https://example.test",
        retry_count=0,
    ).fetch_json(plan, cache)

    assert result.not_modified is True
    assert result.cached is True
    assert result.data == cached_payload
    assert SequenceAsyncClient.calls[0]["headers"]["If-None-Match"] == "etag-1"


@pytest.mark.asyncio
async def test_fetch_json_retries_rate_limit_then_returns_success() -> None:
    plan = plan_items()
    cache = InMemoryCacheStore()
    SequenceAsyncClient.responses = [
        httpx.Response(429),
        httpx.Response(200, json={"items": [], "take": 50}),
    ]

    result = await AihotClient(
        base_url="https://example.test",
        retry_count=1,
    ).fetch_json(plan, cache)

    assert result.status_code == 200
    assert result.data == {"items": [], "take": 50}
    assert len(SequenceAsyncClient.calls) == 2
