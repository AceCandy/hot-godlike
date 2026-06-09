import pytest

from app.core.errors import ErrorCode, QueryServiceError
from app.services.collection import SourceInput
from app.services.collection_registry import (
    InMemorySourceRepository,
    SqliteSourceRepository,
    build_source_repository,
)


def rss_source_input() -> SourceInput:
    return SourceInput(
        name="GitHub Blog",
        type="rss",
        category="tech",
        url="https://github.blog/feed/",
        route=None,
        enabled=True,
        fetchIntervalMinutes=30,
        timeoutSeconds=30,
        retryCount=2,
        concurrencyLimit=1,
        trustLevel="medium",
        requiresCookie=False,
    )


def test_sqlite_source_repository_persists_sources_across_instances(tmp_path) -> None:
    db_path = tmp_path / "hot_godlike.sqlite"
    repository = SqliteSourceRepository.from_path(str(db_path))

    created = repository.create(rss_source_input())
    source_id = created["id"]
    repository.update(source_id, {"name": "GitHub Blog Feed", "fetchIntervalMinutes": 60})
    repository.set_fetch_metadata(
        source_id,
        etag="etag-new",
        last_modified="Sat, 30 May 2026 00:00:00 GMT",
        fetched_at="2026-05-30T00:00:00Z",
    )
    repository.set_status(source_id, "degraded")

    reopened = SqliteSourceRepository.from_path(str(db_path))
    fetched = reopened.get(source_id)
    listed = reopened.list(source_type="rss", status="degraded", take=10)

    assert db_path.exists()
    assert fetched["name"] == "GitHub Blog Feed"
    assert fetched["enabled"] is True
    assert fetched["status"] == "degraded"
    assert fetched["fetchIntervalMinutes"] == 60
    assert fetched["etag"] == "etag-new"
    assert fetched["lastModified"] == "Sat, 30 May 2026 00:00:00 GMT"
    assert fetched["lastFetchedAt"] == "2026-05-30T00:00:00Z"
    assert fetched["createdAt"] == created["createdAt"]
    assert listed["items"][0]["id"] == source_id


def test_sqlite_source_repository_maps_missing_source_to_contract_error(tmp_path) -> None:
    repository = SqliteSourceRepository.from_path(str(tmp_path / "hot_godlike.sqlite"))

    with pytest.raises(QueryServiceError) as exc_info:
        repository.get("src_missing")

    assert exc_info.value.code == ErrorCode.SOURCE_NOT_FOUND
    assert exc_info.value.details == {"sourceId": "src_missing"}


def test_build_source_repository_supports_explicit_local_storage(tmp_path) -> None:
    repository = build_source_repository(
        storage_mode="local",
        local_sqlite_path=str(tmp_path / "hot_godlike.sqlite"),
        use_postgres=False,
        postgres_dsn=None,
    )

    assert isinstance(repository, SqliteSourceRepository)


def test_build_source_repository_still_defaults_to_memory(tmp_path) -> None:
    repository = build_source_repository(
        storage_mode=None,
        local_sqlite_path=str(tmp_path / "hot_godlike.sqlite"),
        use_postgres=False,
        postgres_dsn=None,
    )

    assert isinstance(repository, InMemorySourceRepository)
