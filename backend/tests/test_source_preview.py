from collections.abc import Awaitable, Callable

import pytest

from app.core.errors import ErrorCode, QueryServiceError
from app.core.errors import source_rate_limited
from app.services.collection import SourceInput
from app.services.source_preview import FeedFetchResult, SourcePreviewer
from app.services.ssrf import SSRFGuard

RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <item>
      <title>First item</title>
      <link>https://example.com/first</link>
      <pubDate>Fri, 29 May 2026 00:00:00 GMT</pubDate>
      <description>First summary</description>
    </item>
    <item>
      <title>Second item</title>
      <link>https://example.com/second</link>
      <description>Second summary</description>
    </item>
  </channel>
</rss>
"""


def rsshub_source() -> SourceInput:
    return SourceInput(
        name="Hacker News",
        type="rsshub",
        category="tech",
        url=None,
        route="/hackernews/frontpage",
        enabled=True,
        fetchIntervalMinutes=30,
        timeoutSeconds=30,
        retryCount=2,
        concurrencyLimit=1,
        trustLevel="medium",
        requiresCookie=False,
    )


@pytest.mark.asyncio
async def test_previewer_builds_rsshub_url_and_parses_rss_items() -> None:
    seen_urls: list[str] = []
    seen_headers: list[dict[str, str]] = []

    async def fetch_text(url: str, source_input: SourceInput, headers: dict[str, str]) -> str:
        seen_urls.append(url)
        seen_headers.append(headers)
        return RSS_XML

    previewer = make_previewer(fetch_text)

    result = await previewer.preview(rsshub_source())

    assert seen_urls == ["https://rsshub.example.com/hackernews/frontpage"]
    assert "User-Agent" in seen_headers[0]
    assert result["source"] == {
        "name": "Hacker News",
        "type": "rsshub",
        "route": "/hackernews/frontpage",
    }
    assert result["sampleItems"][0] == {
        "title": "First item",
        "url": "https://example.com/first",
        "publishedAt": "Fri, 29 May 2026 00:00:00 GMT",
        "contentSnippet": "First summary",
    }


@pytest.mark.asyncio
async def test_previewer_rejects_malformed_rss_with_contract_error() -> None:
    async def fetch_text(url: str, source_input: SourceInput, headers: dict[str, str]) -> str:
        return "<rss><channel>"

    previewer = make_previewer(fetch_text)

    with pytest.raises(QueryServiceError) as exc:
        await previewer.preview(rsshub_source())

    assert exc.value.code == ErrorCode.SOURCE_BAD_RESPONSE


@pytest.mark.asyncio
async def test_previewer_retries_retryable_fetch_errors() -> None:
    attempts = 0

    async def fetch_text(url: str, source_input: SourceInput, headers: dict[str, str]) -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise source_rate_limited({"attempt": attempts})
        return RSS_XML

    previewer = make_previewer(fetch_text)

    result = await previewer.preview(rsshub_source())

    assert attempts == 2
    assert result["sampleItems"][0]["title"] == "First item"


@pytest.mark.asyncio
async def test_fetch_items_with_metadata_passes_conditional_headers() -> None:
    seen_headers: list[dict[str, str]] = []

    async def fetch_text(url: str, source_input: SourceInput, headers: dict[str, str]) -> str:
        seen_headers.append(headers)
        return RSS_XML

    previewer = make_previewer(fetch_text)

    result = await previewer.fetch_items_with_metadata(
        rsshub_source(),
        etag="etag-1",
        last_modified="Fri, 29 May 2026 00:00:00 GMT",
    )

    assert result.items[0]["title"] == "First item"
    assert seen_headers[0]["If-None-Match"] == "etag-1"
    assert seen_headers[0]["If-Modified-Since"] == "Fri, 29 May 2026 00:00:00 GMT"


@pytest.mark.asyncio
async def test_fetch_items_with_metadata_handles_not_modified_without_parsing_body() -> None:
    async def fetch_text(url: str, source_input: SourceInput, headers: dict[str, str]) -> FeedFetchResult:
        return FeedFetchResult(text="", etag="etag-1", not_modified=True)

    previewer = make_previewer(fetch_text)

    result = await previewer.fetch_items_with_metadata(rsshub_source(), etag="etag-1")

    assert result.items == []
    assert result.etag == "etag-1"


def make_previewer(
    fetch_text: Callable[[str, SourceInput, dict[str, str]], Awaitable[str | FeedFetchResult]],
) -> SourcePreviewer:
    return SourcePreviewer(
        fetch_text=fetch_text,
        rsshub_base_url="https://rsshub.example.com",
        guard=SSRFGuard(resolve_host=lambda host: ["93.184.216.34"]),
    )
