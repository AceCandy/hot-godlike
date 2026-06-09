from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
from uuid import uuid4

from app.core.errors import fetch_run_not_found, raw_item_not_found
from app.core.envelope import trace_id


# SourceHealth 策略集中在这里，保证内存和 PostgreSQL store 使用同一套阈值。
DEGRADED_FAILURE_THRESHOLD = 3
CIRCUIT_OPEN_FAILURE_THRESHOLD = 5
CIRCUIT_OPEN_COOLDOWN_MINUTES = 30
DEGRADED_INTERVAL_MULTIPLIER = 3


class InMemoryCollectionStore:
    def __init__(self) -> None:
        self._runs: dict[str, dict[str, Any]] = {}
        self._raw_items: dict[str, dict[str, Any]] = {}
        self._health: dict[str, dict[str, Any]] = {}
        self._dedupe_keys: set[tuple[str, str]] = set()
        self._idempotency: dict[tuple[str, str], str] = {}

    def existing_idempotent_run(self, source_id: str, idempotency_key: str | None) -> dict[str, Any] | None:
        if not idempotency_key:
            return None
        run_id = self._idempotency.get((source_id, idempotency_key))
        return dict(self._runs[run_id]) if run_id else None

    def start_run(
        self,
        *,
        source_id: str,
        trigger: str,
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        now = _utc_now()
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"
        run = {
            "id": run_id,
            "sourceId": source_id,
            "trigger": trigger,
            "status": "running",
            "startedAt": now,
            "finishedAt": None,
            "durationMs": None,
            "fetchedCount": 0,
            "newCount": 0,
            "duplicateCount": 0,
            "ignoredCount": 0,
            "errorCode": None,
            "errorMessage": None,
            "traceId": trace_id(),
        }
        self._runs[run_id] = run
        if idempotency_key:
            self._idempotency[(source_id, idempotency_key)] = run_id
        return dict(run)

    def finish_run(
        self,
        run_id: str,
        *,
        status: str,
        fetched_count: int,
        new_count: int,
        duplicate_count: int,
        ignored_count: int,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        run = self._runs.get(run_id)
        if not run:
            raise fetch_run_not_found(run_id)
        finished_at = _utc_now()
        run.update(
            {
                "status": status,
                "finishedAt": finished_at,
                "durationMs": _duration_ms(run["startedAt"], finished_at),
                "fetchedCount": fetched_count,
                "newCount": new_count,
                "duplicateCount": duplicate_count,
                "ignoredCount": ignored_count,
                "errorCode": error_code,
                "errorMessage": error_message,
            }
        )
        return dict(run)

    def save_raw_items(self, items: list[dict[str, Any]]) -> tuple[int, int]:
        new_count = 0
        duplicate_count = 0
        for item in items:
            key = (item["sourceId"], item["dedupeKey"])
            if key in self._dedupe_keys:
                duplicate_count += 1
                continue
            self._dedupe_keys.add(key)
            self._raw_items[item["id"]] = dict(item)
            new_count += 1
        return new_count, duplicate_count

    def record_success(self, source: dict[str, Any]) -> dict[str, Any]:
        now = _utc_now()
        status = _healthy_status(source)
        health = {
            "sourceId": source["id"],
            "status": status,
            "lastSucceededAt": now,
            "lastFailedAt": None,
            "consecutiveFailures": 0,
            "nextFetchAt": _next_fetch_at(source, now, status=status),
            "circuitOpenedAt": None,
            "degradedUntil": None,
            "lastErrorCode": None,
            "lastErrorMessage": None,
        }
        self._health[source["id"]] = health
        return dict(health)

    def record_failure(self, source: dict[str, Any], *, error_code: str, error_message: str) -> dict[str, Any]:
        previous = self._health.get(source["id"], {})
        failures = int(previous.get("consecutiveFailures", 0)) + 1
        status = _failure_status(source, failures)
        now = _utc_now()
        next_fetch_at = _next_fetch_at(source, now, status=status)
        health = {
            "sourceId": source["id"],
            "status": status,
            "lastSucceededAt": previous.get("lastSucceededAt"),
            "lastFailedAt": now,
            "consecutiveFailures": failures,
            "nextFetchAt": next_fetch_at,
            "circuitOpenedAt": now if status == "circuit_open" else None,
            "degradedUntil": next_fetch_at if status == "degraded" else None,
            "lastErrorCode": error_code,
            "lastErrorMessage": error_message,
        }
        self._health[source["id"]] = health
        return dict(health)

    def list_runs(self, *, source_id: str | None = None, status: str | None = None, take: int = 50) -> dict[str, Any]:
        items = list(self._runs.values())
        if source_id:
            items = [item for item in items if item["sourceId"] == source_id]
        if status:
            items = [item for item in items if item["status"] == status]
        return _page(items, take)

    def get_run(self, run_id: str) -> dict[str, Any]:
        run = self._runs.get(run_id)
        if not run:
            raise fetch_run_not_found(run_id)
        return dict(run)

    def list_raw_items(
        self,
        *,
        source_id: str | None = None,
        status: str | None = None,
        q: str | None = None,
        take: int = 50,
    ) -> dict[str, Any]:
        items = list(self._raw_items.values())
        if source_id:
            items = [item for item in items if item["sourceId"] == source_id]
        if status:
            items = [item for item in items if item["status"] == status]
        if q:
            needle = q.lower()
            items = [item for item in items if needle in item["title"].lower()]
        return _page(items, take)

    def get_raw_item(self, raw_item_id: str) -> dict[str, Any]:
        item = self._raw_items.get(raw_item_id)
        if not item:
            raise raw_item_not_found(raw_item_id)
        return dict(item)

    def list_health(self, *, source_id: str | None = None, status: str | None = None, take: int = 50) -> dict[str, Any]:
        items = list(self._health.values())
        if source_id:
            items = [item for item in items if item["sourceId"] == source_id]
        if status:
            items = [item for item in items if item["status"] == status]
        return _page(items, take)


class CollectionStoreConnection(Protocol):
    def execute(self, sql: str, params: dict[str, Any] | None = None) -> Any: ...

    def commit(self) -> None: ...


CollectionStoreConnectionFactory = Callable[[], CollectionStoreConnection]


class PostgresCollectionStore:
    def __init__(self, connection_factory: CollectionStoreConnectionFactory) -> None:
        self._connection_factory = connection_factory

    @classmethod
    def from_dsn(cls, dsn: str) -> "PostgresCollectionStore":
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("PostgresCollectionStore 需要安装 psycopg 依赖。") from exc
        return cls(lambda: psycopg.connect(dsn, row_factory=dict_row))

    def existing_idempotent_run(self, source_id: str, idempotency_key: str | None) -> dict[str, Any] | None:
        if not idempotency_key:
            return None
        with self._connection_factory() as connection:
            row = connection.execute(
                """
                select * from fetch_runs
                where source_id = %(source_id)s and idempotency_key = %(idempotency_key)s
                """,
                {"source_id": source_id, "idempotency_key": idempotency_key},
            ).fetchone()
        return _run_from_row(row) if row else None

    def start_run(
        self,
        *,
        source_id: str,
        trigger: str,
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        now = _utc_now_datetime()
        params = {
            "id": f"run_{now.strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}",
            "source_id": source_id,
            "trigger": trigger,
            "status": "running",
            "started_at": now,
            "finished_at": None,
            "duration_ms": None,
            "fetched_count": 0,
            "new_count": 0,
            "duplicate_count": 0,
            "ignored_count": 0,
            "error_code": None,
            "error_message": None,
            "trace_id": trace_id(),
            "idempotency_key": idempotency_key,
        }
        with self._connection_factory() as connection:
            row = connection.execute(_INSERT_RUN_SQL, params).fetchone()
            connection.commit()
        return _run_from_row(row)

    def finish_run(
        self,
        run_id: str,
        *,
        status: str,
        fetched_count: int,
        new_count: int,
        duplicate_count: int,
        ignored_count: int,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        current = self.get_run(run_id)
        finished_at = _utc_now_datetime()
        params = {
            "run_id": run_id,
            "status": status,
            "finished_at": finished_at,
            "duration_ms": _duration_ms(current["startedAt"], _format_utc(finished_at)),
            "fetched_count": fetched_count,
            "new_count": new_count,
            "duplicate_count": duplicate_count,
            "ignored_count": ignored_count,
            "error_code": error_code,
            "error_message": error_message,
        }
        with self._connection_factory() as connection:
            row = connection.execute(_FINISH_RUN_SQL, params).fetchone()
            if not row:
                raise fetch_run_not_found(run_id)
            connection.commit()
        return _run_from_row(row)

    def save_raw_items(self, items: list[dict[str, Any]]) -> tuple[int, int]:
        new_count = 0
        duplicate_count = 0
        with self._connection_factory() as connection:
            for item in items:
                row = connection.execute(_INSERT_RAW_ITEM_SQL, _raw_item_params(item)).fetchone()
                if row:
                    new_count += 1
                else:
                    duplicate_count += 1
            connection.commit()
        return new_count, duplicate_count

    def record_success(self, source: dict[str, Any]) -> dict[str, Any]:
        now = _utc_now_datetime()
        status = _healthy_status(source)
        next_fetch_at = _next_fetch_at_datetime(source, now, status=status)
        health = {
            "source_id": source["id"],
            "status": status,
            "last_succeeded_at": now,
            "last_failed_at": None,
            "consecutive_failures": 0,
            "next_fetch_at": next_fetch_at,
            "circuit_opened_at": None,
            "degraded_until": None,
            "last_error_code": None,
            "last_error_message": None,
            "updated_at": now,
        }
        return self._upsert_health(health)

    def record_failure(self, source: dict[str, Any], *, error_code: str, error_message: str) -> dict[str, Any]:
        previous = self._get_health_row(source["id"])
        failures = int(previous.get("consecutive_failures", 0)) + 1 if previous else 1
        status = _failure_status(source, failures)
        now = _utc_now_datetime()
        next_fetch_at = _next_fetch_at_datetime(source, now, status=status)
        health = {
            "source_id": source["id"],
            "status": status,
            "last_succeeded_at": previous.get("last_succeeded_at") if previous else None,
            "last_failed_at": now,
            "consecutive_failures": failures,
            "next_fetch_at": next_fetch_at,
            "circuit_opened_at": now if status == "circuit_open" else None,
            "degraded_until": next_fetch_at if status == "degraded" else None,
            "last_error_code": error_code,
            "last_error_message": error_message,
            "updated_at": now,
        }
        return self._upsert_health(health)

    def list_runs(self, *, source_id: str | None = None, status: str | None = None, take: int = 50) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": take + 1}
        where: list[str] = []
        if source_id:
            where.append("source_id = %(source_id)s")
            params["source_id"] = source_id
        if status:
            where.append("status = %(status)s")
            params["status"] = status
        where_sql = f" where {' and '.join(where)}" if where else ""
        with self._connection_factory() as connection:
            rows = connection.execute(
                f"select * from fetch_runs{where_sql} order by started_at desc limit %(limit)s",
                params,
            ).fetchall()
        return _page([_run_from_row(row) for row in rows[:take]], take, has_next=len(rows) > take)

    def get_run(self, run_id: str) -> dict[str, Any]:
        with self._connection_factory() as connection:
            row = connection.execute(
                "select * from fetch_runs where id = %(run_id)s",
                {"run_id": run_id},
            ).fetchone()
        if not row:
            raise fetch_run_not_found(run_id)
        return _run_from_row(row)

    def list_raw_items(
        self,
        *,
        source_id: str | None = None,
        status: str | None = None,
        q: str | None = None,
        take: int = 50,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": take + 1}
        where: list[str] = []
        if source_id:
            where.append("source_id = %(source_id)s")
            params["source_id"] = source_id
        if status:
            where.append("status = %(status)s")
            params["status"] = status
        if q:
            where.append("title ilike %(q)s")
            params["q"] = f"%{q}%"
        where_sql = f" where {' and '.join(where)}" if where else ""
        with self._connection_factory() as connection:
            rows = connection.execute(
                f"select * from raw_items{where_sql} order by fetched_at desc limit %(limit)s",
                params,
            ).fetchall()
        return _page([_raw_item_from_row(row) for row in rows[:take]], take, has_next=len(rows) > take)

    def get_raw_item(self, raw_item_id: str) -> dict[str, Any]:
        with self._connection_factory() as connection:
            row = connection.execute(
                "select * from raw_items where id = %(raw_item_id)s",
                {"raw_item_id": raw_item_id},
            ).fetchone()
        if not row:
            raise raw_item_not_found(raw_item_id)
        return _raw_item_from_row(row)

    def list_health(self, *, source_id: str | None = None, status: str | None = None, take: int = 50) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": take + 1}
        where: list[str] = []
        if source_id:
            where.append("source_id = %(source_id)s")
            params["source_id"] = source_id
        if status:
            where.append("status = %(status)s")
            params["status"] = status
        where_sql = f" where {' and '.join(where)}" if where else ""
        with self._connection_factory() as connection:
            rows = connection.execute(
                f"select * from source_health{where_sql} order by updated_at desc limit %(limit)s",
                params,
            ).fetchall()
        return _page([_health_from_row(row) for row in rows[:take]], take, has_next=len(rows) > take)

    def _get_health_row(self, source_id: str) -> dict[str, Any] | None:
        with self._connection_factory() as connection:
            return connection.execute(
                "select * from source_health where source_id = %(source_id)s",
                {"source_id": source_id},
            ).fetchone()

    def _upsert_health(self, health: dict[str, Any]) -> dict[str, Any]:
        with self._connection_factory() as connection:
            row = connection.execute(_UPSERT_HEALTH_SQL, health).fetchone()
            connection.commit()
        return _health_from_row(row)


def build_collection_store(
    *,
    use_postgres: bool,
    postgres_dsn: str | None,
) -> InMemoryCollectionStore | PostgresCollectionStore:
    if use_postgres:
        if not postgres_dsn:
            raise RuntimeError("USE_POSTGRES_COLLECTION_STORE=true 时必须设置 DATABASE_URL 或 POSTGRES_DSN。")
        return PostgresCollectionStore.from_dsn(postgres_dsn)
    return InMemoryCollectionStore()


def _page(items: list[dict[str, Any]], take: int, *, has_next: bool | None = None) -> dict[str, Any]:
    page_has_next = len(items) > take if has_next is None else has_next
    return {
        "items": [dict(item) for item in items[:take]],
        "page": {"take": take, "hasNext": page_has_next, "nextCursor": None},
    }


def _utc_now() -> str:
    return _format_utc(_utc_now_datetime())


def _utc_now_datetime() -> datetime:
    return datetime.now(timezone.utc)


def _duration_ms(started_at: str, finished_at: str) -> int:
    start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    finish = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
    return int((finish - start).total_seconds() * 1000)


def _next_fetch_at(source: dict[str, Any], current: str, *, status: str) -> str:
    return _format_utc(_next_fetch_at_datetime(source, _parse_datetime(current) or _utc_now_datetime(), status=status)) or current


def _healthy_status(source: dict[str, Any]) -> str:
    return "enabled" if source.get("enabled", True) else "disabled"


def _failure_status(source: dict[str, Any], failures: int) -> str:
    if failures >= CIRCUIT_OPEN_FAILURE_THRESHOLD:
        return "circuit_open"
    if failures >= DEGRADED_FAILURE_THRESHOLD:
        return "degraded"
    return _healthy_status(source)


def _next_fetch_at_datetime(source: dict[str, Any], current: datetime, *, status: str) -> datetime:
    if status == "circuit_open":
        return current + timedelta(minutes=CIRCUIT_OPEN_COOLDOWN_MINUTES)
    interval_minutes = int(source.get("fetchIntervalMinutes", 30))
    if status == "degraded":
        interval_minutes *= DEGRADED_INTERVAL_MULTIPLIER
    return current + timedelta(minutes=interval_minutes)


_INSERT_RUN_SQL = """
insert into fetch_runs (
    id, source_id, trigger, status, started_at, finished_at, duration_ms,
    fetched_count, new_count, duplicate_count, ignored_count,
    error_code, error_message, trace_id, idempotency_key
) values (
    %(id)s, %(source_id)s, %(trigger)s, %(status)s, %(started_at)s, %(finished_at)s, %(duration_ms)s,
    %(fetched_count)s, %(new_count)s, %(duplicate_count)s, %(ignored_count)s,
    %(error_code)s, %(error_message)s, %(trace_id)s, %(idempotency_key)s
) returning *
"""

_FINISH_RUN_SQL = """
update fetch_runs set
    status = %(status)s,
    finished_at = %(finished_at)s,
    duration_ms = %(duration_ms)s,
    fetched_count = %(fetched_count)s,
    new_count = %(new_count)s,
    duplicate_count = %(duplicate_count)s,
    ignored_count = %(ignored_count)s,
    error_code = %(error_code)s,
    error_message = %(error_message)s
where id = %(run_id)s
returning *
"""

_INSERT_RAW_ITEM_SQL = """
insert into raw_items (
    id, source_id, source_name, title, url, normalized_url, published_at, fetched_at,
    author, summary, content_snippet, hot_score, rank, image, raw_payload_ref,
    status, dedupe_key, created_at
) values (
    %(id)s, %(source_id)s, %(source_name)s, %(title)s, %(url)s, %(normalized_url)s, %(published_at)s, %(fetched_at)s,
    %(author)s, %(summary)s, %(content_snippet)s, %(hot_score)s, %(rank)s, %(image)s, %(raw_payload_ref)s,
    %(status)s, %(dedupe_key)s, %(created_at)s
) on conflict (source_id, dedupe_key) do nothing
returning id
"""

_UPSERT_HEALTH_SQL = """
insert into source_health (
    source_id, status, last_succeeded_at, last_failed_at, consecutive_failures,
    next_fetch_at, circuit_opened_at, degraded_until, last_error_code,
    last_error_message, updated_at
) values (
    %(source_id)s, %(status)s, %(last_succeeded_at)s, %(last_failed_at)s, %(consecutive_failures)s,
    %(next_fetch_at)s, %(circuit_opened_at)s, %(degraded_until)s, %(last_error_code)s,
    %(last_error_message)s, %(updated_at)s
) on conflict (source_id) do update set
    status = excluded.status,
    last_succeeded_at = excluded.last_succeeded_at,
    last_failed_at = excluded.last_failed_at,
    consecutive_failures = excluded.consecutive_failures,
    next_fetch_at = excluded.next_fetch_at,
    circuit_opened_at = excluded.circuit_opened_at,
    degraded_until = excluded.degraded_until,
    last_error_code = excluded.last_error_code,
    last_error_message = excluded.last_error_message,
    updated_at = excluded.updated_at
returning *
"""


def _raw_item_params(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "source_id": item["sourceId"],
        "source_name": item["sourceName"],
        "title": item["title"],
        "url": item["url"],
        "normalized_url": item["normalizedUrl"],
        "published_at": _parse_datetime(item.get("publishedAt")),
        "fetched_at": _parse_datetime(item["fetchedAt"]),
        "author": item.get("author"),
        "summary": item.get("summary"),
        "content_snippet": item.get("contentSnippet"),
        "hot_score": item.get("hotScore"),
        "rank": item.get("rank"),
        "image": item.get("image"),
        "raw_payload_ref": item.get("rawPayloadRef"),
        "status": item["status"],
        "dedupe_key": item["dedupeKey"],
        "created_at": _utc_now_datetime(),
    }


def _run_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "sourceId": row["source_id"],
        "trigger": row["trigger"],
        "status": row["status"],
        "startedAt": _format_utc(row["started_at"]),
        "finishedAt": _format_utc(row["finished_at"]),
        "durationMs": row["duration_ms"],
        "fetchedCount": row["fetched_count"],
        "newCount": row["new_count"],
        "duplicateCount": row["duplicate_count"],
        "ignoredCount": row["ignored_count"],
        "errorCode": row["error_code"],
        "errorMessage": row["error_message"],
        "traceId": row["trace_id"],
    }


def _raw_item_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "sourceId": row["source_id"],
        "sourceName": row["source_name"],
        "title": row["title"],
        "url": row["url"],
        "normalizedUrl": row["normalized_url"],
        "publishedAt": _format_utc(row["published_at"]),
        "fetchedAt": _format_utc(row["fetched_at"]),
        "author": row["author"],
        "summary": row["summary"],
        "contentSnippet": row["content_snippet"],
        "hotScore": row["hot_score"],
        "rank": row["rank"],
        "image": row["image"],
        "rawPayloadRef": row["raw_payload_ref"],
        "status": row["status"],
        "dedupeKey": row["dedupe_key"],
    }


def _health_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "sourceId": row["source_id"],
        "status": row["status"],
        "lastSucceededAt": _format_utc(row["last_succeeded_at"]),
        "lastFailedAt": _format_utc(row["last_failed_at"]),
        "consecutiveFailures": row["consecutive_failures"],
        "nextFetchAt": _format_utc(row["next_fetch_at"]),
        "circuitOpenedAt": _format_utc(row["circuit_opened_at"]),
        "degradedUntil": _format_utc(row["degraded_until"]),
        "lastErrorCode": row["last_error_code"],
        "lastErrorMessage": row["last_error_message"],
    }


def _parse_datetime(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise TypeError(f"unsupported datetime value: {value!r}")


def _format_utc(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        if value.endswith("Z"):
            return value
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if isinstance(value, datetime):
        normalized = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return normalized.isoformat().replace("+00:00", "Z")
    return str(value)
