# M2 采集 API 共享契约

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 上游依赖：M1 `docs/contracts/query-api.md`、统一 response envelope
> 使用对象：M2 后端采集基础设施、M2 前端数据源管理入口、自动化测试、不同 AI coding 客户端
> 原则：M2 只做多源采集、归一化、入库、运行记录和源健康；不做聚类、价值判断、背景补全、AI 点评和分发。

## 1. 目标

定义 M2 阶段的数据源、抓取任务、原始条目和源健康 API。后端按本文实现；前端按本文展示和触发；测试按本文构造 fixture。任何实现不得绕过本文直接暴露 RSS/RSSHub/AI HOT 原始响应。

M2 覆盖：

- Source Registry。
- AI HOT API、AI HOT RSS、RSSHub route、自定义 RSS。
- Source preview。
- 手动触发 source 抓取。
- FetchRun 列表和详情。
- RawItem 查询。
- SourceHealth 查询。
- 统一响应、统一错误、统一 trace。

## 2. 全局约定

### 2.1 Base URL

沿用 M1：

```text
http://localhost:8000/api
```

### 2.2 响应 envelope

所有 API 仍使用 M1 envelope：

```json
{
  "data": {},
  "meta": {
    "traceId": "tr_20260529_000001",
    "source": "hot-godlike",
    "cached": false,
    "query": {},
    "warnings": []
  },
  "error": null
}
```

失败响应：

```json
{
  "data": null,
  "meta": {
    "traceId": "tr_20260529_000001",
    "source": "hot-godlike",
    "cached": false,
    "query": {},
    "warnings": []
  },
  "error": {
    "code": "SOURCE_UNREACHABLE",
    "message": "数据源暂时不可访问，请稍后重试。",
    "details": {
      "sourceId": "src_aihot_api"
    },
    "retryable": true
  }
}
```

### 2.3 分页

M2 管理 API 使用 cursor 分页：

```json
{
  "items": [],
  "page": {
    "take": 50,
    "hasNext": false,
    "nextCursor": null
  }
}
```

### 2.4 时间

- 所有服务端存储和 API 输出使用 ISO 8601 UTC。
- 前端展示时可转换为用户本地时区。
- 调度配置使用分钟级 interval，不在 M2 支持复杂 cron。

## 3. 枚举

### 3.1 SourceType

```ts
type SourceType = "aihot_api" | "aihot_rss" | "rss" | "rsshub";
```

说明：

- `aihot_api`：复用 M1 AI HOT client 能力，作为高可信种子源。
- `aihot_rss`：AI HOT RSS feed。
- `rss`：普通 RSS/Atom URL。
- `rsshub`：RSSHub route，通过主备 RSSHub base URL 生成 feed URL。

M2 不实现 `hot_search`、`news_site`、`social`、`website`，这些留给后续阶段扩展。

### 3.2 SourceStatus

```ts
type SourceStatus = "enabled" | "disabled" | "degraded" | "circuit_open";
```

### 3.3 FetchRunStatus

```ts
type FetchRunStatus = "queued" | "running" | "succeeded" | "partial_failed" | "failed" | "cancelled";
```

### 3.4 TrustLevel

```ts
type TrustLevel = "high" | "medium" | "low";
```

### 3.5 RawItemStatus

```ts
type RawItemStatus = "new" | "duplicate" | "ignored" | "failed";
```

## 4. 数据结构

### 4.1 SourceConfig

```json
{
  "id": "src_aihot_api",
  "name": "AI HOT API",
  "type": "aihot_api",
  "category": "ai",
  "url": "https://aihot.virxact.com/api/public/items",
  "route": null,
  "enabled": true,
  "status": "enabled",
  "fetchIntervalMinutes": 30,
  "timeoutSeconds": 30,
  "retryCount": 2,
  "concurrencyLimit": 1,
  "trustLevel": "high",
  "requiresCookie": false,
  "firstFetchMode": "ingest_only",
  "etag": null,
  "lastModified": null,
  "lastFetchedAt": null,
  "createdAt": "2026-05-29T00:00:00Z",
  "updatedAt": "2026-05-29T00:00:00Z"
}
```

字段规则：

- `id` 由后端生成或按配置导入，前端创建时不传。
- `name/type/category/enabled/fetchIntervalMinutes/timeoutSeconds/retryCount/trustLevel` 必填。
- `url` 对 `rss`、`aihot_rss` 必填；对 `rsshub` 可为空。
- `route` 对 `rsshub` 必填，例如 `/hackernews/frontpage`。
- `requiresCookie=true` 在 M2 只允许保存配置占位，不允许实际抓取。
- `firstFetchMode` 固定为 `ingest_only`，表示首次抓取只入库不推送。

### 4.2 SourceInput

```json
{
  "name": "Hacker News",
  "type": "rsshub",
  "category": "tech",
  "url": null,
  "route": "/hackernews/frontpage",
  "enabled": true,
  "fetchIntervalMinutes": 30,
  "timeoutSeconds": 30,
  "retryCount": 2,
  "concurrencyLimit": 1,
  "trustLevel": "medium",
  "requiresCookie": false
}
```

校验规则：

- `name` 长度 1-80。
- `category` 长度 1-40，只允许字母、数字、短横线、下划线。
- `fetchIntervalMinutes` 范围 5-1440。
- `timeoutSeconds` 范围 5-60。
- `retryCount` 范围 0-3。
- `concurrencyLimit` 范围 1-5。
- `url` 必须为 `http` 或 `https`。
- `url` 必须通过 SSRF 防护，禁止 localhost、内网 IP、链路本地地址、file 协议、ftp 协议。

### 4.3 SourcePreview

```json
{
  "source": {
    "name": "Hacker News",
    "type": "rsshub",
    "route": "/hackernews/frontpage"
  },
  "sampleItems": [
    {
      "title": "Example item",
      "url": "https://example.com/item",
      "publishedAt": "2026-05-29T00:00:00Z",
      "contentSnippet": "Preview only"
    }
  ],
  "warnings": []
}
```

### 4.4 FetchRun

```json
{
  "id": "run_20260529_000001",
  "sourceId": "src_aihot_api",
  "trigger": "manual",
  "status": "succeeded",
  "startedAt": "2026-05-29T00:00:00Z",
  "finishedAt": "2026-05-29T00:00:02Z",
  "durationMs": 2200,
  "fetchedCount": 30,
  "newCount": 12,
  "duplicateCount": 18,
  "ignoredCount": 0,
  "errorCode": null,
  "errorMessage": null,
  "traceId": "tr_20260529_000001"
}
```

`trigger` 枚举：

```ts
type FetchTrigger = "manual" | "schedule" | "retry" | "preview";
```

### 4.5 RawItem

```json
{
  "id": "raw_src_aihot_api_abcd1234",
  "sourceId": "src_aihot_api",
  "sourceName": "AI HOT API",
  "title": "string",
  "url": "https://example.com",
  "normalizedUrl": "https://example.com",
  "publishedAt": "2026-05-29T00:00:00Z",
  "fetchedAt": "2026-05-29T00:00:03Z",
  "author": null,
  "summary": null,
  "contentSnippet": null,
  "hotScore": null,
  "rank": null,
  "image": null,
  "rawPayloadRef": "raw_payload/raw_src_aihot_api_abcd1234.json",
  "status": "new"
}
```

字段规则：

- `id/title/url/sourceId/fetchedAt` 必须存在。
- `normalizedUrl` 必须由后端生成，不能信任来源原值。
- `summary/contentSnippet/publishedAt/author/hotScore/rank/image` 可为 `null`。
- `rawPayloadRef` 可以是数据库 JSONB 引用、对象存储 key 或空值；不能在列表 API 返回完整原始 payload。

### 4.6 SourceHealth

```json
{
  "sourceId": "src_aihot_api",
  "status": "enabled",
  "lastSucceededAt": "2026-05-29T00:00:02Z",
  "lastFailedAt": null,
  "consecutiveFailures": 0,
  "nextFetchAt": "2026-05-29T00:30:00Z",
  "circuitOpenedAt": null,
  "degradedUntil": null,
  "lastErrorCode": null,
  "lastErrorMessage": null
}
```

策略规则：

- 连续失败 3 次后，`status` 进入 `degraded`；`nextFetchAt` 延后为 `lastFailedAt + fetchIntervalMinutes * 3`，`degradedUntil` 与该次 `nextFetchAt` 一致。
- 连续失败 5 次后，`status` 进入 `circuit_open`；`circuitOpenedAt` 写入当前失败时间，`nextFetchAt` 延后 30 分钟，`degradedUntil` 清空。
- 成功抓取后，`status` 恢复为 `enabled`，`consecutiveFailures` 归零，并按 source 原始 `fetchIntervalMinutes` 计算下一次抓取时间。
- SourceConfig `status` 必须和最新 SourceHealth `status` 同步；scheduler 按 SourceConfig `enabled` 布尔值扫描 source，再由 SourceHealth `nextFetchAt` 控制调度窗口。

## 5. 错误码

| code | HTTP | retryable | 场景 |
|---|---:|:---:|---|
| `BAD_REQUEST` | 400 | 否 | 参数格式错误 |
| `SOURCE_NOT_FOUND` | 404 | 否 | source 不存在 |
| `SOURCE_DISABLED` | 409 | 否 | source 已停用，不能触发抓取 |
| `SOURCE_COOKIE_REQUIRED` | 409 | 否 | M2 不抓取 cookie 类 source |
| `SOURCE_UNREACHABLE` | 502 | 是 | RSS/RSSHub/AI HOT 无法访问 |
| `SOURCE_TIMEOUT` | 504 | 是 | 抓取超时 |
| `SOURCE_BAD_RESPONSE` | 502 | 是 | RSS/XML/JSON 解析失败 |
| `SOURCE_SSRF_BLOCKED` | 400 | 否 | URL 被 SSRF 防护拦截 |
| `SOURCE_RATE_LIMITED` | 503 | 是 | 上游限流 |
| `FETCH_RUN_NOT_FOUND` | 404 | 否 | run 不存在 |
| `RAW_ITEM_NOT_FOUND` | 404 | 否 | raw item 不存在 |
| `INTERNAL_ERROR` | 500 | 否 | 未知错误 |

## 6. API 端点

### 6.1 创建 source

```http
POST /api/sources
```

请求体：`SourceInput`

响应：`SourceConfig`

### 6.2 更新 source

```http
PATCH /api/sources/{sourceId}
```

请求体：`Partial<SourceInput>`

响应：`SourceConfig`

### 6.3 查询 source 列表

```http
GET /api/sources?type=rsshub&status=enabled&take=50&cursor=opaque
```

响应：

```json
{
  "items": [],
  "page": {
    "take": 50,
    "hasNext": false,
    "nextCursor": null
  }
}
```

### 6.4 查询 source 详情

```http
GET /api/sources/{sourceId}
```

响应：`SourceConfig`

### 6.5 启停 source

```http
POST /api/sources/{sourceId}/enable
POST /api/sources/{sourceId}/disable
```

响应：`SourceConfig`

### 6.6 预览 source

```http
POST /api/sources/preview
```

请求体：`SourceInput`

响应：`SourcePreview`

规则：

- preview 不入库。
- preview 也必须执行 SSRF 防护和超时。
- preview 返回最多 5 条 sample item。

### 6.7 手动触发抓取

```http
POST /api/sources/{sourceId}/fetch
```

请求体：

```json
{
  "idempotencyKey": "manual_20260529_000001",
  "reason": "manual smoke"
}
```

响应：`FetchRun`

规则：

- 同一 `idempotencyKey` 重复请求返回同一个或等价 run，不重复抓取。
- source disabled 时返回 `SOURCE_DISABLED`。
- requiresCookie source 返回 `SOURCE_COOKIE_REQUIRED`。

### 6.8 查询 fetch runs

```http
GET /api/fetch-runs?sourceId=src_aihot_api&status=succeeded&take=50&cursor=opaque
```

响应：分页 `FetchRun[]`。

### 6.9 查询 fetch run 详情

```http
GET /api/fetch-runs/{runId}
```

响应：`FetchRun`

### 6.10 查询 raw items

```http
GET /api/raw-items?sourceId=src_aihot_api&status=new&q=OpenAI&take=50&cursor=opaque
```

响应：分页 `RawItem[]`。

### 6.11 查询 raw item 详情

```http
GET /api/raw-items/{rawItemId}
```

响应：`RawItem`

### 6.12 查询 source health

```http
GET /api/source-health?sourceId=src_aihot_api&status=degraded&take=50&cursor=opaque
```

响应：分页 `SourceHealth[]`。

## 7. 存储契约

M2 正式 / 共享环境必须落 PostgreSQL 表：

- `sources`
- `fetch_runs`
- `raw_items`
- `source_health`

本地开发允许显式启用 SQLite 持久化模式：

- `STORAGE_MODE=local`
- 默认路径为 `backend/data/hot_godlike.sqlite`
- 可通过 `LOCAL_STORAGE_PATH` 覆盖
- SQLite 必须保存同一组 `sources`、`fetch_runs`、`raw_items`、`source_health` 数据
- 内存模式仅用于本地开发和测试，不保证重启后数据存在

不得在 PostgreSQL 配置缺失时静默降级到本地文件；存储模式必须由配置显式选择。

M2 必须使用 Redis key：

- `source:lock:{source_id}`：源级抓取锁。
- `source:etag:{source_id}`：ETag。
- `source:last_modified:{source_id}`：Last-Modified。
- `source:dedupe:{source_id}`：源内去重集合。
- `fetch_run:progress:{run_id}`：轻量进度。

## 8. 去重契约

RawItem 源内去重键：

```text
source_id + normalized_url
```

当 URL 缺失或不稳定时可退化为：

```text
source_id + normalized_title + published_date
```

规则：

- M2 只做源内去重，不做跨源事件聚类。
- 命中源内重复时不得重复插入 `raw_items`。
- 重复条目必须计入 `FetchRun.duplicateCount`。

## 9. 安全边界

- 任意 URL 抓取必须执行 SSRF 防护。
- 禁止访问 localhost、127.0.0.0/8、10.0.0.0/8、172.16.0.0/12、192.168.0.0/16、169.254.0.0/16、::1、fc00::/7、fe80::/10。
- 禁止 `file://`、`ftp://`、`gopher://` 等非 HTTP(S) 协议。
- DNS 解析后的 IP 也必须检查。
- Cookie、Authorization、Webhook URL 等敏感值不得出现在普通日志、API 响应或测试 fixture。
- 外部内容按不可信输入处理，不进入系统 prompt。

## 10. Mock Fixture 要求

后端测试必须提供：

- AI HOT API fixture。
- AI HOT RSS fixture。
- RSSHub route fixture。
- 自定义 RSS fixture。
- malformed RSS fixture。
- timeout fixture。
- 429/503 fixture。
- duplicate item fixture。
- private IP / localhost URL fixture。

前端 mock 必须覆盖：

- source 列表。
- source 创建成功。
- source preview 成功和失败。
- 手动 fetch 触发成功。
- fetch run 成功、失败、运行中。
- raw item 列表。
- source health degraded / circuit open。

## 11. 非目标

M2 不包含：

- 跨源事件聚类。
- 价值判断。
- 背景补全。
- AI 点评。
- 分发推送。
- 复杂权限和多租户。
- Cookie 类 source 实际抓取。
- 大规模网站爬虫。
