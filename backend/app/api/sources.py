from typing import Annotated, Any

from fastapi import APIRouter, Body, Query, Request
from fastapi.responses import JSONResponse

from app.core.envelope import success_payload, trace_id
from app.core.errors import bad_request
from app.services.collection import SOURCE_TYPES, SourceInput

router = APIRouter(tags=["sources"])
SOURCE_STATUSES = {"enabled", "disabled", "degraded", "circuit_open"}


@router.post("/sources")
async def create_source(
    request: Request,
    body: Annotated[dict[str, Any], Body()],
) -> JSONResponse:
    source_input = _source_input(body)
    source = request.app.state.source_repository.create(source_input)
    return _success(source, query={})


@router.patch("/sources/{source_id}")
async def update_source(
    request: Request,
    source_id: str,
    body: Annotated[dict[str, Any], Body()],
) -> JSONResponse:
    source = request.app.state.source_repository.update(source_id, body)
    return _success(source, query={})


@router.get("/sources")
async def list_sources(
    request: Request,
    type: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    take: Annotated[int, Query()] = 50,
) -> JSONResponse:
    if type is not None and type not in SOURCE_TYPES:
        raise bad_request("type 不在支持范围内。", {"type": type})
    if status is not None and status not in SOURCE_STATUSES:
        raise bad_request("status 不在支持范围内。", {"status": status})
    if take < 1 or take > 100:
        raise bad_request("take 必须在 1 到 100 之间。", {"take": take})

    data = request.app.state.source_repository.list(
        source_type=type,
        status=status,
        take=take,
    )
    query = {key: value for key, value in {"type": type, "status": status, "take": take}.items() if value is not None}
    return _success(data, query=query)


@router.get("/sources/{source_id}")
async def get_source(request: Request, source_id: str) -> JSONResponse:
    source = request.app.state.source_repository.get(source_id)
    return _success(source, query={})


@router.post("/sources/preview")
async def preview_source(
    request: Request,
    body: Annotated[dict[str, Any], Body()],
) -> JSONResponse:
    source_input = _source_input(body)
    data = await request.app.state.source_previewer.preview(source_input)
    return _success(data, query={})


@router.post("/sources/{source_id}/fetch")
async def fetch_source(
    request: Request,
    source_id: str,
    body: Annotated[dict[str, Any] | None, Body()] = None,
) -> JSONResponse:
    payload = body or {}
    run = await request.app.state.collection_runner.fetch_source(
        source_id,
        idempotency_key=payload.get("idempotencyKey"),
    )
    return _success(run, query={})


@router.post("/sources/{source_id}/enable")
async def enable_source(request: Request, source_id: str) -> JSONResponse:
    source = request.app.state.source_repository.set_enabled(source_id, True)
    return _success(source, query={})


@router.post("/sources/{source_id}/disable")
async def disable_source(request: Request, source_id: str) -> JSONResponse:
    source = request.app.state.source_repository.set_enabled(source_id, False)
    return _success(source, query={})


def _source_input(body: dict[str, Any]) -> SourceInput:
    return SourceInput(
        name=body.get("name"),
        type=body.get("type"),
        category=body.get("category"),
        url=body.get("url"),
        route=body.get("route"),
        enabled=body.get("enabled", True),
        fetchIntervalMinutes=body.get("fetchIntervalMinutes"),
        timeoutSeconds=body.get("timeoutSeconds"),
        retryCount=body.get("retryCount"),
        concurrencyLimit=body.get("concurrencyLimit"),
        trustLevel=body.get("trustLevel"),
        requiresCookie=body.get("requiresCookie", False),
    )


def _success(data: Any, *, query: dict[str, Any]) -> JSONResponse:
    payload = success_payload(
        data,
        trace=trace_id(),
        query=query,
        source="hot-godlike",
    )
    return JSONResponse(content=payload)
