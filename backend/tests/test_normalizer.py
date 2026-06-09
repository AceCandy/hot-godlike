from app.services.normalizer import normalize_daily, normalize_dailies, normalize_items


def test_normalize_items_maps_contract_fields() -> None:
    payload = {
        "items": [
            {
                "id": "1",
                "title": "标题",
                "title_en": "Title",
                "url": "https://example.com",
                "source": {"name": "Example"},
                "published_at": "2026-05-29T00:00:00Z",
                "summary": "摘要",
                "category": "paper",
                "tags": ["AI"],
                "score": 90,
            }
        ],
        "hasNext": True,
        "nextCursor": "next",
        "take": 50,
    }

    result = normalize_items(
        payload,
        window={"label": "过去 24 小时", "since": None, "timezone": "Asia/Shanghai"},
    )

    assert result["items"][0]["titleEn"] == "Title"
    assert result["items"][0]["source"] == "Example"
    assert result["items"][0]["category"] == "paper"
    assert result["page"]["hasNext"] is True
    assert result["page"]["nextCursor"] == "next"


def test_normalize_items_skips_invalid_items_without_fabricating_fields() -> None:
    payload = {
        "items": [
            {"id": "missing-title", "url": "https://example.com", "source": "Example"},
            {"id": "ok", "title": "标题", "url": "https://example.com/ok", "source": "Example"},
        ]
    }

    result = normalize_items(payload, window={"label": "默认时间窗", "since": None, "timezone": "Asia/Shanghai"})

    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == "ok"


def test_normalize_daily_maps_sections() -> None:
    payload = {
        "date": "2026-05-29",
        "lead": {"title": "日报", "leadParagraph": "导语"},
        "sections": [
            {
                "label": "产品发布/更新",
                "items": [
                    {
                        "title": "事件",
                        "summary": "摘要",
                        "sourceName": "Source",
                        "sourceUrl": "https://example.com",
                    }
                ],
            }
        ],
    }

    result = normalize_daily(payload)

    assert result["date"] == "2026-05-29"
    assert result["lead"]["leadParagraph"] == "导语"
    assert result["sections"][0]["items"][0]["sourceUrl"] == "https://example.com"


def test_normalize_dailies_accepts_data_items() -> None:
    result = normalize_dailies({"items": [{"date": "2026-05-29", "itemCount": 3}]})

    assert result == [
        {"date": "2026-05-29", "weekday": "星期五", "title": None, "itemCount": 3}
    ]


def test_normalize_dailies_maps_aihot_lead_title_without_fabricating_count() -> None:
    result = normalize_dailies(
        {
            "items": [
                {
                    "date": "2026-05-28",
                    "generatedAt": "2026-05-28T00:00:00.348Z",
                    "leadTitle": "Runway 推出 Model Context Protocol 服务器",
                }
            ]
        }
    )

    assert result == [
        {
            "date": "2026-05-28",
            "weekday": "星期四",
            "title": "Runway 推出 Model Context Protocol 服务器",
            "itemCount": None,
        }
    ]
