import pytest

from app.core.errors import QueryServiceError, source_rate_limited, source_ssrf_blocked
from app.services.fetch_control import (
    InMemorySourceLockStore,
    RedisSourceDedupeStore,
    RedisSourceLockStore,
    build_source_dedupe_store,
    build_source_lock_store,
    collection_request_headers,
    redis_key,
    retry_operation,
    source_lock_ttl_seconds,
)


def test_redis_keys_match_m2_contract() -> None:
    assert redis_key.source_lock("src_aihot_api") == "source:lock:src_aihot_api"
    assert redis_key.source_etag("src_aihot_api") == "source:etag:src_aihot_api"
    assert redis_key.source_last_modified("src_aihot_api") == "source:last_modified:src_aihot_api"
    assert redis_key.source_dedupe("src_aihot_api") == "source:dedupe:src_aihot_api"
    assert redis_key.fetch_run_progress("run_1") == "fetch_run:progress:run_1"


def test_source_lock_ttl_exceeds_timeout_retry_budget() -> None:
    ttl = source_lock_ttl_seconds(timeout_seconds=30, retry_count=2)

    assert ttl > 90


def test_redis_source_lock_uses_set_nx_ex_and_delete() -> None:
    client = FakeRedisClient()
    store = RedisSourceLockStore(client)

    key = store.acquire("src_1", ttl_seconds=95)
    store.release("src_1")

    assert key == "source:lock:src_1"
    assert client.set_calls == [
        {"name": "source:lock:src_1", "value": "locked", "nx": True, "ex": 95}
    ]
    assert client.deleted == ["source:lock:src_1"]


def test_redis_source_lock_returns_rate_limited_when_lock_exists() -> None:
    client = FakeRedisClient(set_result=False)
    store = RedisSourceLockStore(client)

    with pytest.raises(QueryServiceError) as exc:
        store.acquire("src_1", ttl_seconds=95)

    assert exc.value.code == "SOURCE_RATE_LIMITED"
    assert exc.value.details["lockKey"] == "source:lock:src_1"


def test_redis_source_dedupe_reserves_keys_with_sadd_and_can_release() -> None:
    client = FakeRedisClient(sadd_results=[1, 0])
    store = RedisSourceDedupeStore(client)

    first = store.reserve("src_1", "url:https://example.com/a")
    second = store.reserve("src_1", "url:https://example.com/a")
    store.release("src_1", ["url:https://example.com/a"])

    assert first is True
    assert second is False
    assert client.sadd_calls == [
        ("source:dedupe:src_1", ("url:https://example.com/a",)),
        ("source:dedupe:src_1", ("url:https://example.com/a",)),
    ]
    assert client.srem_calls == [
        ("source:dedupe:src_1", ("url:https://example.com/a",))
    ]


def test_build_source_lock_store_defaults_to_memory() -> None:
    store = build_source_lock_store(use_redis=False, redis_url="redis://example")

    assert isinstance(store, InMemorySourceLockStore)


def test_build_source_dedupe_store_defaults_to_none() -> None:
    store = build_source_dedupe_store(use_redis=False, redis_url="redis://example")

    assert store is None


def test_collection_request_headers_include_conditional_headers() -> None:
    headers = collection_request_headers(
        user_agent="hot-godlike-agent/0.1",
        etag="etag-1",
        last_modified="Fri, 29 May 2026 00:00:00 GMT",
    )

    assert headers == {
        "User-Agent": "hot-godlike-agent/0.1",
        "If-None-Match": "etag-1",
        "If-Modified-Since": "Fri, 29 May 2026 00:00:00 GMT",
    }


@pytest.mark.asyncio
async def test_retry_operation_retries_retryable_errors() -> None:
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise source_rate_limited({"attempt": attempts})
        return "ok"

    result = await retry_operation(operation, retry_count=2)

    assert result == "ok"
    assert attempts == 2


@pytest.mark.asyncio
async def test_retry_operation_does_not_retry_non_retryable_errors() -> None:
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        raise source_ssrf_blocked(details={"attempt": attempts})

    with pytest.raises(QueryServiceError):
        await retry_operation(operation, retry_count=2)

    assert attempts == 1


class FakeRedisClient:
    def __init__(
        self,
        *,
        set_result: bool = True,
        sadd_results: list[int] | None = None,
    ) -> None:
        self.set_result = set_result
        self.sadd_results = list(sadd_results or [])
        self.set_calls: list[dict[str, object]] = []
        self.sadd_calls: list[tuple[str, tuple[str, ...]]] = []
        self.srem_calls: list[tuple[str, tuple[str, ...]]] = []
        self.deleted: list[str] = []

    def set(self, *, name: str, value: str, nx: bool, ex: int) -> bool:
        self.set_calls.append({"name": name, "value": value, "nx": nx, "ex": ex})
        return self.set_result

    def delete(self, name: str) -> int:
        self.deleted.append(name)
        return 1

    def sadd(self, name: str, *values: str) -> int:
        self.sadd_calls.append((name, values))
        if self.sadd_results:
            return self.sadd_results.pop(0)
        return len(values)

    def srem(self, name: str, *values: str) -> int:
        self.srem_calls.append((name, values))
        return len(values)
