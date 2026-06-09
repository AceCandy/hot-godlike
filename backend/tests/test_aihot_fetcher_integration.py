from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.aihot_client import UpstreamResult
from app.services.cache import InMemoryCacheStore
from app.services.collection_registry import InMemorySourceRepository
from app.services.collection_store import InMemoryCollectionStore
from app.services.planner import QueryPlan


def test_manual_fetch_aihot_api_uses_fetcher_pool_and_writes_raw_items() -> None:
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
    app = create_app(
        aihot_client=aihot_client,
        cache=InMemoryCacheStore(),
        source_repository=InMemorySourceRepository(),
        collection_store=InMemoryCollectionStore(),
    )
    client = TestClient(app)
    source = client.post("/api/sources", json=aihot_api_input()).json()["data"]

    fetch_response = client.post(
        f"/api/sources/{source['id']}/fetch",
        json={"idempotencyKey": "manual-aihot"},
    )
    raw_response = client.get(f"/api/raw-items?sourceId={source['id']}")

    run = fetch_response.json()["data"]
    raw_items = raw_response.json()["data"]["items"]
    assert run["status"] == "succeeded"
    assert run["fetchedCount"] == 1
    assert run["newCount"] == 1
    assert raw_items[0]["title"] == "OpenAI 发布新产品"
    assert raw_items[0]["hotScore"] == 98
    assert aihot_client.calls[0].upstream_path == "/api/public/items"


class FakeAihotClient:
    def __init__(self, response: UpstreamResult) -> None:
        self.response = response
        self.calls: list[QueryPlan] = []

    async def fetch_json(self, plan: QueryPlan, cache: InMemoryCacheStore) -> UpstreamResult:
        self.calls.append(plan)
        return self.response


def aihot_api_input() -> dict[str, Any]:
    return {
        "name": "AI HOT API",
        "type": "aihot_api",
        "category": "ai",
        "url": None,
        "route": None,
        "enabled": True,
        "fetchIntervalMinutes": 30,
        "timeoutSeconds": 30,
        "retryCount": 2,
        "concurrencyLimit": 1,
        "trustLevel": "high",
        "requiresCookie": False,
    }
