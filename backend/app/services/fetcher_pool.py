from datetime import datetime, timezone
from typing import Any, Protocol

from app.core.errors import (
    ErrorCode,
    QueryServiceError,
    source_bad_response,
    source_rate_limited,
    source_timeout,
    source_unreachable,
)
from app.services.aihot_client import AihotClient
from app.services.cache import InMemoryCacheStore
from app.services.collection import SourceInput
from app.services.fetch_control import InMemorySourceMetadataStore, RedisSourceMetadataStore
from app.services.normalizer import normalize_items
from app.services.planner import plan_items
from app.services.source_preview import SourcePreviewer


class TypedFetcher(Protocol):
    async def fetch(self, source: dict[str, Any]) -> list[dict[str, Any]]: ...


class FetcherPool:
    def __init__(
        self,
        *,
        aihot_fetcher: TypedFetcher,
        feed_fetcher: TypedFetcher,
    ) -> None:
        self._aihot_fetcher = aihot_fetcher
        self._feed_fetcher = feed_fetcher

    async def fetch(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        source_type = source["type"]
        if source_type == "aihot_api":
            return await self._aihot_fetcher.fetch(source)
        if source_type in {"aihot_rss", "rss", "rsshub"}:
            return await self._feed_fetcher.fetch(source)
        raise source_bad_response({"reason": "unsupported_source_type", "type": source_type})


class AihotApiFetcher:
    def __init__(self, *, aihot_client: AihotClient, cache: InMemoryCacheStore) -> None:
        self._aihot_client = aihot_client
        self._cache = cache

    async def fetch(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        plan = plan_items(mode="selected", take=50)
        try:
            result = await self._aihot_client.fetch_json(plan, self._cache)
            if result.not_modified:
                return []
            normalized = normalize_items(result.data, window=plan.window)
        except QueryServiceError as exc:
            raise _collection_error(exc, source["id"]) from exc
        return [_aihot_raw_item(item) for item in normalized["items"]]


class FeedSourceFetcher:
    def __init__(
        self,
        *,
        previewer: SourcePreviewer,
        source_repository: Any | None = None,
        metadata_store: InMemorySourceMetadataStore | RedisSourceMetadataStore | None = None,
    ) -> None:
        self._previewer = previewer
        self._source_repository = source_repository
        self._metadata_store = metadata_store

    async def fetch(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        source_input = SourceInput(
            name=source["name"],
            type=source["type"],
            category=source["category"],
            url=source["url"],
            route=source["route"],
            enabled=source["enabled"],
            fetchIntervalMinutes=source["fetchIntervalMinutes"],
            timeoutSeconds=source["timeoutSeconds"],
            retryCount=source["retryCount"],
            concurrencyLimit=source["concurrencyLimit"],
            trustLevel=source["trustLevel"],
            requiresCookie=source["requiresCookie"],
        )
        metadata = self._metadata_store.get(source["id"]) if self._metadata_store else None
        etag = (metadata.etag if metadata else None) or source.get("etag")
        last_modified = (metadata.last_modified if metadata else None) or source.get("lastModified")
        result = await self._previewer.fetch_items_with_metadata(
            source_input,
            etag=etag,
            last_modified=last_modified,
        )
        if self._metadata_store:
            self._metadata_store.set(
                source["id"],
                etag=result.etag,
                last_modified=result.last_modified,
            )
        if self._source_repository and hasattr(self._source_repository, "set_fetch_metadata"):
            self._source_repository.set_fetch_metadata(
                source["id"],
                etag=result.etag,
                last_modified=result.last_modified,
                fetched_at=_format_utc(datetime.now(timezone.utc)),
            )
        return result.items


def build_fetcher_pool(
    *,
    aihot_client: AihotClient,
    cache: InMemoryCacheStore,
    previewer: SourcePreviewer,
    source_repository: Any | None,
    metadata_store: InMemorySourceMetadataStore | RedisSourceMetadataStore | None,
) -> FetcherPool:
    return FetcherPool(
        aihot_fetcher=AihotApiFetcher(aihot_client=aihot_client, cache=cache),
        feed_fetcher=FeedSourceFetcher(
            previewer=previewer,
            source_repository=source_repository,
            metadata_store=metadata_store,
        ),
    )


def _aihot_raw_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": item["title"],
        "url": item["url"],
        "publishedAt": item.get("publishedAt"),
        "summary": item.get("summary"),
        "hotScore": item.get("score"),
    }


def _collection_error(exc: QueryServiceError, source_id: str) -> QueryServiceError:
    details = {"sourceId": source_id}
    if exc.code == ErrorCode.UPSTREAM_RATE_LIMITED:
        return source_rate_limited(details)
    if exc.code == ErrorCode.UPSTREAM_TIMEOUT:
        return source_timeout(details)
    if exc.code == ErrorCode.UPSTREAM_BAD_RESPONSE:
        return source_bad_response(details)
    return source_unreachable({"sourceId": source_id, "upstreamCode": exc.code.value})


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
