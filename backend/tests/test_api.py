from typing import Any

from fastapi.testclient import TestClient

from app.core.errors import upstream_not_found
from app.main import create_app
from app.services.aihot_client import UpstreamResult
from app.services.cache import InMemoryCacheStore
from app.services.planner import QueryPlan


class FakeAihotClient:
    def __init__(self, responses: dict[str, UpstreamResult | Exception]) -> None:
        self.responses = responses
        self.calls: list[QueryPlan] = []

    async def fetch_json(
        self, plan: QueryPlan, cache: InMemoryCacheStore
    ) -> UpstreamResult:
        self.calls.append(plan)
        response = self.responses[plan.upstream_path]
        if isinstance(response, Exception):
            raise response
        return response


def make_client(fake: FakeAihotClient) -> TestClient:
    app = create_app(aihot_client=fake, cache=InMemoryCacheStore())
    return TestClient(app)


def item_payload() -> dict[str, Any]:
    return {
        "items": [
            {
                "id": "item-1",
                "title": "OpenAI 发布新产品",
                "url": "https://example.com/openai",
                "source": "AI HOT",
                "summary": None,
                "category": "ai-products",
            }
        ],
        "hasNext": False,
        "nextCursor": None,
        "take": 50,
    }


def test_query_items_success_envelope() -> None:
    fake = FakeAihotClient({"/api/public/items": UpstreamResult(item_payload(), 200)})
    client = make_client(fake)

    response = client.get("/api/query/items")

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["meta"]["source"] == "aihot"
    assert body["meta"]["query"]["mode"] == "selected"
    assert body["data"]["items"][0]["title"] == "OpenAI 发布新产品"
    assert fake.calls[0].params["mode"] == "selected"


def test_query_items_not_modified_returns_cached_payload() -> None:
    fake = FakeAihotClient(
        {
            "/api/public/items": UpstreamResult(
                item_payload(),
                304,
                etag="etag-1",
                not_modified=True,
                cached=True,
            )
        }
    )
    client = make_client(fake)

    response = client.get("/api/query/items")

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["cached"] is True
    assert body["data"]["items"][0]["id"] == "item-1"
    assert "缓存" in body["meta"]["warnings"][0]


def test_query_items_all_mode_and_category() -> None:
    fake = FakeAihotClient({"/api/public/items": UpstreamResult(item_payload(), 200)})
    client = make_client(fake)

    response = client.get("/api/query/items?mode=all&category=paper&timePreset=7d")

    assert response.status_code == 200
    assert fake.calls[0].params["mode"] == "all"
    assert fake.calls[0].params["category"] == "paper"
    assert "since" in fake.calls[0].params


def test_query_items_short_keyword_returns_contract_error() -> None:
    fake = FakeAihotClient({"/api/public/items": UpstreamResult(item_payload(), 200)})
    client = make_client(fake)

    response = client.get("/api/query/items?q=a")

    assert response.status_code == 400
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "BAD_REQUEST"
    assert body["error"]["retryable"] is False


def test_query_daily_success() -> None:
    fake = FakeAihotClient(
        {
            "/api/public/daily": UpstreamResult(
                {"date": "2026-05-29", "sections": []}, 200
            )
        }
    )
    client = make_client(fake)

    response = client.get("/api/query/daily")

    assert response.status_code == 200
    assert response.json()["data"]["date"] == "2026-05-29"


def test_query_daily_not_found_uses_contract_error() -> None:
    fake = FakeAihotClient({"/api/public/daily/2099-01-01": upstream_not_found()})
    client = make_client(fake)

    response = client.get("/api/query/daily?date=2099-01-01")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "UPSTREAM_NOT_FOUND"


def test_query_dailies_success() -> None:
    fake = FakeAihotClient(
        {"/api/public/dailies": UpstreamResult({"items": [{"date": "2026-05-29"}]}, 200)}
    )
    client = make_client(fake)

    response = client.get("/api/query/dailies?take=3")

    assert response.status_code == 200
    assert response.json()["data"][0]["date"] == "2026-05-29"
    assert fake.calls[0].params["take"] == 3


def test_query_help_does_not_call_upstream() -> None:
    fake = FakeAihotClient({})
    client = make_client(fake)

    response = client.get("/api/query/help")

    assert response.status_code == 200
    assert response.json()["data"]["categories"][0]["value"] == "ai-models"
    assert fake.calls == []
