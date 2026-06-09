import pytest

from app.services.collection_runner import default_source_item_fetcher
from app.services.fetch_control import InMemorySourceMetadataStore, RedisSourceMetadataStore, redis_key
from app.services.source_preview import FeedItemsResult


def test_redis_source_metadata_store_reads_and_writes_contract_keys() -> None:
    client = FakeRedisMetadataClient(
        {
            "source:etag:src_1": b"etag-old",
            "source:last_modified:src_1": "Fri, 29 May 2026 00:00:00 GMT",
        }
    )
    store = RedisSourceMetadataStore(client)

    metadata = store.get("src_1")
    store.set("src_1", etag="etag-new", last_modified="Sat, 30 May 2026 00:00:00 GMT")
    store.set("src_1", etag=None, last_modified=None)

    assert metadata.etag == "etag-old"
    assert metadata.last_modified == "Fri, 29 May 2026 00:00:00 GMT"
    assert client.get_calls == [
        redis_key.source_etag("src_1"),
        redis_key.source_last_modified("src_1"),
    ]
    assert client.set_calls == [
        {"name": "source:etag:src_1", "value": "etag-new"},
        {"name": "source:last_modified:src_1", "value": "Sat, 30 May 2026 00:00:00 GMT"},
    ]
    assert client.deleted == ["source:etag:src_1", "source:last_modified:src_1"]


@pytest.mark.asyncio
async def test_default_fetcher_uses_metadata_store_and_persists_response_metadata() -> None:
    metadata_store = InMemorySourceMetadataStore()
    metadata_store.set(
        "src_1",
        etag="etag-old",
        last_modified="Fri, 29 May 2026 00:00:00 GMT",
    )
    previewer = FakePreviewer()
    repository = FakeSourceRepository()
    fetcher = default_source_item_fetcher(
        previewer,
        source_repository=repository,
        metadata_store=metadata_store,
    )

    items = await fetcher(source_payload())
    metadata = metadata_store.get("src_1")

    assert items == [{"title": "First item", "url": "https://example.com/first"}]
    assert previewer.seen == {
        "etag": "etag-old",
        "last_modified": "Fri, 29 May 2026 00:00:00 GMT",
    }
    assert metadata.etag == "etag-new"
    assert metadata.last_modified == "Sat, 30 May 2026 00:00:00 GMT"
    assert repository.metadata_updates[0]["source_id"] == "src_1"
    assert repository.metadata_updates[0]["etag"] == "etag-new"
    assert repository.metadata_updates[0]["last_modified"] == "Sat, 30 May 2026 00:00:00 GMT"
    assert repository.metadata_updates[0]["fetched_at"].endswith("Z")


def source_payload() -> dict[str, object]:
    return {
        "id": "src_1",
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
        "etag": None,
        "lastModified": None,
    }


class FakePreviewer:
    def __init__(self) -> None:
        self.seen: dict[str, str | None] = {}

    async def fetch_items_with_metadata(self, source_input, *, etag, last_modified):
        self.seen = {"etag": etag, "last_modified": last_modified}
        return FeedItemsResult(
            items=[{"title": "First item", "url": "https://example.com/first"}],
            etag="etag-new",
            last_modified="Sat, 30 May 2026 00:00:00 GMT",
        )


class FakeSourceRepository:
    def __init__(self) -> None:
        self.metadata_updates: list[dict[str, object]] = []

    def set_fetch_metadata(
        self,
        source_id: str,
        *,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> None:
        self.metadata_updates.append(
            {
                "source_id": source_id,
                "etag": etag,
                "last_modified": last_modified,
                "fetched_at": fetched_at,
            }
        )


class FakeRedisMetadataClient:
    def __init__(self, values: dict[str, object] | None = None) -> None:
        self.values = values or {}
        self.get_calls: list[str] = []
        self.set_calls: list[dict[str, str]] = []
        self.deleted: list[str] = []

    def get(self, name: str) -> object:
        self.get_calls.append(name)
        return self.values.get(name)

    def set(self, name: str, value: str) -> bool:
        self.set_calls.append({"name": name, "value": value})
        self.values[name] = value
        return True

    def delete(self, name: str) -> int:
        self.deleted.append(name)
        self.values.pop(name, None)
        return 1
