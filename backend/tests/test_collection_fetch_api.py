from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.collection_registry import InMemorySourceRepository
from app.services.collection_store import InMemoryCollectionStore


class FakeItemFetcher:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def __call__(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        self.calls.append(source)
        return [
            {
                "title": "First item",
                "url": "https://example.com/item?id=1&utm_source=test",
                "publishedAt": "2026-05-29T00:00:00Z",
                "summary": "First summary",
            },
            {
                "title": "Duplicate item",
                "url": "https://example.com/item?id=1",
                "publishedAt": "2026-05-29T00:00:00Z",
                "summary": "Duplicate summary",
            },
        ]


def make_client(fetcher: FakeItemFetcher, source_dedupe_store: object | None = None) -> TestClient:
    app = create_app(
        source_repository=InMemorySourceRepository(),
        collection_store=InMemoryCollectionStore(),
        source_item_fetcher=fetcher,
        source_dedupe_store=source_dedupe_store,
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


def test_manual_fetch_writes_run_raw_items_and_health() -> None:
    fetcher = FakeItemFetcher()
    client = make_client(fetcher)
    source = client.post("/api/sources", json=rsshub_input()).json()["data"]

    fetch_response = client.post(
        f"/api/sources/{source['id']}/fetch",
        json={"idempotencyKey": "manual-1", "reason": "manual smoke"},
    )
    runs_response = client.get(f"/api/fetch-runs?sourceId={source['id']}")
    raw_response = client.get(f"/api/raw-items?sourceId={source['id']}")
    health_response = client.get(f"/api/source-health?sourceId={source['id']}")

    assert fetch_response.status_code == 200
    run = fetch_response.json()["data"]
    assert run["sourceId"] == source["id"]
    assert run["trigger"] == "manual"
    assert run["status"] == "succeeded"
    assert run["fetchedCount"] == 2
    assert run["newCount"] == 1
    assert run["duplicateCount"] == 1
    assert run["ignoredCount"] == 0
    assert run["traceId"].startswith("tr_")

    assert runs_response.json()["data"]["items"][0]["id"] == run["id"]
    raw_items = raw_response.json()["data"]["items"]
    assert len(raw_items) == 1
    assert raw_items[0]["title"] == "First item"
    assert raw_items[0]["normalizedUrl"] == "https://example.com/item?id=1"

    raw_detail = client.get(f"/api/raw-items/{raw_items[0]['id']}")
    assert raw_detail.json()["data"]["id"] == raw_items[0]["id"]

    health = health_response.json()["data"]["items"][0]
    assert health["sourceId"] == source["id"]
    assert health["status"] == "enabled"
    assert health["consecutiveFailures"] == 0
    assert health["lastSucceededAt"] is not None


def test_manual_fetch_reuses_idempotency_key_without_duplicate_fetch() -> None:
    fetcher = FakeItemFetcher()
    client = make_client(fetcher)
    source = client.post("/api/sources", json=rsshub_input()).json()["data"]

    first = client.post(
        f"/api/sources/{source['id']}/fetch",
        json={"idempotencyKey": "manual-1"},
    )
    second = client.post(
        f"/api/sources/{source['id']}/fetch",
        json={"idempotencyKey": "manual-1"},
    )

    assert first.json()["data"]["id"] == second.json()["data"]["id"]
    assert len(fetcher.calls) == 1


def test_manual_fetch_counts_redis_dedupe_hits_without_writing_raw_items() -> None:
    fetcher = FakeItemFetcher()
    dedupe_store = FakeDedupeStore(existing_dedupe_keys={"url:https://example.com/item?id=1"})
    client = make_client(fetcher, source_dedupe_store=dedupe_store)
    source = client.post("/api/sources", json=rsshub_input()).json()["data"]

    response = client.post(
        f"/api/sources/{source['id']}/fetch",
        json={"idempotencyKey": "manual-1"},
    )
    raw_response = client.get(f"/api/raw-items?sourceId={source['id']}")

    run = response.json()["data"]
    assert run["fetchedCount"] == 2
    assert run["newCount"] == 0
    assert run["duplicateCount"] == 2
    assert raw_response.json()["data"]["items"] == []
    assert dedupe_store.reserve_calls == [
        (source["id"], "url:https://example.com/item?id=1"),
        (source["id"], "url:https://example.com/item?id=1"),
    ]


def test_manual_fetch_disabled_source_returns_contract_error() -> None:
    fetcher = FakeItemFetcher()
    client = make_client(fetcher)
    source = client.post("/api/sources", json=rsshub_input()).json()["data"]
    client.post(f"/api/sources/{source['id']}/disable")

    response = client.post(f"/api/sources/{source['id']}/fetch", json={})

    assert response.status_code == 409
    body = response.json()
    assert body["meta"]["source"] == "hot-godlike"
    assert body["error"]["code"] == "SOURCE_DISABLED"
    assert body["error"]["retryable"] is False


class FakeDedupeStore:
    def __init__(self, *, existing_dedupe_keys: set[str] | None = None) -> None:
        self.existing_dedupe_keys = existing_dedupe_keys or set()
        self.reserve_calls: list[tuple[str, str]] = []
        self.release_calls: list[tuple[str, tuple[str, ...]]] = []

    def reserve(self, source_id: str, dedupe_key: str) -> bool:
        self.reserve_calls.append((source_id, dedupe_key))
        if dedupe_key in self.existing_dedupe_keys:
            return False
        self.existing_dedupe_keys.add(dedupe_key)
        return True

    def release(self, source_id: str, dedupe_keys: list[str]) -> None:
        self.release_calls.append((source_id, tuple(dedupe_keys)))
        for dedupe_key in dedupe_keys:
            self.existing_dedupe_keys.discard(dedupe_key)
