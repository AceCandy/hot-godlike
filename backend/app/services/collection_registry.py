from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from app.core.errors import source_not_found
from app.services.collection import SourceInput
from app.services.sqlite_storage import (
    ensure_collection_schema,
    normalize_storage_mode,
    sqlite_connection_factory,
    sqlite_params,
)


class InMemorySourceRepository:
    def __init__(self) -> None:
        self._sources: dict[str, dict[str, Any]] = {}

    def create(self, source_input: SourceInput) -> dict[str, Any]:
        now = _utc_now()
        source_id = f"src_{_slug(source_input.name)}_{uuid4().hex[:8]}"
        source = {
            "id": source_id,
            "name": source_input.name.strip(),
            "type": source_input.type,
            "category": source_input.category.strip(),
            "url": source_input.url,
            "route": source_input.route,
            "enabled": source_input.enabled,
            "status": "enabled" if source_input.enabled else "disabled",
            "fetchIntervalMinutes": source_input.fetchIntervalMinutes,
            "timeoutSeconds": source_input.timeoutSeconds,
            "retryCount": source_input.retryCount,
            "concurrencyLimit": source_input.concurrencyLimit,
            "trustLevel": source_input.trustLevel,
            "requiresCookie": source_input.requiresCookie,
            "firstFetchMode": "ingest_only",
            "etag": None,
            "lastModified": None,
            "lastFetchedAt": None,
            "createdAt": now,
            "updatedAt": now,
        }
        self._sources[source_id] = source
        return dict(source)

    def list(
        self,
        *,
        source_type: str | None = None,
        status: str | None = None,
        take: int = 50,
    ) -> dict[str, Any]:
        items = list(self._sources.values())
        if source_type:
            items = [item for item in items if item["type"] == source_type]
        if status:
            items = [item for item in items if item["status"] == status]
        return {
            "items": [dict(item) for item in items[:take]],
            "page": {
                "take": take,
                "hasNext": len(items) > take,
                "nextCursor": None,
            },
        }

    def get(self, source_id: str) -> dict[str, Any]:
        source = self._sources.get(source_id)
        if not source:
            raise source_not_found(source_id)
        return dict(source)

    def update(self, source_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        current = self._sources.get(source_id)
        if not current:
            raise source_not_found(source_id)

        merged = dict(current)
        merged.update({key: value for key, value in updates.items() if key in _SOURCE_INPUT_KEYS})
        source_input = SourceInput(
            name=merged["name"],
            type=merged["type"],
            category=merged["category"],
            url=merged["url"],
            route=merged["route"],
            enabled=merged["enabled"],
            fetchIntervalMinutes=merged["fetchIntervalMinutes"],
            timeoutSeconds=merged["timeoutSeconds"],
            retryCount=merged["retryCount"],
            concurrencyLimit=merged["concurrencyLimit"],
            trustLevel=merged["trustLevel"],
            requiresCookie=merged["requiresCookie"],
        )
        current.update(
            {
                "name": source_input.name.strip(),
                "type": source_input.type,
                "category": source_input.category.strip(),
                "url": source_input.url,
                "route": source_input.route,
                "enabled": source_input.enabled,
                "status": "enabled" if source_input.enabled else "disabled",
                "fetchIntervalMinutes": source_input.fetchIntervalMinutes,
                "timeoutSeconds": source_input.timeoutSeconds,
                "retryCount": source_input.retryCount,
                "concurrencyLimit": source_input.concurrencyLimit,
                "trustLevel": source_input.trustLevel,
                "requiresCookie": source_input.requiresCookie,
                "updatedAt": _utc_now(),
            }
        )
        return dict(current)

    def set_enabled(self, source_id: str, enabled: bool) -> dict[str, Any]:
        source = self._sources.get(source_id)
        if not source:
            raise source_not_found(source_id)
        source["enabled"] = enabled
        source["status"] = "enabled" if enabled else "disabled"
        source["updatedAt"] = _utc_now()
        return dict(source)

    def set_status(self, source_id: str, status: str) -> dict[str, Any]:
        source = self._sources.get(source_id)
        if not source:
            raise source_not_found(source_id)
        source["status"] = status
        source["updatedAt"] = _utc_now()
        return dict(source)

    def set_fetch_metadata(
        self,
        source_id: str,
        *,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> dict[str, Any]:
        source = self._sources.get(source_id)
        if not source:
            raise source_not_found(source_id)
        source["etag"] = etag
        source["lastModified"] = last_modified
        source["lastFetchedAt"] = fetched_at
        source["updatedAt"] = _utc_now()
        return dict(source)


class SourceRepositoryConnection(Protocol):
    def execute(self, sql: str, params: dict[str, Any] | None = None) -> Any: ...

    def commit(self) -> None: ...


SourceRepositoryConnectionFactory = Callable[[], SourceRepositoryConnection]


class PostgresSourceRepository:
    def __init__(self, connection_factory: SourceRepositoryConnectionFactory) -> None:
        self._connection_factory = connection_factory

    @classmethod
    def from_dsn(cls, dsn: str) -> "PostgresSourceRepository":
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("PostgresSourceRepository 需要安装 psycopg 依赖。") from exc
        return cls(lambda: psycopg.connect(dsn, row_factory=dict_row))

    def create(self, source_input: SourceInput) -> dict[str, Any]:
        now = _utc_now_datetime()
        params = _source_insert_params(
            source_id=f"src_{_slug(source_input.name)}_{uuid4().hex[:8]}",
            source_input=source_input,
            now=now,
        )
        with self._connection_factory() as connection:
            row = connection.execute(_INSERT_SOURCE_SQL, params).fetchone()
            connection.commit()
        return _source_from_row(row)

    def list(
        self,
        *,
        source_type: str | None = None,
        status: str | None = None,
        take: int = 50,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": take + 1}
        where: list[str] = []
        if source_type:
            where.append("type = %(source_type)s")
            params["source_type"] = source_type
        if status:
            where.append("status = %(status)s")
            params["status"] = status
        where_sql = f" where {' and '.join(where)}" if where else ""
        sql = f"select * from sources{where_sql} order by created_at asc limit %(limit)s"
        with self._connection_factory() as connection:
            rows = connection.execute(sql, params).fetchall()
        items = [_source_from_row(row) for row in rows[:take]]
        return {
            "items": items,
            "page": {
                "take": take,
                "hasNext": len(rows) > take,
                "nextCursor": None,
            },
        }

    def get(self, source_id: str) -> dict[str, Any]:
        with self._connection_factory() as connection:
            row = connection.execute(
                "select * from sources where id = %(source_id)s",
                {"source_id": source_id},
            ).fetchone()
        if not row:
            raise source_not_found(source_id)
        return _source_from_row(row)

    def update(self, source_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        with self._connection_factory() as connection:
            row = connection.execute(
                "select * from sources where id = %(source_id)s",
                {"source_id": source_id},
            ).fetchone()
            if not row:
                raise source_not_found(source_id)

            current = _source_from_row(row)
            merged = dict(current)
            merged.update({key: value for key, value in updates.items() if key in _SOURCE_INPUT_KEYS})
            source_input = SourceInput(
                name=merged["name"],
                type=merged["type"],
                category=merged["category"],
                url=merged["url"],
                route=merged["route"],
                enabled=merged["enabled"],
                fetchIntervalMinutes=merged["fetchIntervalMinutes"],
                timeoutSeconds=merged["timeoutSeconds"],
                retryCount=merged["retryCount"],
                concurrencyLimit=merged["concurrencyLimit"],
                trustLevel=merged["trustLevel"],
                requiresCookie=merged["requiresCookie"],
            )
            updated = connection.execute(
                _UPDATE_SOURCE_SQL,
                _source_update_params(source_id=source_id, source_input=source_input, now=_utc_now_datetime()),
            ).fetchone()
            connection.commit()
        return _source_from_row(updated)

    def set_enabled(self, source_id: str, enabled: bool) -> dict[str, Any]:
        with self._connection_factory() as connection:
            row = connection.execute(
                _SET_SOURCE_ENABLED_SQL,
                {
                    "source_id": source_id,
                    "enabled": enabled,
                    "status": "enabled" if enabled else "disabled",
                    "updated_at": _utc_now_datetime(),
                },
            ).fetchone()
            if not row:
                raise source_not_found(source_id)
            connection.commit()
        return _source_from_row(row)

    def set_status(self, source_id: str, status: str) -> dict[str, Any]:
        with self._connection_factory() as connection:
            row = connection.execute(
                _SET_SOURCE_STATUS_SQL,
                {
                    "source_id": source_id,
                    "status": status,
                    "updated_at": _utc_now_datetime(),
                },
            ).fetchone()
            if not row:
                raise source_not_found(source_id)
            connection.commit()
        return _source_from_row(row)

    def set_fetch_metadata(
        self,
        source_id: str,
        *,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> dict[str, Any]:
        with self._connection_factory() as connection:
            row = connection.execute(
                _SET_SOURCE_FETCH_METADATA_SQL,
                {
                    "source_id": source_id,
                    "etag": etag,
                    "last_modified": last_modified,
                    "last_fetched_at": _parse_datetime(fetched_at),
                    "updated_at": _utc_now_datetime(),
                },
            ).fetchone()
            if not row:
                raise source_not_found(source_id)
            connection.commit()
        return _source_from_row(row)


class SqliteSourceRepository:
    def __init__(self, connection_factory: SourceRepositoryConnectionFactory) -> None:
        self._connection_factory = connection_factory
        with self._connection_factory() as connection:
            ensure_collection_schema(connection)

    @classmethod
    def from_path(cls, path: str) -> "SqliteSourceRepository":
        return cls(sqlite_connection_factory(path))

    def create(self, source_input: SourceInput) -> dict[str, Any]:
        now = _utc_now_datetime()
        params = _source_insert_params(
            source_id=f"src_{_slug(source_input.name)}_{uuid4().hex[:8]}",
            source_input=source_input,
            now=now,
        )
        with self._connection_factory() as connection:
            connection.execute(_SQLITE_INSERT_SOURCE_SQL, sqlite_params(params))
            connection.commit()
        return self.get(params["id"])

    def list(
        self,
        *,
        source_type: str | None = None,
        status: str | None = None,
        take: int = 50,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": take + 1}
        where: list[str] = []
        if source_type:
            where.append("type = :source_type")
            params["source_type"] = source_type
        if status:
            where.append("status = :status")
            params["status"] = status
        where_sql = f" where {' and '.join(where)}" if where else ""
        with self._connection_factory() as connection:
            rows = connection.execute(
                f"select * from sources{where_sql} order by created_at asc limit :limit",
                params,
            ).fetchall()
        items = [_source_from_row(row) for row in rows[:take]]
        return {
            "items": items,
            "page": {
                "take": take,
                "hasNext": len(rows) > take,
                "nextCursor": None,
            },
        }

    def get(self, source_id: str) -> dict[str, Any]:
        with self._connection_factory() as connection:
            row = connection.execute(
                "select * from sources where id = :source_id",
                {"source_id": source_id},
            ).fetchone()
        if not row:
            raise source_not_found(source_id)
        return _source_from_row(row)

    def update(self, source_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        current = self.get(source_id)
        merged = dict(current)
        merged.update({key: value for key, value in updates.items() if key in _SOURCE_INPUT_KEYS})
        source_input = SourceInput(
            name=merged["name"],
            type=merged["type"],
            category=merged["category"],
            url=merged["url"],
            route=merged["route"],
            enabled=merged["enabled"],
            fetchIntervalMinutes=merged["fetchIntervalMinutes"],
            timeoutSeconds=merged["timeoutSeconds"],
            retryCount=merged["retryCount"],
            concurrencyLimit=merged["concurrencyLimit"],
            trustLevel=merged["trustLevel"],
            requiresCookie=merged["requiresCookie"],
        )
        with self._connection_factory() as connection:
            cursor = connection.execute(
                _SQLITE_UPDATE_SOURCE_SQL,
                sqlite_params(
                    _source_update_params(
                        source_id=source_id,
                        source_input=source_input,
                        now=_utc_now_datetime(),
                    )
                ),
            )
            if cursor.rowcount == 0:
                raise source_not_found(source_id)
            connection.commit()
        return self.get(source_id)

    def set_enabled(self, source_id: str, enabled: bool) -> dict[str, Any]:
        with self._connection_factory() as connection:
            cursor = connection.execute(
                _SQLITE_SET_SOURCE_ENABLED_SQL,
                sqlite_params(
                    {
                        "source_id": source_id,
                        "enabled": enabled,
                        "status": "enabled" if enabled else "disabled",
                        "updated_at": _utc_now_datetime(),
                    }
                ),
            )
            if cursor.rowcount == 0:
                raise source_not_found(source_id)
            connection.commit()
        return self.get(source_id)

    def set_status(self, source_id: str, status: str) -> dict[str, Any]:
        with self._connection_factory() as connection:
            cursor = connection.execute(
                _SQLITE_SET_SOURCE_STATUS_SQL,
                sqlite_params(
                    {
                        "source_id": source_id,
                        "status": status,
                        "updated_at": _utc_now_datetime(),
                    }
                ),
            )
            if cursor.rowcount == 0:
                raise source_not_found(source_id)
            connection.commit()
        return self.get(source_id)

    def set_fetch_metadata(
        self,
        source_id: str,
        *,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> dict[str, Any]:
        with self._connection_factory() as connection:
            cursor = connection.execute(
                _SQLITE_SET_SOURCE_FETCH_METADATA_SQL,
                sqlite_params(
                    {
                        "source_id": source_id,
                        "etag": etag,
                        "last_modified": last_modified,
                        "last_fetched_at": _parse_datetime(fetched_at),
                        "updated_at": _utc_now_datetime(),
                    }
                ),
            )
            if cursor.rowcount == 0:
                raise source_not_found(source_id)
            connection.commit()
        return self.get(source_id)


def build_source_repository(
    *,
    storage_mode: str | None = None,
    local_sqlite_path: str | None = None,
    use_postgres: bool,
    postgres_dsn: str | None,
) -> InMemorySourceRepository | PostgresSourceRepository | SqliteSourceRepository:
    mode = normalize_storage_mode(storage_mode)
    if mode == "local":
        if not local_sqlite_path:
            raise RuntimeError("STORAGE_MODE=local 时必须设置 LOCAL_STORAGE_PATH。")
        return SqliteSourceRepository.from_path(local_sqlite_path)
    if mode == "postgres":
        use_postgres = True
    if mode == "memory":
        use_postgres = False

    if use_postgres:
        if not postgres_dsn:
            raise RuntimeError("USE_POSTGRES_SOURCE_REPOSITORY=true 时必须设置 DATABASE_URL 或 POSTGRES_DSN。")
        return PostgresSourceRepository.from_dsn(postgres_dsn)
    return InMemorySourceRepository()


def _utc_now() -> str:
    return _format_utc(_utc_now_datetime())


def _utc_now_datetime() -> datetime:
    return datetime.now(timezone.utc)


def _slug(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "_" for char in value.strip()]
    slug = "".join(chars).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug[:32] or "source"


_SOURCE_INPUT_KEYS = {
    "name",
    "type",
    "category",
    "url",
    "route",
    "enabled",
    "fetchIntervalMinutes",
    "timeoutSeconds",
    "retryCount",
    "concurrencyLimit",
    "trustLevel",
    "requiresCookie",
}


_INSERT_SOURCE_SQL = """
insert into sources (
    id, name, type, category, url, route, enabled, status,
    fetch_interval_minutes, timeout_seconds, retry_count, concurrency_limit,
    trust_level, requires_cookie, first_fetch_mode, created_at, updated_at
) values (
    %(id)s, %(name)s, %(type)s, %(category)s, %(url)s, %(route)s, %(enabled)s, %(status)s,
    %(fetch_interval_minutes)s, %(timeout_seconds)s, %(retry_count)s, %(concurrency_limit)s,
    %(trust_level)s, %(requires_cookie)s, %(first_fetch_mode)s, %(created_at)s, %(updated_at)s
) returning *
"""

_UPDATE_SOURCE_SQL = """
update sources set
    name = %(name)s,
    type = %(type)s,
    category = %(category)s,
    url = %(url)s,
    route = %(route)s,
    enabled = %(enabled)s,
    status = %(status)s,
    fetch_interval_minutes = %(fetch_interval_minutes)s,
    timeout_seconds = %(timeout_seconds)s,
    retry_count = %(retry_count)s,
    concurrency_limit = %(concurrency_limit)s,
    trust_level = %(trust_level)s,
    requires_cookie = %(requires_cookie)s,
    updated_at = %(updated_at)s
where id = %(source_id)s
returning *
"""

_SET_SOURCE_ENABLED_SQL = """
update sources set
    enabled = %(enabled)s,
    status = %(status)s,
    updated_at = %(updated_at)s
where id = %(source_id)s
returning *
"""

_SET_SOURCE_STATUS_SQL = """
update sources set
    status = %(status)s,
    updated_at = %(updated_at)s
where id = %(source_id)s
returning *
"""

_SET_SOURCE_FETCH_METADATA_SQL = """
update sources set
    etag = %(etag)s,
    last_modified = %(last_modified)s,
    last_fetched_at = %(last_fetched_at)s,
    updated_at = %(updated_at)s
where id = %(source_id)s
returning *
"""

_SQLITE_INSERT_SOURCE_SQL = """
insert into sources (
    id, name, type, category, url, route, enabled, status,
    fetch_interval_minutes, timeout_seconds, retry_count, concurrency_limit,
    trust_level, requires_cookie, first_fetch_mode, created_at, updated_at
) values (
    :id, :name, :type, :category, :url, :route, :enabled, :status,
    :fetch_interval_minutes, :timeout_seconds, :retry_count, :concurrency_limit,
    :trust_level, :requires_cookie, :first_fetch_mode, :created_at, :updated_at
)
"""

_SQLITE_UPDATE_SOURCE_SQL = """
update sources set
    name = :name,
    type = :type,
    category = :category,
    url = :url,
    route = :route,
    enabled = :enabled,
    status = :status,
    fetch_interval_minutes = :fetch_interval_minutes,
    timeout_seconds = :timeout_seconds,
    retry_count = :retry_count,
    concurrency_limit = :concurrency_limit,
    trust_level = :trust_level,
    requires_cookie = :requires_cookie,
    updated_at = :updated_at
where id = :source_id
"""

_SQLITE_SET_SOURCE_ENABLED_SQL = """
update sources set
    enabled = :enabled,
    status = :status,
    updated_at = :updated_at
where id = :source_id
"""

_SQLITE_SET_SOURCE_STATUS_SQL = """
update sources set
    status = :status,
    updated_at = :updated_at
where id = :source_id
"""

_SQLITE_SET_SOURCE_FETCH_METADATA_SQL = """
update sources set
    etag = :etag,
    last_modified = :last_modified,
    last_fetched_at = :last_fetched_at,
    updated_at = :updated_at
where id = :source_id
"""


def _source_insert_params(*, source_id: str, source_input: SourceInput, now: datetime) -> dict[str, Any]:
    params = _source_config_params(source_input)
    params.update(
        {
            "id": source_id,
            "first_fetch_mode": "ingest_only",
            "created_at": now,
            "updated_at": now,
        }
    )
    return params


def _source_update_params(*, source_id: str, source_input: SourceInput, now: datetime) -> dict[str, Any]:
    params = _source_config_params(source_input)
    params.update({"source_id": source_id, "updated_at": now})
    return params


def _source_config_params(source_input: SourceInput) -> dict[str, Any]:
    return {
        "name": source_input.name.strip(),
        "type": source_input.type,
        "category": source_input.category.strip(),
        "url": source_input.url,
        "route": source_input.route,
        "enabled": source_input.enabled,
        "status": "enabled" if source_input.enabled else "disabled",
        "fetch_interval_minutes": source_input.fetchIntervalMinutes,
        "timeout_seconds": source_input.timeoutSeconds,
        "retry_count": source_input.retryCount,
        "concurrency_limit": source_input.concurrencyLimit,
        "trust_level": source_input.trustLevel,
        "requires_cookie": source_input.requiresCookie,
    }


def _source_from_row(row: Any) -> dict[str, Any]:
    if not row:
        raise RuntimeError("source row is empty")
    row = dict(row)
    return {
        "id": row["id"],
        "name": row["name"],
        "type": row["type"],
        "category": row["category"],
        "url": row["url"],
        "route": row["route"],
        "enabled": bool(row["enabled"]),
        "status": row["status"],
        "fetchIntervalMinutes": row["fetch_interval_minutes"],
        "timeoutSeconds": row["timeout_seconds"],
        "retryCount": row["retry_count"],
        "concurrencyLimit": row["concurrency_limit"],
        "trustLevel": row["trust_level"],
        "requiresCookie": bool(row["requires_cookie"]),
        "firstFetchMode": row["first_fetch_mode"],
        "etag": row.get("etag"),
        "lastModified": row.get("last_modified"),
        "lastFetchedAt": _format_utc(row.get("last_fetched_at")),
        "createdAt": _format_utc(row["created_at"]),
        "updatedAt": _format_utc(row["updated_at"]),
    }


def _format_utc(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        if value.endswith("Z"):
            return value
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    if isinstance(value, datetime):
        normalized = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return normalized.isoformat().replace("+00:00", "Z")
    return str(value)


def _parse_datetime(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise TypeError(f"unsupported datetime value: {value!r}")
