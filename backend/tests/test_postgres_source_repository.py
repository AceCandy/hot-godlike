from datetime import datetime, timezone
from typing import Any

import pytest

from app.core.errors import ErrorCode, QueryServiceError
from app.services.collection import SourceInput
from app.services.collection_registry import PostgresSourceRepository


class FakeCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def fetchone(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def fetchall(self) -> list[dict[str, Any]]:
        return list(self._rows)


class FakePostgresState:
    def __init__(self) -> None:
        self.sources: dict[str, dict[str, Any]] = {}
        self.executed: list[str] = []
        self.commits = 0


class FakePostgresConnection:
    def __init__(self, state: FakePostgresState) -> None:
        self._state = state

    def __enter__(self) -> "FakePostgresConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> FakeCursor:
        normalized_sql = " ".join(sql.lower().split())
        self._state.executed.append(normalized_sql)
        params = params or {}

        if normalized_sql.startswith("insert into sources"):
            self._state.sources[params["id"]] = _source_row(params)
            return FakeCursor([self._state.sources[params["id"]]])

        if normalized_sql.startswith("select * from sources where id"):
            row = self._state.sources.get(params["source_id"])
            return FakeCursor([row] if row else [])

        if normalized_sql.startswith("select * from sources"):
            rows = list(self._state.sources.values())
            if params.get("source_type"):
                rows = [row for row in rows if row["type"] == params["source_type"]]
            if params.get("status"):
                rows = [row for row in rows if row["status"] == params["status"]]
            rows = rows[: params["limit"]]
            return FakeCursor(rows)

        if normalized_sql.startswith("update sources set name"):
            row = self._state.sources.get(params["source_id"])
            if not row:
                return FakeCursor([])
            row.update(_source_update(params))
            return FakeCursor([row])

        if normalized_sql.startswith("update sources set enabled"):
            row = self._state.sources.get(params["source_id"])
            if not row:
                return FakeCursor([])
            row["enabled"] = params["enabled"]
            row["status"] = "enabled" if params["enabled"] else "disabled"
            row["updated_at"] = params["updated_at"]
            return FakeCursor([row])

        if normalized_sql.startswith("update sources set etag"):
            row = self._state.sources.get(params["source_id"])
            if not row:
                return FakeCursor([])
            row["etag"] = params["etag"]
            row["last_modified"] = params["last_modified"]
            row["last_fetched_at"] = params["last_fetched_at"]
            row["updated_at"] = params["updated_at"]
            return FakeCursor([row])

        if normalized_sql.startswith("update sources set status"):
            row = self._state.sources.get(params["source_id"])
            if not row:
                return FakeCursor([])
            row["status"] = params["status"]
            row["updated_at"] = params["updated_at"]
            return FakeCursor([row])

        raise AssertionError(f"Unexpected SQL: {sql}")

    def commit(self) -> None:
        self._state.commits += 1


def make_repository(state: FakePostgresState) -> PostgresSourceRepository:
    return PostgresSourceRepository(lambda: FakePostgresConnection(state))


def rsshub_source_input() -> SourceInput:
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


def test_postgres_source_repository_round_trips_contract_shape() -> None:
    state = FakePostgresState()
    repository = make_repository(state)

    created = repository.create(rsshub_source_input())
    source_id = created["id"]
    listed = repository.list(source_type="rsshub", status="enabled", take=10)
    updated = repository.update(source_id, {"name": "HN Frontpage", "fetchIntervalMinutes": 60})
    metadata = repository.set_fetch_metadata(
        source_id,
        etag="etag-new",
        last_modified="Sat, 30 May 2026 00:00:00 GMT",
        fetched_at="2026-05-30T00:00:00Z",
    )
    degraded = repository.set_status(source_id, "degraded")
    recovered = repository.set_status(source_id, "enabled")
    disabled = repository.set_enabled(source_id, False)
    fetched = repository.get(source_id)

    assert source_id.startswith("src_hacker_news_")
    assert created["status"] == "enabled"
    assert created["firstFetchMode"] == "ingest_only"
    assert created["createdAt"].endswith("Z")
    assert listed["items"][0]["id"] == source_id
    assert listed["page"] == {"take": 10, "hasNext": False, "nextCursor": None}
    assert updated["name"] == "HN Frontpage"
    assert updated["route"] == "/hackernews/frontpage"
    assert updated["fetchIntervalMinutes"] == 60
    assert updated["createdAt"] == created["createdAt"]
    assert metadata["etag"] == "etag-new"
    assert metadata["lastModified"] == "Sat, 30 May 2026 00:00:00 GMT"
    assert metadata["lastFetchedAt"] == "2026-05-30T00:00:00Z"
    assert degraded["enabled"] is True
    assert degraded["status"] == "degraded"
    assert recovered["status"] == "enabled"
    assert disabled["enabled"] is False
    assert disabled["status"] == "disabled"
    assert fetched["status"] == "disabled"
    assert fetched["etag"] == "etag-new"
    assert state.commits == 6
    assert any("insert into sources" in sql for sql in state.executed)
    assert any("update sources set name" in sql for sql in state.executed)


def test_postgres_source_repository_maps_missing_source_to_contract_error() -> None:
    repository = make_repository(FakePostgresState())

    with pytest.raises(QueryServiceError) as exc_info:
        repository.get("src_missing")

    assert exc_info.value.code == ErrorCode.SOURCE_NOT_FOUND
    assert exc_info.value.details == {"sourceId": "src_missing"}


def _source_row(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": params["id"],
        "name": params["name"],
        "type": params["type"],
        "category": params["category"],
        "url": params["url"],
        "route": params["route"],
        "enabled": params["enabled"],
        "status": params["status"],
        "fetch_interval_minutes": params["fetch_interval_minutes"],
        "timeout_seconds": params["timeout_seconds"],
        "retry_count": params["retry_count"],
        "concurrency_limit": params["concurrency_limit"],
        "trust_level": params["trust_level"],
        "requires_cookie": params["requires_cookie"],
        "first_fetch_mode": params["first_fetch_mode"],
        "etag": None,
        "last_modified": None,
        "last_fetched_at": None,
        "created_at": params["created_at"],
        "updated_at": params["updated_at"],
    }


def _source_update(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": params["name"],
        "type": params["type"],
        "category": params["category"],
        "url": params["url"],
        "route": params["route"],
        "enabled": params["enabled"],
        "status": params["status"],
        "fetch_interval_minutes": params["fetch_interval_minutes"],
        "timeout_seconds": params["timeout_seconds"],
        "retry_count": params["retry_count"],
        "concurrency_limit": params["concurrency_limit"],
        "trust_level": params["trust_level"],
        "requires_cookie": params["requires_cookie"],
        "updated_at": params.get("updated_at", datetime.now(timezone.utc)),
    }
