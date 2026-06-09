from typing import Annotated, Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from app.core.envelope import success_payload, trace_id
from app.core.errors import bad_request

router = APIRouter(tags=["collection"])


@router.get("/fetch-runs")
async def list_fetch_runs(
    request: Request,
    sourceId: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    take: Annotated[int, Query()] = 50,
) -> JSONResponse:
    _validate_take(take)
    data = request.app.state.collection_store.list_runs(
        source_id=sourceId,
        status=status,
        take=take,
    )
    return _success(data, query=_query(sourceId=sourceId, status=status, take=take))


@router.get("/fetch-runs/{run_id}")
async def get_fetch_run(request: Request, run_id: str) -> JSONResponse:
    return _success(request.app.state.collection_store.get_run(run_id), query={})


@router.get("/raw-items")
async def list_raw_items(
    request: Request,
    sourceId: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
    take: Annotated[int, Query()] = 50,
) -> JSONResponse:
    _validate_take(take)
    data = request.app.state.collection_store.list_raw_items(
        source_id=sourceId,
        status=status,
        q=q,
        take=take,
    )
    return _success(data, query=_query(sourceId=sourceId, status=status, q=q, take=take))


@router.get("/raw-items/{raw_item_id}")
async def get_raw_item(request: Request, raw_item_id: str) -> JSONResponse:
    return _success(request.app.state.collection_store.get_raw_item(raw_item_id), query={})


@router.get("/source-health")
async def list_source_health(
    request: Request,
    sourceId: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    take: Annotated[int, Query()] = 50,
) -> JSONResponse:
    _validate_take(take)
    data = request.app.state.collection_store.list_health(
        source_id=sourceId,
        status=status,
        take=take,
    )
    return _success(data, query=_query(sourceId=sourceId, status=status, take=take))


def _success(data: Any, *, query: dict[str, Any]) -> JSONResponse:
    payload = success_payload(
        data,
        trace=trace_id(),
        query=query,
        source="hot-godlike",
    )
    return JSONResponse(content=payload)


def _validate_take(take: int) -> None:
    if take < 1 or take > 100:
        raise bad_request("take 必须在 1 到 100 之间。", {"take": take})


def _query(**values: Any) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}
