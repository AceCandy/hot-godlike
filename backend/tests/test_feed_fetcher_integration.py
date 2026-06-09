from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.collection import SourceInput
from app.services.collection_registry import InMemorySourceRepository
from app.services.collection_store import InMemoryCollectionStore
from app.services.source_preview import FeedFetchResult, SourcePreviewer
from app.services.ssrf import SSRFGuard

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_manual_fetch_custom_rss_fixture_writes_raw_items_and_metadata() -> None:
    upstream = FixtureFeedFetcher(
        {
            "https://93.184.216.34/custom-rss.xml": FeedFetchResult(
                text=fixture_text("custom-rss.xml"),
                etag="etag-custom-rss",
                last_modified="Fri, 29 May 2026 00:10:00 GMT",
            )
        }
    )
    client = make_client(upstream)
    source = client.post("/api/sources", json=custom_rss_input()).json()["data"]

    fetch_response = client.post(
        f"/api/sources/{source['id']}/fetch",
        json={"idempotencyKey": "manual-custom-rss"},
    )
    raw_response = client.get(f"/api/raw-items?sourceId={source['id']}")
    source_response = client.get(f"/api/sources/{source['id']}")

    run = fetch_response.json()["data"]
    raw_items = raw_response.json()["data"]["items"]
    updated_source = source_response.json()["data"]
    assert fetch_response.status_code == 200
    assert run["status"] == "succeeded"
    assert run["fetchedCount"] == 2
    assert run["newCount"] == 2
    assert run["duplicateCount"] == 0
    assert {item["title"] for item in raw_items} == {
        "Custom RSS first item",
        "Custom RSS second item",
    }
    assert any(item["normalizedUrl"] == "https://example.com/custom/first?id=1" for item in raw_items)
    assert updated_source["etag"] == "etag-custom-rss"
    assert updated_source["lastModified"] == "Fri, 29 May 2026 00:10:00 GMT"
    assert updated_source["lastFetchedAt"] is not None
    assert upstream.calls[0]["headers"]["User-Agent"]


def test_manual_fetch_rsshub_route_uses_configured_base_url() -> None:
    upstream = FixtureFeedFetcher(
        {
            "https://rsshub.example.com/hackernews/frontpage": FeedFetchResult(
                text=fixture_text("rsshub-hackernews.xml"),
                etag="etag-rsshub",
            )
        }
    )
    client = make_client(upstream)
    source = client.post("/api/sources", json=rsshub_input()).json()["data"]

    fetch_response = client.post(
        f"/api/sources/{source['id']}/fetch",
        json={"idempotencyKey": "manual-rsshub"},
    )
    raw_response = client.get(f"/api/raw-items?sourceId={source['id']}")

    assert fetch_response.status_code == 200
    assert fetch_response.json()["data"]["newCount"] == 1
    assert raw_response.json()["data"]["items"][0]["title"] == "RSSHub frontpage item"
    assert upstream.calls[0]["url"] == "https://rsshub.example.com/hackernews/frontpage"


def test_manual_fetch_malformed_rss_fixture_records_failed_run_and_health() -> None:
    upstream = FixtureFeedFetcher(
        {
            "https://93.184.216.34/malformed-rss.xml": FeedFetchResult(
                text=fixture_text("malformed-rss.xml"),
            )
        }
    )
    client = make_client(upstream)
    source = client.post(
        "/api/sources",
        json=custom_rss_input(
            name="Malformed RSS",
            url="https://93.184.216.34/malformed-rss.xml",
        ),
    ).json()["data"]

    fetch_response = client.post(
        f"/api/sources/{source['id']}/fetch",
        json={"idempotencyKey": "manual-malformed-rss"},
    )
    runs_response = client.get(f"/api/fetch-runs?sourceId={source['id']}")
    health_response = client.get(f"/api/source-health?sourceId={source['id']}")

    body = fetch_response.json()
    failed_run = runs_response.json()["data"]["items"][0]
    health = health_response.json()["data"]["items"][0]
    assert fetch_response.status_code == 502
    assert body["error"]["code"] == "SOURCE_BAD_RESPONSE"
    assert failed_run["status"] == "failed"
    assert failed_run["errorCode"] == "SOURCE_BAD_RESPONSE"
    assert health["consecutiveFailures"] == 1
    assert health["lastErrorCode"] == "SOURCE_BAD_RESPONSE"


class FixtureFeedFetcher:
    def __init__(self, responses: dict[str, FeedFetchResult]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    async def __call__(self, url: str, source_input: SourceInput, headers: dict[str, str]) -> FeedFetchResult:
        self.calls.append(
            {
                "url": url,
                "sourceType": source_input.type,
                "headers": headers,
            }
        )
        return self.responses[url]


def make_client(fetcher: FixtureFeedFetcher) -> TestClient:
    previewer = SourcePreviewer(
        fetch_text=fetcher,
        rsshub_base_url="https://rsshub.example.com",
        guard=SSRFGuard(resolve_host=lambda host: ["93.184.216.34"]),
    )
    app = create_app(
        source_repository=InMemorySourceRepository(),
        collection_store=InMemoryCollectionStore(),
        source_previewer=previewer,
    )
    return TestClient(app)


def custom_rss_input(
    *,
    name: str = "Custom RSS",
    url: str = "https://93.184.216.34/custom-rss.xml",
) -> dict[str, Any]:
    return {
        "name": name,
        "type": "rss",
        "category": "tech",
        "url": url,
        "route": None,
        "enabled": True,
        "fetchIntervalMinutes": 30,
        "timeoutSeconds": 30,
        "retryCount": 2,
        "concurrencyLimit": 1,
        "trustLevel": "medium",
        "requiresCookie": False,
    }


def rsshub_input() -> dict[str, Any]:
    return {
        "name": "RSSHub Hacker News",
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


def fixture_text(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")
