from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

import httpx

from app.core.config import settings
from app.core.errors import (
    source_bad_response,
    source_cookie_required,
    source_rate_limited,
    source_timeout,
    source_unreachable,
)
from app.services.collection import SourceInput, build_rsshub_feed_url
from app.services.fetch_control import collection_request_headers, retry_operation
from app.services.ssrf import SSRFGuard

@dataclass(frozen=True)
class FeedFetchResult:
    text: str
    etag: str | None = None
    last_modified: str | None = None
    not_modified: bool = False


@dataclass(frozen=True)
class FeedItemsResult:
    items: list[dict[str, Any]]
    etag: str | None = None
    last_modified: str | None = None


FetchText = Callable[[str, SourceInput, dict[str, str]], Awaitable[str | FeedFetchResult]]


class SourcePreviewer:
    def __init__(
        self,
        *,
        fetch_text: FetchText | None = None,
        rsshub_base_url: str | None = None,
        guard: SSRFGuard | None = None,
    ) -> None:
        self._fetch_text = fetch_text or self._default_fetch_text
        self._rsshub_base_url = rsshub_base_url or settings.rsshub_base_url
        self._guard = guard or SSRFGuard()

    async def preview(self, source_input: SourceInput) -> dict[str, Any]:
        sample_items = await self.fetch_items(source_input, limit=5)
        return {
            "source": {
                "name": source_input.name,
                "type": source_input.type,
                "route": source_input.route,
            },
            "sampleItems": sample_items,
            "warnings": [],
        }

    async def fetch_items(self, source_input: SourceInput, *, limit: int | None = None) -> list[dict[str, Any]]:
        result = await self.fetch_items_with_metadata(source_input, limit=limit)
        return result.items

    async def fetch_items_with_metadata(
        self,
        source_input: SourceInput,
        *,
        limit: int | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> FeedItemsResult:
        if source_input.requiresCookie:
            raise source_cookie_required()

        url = self._preview_url(source_input)
        headers = collection_request_headers(
            user_agent=settings.user_agent,
            etag=etag,
            last_modified=last_modified,
        )
        fetch_result = await retry_operation(
            lambda: self._fetch_text(url, source_input, headers),
            retry_count=source_input.retryCount,
        )
        normalized_result = fetch_result if isinstance(fetch_result, FeedFetchResult) else FeedFetchResult(text=fetch_result)
        if normalized_result.not_modified:
            return FeedItemsResult(
                items=[],
                etag=normalized_result.etag,
                last_modified=normalized_result.last_modified,
            )
        text = normalized_result.text
        items = _parse_feed_items(text)
        return FeedItemsResult(
            items=items[:limit] if limit is not None else items,
            etag=normalized_result.etag,
            last_modified=normalized_result.last_modified,
        )

    def _preview_url(self, source_input: SourceInput) -> str:
        if source_input.type == "rsshub":
            return build_rsshub_feed_url(
                base_url=self._rsshub_base_url,
                route=source_input.route or "",
                guard=self._guard,
            )
        if source_input.type in {"rss", "aihot_rss"} and source_input.url:
            self._guard.validate_url(source_input.url)
            return source_input.url
        raise source_bad_response({"reason": "unsupported_preview_source", "type": source_input.type})

    async def _default_fetch_text(self, url: str, source_input: SourceInput, headers: dict[str, str]) -> FeedFetchResult:
        try:
            async with httpx.AsyncClient(
                headers=headers,
                timeout=source_input.timeoutSeconds,
            ) as client:
                response = await client.get(url)
        except httpx.TimeoutException as exc:
            raise source_timeout({"url": url}) from exc
        except httpx.HTTPError as exc:
            raise source_unreachable({"url": url}) from exc

        if response.status_code == 304:
            return FeedFetchResult(
                text="",
                etag=response.headers.get("etag"),
                last_modified=response.headers.get("last-modified"),
                not_modified=True,
            )
        if response.status_code == 429:
            raise source_rate_limited({"url": url, "statusCode": response.status_code})
        if response.status_code >= 500:
            raise source_unreachable({"url": url, "statusCode": response.status_code})
        if response.status_code >= 400:
            raise source_bad_response({"url": url, "statusCode": response.status_code})
        return FeedFetchResult(
            text=response.text,
            etag=response.headers.get("etag"),
            last_modified=response.headers.get("last-modified"),
        )


def _parse_feed_items(text: str) -> list[dict[str, Any]]:
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        raise source_bad_response({"reason": "malformed_xml"}) from exc

    if _tag(root) == "rss":
        channel = _first_child(root, "channel")
        if channel is None:
            raise source_bad_response({"reason": "rss_channel_missing"})
        return [_rss_item(item) for item in _children(channel, "item")]
    if _tag(root) == "feed":
        return [_atom_item(entry) for entry in _children(root, "entry")]
    raise source_bad_response({"reason": "unsupported_feed_root", "root": _tag(root)})


def _rss_item(item: ElementTree.Element) -> dict[str, Any]:
    return {
        "title": _child_text(item, "title"),
        "url": _child_text(item, "link"),
        "publishedAt": _child_text(item, "pubDate"),
        "contentSnippet": _child_text(item, "description"),
    }


def _atom_item(entry: ElementTree.Element) -> dict[str, Any]:
    return {
        "title": _child_text(entry, "title"),
        "url": _atom_link(entry),
        "publishedAt": _child_text(entry, "published") or _child_text(entry, "updated"),
        "contentSnippet": _child_text(entry, "summary") or _child_text(entry, "content"),
    }


def _children(element: ElementTree.Element, tag: str) -> list[ElementTree.Element]:
    expected = tag.lower()
    return [child for child in list(element) if _tag(child) == expected]


def _first_child(element: ElementTree.Element, tag: str) -> ElementTree.Element | None:
    expected = tag.lower()
    for child in list(element):
        if _tag(child) == expected:
            return child
    return None


def _child_text(element: ElementTree.Element, tag: str) -> str | None:
    child = _first_child(element, tag)
    if child is None or child.text is None:
        return None
    value = child.text.strip()
    return value or None


def _atom_link(entry: ElementTree.Element) -> str | None:
    link = _first_child(entry, "link")
    if link is None:
        return None
    href = link.attrib.get("href")
    if href:
        return href.strip()
    return link.text.strip() if link.text else None


def _tag(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1].lower()
