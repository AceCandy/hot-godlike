# M1 查询 API 共享契约

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 使用对象：后端查询内核、前端查询工作台、自动化测试、不同 AI coding 客户端
> 原则：前端只调用本系统 API，不直接调用 AI HOT；AI HOT 细节由后端适配。

## 1. 目标

本契约定义 M1 阶段前后端共享的只读查询 API。后端按本文实现接口；前端按本文使用 mock 或真实后端开发；双方不得绕过契约直接依赖 AI HOT 的公开接口字段。

M1 只覆盖公开查询与种子源内核：

- 精选 / 全部 AI 动态查询。
- 分类、关键词、时间窗查询。
- 最新日报、指定日期日报。
- 日报归档列表。
- 帮助信息。
- 统一响应、统一错误、统一追踪字段。

## 2. 全局约定

### 2.1 Base URL

开发环境默认：

```text
http://localhost:8000/api
```

前端通过环境变量配置：

```text
VITE_API_BASE_URL=http://localhost:8000/api
```

### 2.2 响应 envelope

所有 API 响应都使用同一 envelope。

成功：

```json
{
  "data": {},
  "meta": {
    "traceId": "tr_20260528_000001",
    "source": "aihot",
    "cached": false,
    "query": {},
    "warnings": []
  },
  "error": null
}
```

失败：

```json
{
  "data": null,
  "meta": {
    "traceId": "tr_20260528_000001",
    "source": "aihot",
    "cached": false,
    "query": {},
    "warnings": []
  },
  "error": {
    "code": "UPSTREAM_TIMEOUT",
    "message": "数据源请求超时，请稍后重试。",
    "details": {
      "upstreamStatus": null
    },
    "retryable": true
  }
}
```

### 2.3 错误码

| code | HTTP | retryable | 场景 |
|---|---:|:---:|---|
| `BAD_REQUEST` | 400 | 否 | 参数格式错误、时间窗非法、关键词过短 |
| `UPSTREAM_FORBIDDEN` | 502 | 否 | AI HOT 返回 403，通常是 User-Agent 或源限制问题 |
| `UPSTREAM_NOT_FOUND` | 404 | 否 | 指定日期日报不存在 |
| `UPSTREAM_RATE_LIMITED` | 503 | 是 | AI HOT 返回 429 或等价限流 |
| `UPSTREAM_UNAVAILABLE` | 503 | 是 | AI HOT 返回 5xx |
| `UPSTREAM_TIMEOUT` | 504 | 是 | 请求超时 |
| `UPSTREAM_BAD_RESPONSE` | 502 | 是 | JSON/RSS 解析失败或 schema 不符合预期 |
| `INTERNAL_ERROR` | 500 | 否 | 本系统未知错误 |

### 2.4 分页

M1 使用 cursor 分页。后端不能解析 AI HOT cursor，只能原样透传和保存。

```json
{
  "page": {
    "take": 50,
    "hasNext": true,
    "nextCursor": "opaque-cursor"
  }
}
```

### 2.5 时间与时区

- 用户自然语言时间由后端解析。
- API 显式时间使用 ISO 8601。
- 用户视角默认时区为 `Asia/Shanghai`。
- 向 AI HOT items API 传递 `since` 时必须转换为 ISO 8601 UTC。
- items 查询最长 7 天；超过 7 天必须返回提示或建议使用日报归档。

### 2.6 分类枚举

| 前端显示 | API category | 日报 section |
|---|---|---|
| 模型 | `ai-models` | 模型发布/更新 |
| 产品 | `ai-products` | 产品发布/更新 |
| 行业 | `industry` | 行业动态 |
| 论文 | `paper` | 论文研究 |
| 技巧 | `tip` | 技巧与观点 |

## 3. 数据结构

### 3.1 QueryItem

```json
{
  "id": "string",
  "title": "string",
  "titleEn": null,
  "url": "https://example.com",
  "source": "string",
  "publishedAt": "2026-05-28T01:23:45Z",
  "summary": "string",
  "category": "ai-products",
  "tags": [],
  "score": null
}
```

字段规则：

- `id/title/url/source` 必须存在。
- `publishedAt` 可为 `null`，前端显示“发布时间未知”。
- `summary` 可为 `null` 或空字符串，前端显示“该条暂无摘要”。
- `titleEn` 为 `null` 时前端不展示英文标题。
- `score` 如果来自公开页面但 API 不提供，则保持 `null`，不得编造。

### 3.2 QueryItemList

```json
{
  "items": [],
  "page": {
    "take": 50,
    "hasNext": false,
    "nextCursor": null
  },
  "window": {
    "label": "过去 24 小时",
    "since": "2026-05-27T16:00:00Z",
    "timezone": "Asia/Shanghai"
  }
}
```

### 3.3 DailyReport

```json
{
  "date": "2026-05-28",
  "generatedAt": "2026-05-28T00:00:00Z",
  "windowStart": "2026-05-27T00:00:00Z",
  "windowEnd": "2026-05-28T00:00:00Z",
  "lead": {
    "title": "string",
    "leadParagraph": "string"
  },
  "sections": [
    {
      "label": "产品发布/更新",
      "items": [
        {
          "title": "string",
          "summary": "string",
          "sourceName": "string",
          "sourceUrl": "https://example.com"
        }
      ]
    }
  ],
  "flashes": []
}
```

### 3.4 DailyArchiveItem

```json
{
  "date": "2026-05-28",
  "weekday": "星期四",
  "title": "string",
  "itemCount": 12
}
```

### 3.5 HelpResponse

```json
{
  "examples": [
    "今天 AI 圈有什么",
    "最近 OpenAI 有什么发布",
    "看一下今天的 AI 日报"
  ],
  "categories": [
    { "label": "模型", "value": "ai-models" }
  ],
  "limits": [
    "items 查询最长支持最近 7 天",
    "关键事实请打开原文核对"
  ]
}
```

## 4. API 端点

### 4.1 查询动态

```http
GET /api/query/items
```

参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `mode` | `selected` / `all` | 否 | 默认 `selected` |
| `category` | enum | 否 | 分类枚举 |
| `q` | string | 否 | 关键词，长度 2-200 |
| `since` | ISO datetime | 否 | 显式时间窗起点 |
| `timePreset` | string | 否 | `today`、`yesterday`、`24h`、`3d`、`7d` |
| `take` | integer | 否 | 1-100，默认 50 |
| `cursor` | string | 否 | opaque cursor |

成功响应：

```json
{
  "data": {
    "items": [],
    "page": {
      "take": 50,
      "hasNext": false,
      "nextCursor": null
    },
    "window": {
      "label": "过去 24 小时",
      "since": "2026-05-27T16:00:00Z",
      "timezone": "Asia/Shanghai"
    }
  },
  "meta": {
    "traceId": "tr_20260528_000001",
    "source": "aihot",
    "cached": false,
    "query": {
      "mode": "selected",
      "take": 50
    },
    "warnings": [
      "摘要由 AI HOT 生成，关键事实请打开原文核对。"
    ]
  },
  "error": null
}
```

### 4.2 最新日报

```http
GET /api/query/daily
```

参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `date` | `YYYY-MM-DD` | 否 | 不传则取最新日报 |

说明：

- 前端查询“今天日报”时可以不传 `date`，由后端请求 AI HOT 最新日报。
- 前端查询指定日期日报时传 `date`。

### 4.3 日报归档

```http
GET /api/query/dailies
```

参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `take` | integer | 否 | 1-100，默认 30 |

### 4.4 帮助信息

```http
GET /api/query/help
```

返回可用分类、示例问题、限制和提示，用于前端空状态或帮助弹层。

## 5. 前后端协作规则

- 前端不得直接调用 `https://aihot.virxact.com`。
- 后端不得返回 AI HOT 原始响应作为公开 API。
- 后端必须把 AI HOT 字段映射成本契约字段。
- 前端必须展示 `meta.warnings` 中的来源和核对提示。
- 前端必须在错误态展示 `error.message`，并根据 `retryable` 决定是否展示重试按钮。
- 契约变更必须先改本文，再分别改后端和前端。

## 6. Mock 要求

前端可以使用 mock 数据并行开发，mock 必须覆盖：

- 有结果的精选查询。
- 空结果。
- 关键词查询。
- 分类查询。
- 最新日报。
- 日报归档。
- 403、404、429/503、超时、JSON 解析失败。

## 7. 非目标

M1 API 不包含：

- 登录、用户、订阅、推送。
- 数据库持久化。
- 多源采集入库。
- 聚类、评分、背景补全、AI 点评。
- Web 管理台写操作。
