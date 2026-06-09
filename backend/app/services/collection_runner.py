from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

from app.core.errors import QueryServiceError, source_cookie_required, source_disabled
from app.services.collection import normalize_raw_item
from app.services.collection_registry import InMemorySourceRepository, PostgresSourceRepository
from app.services.collection_store import InMemoryCollectionStore, PostgresCollectionStore
from app.services.fetcher_pool import FeedSourceFetcher
from app.services.fetch_control import (
    InMemorySourceLockStore,
    RedisSourceLockStore,
    SourceDedupeStore,
    source_lock_ttl_seconds,
)
from app.services.fetch_control import InMemorySourceMetadataStore, RedisSourceMetadataStore
from app.services.source_preview import SourcePreviewer

SourceItemFetcher = Callable[[dict[str, Any]], Awaitable[list[dict[str, Any]]]]


class CollectionRunner:
    def __init__(
        self,
        *,
        source_repository: InMemorySourceRepository | PostgresSourceRepository,
        store: InMemoryCollectionStore | PostgresCollectionStore,
        fetch_items: SourceItemFetcher,
        lock_store: InMemorySourceLockStore | RedisSourceLockStore,
        source_dedupe_store: SourceDedupeStore | None = None,
    ) -> None:
        self._source_repository = source_repository
        self._store = store
        self._fetch_items = fetch_items
        self._lock_store = lock_store
        self._source_dedupe_store = source_dedupe_store

    async def fetch_source(
        self,
        source_id: str,
        *,
        idempotency_key: str | None,
        trigger: str = "manual",
    ) -> dict[str, Any]:
        source = self._source_repository.get(source_id)
        if not source["enabled"]:
            raise source_disabled(source_id)
        if source["requiresCookie"]:
            raise source_cookie_required(source_id)

        existing = self._store.existing_idempotent_run(source_id, idempotency_key)
        if existing:
            return existing

        self._lock_store.acquire(
            source_id,
            ttl_seconds=source_lock_ttl_seconds(
                timeout_seconds=source["timeoutSeconds"],
                retry_count=source["retryCount"],
            ),
        )
        run = self._store.start_run(
            source_id=source_id,
            trigger=trigger,
            idempotency_key=idempotency_key,
        )
        try:
            raw_items = await self._fetch_items(source)
            fetched_at = datetime.now(timezone.utc)
            normalized_items: list[dict[str, Any]] = []
            ignored_count = 0
            for raw in raw_items:
                item = normalize_raw_item(
                    source_id=source["id"],
                    source_name=source["name"],
                    raw=raw,
                    fetched_at=fetched_at,
                )
                if item is None:
                    ignored_count += 1
                else:
                    normalized_items.append(item)
            items_to_save, dedupe_duplicate_count, reserved_dedupe_keys = self._reserve_dedupe_keys(
                source["id"],
                normalized_items,
            )
            try:
                new_count, store_duplicate_count = self._store.save_raw_items(items_to_save)
            except Exception:
                self._release_reserved_dedupe_keys(source["id"], reserved_dedupe_keys)
                raise
            duplicate_count = dedupe_duplicate_count + store_duplicate_count
            finished = self._store.finish_run(
                run["id"],
                status="succeeded",
                fetched_count=len(raw_items),
                new_count=new_count,
                duplicate_count=duplicate_count,
                ignored_count=ignored_count,
            )
            health = self._store.record_success(source)
            self._source_repository.set_status(source["id"], health["status"])
            return finished
        except QueryServiceError as exc:
            self._store.finish_run(
                run["id"],
                status="failed",
                fetched_count=0,
                new_count=0,
                duplicate_count=0,
                ignored_count=0,
                error_code=exc.code.value,
                error_message=exc.message,
            )
            health = self._store.record_failure(source, error_code=exc.code.value, error_message=exc.message)
            self._source_repository.set_status(source["id"], health["status"])
            raise
        finally:
            self._lock_store.release(source_id)

    def _reserve_dedupe_keys(
        self,
        source_id: str,
        items: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], int, list[str]]:
        if not self._source_dedupe_store:
            return items, 0, []

        items_to_save: list[dict[str, Any]] = []
        reserved_dedupe_keys: list[str] = []
        duplicate_count = 0
        for item in items:
            dedupe_key = item["dedupeKey"]
            if self._source_dedupe_store.reserve(source_id, dedupe_key):
                reserved_dedupe_keys.append(dedupe_key)
                items_to_save.append(item)
            else:
                duplicate_count += 1
        return items_to_save, duplicate_count, reserved_dedupe_keys

    def _release_reserved_dedupe_keys(
        self,
        source_id: str,
        dedupe_keys: list[str],
    ) -> None:
        if self._source_dedupe_store and dedupe_keys:
            self._source_dedupe_store.release(source_id, dedupe_keys)


def default_source_item_fetcher(
    previewer: SourcePreviewer,
    *,
    source_repository: Any | None = None,
    metadata_store: InMemorySourceMetadataStore | RedisSourceMetadataStore | None = None,
) -> SourceItemFetcher:
    return FeedSourceFetcher(
        previewer=previewer,
        source_repository=source_repository,
        metadata_store=metadata_store,
    ).fetch
