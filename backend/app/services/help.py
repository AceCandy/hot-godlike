def help_response() -> dict[str, list[dict[str, str]] | list[str]]:
    return {
        "examples": [
            "今天 AI 圈有什么",
            "最近 OpenAI 有什么发布",
            "看一下今天的 AI 日报",
            "最近一周 AI 论文",
        ],
        "categories": [
            {"label": "模型", "value": "ai-models"},
            {"label": "产品", "value": "ai-products"},
            {"label": "行业", "value": "industry"},
            {"label": "论文", "value": "paper"},
            {"label": "技巧", "value": "tip"},
        ],
        "limits": [
            "items 查询最长支持最近 7 天",
            "关键事实请打开原文核对",
            "关键词至少 2 个字符",
        ],
    }
