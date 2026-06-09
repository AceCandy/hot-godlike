from datetime import datetime, timezone

import pytest

from app.core.errors import ErrorCode, QueryServiceError
from app.services.collection import (
    SourceInput,
    build_rsshub_feed_url,
    normalize_raw_item,
)
from app.services.ssrf import SSRFGuard


def test_source_input_validates_rss_url_with_ssrf_guard() -> None:
    with pytest.raises(QueryServiceError) as exc:
        SourceInput(
            name="Local RSS",
            type="rss",
            category="tech",
            url="http://127.0.0.1/feed.xml",
            route=None,
            enabled=True,
            fetchIntervalMinutes=30,
            timeoutSeconds=30,
            retryCount=2,
            concurrencyLimit=1,
            trustLevel="medium",
            requiresCookie=False,
        )

    assert exc.value.code == ErrorCode.SOURCE_SSRF_BLOCKED


def test_source_input_requires_rsshub_route() -> None:
    with pytest.raises(QueryServiceError) as exc:
        SourceInput(
            name="HN",
            type="rsshub",
            category="tech",
            url=None,
            route=None,
            enabled=True,
            fetchIntervalMinutes=30,
            timeoutSeconds=30,
            retryCount=2,
            concurrencyLimit=1,
            trustLevel="medium",
            requiresCookie=False,
        )

    assert exc.value.code == ErrorCode.BAD_REQUEST
    assert "route" in exc.value.details


def test_source_input_rejects_invalid_category_and_ranges() -> None:
    with pytest.raises(QueryServiceError) as exc:
        SourceInput(
            name="Bad",
            type="rss",
            category="科技",
            url="https://example.com/feed.xml",
            route=None,
            enabled=True,
            fetchIntervalMinutes=3,
            timeoutSeconds=30,
            retryCount=2,
            concurrencyLimit=1,
            trustLevel="medium",
            requiresCookie=False,
        )

    assert exc.value.code == ErrorCode.BAD_REQUEST
    assert "category" in exc.value.details


def test_ssrf_guard_blocks_private_hostnames_and_file_scheme() -> None:
    guard = SSRFGuard(resolve_host=lambda host: ["10.0.0.8"])

    with pytest.raises(QueryServiceError) as private_exc:
        guard.validate_url("https://internal.example.com/feed.xml")
    with pytest.raises(QueryServiceError) as scheme_exc:
        guard.validate_url("file:///etc/passwd")

    assert private_exc.value.code == ErrorCode.SOURCE_SSRF_BLOCKED
    assert scheme_exc.value.code == ErrorCode.SOURCE_SSRF_BLOCKED


def test_build_rsshub_feed_url_normalizes_route_and_checks_base_url() -> None:
    guard = SSRFGuard(resolve_host=lambda host: ["93.184.216.34"])

    url = build_rsshub_feed_url(
        base_url="https://rsshub.example.com/",
        route="hackernews/frontpage",
        guard=guard,
    )

    assert url == "https://rsshub.example.com/hackernews/frontpage"


def test_normalize_raw_item_generates_normalized_url_and_dedupe_key() -> None:
    fetched_at = datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)

    item = normalize_raw_item(
        source_id="src_rss",
        source_name="Example RSS",
        raw={
            "title": "  Example Item  ",
            "url": "HTTPS://Example.com/news/?utm_source=x&id=1#section",
            "publishedAt": "2026-05-29T00:00:00Z",
            "summary": "摘要",
            "rank": "3",
        },
        fetched_at=fetched_at,
    )

    assert item is not None
    assert item["title"] == "Example Item"
    assert item["normalizedUrl"] == "https://example.com/news/?id=1"
    assert item["dedupeKey"] == "url:https://example.com/news/?id=1"
    assert item["rank"] == 3
    assert item["status"] == "new"


def test_normalize_raw_item_falls_back_to_title_date_key_when_url_missing() -> None:
    fetched_at = datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)

    item = normalize_raw_item(
        source_id="src_rss",
        source_name="Example RSS",
        raw={"title": "OpenAI 发布 新模型", "publishedAt": "2026-05-29T00:00:00Z"},
        fetched_at=fetched_at,
    )

    assert item is not None
    assert item["url"] == ""
    assert item["normalizedUrl"] == ""
    assert item["dedupeKey"] == "title_date:openai-发布-新模型:2026-05-29"


def test_normalize_raw_item_ignores_missing_title() -> None:
    item = normalize_raw_item(
        source_id="src_rss",
        source_name="Example RSS",
        raw={"url": "https://example.com"},
        fetched_at=datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc),
    )

    assert item is None
