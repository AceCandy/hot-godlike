from datetime import datetime, timezone

import pytest

from app.core.errors import ErrorCode, QueryServiceError
from app.services.planner import plan_dailies, plan_items, request_headers
from app.services.time_window import resolve_since


def test_plan_items_defaults_to_selected() -> None:
    plan = plan_items()

    assert plan.upstream_path == "/api/public/items"
    assert plan.params["mode"] == "selected"
    assert plan.params["take"] == 50
    assert plan.public_query["mode"] == "selected"


def test_plan_items_validates_query_length() -> None:
    with pytest.raises(QueryServiceError) as exc:
        plan_items(q="a")

    assert exc.value.code == ErrorCode.BAD_REQUEST
    assert "关键词至少" in exc.value.message


def test_plan_items_preserves_cursor_as_opaque_value() -> None:
    plan = plan_items(cursor="opaque-cursor")

    assert plan.params["cursor"] == "opaque-cursor"


def test_plan_items_validates_category() -> None:
    with pytest.raises(QueryServiceError) as exc:
        plan_items(category="invalid")

    assert exc.value.code == ErrorCode.BAD_REQUEST


def test_plan_dailies_take_range() -> None:
    with pytest.raises(QueryServiceError):
        plan_dailies(take=0)


def test_resolve_since_uses_utc_for_time_preset() -> None:
    now = datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)

    since, window = resolve_since(since=None, time_preset="24h", now=now)

    assert since == "2026-05-28T08:00:00Z"
    assert window["label"] == "过去 24 小时"


def test_resolve_since_rejects_older_than_seven_days() -> None:
    now = datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)

    with pytest.raises(QueryServiceError) as exc:
        resolve_since(since="2026-05-01T00:00:00Z", time_preset=None, now=now)

    assert exc.value.code == ErrorCode.BAD_REQUEST
    assert "最长支持最近 7 天" in exc.value.message


def test_request_headers_include_user_agent_and_etag() -> None:
    headers = request_headers("etag-1")

    assert headers["User-Agent"].startswith("hot-godlike-agent/0.1")
    assert headers["If-None-Match"] == "etag-1"
