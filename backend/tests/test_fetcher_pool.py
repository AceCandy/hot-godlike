from typing import Any

import pytest

from app.core.errors import QueryServiceError, upstream_rate_limited
from app.services.aihot_client import UpstreamResult
from app.services.cache import InMemoryCacheStore
from app.services.fetcher_pool import AihotApiFetcher, FetcherPool
from app.services.planner import QueryPlan


@pytest.mark.asyncio
async def test_fetcher_pool_dispatches_aihot_api_to_aihot_fetcher() -> None:
    aihot_client = FakeAihotClient(
        UpstreamResult(
            {
                "items": [
                    {
                        "id": "item-1",
                        "title": "OpenAI 发布新产品",
                        "url": "https://example.com/openai",
                        "source": "AI HOT",
                        "summary": "AI HOT summary",
                        "score": 98,
                    }
                ],
                "hasNext": False,
                "take": 50,
            },
            200,
        )
    )
    pool = FetcherPool(
        aihot_fetcher=AihotApiFetcher(aihot_client=aihot_client, cache=InMemoryCacheStore()),
        feed_fetcher=FailingFeedFetcher(),
    )

    items = await pool.fetch(source_payload("aihot_api"))

    assert aihot_client.calls[0].upstream_path == "/api/public/items"
    assert aihot_client.calls[0].params == {"mode": "selected", "take": 50}
    assert items == [
        {
            "title": "OpenAI 发布新产品",
            "url": "https://example.com/openai",
            "publishedAt": None,
            "summary": "AI HOT summary",
            "hotScore": 98,
        }
    ]


@pytest.mark.asyncio
async def test_fetcher_pool_dispatches_feed_sources_to_feed_fetcher() -> None:
    feed_fetcher = FakeFeedFetcher()
    pool = FetcherPool(
        aihot_fetcher=FailingAihotFetcher(),
        feed_fetcher=feed_fetcher,
    )

    items = await pool.fetch(source_payload("rsshub"))

    assert items == [{"title": "Feed item", "url": "https://example.com/feed"}]
    assert feed_fetcher.calls == ["src_1"]


@pytest.mark.asyncio
async def test_aihot_fetcher_maps_upstream_errors_to_collection_errors() -> None:
    fetcher = AihotApiFetcher(
        aihot_client=FakeAihotClient(upstream_rate_limited()),
        cache=InMemoryCacheStore(),
    )

    with pytest.raises(QueryServiceError) as exc:
        await fetcher.fetch(source_payload("aihot_api"))

    assert exc.value.code == "SOURCE_RATE_LIMITED"
    assert exc.value.details == {"sourceId": "src_1"}


class FakeAihotClient:
    def __init__(self, response: UpstreamResult | QueryServiceError) -> None:
        self.response = response
        self.calls: list[QueryPlan] = []

    async def fetch_json(self, plan: QueryPlan, cache: InMemoryCacheStore) -> UpstreamResult:
        self.calls.append(plan)
        if isinstance(self.response, QueryServiceError):
            raise self.response
        return self.response


class FakeFeedFetcher:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def fetch(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        self.calls.append(source["id"])
        return [{"title": "Feed item", "url": "https://example.com/feed"}]


class FailingFeedFetcher:
    async def fetch(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        raise AssertionError("feed fetcher should not be called")


class FailingAihotFetcher:
    async def fetch(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        raise AssertionError("AI HOT fetcher should not be called")


def source_payload(source_type: str) -> dict[str, Any]:
    return {
        "id": "src_1",
        "name": "Source",
        "type": source_type,
        "category": "ai",
        "url": None,
        "route": "/hackernews/frontpage" if source_type == "rsshub" else None,
        "enabled": True,
        "status": "enabled",
        "fetchIntervalMinutes": 30,
        "timeoutSeconds": 30,
        "retryCount": 2,
        "concurrencyLimit": 1,
        "trustLevel": "high",
        "requiresCookie": False,
    }
