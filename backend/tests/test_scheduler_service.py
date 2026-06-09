from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from app.core.errors import QueryServiceError, source_timeout
from app.services.collection import SourceInput
from app.services.collection_registry import InMemorySourceRepository
from app.services.collection_runner import CollectionRunner
from app.services.collection_store import InMemoryCollectionStore
from app.services.fetch_control import InMemorySourceLockStore
from app.services.scheduler import SchedulerService


@pytest.mark.asyncio
async def test_scheduler_fetches_due_source_with_schedule_trigger_and_sets_next_fetch_at() -> None:
    now = datetime(2026, 5, 29, 0, 0, 0, tzinfo=timezone.utc)
    repository = InMemorySourceRepository()
    source = repository.create(rsshub_source_input())
    store = InMemoryCollectionStore()
    fetcher = FakeSourceItemFetcher()
    runner = CollectionRunner(
        source_repository=repository,
        store=store,
        fetch_items=fetcher,
        lock_store=InMemorySourceLockStore(),
    )
    scheduler = SchedulerService(
        source_repository=repository,
        collection_store=store,
        runner=runner,
        now_func=lambda: now,
    )

    first = await scheduler.run_due_once()
    second = await scheduler.run_due_once()

    runs = store.list_runs(source_id=source["id"], take=10)["items"]
    health = store.list_health(source_id=source["id"], take=10)["items"][0]
    assert first == {"scanned": 1, "due": 1, "fetched": 1, "skipped": 0, "failed": 0}
    assert second == {"scanned": 1, "due": 0, "fetched": 0, "skipped": 1, "failed": 0}
    assert runs[0]["trigger"] == "schedule"
    assert fetcher.calls == [source["id"]]
    assert health["nextFetchAt"] is not None


@pytest.mark.asyncio
async def test_scheduler_skips_circuit_open_source_until_next_fetch_at() -> None:
    now = datetime(2026, 5, 29, 0, 0, 0, tzinfo=timezone.utc)
    repository = InMemorySourceRepository()
    source = repository.create(rsshub_source_input())
    store = InMemoryCollectionStore()
    for _ in range(5):
        store.record_failure(source, error_code="SOURCE_TIMEOUT", error_message="timeout")
    runner = CollectionRunner(
        source_repository=repository,
        store=store,
        fetch_items=FakeSourceItemFetcher(),
        lock_store=InMemorySourceLockStore(),
    )
    scheduler = SchedulerService(
        source_repository=repository,
        collection_store=store,
        runner=runner,
        now_func=lambda: now,
    )

    result = await scheduler.run_due_once()

    health = store.list_health(source_id=source["id"], take=10)["items"][0]
    assert result == {"scanned": 1, "due": 0, "fetched": 0, "skipped": 1, "failed": 0}
    assert health["status"] == "circuit_open"
    assert health["nextFetchAt"] is not None


@pytest.mark.asyncio
async def test_runner_syncs_degraded_source_status_and_scheduler_recovers_when_due() -> None:
    repository = InMemorySourceRepository()
    source = repository.create(rsshub_source_input())
    store = InMemoryCollectionStore()
    failing_runner = CollectionRunner(
        source_repository=repository,
        store=store,
        fetch_items=FailingSourceItemFetcher(),
        lock_store=InMemorySourceLockStore(),
    )

    for attempt in range(3):
        with pytest.raises(QueryServiceError):
            await failing_runner.fetch_source(
                source["id"],
                idempotency_key=f"fail-{attempt}",
                trigger="schedule",
            )

    degraded_source = repository.get(source["id"])
    degraded_health = store.list_health(source_id=source["id"], take=1)["items"][0]
    assert degraded_source["enabled"] is True
    assert degraded_source["status"] == "degraded"
    assert degraded_health["status"] == "degraded"
    assert _parse_time(degraded_health["nextFetchAt"]) - _parse_time(degraded_health["lastFailedAt"]) == timedelta(
        minutes=90
    )
    assert degraded_health["degradedUntil"] == degraded_health["nextFetchAt"]

    success_fetcher = FakeSourceItemFetcher()
    recovery_runner = CollectionRunner(
        source_repository=repository,
        store=store,
        fetch_items=success_fetcher,
        lock_store=InMemorySourceLockStore(),
    )
    scheduler = SchedulerService(
        source_repository=repository,
        collection_store=store,
        runner=recovery_runner,
        now_func=lambda: _parse_time(degraded_health["nextFetchAt"]),
    )

    result = await scheduler.run_due_once()

    recovered_source = repository.get(source["id"])
    recovered_health = store.list_health(source_id=source["id"], take=1)["items"][0]
    assert result == {"scanned": 1, "due": 1, "fetched": 1, "skipped": 0, "failed": 0}
    assert success_fetcher.calls == [source["id"]]
    assert recovered_source["status"] == "enabled"
    assert recovered_health["status"] == "enabled"
    assert recovered_health["consecutiveFailures"] == 0


class FakeSourceItemFetcher:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def __call__(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        self.calls.append(source["id"])
        return [
            {
                "title": "Scheduled item",
                "url": "https://example.com/scheduled",
                "publishedAt": "2026-05-29T00:00:00Z",
                "summary": "Scheduled summary",
            }
        ]


class FailingSourceItemFetcher:
    async def __call__(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        raise source_timeout({"sourceId": source["id"]})


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


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
