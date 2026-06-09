from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from app.core.envelope import ORIGINAL_SOURCE_WARNING, success_payload, trace_id
from app.core.errors import QueryServiceError
from app.services.help import help_response
from app.services.normalizer import (
    normalize_daily,
    normalize_dailies,
    normalize_items,
    not_modified_items,
)
from app.services.planner import plan_daily, plan_dailies, plan_items

router = APIRouter(tags=["query"])


@router.get("/query/items")
async def query_items(
    request: Request,
    mode: Annotated[str, Query()] = "selected",
    category: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
    since: Annotated[str | None, Query()] = None,
    timePreset: Annotated[str | None, Query()] = None,
    take: Annotated[int, Query()] = 50,
    cursor: Annotated[str | None, Query()] = None,
) -> JSONResponse:
    trace = trace_id()
    try:
        plan = plan_items(
            mode=mode,
            category=category,
            q=q,
            since=since,
            time_preset=timePreset,
            take=take,
            cursor=cursor,
        )
        upstream = await request.app.state.aihot_client.fetch_json(
            plan, request.app.state.cache
        )
        if upstream.not_modified and upstream.cached and upstream.data is not None:
            data = normalize_items(upstream.data, window=plan.window)
            warnings = ["数据源未更新，返回缓存内容。", ORIGINAL_SOURCE_WARNING]
        elif upstream.not_modified:
            data = not_modified_items(window=plan.window)
            warnings = ["数据源未更新，暂无可用缓存。", ORIGINAL_SOURCE_WARNING]
        else:
            data = normalize_items(upstream.data, window=plan.window)
            warnings = [ORIGINAL_SOURCE_WARNING]
        payload = success_payload(
            data,
            trace=trace,
            query=plan.public_query,
            cached=upstream.cached,
            warnings=warnings,
        )
        return JSONResponse(content=payload)
    except QueryServiceError as exc:
        raise exc


@router.get("/query/daily")
async def query_daily(
    request: Request,
    date: Annotated[str | None, Query()] = None,
) -> JSONResponse:
    trace = trace_id()
    plan = plan_daily(date=date)
    upstream = await request.app.state.aihot_client.fetch_json(plan, request.app.state.cache)
    data = normalize_daily(upstream.data or {})
    payload = success_payload(
        data,
        trace=trace,
        query=plan.public_query,
        cached=upstream.cached,
        warnings=[ORIGINAL_SOURCE_WARNING],
    )
    return JSONResponse(content=payload)


@router.get("/query/dailies")
async def query_dailies(
    request: Request,
    take: Annotated[int, Query()] = 30,
) -> JSONResponse:
    trace = trace_id()
    plan = plan_dailies(take=take)
    upstream = await request.app.state.aihot_client.fetch_json(plan, request.app.state.cache)
    data = normalize_dailies(upstream.data or {})
    payload = success_payload(
        data,
        trace=trace,
        query=plan.public_query,
        cached=upstream.cached,
        warnings=[ORIGINAL_SOURCE_WARNING],
    )
    return JSONResponse(content=payload)


@router.get("/query/help")
async def query_help() -> JSONResponse:
    payload = success_payload(
        help_response(),
        trace=trace_id(),
        query={},
        warnings=[ORIGINAL_SOURCE_WARNING],
    )
    return JSONResponse(content=payload)
