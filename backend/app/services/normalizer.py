from typing import Any
from datetime import date

from app.core.errors import upstream_bad_response
from app.services.planner import ALLOWED_CATEGORIES


def normalize_items(payload: Any, *, window: dict[str, str | None]) -> dict[str, Any]:
    container = _object_payload(payload)
    items = _extract_list(container, "items")
    normalized_items = [item for raw in items if (item := _normalize_item(raw))]
    return {
        "items": normalized_items,
        "page": {
            "take": _read_int(container, "take") or len(normalized_items),
            "hasNext": bool(container.get("hasNext", container.get("has_next", False))),
            "nextCursor": container.get("nextCursor") or container.get("next_cursor"),
        },
        "window": window,
    }


def normalize_daily(payload: Any) -> dict[str, Any]:
    container = _object_payload(payload)
    return {
        "date": container.get("date"),
        "generatedAt": container.get("generatedAt") or container.get("generated_at"),
        "windowStart": container.get("windowStart") or container.get("window_start"),
        "windowEnd": container.get("windowEnd") or container.get("window_end"),
        "lead": _normalize_lead(container.get("lead")),
        "sections": [_normalize_section(section) for section in _extract_list(container, "sections")],
        "flashes": [_normalize_flash(flash) for flash in _extract_list(container, "flashes")],
    }


def normalize_dailies(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        items = payload
    else:
        container = _object_payload(payload)
        items = (
            _maybe_list(container.get("items"))
            or _maybe_list(container.get("dailies"))
            or _maybe_list(container.get("data"))
            or []
        )
    return [_normalize_daily_archive(item) for item in items if isinstance(item, dict)]


def not_modified_items(*, window: dict[str, str | None]) -> dict[str, Any]:
    return {
        "items": [],
        "page": {"take": 0, "hasNext": False, "nextCursor": None},
        "window": window,
    }


def _normalize_item(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    item_id = raw.get("id")
    title = raw.get("title")
    url = raw.get("url")
    source = _source_name(raw.get("source") or raw.get("sourceName") or raw.get("source_name"))
    if not item_id or not title or not url or not source:
        return None
    category = raw.get("category")
    if category not in ALLOWED_CATEGORIES:
        category = None
    tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []
    return {
        "id": str(item_id),
        "title": str(title),
        "titleEn": raw.get("titleEn") or raw.get("title_en"),
        "url": str(url),
        "source": source,
        "publishedAt": raw.get("publishedAt") or raw.get("published_at"),
        "summary": raw.get("summary"),
        "category": category,
        "tags": tags,
        "score": raw.get("score"),
    }


def _normalize_lead(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    return {
        "title": raw.get("title"),
        "leadParagraph": raw.get("leadParagraph") or raw.get("lead_paragraph"),
    }


def _normalize_section(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"label": None, "items": []}
    return {
        "label": raw.get("label"),
        "items": [_normalize_daily_item(item) for item in _maybe_list(raw.get("items")) or []],
    }


def _normalize_daily_item(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"title": None, "summary": None, "sourceName": None, "sourceUrl": None}
    return {
        "title": raw.get("title"),
        "summary": raw.get("summary"),
        "sourceName": raw.get("sourceName") or raw.get("source_name"),
        "sourceUrl": raw.get("sourceUrl") or raw.get("source_url"),
    }


def _normalize_flash(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"title": None, "sourceName": None, "sourceUrl": None, "publishedAt": None}
    return {
        "title": raw.get("title"),
        "sourceName": raw.get("sourceName") or raw.get("source_name"),
        "sourceUrl": raw.get("sourceUrl") or raw.get("source_url"),
        "publishedAt": raw.get("publishedAt") or raw.get("published_at"),
    }


def _normalize_daily_archive(raw: dict[str, Any]) -> dict[str, Any]:
    archive_date = raw.get("date")
    return {
        "date": archive_date,
        "weekday": raw.get("weekday") or _weekday_label(archive_date),
        "title": raw.get("title") or raw.get("leadTitle") or raw.get("lead_title"),
        "itemCount": _first_present(raw, "itemCount", "item_count", "count"),
    }


def _object_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise upstream_bad_response({"reason": "expected object payload"})
    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return payload


def _extract_list(container: dict[str, Any], key: str) -> list[Any]:
    values = container.get(key)
    if values is None and isinstance(container.get("data"), dict):
        values = container["data"].get(key)
    if values is None:
        return []
    if not isinstance(values, list):
        raise upstream_bad_response({"reason": f"{key} must be an array"})
    return values


def _maybe_list(value: Any) -> list[Any] | None:
    return value if isinstance(value, list) else None


def _source_name(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        name = value.get("name") or value.get("title")
        return str(name) if name else None
    return None


def _read_int(container: dict[str, Any], key: str) -> int | None:
    value = container.get(key)
    return value if isinstance(value, int) else None


def _first_present(raw: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw:
            return raw[key]
    return None


def _weekday_label(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    labels = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return labels[parsed.weekday()]
