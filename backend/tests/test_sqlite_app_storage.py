from typing import Any

from fastapi.testclient import TestClient

import app.main as main_module
from app.core.config import Settings
from app.services.collection_registry import SqliteSourceRepository
from app.services.collection_store import SqliteCollectionStore


def test_app_local_storage_mode_persists_source_and_fetch_results(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "hot_godlike.sqlite"
    monkeypatch.setattr(
        main_module,
        "settings",
        Settings(storage_mode="local", local_storage_path=str(db_path)),
    )
    app = main_module.create_app(source_item_fetcher=_fake_fetch_items)
    client = TestClient(app)

    source_response = client.post(
        "/api/sources",
        json={
            "name": "Local RSS",
            "type": "rsshub",
            "category": "tech",
            "route": "/local/rss",
            "enabled": True,
            "fetchIntervalMinutes": 30,
            "timeoutSeconds": 30,
            "retryCount": 2,
            "concurrencyLimit": 1,
            "trustLevel": "medium",
        },
    )
    source_id = source_response.json()["data"]["id"]

    fetch_response = client.post(
        f"/api/sources/{source_id}/fetch",
        json={"idempotencyKey": "manual-1"},
    )

    reopened_source = SqliteSourceRepository.from_path(str(db_path)).get(source_id)
    reopened_items = SqliteCollectionStore.from_path(str(db_path)).list_raw_items(
        source_id=source_id,
        take=10,
    )

    assert fetch_response.json()["data"]["status"] == "succeeded"
    assert reopened_source["name"] == "Local RSS"
    assert reopened_items["items"][0]["title"] == "Persisted item"


async def _fake_fetch_items(source: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "title": "Persisted item",
            "url": "https://example.com/item",
            "publishedAt": "2026-05-29T00:00:00Z",
            "summary": "Stored locally",
        }
    ]
