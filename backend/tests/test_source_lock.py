from typing import Any

from fastapi.testclient import TestClient

from app.core.errors import source_rate_limited
from app.main import create_app
from app.services.collection_registry import InMemorySourceRepository
from app.services.collection_store import InMemoryCollectionStore
from app.services.fetch_control import InMemorySourceLockStore


class FakeItemFetcher:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    async def __call__(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        self.calls.append(source)
        if self.fail:
            raise source_rate_limited({"sourceId": source["id"]})
        return [
            {
                "title": "First item",
                "url": "https://example.com/item/1",
                "publishedAt": "2026-05-29T00:00:00Z",
            }
        ]


def make_client(fetcher: FakeItemFetcher, lock_store: InMemorySourceLockStore) -> TestClient:
    app = create_app(
        source_repository=InMemorySourceRepository(),
        collection_store=InMemoryCollectionStore(),
        source_item_fetcher=fetcher,
        source_lock_store=lock_store,
    )
    return TestClient(app)


def rsshub_input() -> dict[str, object]:
    return {
        "name": "Hacker News",
        "type": "rsshub",
        "category": "tech",
        "url": None,
        "route": "/hackernews/frontpage",
        "enabled": True,
        "fetchIntervalMinutes": 30,
        "timeoutSeconds": 30,
        "retryCount": 2,
        "concurrencyLimit": 1,
        "trustLevel": "medium",
        "requiresCookie": False,
    }


def test_manual_fetch_returns_rate_limited_when_source_lock_is_held() -> None:
    fetcher = FakeItemFetcher()
    lock_store = InMemorySourceLockStore()
    client = make_client(fetcher, lock_store)
    source = client.post("/api/sources", json=rsshub_input()).json()["data"]
    lock_store.acquire(source["id"], ttl_seconds=120)

    response = client.post(f"/api/sources/{source['id']}/fetch", json={})

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "SOURCE_RATE_LIMITED"
    assert body["error"]["retryable"] is True
    assert fetcher.calls == []


def test_manual_fetch_releases_source_lock_after_fetch_failure() -> None:
    fetcher = FakeItemFetcher(fail=True)
    lock_store = InMemorySourceLockStore()
    client = make_client(fetcher, lock_store)
    source = client.post("/api/sources", json=rsshub_input()).json()["data"]

    response = client.post(f"/api/sources/{source['id']}/fetch", json={})

    assert response.status_code == 503
    assert lock_store.is_locked(source["id"]) is False
