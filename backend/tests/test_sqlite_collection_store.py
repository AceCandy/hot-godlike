from datetime import datetime, timedelta
from typing import Any

import pytest

from app.core.errors import ErrorCode, QueryServiceError
from app.services.collection_registry import SqliteSourceRepository
from app.services.collection_store import (
    InMemoryCollectionStore,
    SqliteCollectionStore,
    build_collection_store,
)
from tests.test_sqlite_source_repository import rss_source_input


def test_sqlite_collection_store_persists_runs_raw_items_and_health(tmp_path) -> None:
    db_path = tmp_path / "hot_godlike.sqlite"
    source = SqliteSourceRepository.from_path(str(db_path)).create(rss_source_input())
    store = SqliteCollectionStore.from_path(str(db_path))

    run = store.start_run(source_id=source["id"], trigger="manual", idempotency_key="manual-1")
    store.finish_run(
        run["id"],
        status="succeeded",
        fetched_count=2,
        new_count=1,
        duplicate_count=1,
        ignored_count=0,
    )
    new_count, duplicate_count = store.save_raw_items(
        [raw_item_payload(source), raw_item_payload(source, item_id="raw_dup")]
    )
    store.record_success(source)

    reopened = SqliteCollectionStore.from_path(str(db_path))
    existing = reopened.existing_idempotent_run(source["id"], "manual-1")
    repeated_new_count, repeated_duplicate_count = reopened.save_raw_items(
        [raw_item_payload(source, item_id="raw_repeated")]
    )
    runs = reopened.list_runs(source_id=source["id"], status="succeeded", take=10)
    raw_items = reopened.list_raw_items(source_id=source["id"], status="new", q="first", take=10)
    health_items = reopened.list_health(source_id=source["id"], status="enabled", take=10)

    assert existing is not None
    assert existing["id"] == run["id"]
    assert new_count == 1
    assert duplicate_count == 1
    assert repeated_new_count == 0
    assert repeated_duplicate_count == 1
    assert runs["items"][0]["id"] == run["id"]
    assert reopened.get_run(run["id"])["status"] == "succeeded"
    assert raw_items["items"][0]["title"] == "First item"
    assert reopened.get_raw_item(raw_items["items"][0]["id"])["normalizedUrl"] == "https://example.com/item"
    assert health_items["items"][0]["status"] == "enabled"


def test_sqlite_collection_store_records_failure_thresholds(tmp_path) -> None:
    db_path = tmp_path / "hot_godlike.sqlite"
    source = SqliteSourceRepository.from_path(str(db_path)).create(rss_source_input())
    store = SqliteCollectionStore.from_path(str(db_path))

    first = store.record_failure(source, error_code="SOURCE_TIMEOUT", error_message="timeout")
    second = store.record_failure(source, error_code="SOURCE_TIMEOUT", error_message="timeout")
    third = SqliteCollectionStore.from_path(str(db_path)).record_failure(
        source,
        error_code="SOURCE_TIMEOUT",
        error_message="timeout",
    )

    assert first["status"] == "enabled"
    assert second["consecutiveFailures"] == 2
    assert third["status"] == "degraded"
    assert third["consecutiveFailures"] == 3
    assert third["lastErrorCode"] == "SOURCE_TIMEOUT"
    assert _parse_utc(third["nextFetchAt"]) - _parse_utc(third["lastFailedAt"]) == timedelta(minutes=90)
    assert third["degradedUntil"] == third["nextFetchAt"]


def test_sqlite_collection_store_maps_missing_records_to_contract_errors(tmp_path) -> None:
    store = SqliteCollectionStore.from_path(str(tmp_path / "hot_godlike.sqlite"))

    with pytest.raises(QueryServiceError) as run_exc:
        store.get_run("run_missing")
    with pytest.raises(QueryServiceError) as item_exc:
        store.get_raw_item("raw_missing")

    assert run_exc.value.code == ErrorCode.FETCH_RUN_NOT_FOUND
    assert item_exc.value.code == ErrorCode.RAW_ITEM_NOT_FOUND


def test_build_collection_store_supports_explicit_local_storage(tmp_path) -> None:
    store = build_collection_store(
        storage_mode="local",
        local_sqlite_path=str(tmp_path / "hot_godlike.sqlite"),
        use_postgres=False,
        postgres_dsn=None,
    )

    assert isinstance(store, SqliteCollectionStore)


def test_build_collection_store_still_defaults_to_memory(tmp_path) -> None:
    store = build_collection_store(
        storage_mode=None,
        local_sqlite_path=str(tmp_path / "hot_godlike.sqlite"),
        use_postgres=False,
        postgres_dsn=None,
    )

    assert isinstance(store, InMemoryCollectionStore)


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def raw_item_payload(source: dict[str, Any], *, item_id: str = "raw_first") -> dict[str, Any]:
    return {
        "id": item_id,
        "sourceId": source["id"],
        "sourceName": source["name"],
        "title": "First item",
        "url": "https://example.com/item",
        "normalizedUrl": "https://example.com/item",
        "publishedAt": "2026-05-29T00:00:00Z",
        "fetchedAt": "2026-05-29T00:00:03Z",
        "author": None,
        "summary": "Summary",
        "contentSnippet": "Snippet",
        "hotScore": None,
        "rank": 1,
        "image": None,
        "rawPayloadRef": None,
        "status": "new",
        "dedupeKey": "url:https://example.com/item",
    }
