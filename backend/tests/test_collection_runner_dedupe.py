from typing import Any

import pytest

from app.services.collection import SourceInput
from app.services.collection_registry import InMemorySourceRepository
from app.services.collection_runner import CollectionRunner
from app.services.collection_store import InMemoryCollectionStore
from app.services.fetch_control import InMemorySourceLockStore


@pytest.mark.asyncio
async def test_runner_releases_reserved_dedupe_keys_when_raw_store_fails() -> None:
    repository = InMemorySourceRepository()
    source = repository.create(rsshub_source_input())
    dedupe_store = FakeDedupeStore()
    runner = CollectionRunner(
        source_repository=repository,
        store=FailingCollectionStore(),
        fetch_items=SingleItemFetcher(),
        lock_store=InMemorySourceLockStore(),
        source_dedupe_store=dedupe_store,
    )

    with pytest.raises(RuntimeError):
        await runner.fetch_source(source["id"], idempotency_key=None)

    assert dedupe_store.release_calls == [
        (source["id"], ("url:https://example.com/item",))
    ]


class SingleItemFetcher:
    async def __call__(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "title": "First item",
                "url": "https://example.com/item",
                "publishedAt": "2026-05-29T00:00:00Z",
            }
        ]


class FailingCollectionStore(InMemoryCollectionStore):
    def save_raw_items(self, items: list[dict[str, Any]]) -> tuple[int, int]:
        raise RuntimeError("raw store unavailable")


class FakeDedupeStore:
    def __init__(self) -> None:
        self.keys: set[str] = set()
        self.release_calls: list[tuple[str, tuple[str, ...]]] = []

    def reserve(self, source_id: str, dedupe_key: str) -> bool:
        if dedupe_key in self.keys:
            return False
        self.keys.add(dedupe_key)
        return True

    def release(self, source_id: str, dedupe_keys: list[str]) -> None:
        self.release_calls.append((source_id, tuple(dedupe_keys)))
        for dedupe_key in dedupe_keys:
            self.keys.discard(dedupe_key)


def rsshub_source_input() -> SourceInput:
    return SourceInput(
        name="Hacker News",
        type="rsshub",
        category="tech",
        url=None,
        route="/hackernews/frontpage",
        enabled=True,
        fetchIntervalMinutes=30,
        timeoutSeconds=30,
        retryCount=2,
        concurrencyLimit=1,
        trustLevel="medium",
        requiresCookie=False,
    )
