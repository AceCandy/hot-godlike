from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.collection import router as collection_router
from app.api.query import router as query_router
from app.api.sources import router as sources_router
from app.core.config import settings
from app.core.envelope import error_payload, trace_id
from app.core.errors import ErrorCode, QueryServiceError
from app.services.aihot_client import AihotClient
from app.services.cache import InMemoryCacheStore
from app.services.collection_registry import (
    InMemorySourceRepository,
    PostgresSourceRepository,
    SqliteSourceRepository,
    build_source_repository,
)
from app.services.collection_runner import (
    CollectionRunner,
    SourceItemFetcher,
)
from app.services.collection_store import (
    InMemoryCollectionStore,
    PostgresCollectionStore,
    SqliteCollectionStore,
    build_collection_store,
)
from app.services.fetcher_pool import build_fetcher_pool
from app.services.fetch_control import InMemorySourceLockStore, RedisSourceLockStore, build_source_lock_store
from app.services.fetch_control import (
    InMemorySourceMetadataStore,
    RedisSourceMetadataStore,
    build_source_metadata_store,
)
from app.services.fetch_control import SourceDedupeStore, build_source_dedupe_store
from app.services.scheduler import SchedulerService
from app.services.scheduler_worker import build_scheduler_worker
from app.services.source_preview import SourcePreviewer


def create_app(
    *,
    aihot_client: AihotClient | None = None,
    cache: InMemoryCacheStore | None = None,
    source_repository: InMemorySourceRepository | PostgresSourceRepository | SqliteSourceRepository | None = None,
    source_previewer: SourcePreviewer | None = None,
    collection_store: InMemoryCollectionStore | PostgresCollectionStore | SqliteCollectionStore | None = None,
    source_item_fetcher: SourceItemFetcher | None = None,
    source_lock_store: InMemorySourceLockStore | RedisSourceLockStore | None = None,
    source_metadata_store: InMemorySourceMetadataStore | RedisSourceMetadataStore | None = None,
    source_dedupe_store: SourceDedupeStore | None = None,
    scheduler_worker: Any | None = None,
    scheduler_worker_enabled: bool | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.scheduler_worker_enabled:
            app.state.scheduler_worker.start()
        try:
            yield
        finally:
            if app.state.scheduler_worker_enabled:
                app.state.scheduler_worker.stop()

    app = FastAPI(
        title="Hot Godlike Query API",
        version="0.1.0",
        description="M1 public query API for AI HOT seed-source content.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.aihot_client = aihot_client or AihotClient()
    app.state.cache = cache or InMemoryCacheStore()
    app.state.source_repository = source_repository or build_source_repository(
        storage_mode=settings.storage_mode,
        local_sqlite_path=settings.local_storage_path,
        use_postgres=settings.use_postgres_source_repository,
        postgres_dsn=settings.postgres_dsn,
    )
    app.state.source_previewer = source_previewer or SourcePreviewer()
    app.state.collection_store = collection_store or build_collection_store(
        storage_mode=settings.storage_mode,
        local_sqlite_path=settings.local_storage_path,
        use_postgres=settings.use_postgres_collection_store,
        postgres_dsn=settings.postgres_dsn,
    )
    app.state.source_lock_store = source_lock_store or build_source_lock_store(
        use_redis=settings.use_redis_lock,
        redis_url=settings.redis_url,
    )
    app.state.source_metadata_store = source_metadata_store or build_source_metadata_store(
        use_redis=settings.use_redis_source_metadata,
        redis_url=settings.redis_url,
    )
    app.state.source_dedupe_store = source_dedupe_store or build_source_dedupe_store(
        use_redis=settings.use_redis_source_dedupe,
        redis_url=settings.redis_url,
    )
    app.state.fetcher_pool = build_fetcher_pool(
        aihot_client=app.state.aihot_client,
        cache=app.state.cache,
        previewer=app.state.source_previewer,
        source_repository=app.state.source_repository,
        metadata_store=app.state.source_metadata_store,
    )
    app.state.collection_runner = CollectionRunner(
        source_repository=app.state.source_repository,
        store=app.state.collection_store,
        fetch_items=source_item_fetcher or app.state.fetcher_pool.fetch,
        lock_store=app.state.source_lock_store,
        source_dedupe_store=app.state.source_dedupe_store,
    )
    app.state.scheduler_service = SchedulerService(
        source_repository=app.state.source_repository,
        collection_store=app.state.collection_store,
        runner=app.state.collection_runner,
    )
    app.state.scheduler_worker = scheduler_worker or build_scheduler_worker(
        scheduler_service=app.state.scheduler_service,
        interval_seconds=settings.scheduler_worker_interval_seconds,
    )
    app.state.scheduler_worker_enabled = (
        settings.use_scheduler_worker
        if scheduler_worker_enabled is None
        else scheduler_worker_enabled
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(QueryServiceError)
    async def query_error_handler(
        request: Request, exc: QueryServiceError
    ) -> JSONResponse:
        source = "hot-godlike" if _is_collection_path(request.url.path) else "aihot"
        payload = error_payload(
            exc,
            trace=trace_id(),
            query=dict(request.query_params),
            source=source,
        )
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        err = QueryServiceError(
            code=ErrorCode.BAD_REQUEST,
            message="请求参数格式错误，请检查后重试。",
            status_code=400,
            retryable=False,
            details={"errors": exc.errors()},
        )
        payload = error_payload(err, trace=trace_id(), query=dict(request.query_params))
        return JSONResponse(status_code=400, content=payload)

    app.include_router(query_router, prefix="/api")
    app.include_router(sources_router, prefix="/api")
    app.include_router(collection_router, prefix="/api")
    return app


app = create_app()


def _is_collection_path(path: str) -> bool:
    return path.startswith(
        (
            "/api/sources",
            "/api/fetch-runs",
            "/api/raw-items",
            "/api/source-health",
        )
    )
