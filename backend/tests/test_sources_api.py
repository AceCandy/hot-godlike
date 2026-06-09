from fastapi.testclient import TestClient

from app.main import create_app
from app.services.collection_registry import InMemorySourceRepository


class FakeSourcePreviewer:
    def __init__(self) -> None:
        self.calls = []

    async def preview(self, source_input):
        self.calls.append(source_input)
        return {
            "source": {
                "name": source_input.name,
                "type": source_input.type,
                "route": source_input.route,
            },
            "sampleItems": [
                {
                    "title": "Preview item",
                    "url": "https://example.com/item",
                    "publishedAt": "2026-05-29T00:00:00Z",
                    "contentSnippet": "Preview only",
                }
            ],
            "warnings": [],
        }


def make_client(source_previewer=None) -> TestClient:
    app = create_app(
        source_repository=InMemorySourceRepository(),
        source_previewer=source_previewer,
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


def test_create_source_returns_contract_envelope() -> None:
    client = make_client()

    response = client.post("/api/sources", json=rsshub_input())

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["meta"]["source"] == "hot-godlike"
    assert body["data"]["id"].startswith("src_")
    assert body["data"]["name"] == "Hacker News"
    assert body["data"]["status"] == "enabled"
    assert body["data"]["firstFetchMode"] == "ingest_only"
    assert body["data"]["createdAt"].endswith("Z")


def test_list_sources_filters_by_type_and_status() -> None:
    client = make_client()
    client.post("/api/sources", json=rsshub_input())
    disabled = rsshub_input() | {"name": "Disabled Feed", "enabled": False, "route": "/test/feed"}
    client.post("/api/sources", json=disabled)

    response = client.get("/api/sources?type=rsshub&status=enabled&take=10")

    assert response.status_code == 200
    body = response.json()
    assert [item["name"] for item in body["data"]["items"]] == ["Hacker News"]
    assert body["data"]["page"] == {"take": 10, "hasNext": False, "nextCursor": None}


def test_get_source_detail_and_enable_disable() -> None:
    client = make_client()
    created = client.post("/api/sources", json=rsshub_input()).json()["data"]

    disabled = client.post(f"/api/sources/{created['id']}/disable")
    detail = client.get(f"/api/sources/{created['id']}")
    enabled = client.post(f"/api/sources/{created['id']}/enable")

    assert disabled.status_code == 200
    assert disabled.json()["data"]["enabled"] is False
    assert disabled.json()["data"]["status"] == "disabled"
    assert detail.json()["data"]["status"] == "disabled"
    assert enabled.json()["data"]["enabled"] is True
    assert enabled.json()["data"]["status"] == "enabled"


def test_patch_source_updates_config_without_changing_created_at() -> None:
    client = make_client()
    created = client.post("/api/sources", json=rsshub_input()).json()["data"]

    response = client.patch(
        f"/api/sources/{created['id']}",
        json={"name": "HN Frontpage", "fetchIntervalMinutes": 60},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["id"] == created["id"]
    assert body["data"]["name"] == "HN Frontpage"
    assert body["data"]["fetchIntervalMinutes"] == 60
    assert body["data"]["route"] == "/hackernews/frontpage"
    assert body["data"]["createdAt"] == created["createdAt"]
    assert body["data"]["updatedAt"].endswith("Z")


def test_preview_source_returns_samples_without_persisting_source() -> None:
    previewer = FakeSourcePreviewer()
    client = make_client(source_previewer=previewer)

    response = client.post("/api/sources/preview", json=rsshub_input())
    sources = client.get("/api/sources")

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["source"] == "hot-godlike"
    assert body["data"]["sampleItems"][0]["title"] == "Preview item"
    assert previewer.calls[0].route == "/hackernews/frontpage"
    assert sources.json()["data"]["items"] == []


def test_create_source_rejects_ssrf_url_with_contract_error() -> None:
    client = make_client()
    payload = rsshub_input() | {
        "name": "Local RSS",
        "type": "rss",
        "url": "http://127.0.0.1/feed.xml",
        "route": None,
    }

    response = client.post("/api/sources", json=payload)

    assert response.status_code == 400
    body = response.json()
    assert body["data"] is None
    assert body["meta"]["source"] == "hot-godlike"
    assert body["error"]["code"] == "SOURCE_SSRF_BLOCKED"
    assert body["error"]["retryable"] is False


def test_get_missing_source_returns_contract_error() -> None:
    client = make_client()

    response = client.get("/api/sources/src_missing")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "SOURCE_NOT_FOUND"
    assert body["error"]["details"]["sourceId"] == "src_missing"
