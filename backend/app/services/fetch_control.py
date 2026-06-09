from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol, TypeVar

from app.core.errors import QueryServiceError, source_rate_limited

T = TypeVar("T")


@dataclass(frozen=True)
class RedisKeyBuilder:
    def source_lock(self, source_id: str) -> str:
        return f"source:lock:{source_id}"

    def source_etag(self, source_id: str) -> str:
        return f"source:etag:{source_id}"

    def source_last_modified(self, source_id: str) -> str:
        return f"source:last_modified:{source_id}"

    def source_dedupe(self, source_id: str) -> str:
        return f"source:dedupe:{source_id}"

    def fetch_run_progress(self, run_id: str) -> str:
        return f"fetch_run:progress:{run_id}"


redis_key = RedisKeyBuilder()


@dataclass(frozen=True)
class SourceFetchMetadata:
    etag: str | None = None
    last_modified: str | None = None


def source_lock_ttl_seconds(*, timeout_seconds: int, retry_count: int) -> int:
    request_budget = timeout_seconds * (retry_count + 1)
    backoff_budget = sum(2**attempt for attempt in range(retry_count))
    return request_budget + backoff_budget + 5


def collection_request_headers(
    *,
    user_agent: str,
    etag: str | None = None,
    last_modified: str | None = None,
) -> dict[str, str]:
    headers = {"User-Agent": user_agent}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    return headers


class InMemorySourceMetadataStore:
    def __init__(self) -> None:
        self._metadata: dict[str, SourceFetchMetadata] = {}

    def get(self, source_id: str) -> SourceFetchMetadata:
        return self._metadata.get(source_id, SourceFetchMetadata())

    def set(self, source_id: str, *, etag: str | None, last_modified: str | None) -> None:
        self._metadata[source_id] = SourceFetchMetadata(etag=etag, last_modified=last_modified)


class RedisMetadataClient(Protocol):
    def get(self, name: str) -> object: ...

    def set(self, name: str, value: str) -> object: ...

    def delete(self, name: str) -> object: ...


class RedisSourceMetadataStore:
    def __init__(self, client: RedisMetadataClient) -> None:
        self._client = client

    @classmethod
    def from_url(cls, redis_url: str) -> "RedisSourceMetadataStore":
        try:
            from redis import Redis
        except ImportError as exc:
            raise RuntimeError("RedisSourceMetadataStore 需要安装 redis 依赖。") from exc
        return cls(Redis.from_url(redis_url))

    def get(self, source_id: str) -> SourceFetchMetadata:
        return SourceFetchMetadata(
            etag=_decode_redis_value(self._client.get(redis_key.source_etag(source_id))),
            last_modified=_decode_redis_value(self._client.get(redis_key.source_last_modified(source_id))),
        )

    def set(self, source_id: str, *, etag: str | None, last_modified: str | None) -> None:
        _set_or_delete(self._client, redis_key.source_etag(source_id), etag)
        _set_or_delete(self._client, redis_key.source_last_modified(source_id), last_modified)


async def retry_operation(
    operation: Callable[[], Awaitable[T]],
    *,
    retry_count: int,
) -> T:
    attempts = retry_count + 1
    for attempt in range(attempts):
        try:
            return await operation()
        except QueryServiceError as exc:
            if not exc.retryable or attempt >= attempts - 1:
                raise
    raise RuntimeError("unreachable retry state")


class InMemorySourceLockStore:
    def __init__(self) -> None:
        self._locks: dict[str, datetime] = {}

    def acquire(self, source_id: str, *, ttl_seconds: int) -> str:
        key = redis_key.source_lock(source_id)
        now = datetime.now(timezone.utc)
        expires_at = self._locks.get(key)
        if expires_at and expires_at > now:
            raise source_rate_limited({"sourceId": source_id, "lockKey": key})
        self._locks[key] = now + timedelta(seconds=ttl_seconds)
        return key

    def release(self, source_id: str) -> None:
        self._locks.pop(redis_key.source_lock(source_id), None)

    def is_locked(self, source_id: str) -> bool:
        key = redis_key.source_lock(source_id)
        expires_at = self._locks.get(key)
        if not expires_at:
            return False
        if expires_at <= datetime.now(timezone.utc):
            self._locks.pop(key, None)
            return False
        return True


class SyncRedisClient(Protocol):
    def set(self, *, name: str, value: str, nx: bool, ex: int) -> object: ...

    def delete(self, name: str) -> object: ...


class SourceDedupeStore(Protocol):
    def reserve(self, source_id: str, dedupe_key: str) -> bool: ...

    def release(self, source_id: str, dedupe_keys: list[str]) -> None: ...


class RedisSourceLockStore:
    def __init__(self, client: SyncRedisClient) -> None:
        self._client = client

    @classmethod
    def from_url(cls, redis_url: str) -> "RedisSourceLockStore":
        try:
            from redis import Redis
        except ImportError as exc:
            raise RuntimeError("RedisSourceLockStore 需要安装 redis 依赖。") from exc
        return cls(Redis.from_url(redis_url))

    def acquire(self, source_id: str, *, ttl_seconds: int) -> str:
        key = redis_key.source_lock(source_id)
        acquired = self._client.set(name=key, value="locked", nx=True, ex=ttl_seconds)
        if not acquired:
            raise source_rate_limited({"sourceId": source_id, "lockKey": key})
        return key

    def release(self, source_id: str) -> None:
        self._client.delete(redis_key.source_lock(source_id))


class RedisDedupeClient(Protocol):
    def sadd(self, name: str, *values: str) -> object: ...

    def srem(self, name: str, *values: str) -> object: ...


class RedisSourceDedupeStore:
    def __init__(self, client: RedisDedupeClient) -> None:
        self._client = client

    @classmethod
    def from_url(cls, redis_url: str) -> "RedisSourceDedupeStore":
        try:
            from redis import Redis
        except ImportError as exc:
            raise RuntimeError("RedisSourceDedupeStore 需要安装 redis 依赖。") from exc
        return cls(Redis.from_url(redis_url))

    def reserve(self, source_id: str, dedupe_key: str) -> bool:
        # Redis SADD 返回 1 表示新 key，0 表示集合内已存在，可作为源内去重快速路径。
        added = self._client.sadd(redis_key.source_dedupe(source_id), dedupe_key)
        return bool(added)

    def release(self, source_id: str, dedupe_keys: list[str]) -> None:
        if not dedupe_keys:
            return
        self._client.srem(redis_key.source_dedupe(source_id), *dedupe_keys)


def build_source_lock_store(*, use_redis: bool, redis_url: str) -> InMemorySourceLockStore | RedisSourceLockStore:
    if use_redis:
        return RedisSourceLockStore.from_url(redis_url)
    return InMemorySourceLockStore()


def build_source_dedupe_store(
    *,
    use_redis: bool,
    redis_url: str,
) -> RedisSourceDedupeStore | None:
    if use_redis:
        return RedisSourceDedupeStore.from_url(redis_url)
    return None


def build_source_metadata_store(
    *,
    use_redis: bool,
    redis_url: str,
) -> InMemorySourceMetadataStore | RedisSourceMetadataStore:
    if use_redis:
        return RedisSourceMetadataStore.from_url(redis_url)
    return InMemorySourceMetadataStore()


def _decode_redis_value(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _set_or_delete(client: RedisMetadataClient, key: str, value: str | None) -> None:
    if value:
        client.set(key, value)
    else:
        client.delete(key)
