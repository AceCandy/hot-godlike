# M2 后端采集基础设施子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/collection-api.md`
> 上游依赖：M1 查询 API 与 AI HOT client
> 推荐实现客户端：后端 / worker AI coding 客户端
> 技术栈决策：Python + FastAPI + PostgreSQL + Redis + APScheduler worker service。正式 / 共享环境使用 PostgreSQL；本地开发可显式启用 SQLite 持久化模式。

## 1. 目标

实现 M2 阶段的后端采集基础设施：Source Registry、RSS/RSSHub/AI HOT fetcher、RawItem normalizer、RawStore、源内去重、FetchRun、SourceHealth、源级锁、ETag/Last-Modified、SSRF 防护和手动/定时抓取。

M2 的目标是稳定获得标准化 `RawItem`，为 M3 去重聚类提供输入。M2 不判断热点价值，不做跨源聚类，不生成点评，不推送。

## 2. 背景与依赖

M1 已完成：

- 统一 envelope。
- AI HOT client。
- 查询 API。
- 前端查询工作台。

M2 在此基础上扩展：

- 从“临时查询 AI HOT”变成“持久采集多来源”。
- 引入 PostgreSQL 保存 source、run、raw item、health。
- 引入显式本地 SQLite 模式，便于没有 PostgreSQL 的本机环境保留 source 和抓取数据；不得作为静默降级。
- 引入 Redis 保存锁、ETag、Last-Modified、去重集合、轻量 run 状态。
- 参考 HotPush 的 RSSHub/RSS、调度、缓存、规则和多源基础能力，但不照搬其源内 ID 作为跨源聚类能力。

## 3. 范围

### 3.1 In Scope

- `POST /api/sources`
- `PATCH /api/sources/{sourceId}`
- `GET /api/sources`
- `GET /api/sources/{sourceId}`
- `POST /api/sources/{sourceId}/enable`
- `POST /api/sources/{sourceId}/disable`
- `POST /api/sources/preview`
- `POST /api/sources/{sourceId}/fetch`
- `GET /api/fetch-runs`
- `GET /api/fetch-runs/{runId}`
- `GET /api/raw-items`
- `GET /api/raw-items/{rawItemId}`
- `GET /api/source-health`
- PostgreSQL schema 和 migration。
- Redis key 设计与实现。
- SourceRegistry。
- FetcherPool。
- AihotApiFetcher。
- RssFetcher。
- RsshubFetcher。
- RawItemNormalizer。
- RawStore。
- SourceHealthService。
- SchedulerService。
- SSRFGuard。
- ETag / Last-Modified。
- 源级 timeout、retry、concurrency、lock。
- 首次抓取保护：只入库不推送。
- 单元测试、集成测试、mock RSS fixture。

### 3.2 Out of Scope

- M3 跨源事件聚类。
- M4 价值判断和背景补全。
- M5 AI 点评和推送。
- 完整登录权限系统。
- Cookie 类 source 实际抓取。
- 大规模网站爬虫。
- 社交平台登录态采集。
- 前端完整管理后台，只提供 M2 前端 PRD 所需 API。

## 4. 用户故事 / 系统场景

### 4.1 管理员添加 RSSHub source

管理员提交 RSSHub route，例如 `/hackernews/frontpage`。系统校验 route，拼接 RSSHub base URL，执行 preview，返回 sample items。确认后写入 `sources`。

### 4.2 系统定时抓取

Scheduler 根据 source 的 `fetchIntervalMinutes` 触发抓取。Fetcher 获取源级锁，带 ETag/Last-Modified 请求上游，解析响应，归一化 RawItem，源内去重，写入 `raw_items` 和 `fetch_runs`，更新 `source_health`。

### 4.3 单个 source 失败

某 RSS 源超时。系统只标记该 source 的 run failed，不影响其他 source。连续失败达到阈值后，source health 进入 `degraded` 或 `circuit_open`。

### 4.4 首次抓取保护

新 source 第一次抓取可能返回大量历史内容。系统写入 RawItem，但 `FetchRun.trigger` 或 source 标记体现首次抓取，后续阶段不得把这些历史 item 当作新推送候选。

## 5. 模块设计

### 5.1 SourceRegistry

职责：

- source CRUD。
- source enable / disable。
- source 配置校验。
- source 类型和 fetcher 映射。
- source preview 前置校验。

规则：

- M2 source 类型仅支持 `aihot_api`、`aihot_rss`、`rss`、`rsshub`。
- `requiresCookie=true` 只可保存，不可 fetch。
- disabled source 不参与 scheduler，也不可手动 fetch。
- source 更新必须写 `updated_at`。

### 5.2 SSRFGuard

职责：

- 校验 URL scheme。
- 校验 hostname。
- DNS 解析并检查 IP。
- 阻断内网、localhost、链路本地地址。

规则：

- `rss` / `aihot_rss` 的 `url` 必须通过 SSRFGuard。
- `rsshub` 由系统配置的 RSSHub base URL + route 生成，base URL 也必须通过 SSRFGuard。
- 重定向后的最终 URL 也必须再次检查。

### 5.3 FetcherPool

职责：

- 根据 source type 调用对应 fetcher。
- 执行源级锁。
- 执行 timeout、retry、backoff。
- 写入 FetchRun 状态。
- 更新 SourceHealth。

默认参数：

- 单源 timeout：30 秒。
- retry：最多 2 次。
- source concurrency：默认 1。
- 全局采集并发：默认 5。
- retry backoff：指数退避。

### 5.4 AihotApiFetcher

职责：

- 复用 M1 AI HOT client。
- 将 AI HOT items API 转为 RawItem。
- 使用 M1 User-Agent、timeout、错误映射。

规则：

- 不返回 AI HOT 原始响应给 API 调用方。
- 原始 payload 只保存 raw payload ref。

### 5.5 RssFetcher

职责：

- 抓取 RSS / Atom。
- 支持 ETag / Last-Modified。
- 解析 title、link、published、author、summary、image。
- 处理 malformed RSS。

建议依赖：

- `httpx`
- `feedparser`

### 5.6 RsshubFetcher

职责：

- 根据 RSSHub base URL 和 route 构造 feed URL。
- 支持主备 RSSHub 实例。
- 主实例失败时尝试备用实例。
- 记录实际命中的 RSSHub endpoint。

### 5.7 RawItemNormalizer

职责：

- 统一不同来源字段为 `RawItem`。
- 生成 `normalizedUrl`。
- 生成源内去重 key。
- 缺失可选字段返回 `null`。
- 缺失 `title/url/source_id` 的 item 标记 ignored，不编造。

### 5.8 RawStore

职责：

- 写入 raw items。
- 源内去重。
- 查询 raw item 列表和详情。
- 保存 raw payload ref。

规则：

- 唯一约束优先：`source_id + normalized_url`。
- URL 不稳定时使用 `source_id + normalized_title + published_date`。
- 命中重复不报错，计入 duplicate。

### 5.9 SourceHealthService

职责：

- 更新连续失败次数。
- 记录最近成功/失败时间。
- 计算 degraded / circuit_open。
- 提供 health 查询 API。

默认策略：

- 连续失败 3 次：`degraded`。
- degraded 后继续低频抓取，M2 默认低频窗口为 `fetchIntervalMinutes * 3`，并写入 `degradedUntil`。
- 连续失败 5 次：`circuit_open`。
- circuit open 后 30 分钟内不自动抓取。
- 手动 fetch 可返回明确错误或管理员强制重试，M2 默认不做强制重试。
- 成功抓取后恢复为 `enabled`，连续失败次数清零，并同步 SourceConfig `status`。

### 5.10 SchedulerService

职责：

- 使用 APScheduler 周期性扫描 enabled source。
- 根据 `nextFetchAt` 触发 fetch。
- 避免重复调度同一 source。

规则：

- 单 worker 优先。
- worker service 与 API service 可同进程开发，生产可拆分。
- 调度接口保持稳定，后续可替换 Celery/RQ。

## 6. 数据库 Schema

### 6.1 `sources`

字段：

- `id` text primary key
- `name` text not null
- `type` text not null
- `category` text not null
- `url` text null
- `route` text null
- `enabled` boolean not null
- `status` text not null
- `fetch_interval_minutes` integer not null
- `timeout_seconds` integer not null
- `retry_count` integer not null
- `concurrency_limit` integer not null
- `trust_level` text not null
- `requires_cookie` boolean not null default false
- `first_fetch_mode` text not null default `ingest_only`
- `etag` text null
- `last_modified` text null
- `last_fetched_at` timestamptz null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

### 6.2 `fetch_runs`

字段：

- `id` text primary key
- `source_id` text not null references sources(id)
- `trigger` text not null
- `status` text not null
- `started_at` timestamptz not null
- `finished_at` timestamptz null
- `duration_ms` integer null
- `fetched_count` integer not null default 0
- `new_count` integer not null default 0
- `duplicate_count` integer not null default 0
- `ignored_count` integer not null default 0
- `error_code` text null
- `error_message` text null
- `trace_id` text not null
- `idempotency_key` text null

唯一约束：

- `source_id + idempotency_key` where idempotency_key is not null

### 6.3 `raw_items`

字段：

- `id` text primary key
- `source_id` text not null references sources(id)
- `source_name` text not null
- `title` text not null
- `url` text not null
- `normalized_url` text not null
- `published_at` timestamptz null
- `fetched_at` timestamptz not null
- `author` text null
- `summary` text null
- `content_snippet` text null
- `hot_score` text null
- `rank` integer null
- `image` text null
- `raw_payload_ref` text null
- `status` text not null
- `dedupe_key` text not null
- `created_at` timestamptz not null

唯一约束：

- `source_id + dedupe_key`

索引：

- `raw_items(source_id, fetched_at desc)`
- `raw_items(status, fetched_at desc)`
- `raw_items(normalized_url)`

### 6.4 `source_health`

字段：

- `source_id` text primary key references sources(id)
- `status` text not null
- `last_succeeded_at` timestamptz null
- `last_failed_at` timestamptz null
- `consecutive_failures` integer not null default 0
- `next_fetch_at` timestamptz null
- `circuit_opened_at` timestamptz null
- `degraded_until` timestamptz null
- `last_error_code` text null
- `last_error_message` text null
- `updated_at` timestamptz not null

## 7. Redis Key 设计

```text
source:lock:{source_id}
source:etag:{source_id}
source:last_modified:{source_id}
source:dedupe:{source_id}
fetch_run:progress:{run_id}
```

规则：

- lock 必须有 TTL，默认大于 source timeout + retry 总预算。
- ETag / Last-Modified 与 DB 字段保持同步，Redis 作为快速读写。
- dedupe set 可作为快速路径，PostgreSQL unique constraint 是最终兜底。

## 8. API 实现要求

以 `docs/contracts/collection-api.md` 为准。

所有 API 必须：

- 使用统一 envelope。
- 有 trace id。
- 不暴露敏感字段。
- 不返回完整 raw payload。
- 对外错误使用简体中文。

写操作：

- M2 暂不实现完整登录，但代码边界必须预留鉴权 dependency。
- 副作用 API 必须支持 idempotency 或明确不可重复。

## 9. Agent 输入输出

M2 Collector Agent 是逻辑 Agent，不要求独立 LLM。

输入：

- `SourceConfig`
- `FetchTrigger`
- `idempotencyKey`

输出：

- `FetchRun`
- `RawItem[]`
- `SourceHealth`

Trace：

- 每次 fetch 必须记录 trace id。
- 每个 source 的失败原因必须可查。

## 10. 状态机

### 10.1 FetchRun

```text
queued -> running -> succeeded
queued -> running -> partial_failed
queued -> running -> failed
queued -> cancelled
```

规则：

- 单 source fetch 成功但部分 item ignored：`partial_failed` 或 `succeeded` + ignoredCount，具体以错误严重度决定。
- 上游完全失败：`failed`。
- 304 not modified：`succeeded`，fetched/new/duplicate 均可为 0。

### 10.2 SourceHealth

```text
enabled -> degraded -> circuit_open -> enabled
enabled -> disabled
disabled -> enabled
```

规则：

- disabled 不自动抓取。
- degraded 可以继续低频抓取，M2 默认按 source `fetchIntervalMinutes * 3` 计算下一次抓取时间。
- circuit_open 在 30 分钟 cooldown 内不自动抓取，cooldown 到期后可由 scheduler 尝试恢复。

## 11. 错误处理

必须实现 `docs/contracts/collection-api.md` 的错误码。

错误映射：

- 参数错误：`BAD_REQUEST`
- 不存在：`SOURCE_NOT_FOUND` / `FETCH_RUN_NOT_FOUND` / `RAW_ITEM_NOT_FOUND`
- disabled：`SOURCE_DISABLED`
- cookie source：`SOURCE_COOKIE_REQUIRED`
- SSRF：`SOURCE_SSRF_BLOCKED`
- timeout：`SOURCE_TIMEOUT`
- XML/JSON 解析失败：`SOURCE_BAD_RESPONSE`
- 429：`SOURCE_RATE_LIMITED`
- 5xx / 网络错误：`SOURCE_UNREACHABLE`

## 12. 安全与合规

- SSRFGuard 是 M2 阻塞需求，不能延后。
- 任何外部 URL fetch 前必须检查。
- 重定向后的 URL 必须再次检查。
- 日志不得记录 Authorization、Cookie、完整 webhook URL。
- RSS 内容不可信，不得进入系统 prompt。
- Cookie 类 source 不在 M2 实际抓取。

## 13. 测试 Fixture

必须创建：

- `fixtures/aihot-items.json`
- `fixtures/aihot-feed.xml`
- `fixtures/rsshub-hackernews.xml`
- `fixtures/custom-rss.xml`
- `fixtures/malformed-rss.xml`
- `fixtures/duplicate-rss.xml`

Fixture 不得包含真实密钥、cookie、授权头。

## 14. 测试要求

### 14.1 单元测试

- SourceInput 校验。
- SSRFGuard 阻断 localhost / private IP / file scheme。
- RSSHub route 构造。
- ETag / Last-Modified header。
- RawItemNormalizer 字段映射。
- normalized URL。
- dedupe key。
- SourceHealth 状态流转。
- FetchRun 状态流转。

### 14.2 集成测试

- 创建 source。
- preview RSS 成功。
- malformed RSS 返回 `SOURCE_BAD_RESPONSE`。
- 手动 fetch 成功写入 raw items。
- 重复 fetch 不重复写入。
- 单 source 失败不影响另一个 source。
- 429/503 retry。
- timeout retry。
- consecutive failures 进入 degraded / circuit_open。

测试不能断言实时新闻标题。

## 15. 验收标准

- 可创建 AI HOT API、AI HOT RSS、RSSHub route、自定义 RSS source。
- 可 preview RSSHub route 和自定义 RSS。
- 手动触发 fetch 产生 FetchRun。
- 抓取成功写入 RawItem。
- 同一 source 重复抓取不会重复入库。
- 单个 source 失败不影响其他 source。
- 连续失败 source 进入 degraded 或 circuit_open。
- `/api/fetch-runs` 可查看 source、状态、耗时、新增条数、错误。
- `/api/raw-items` 每条至少有 `id/title/url/sourceId/fetchedAt`。
- SSRF 防护测试通过。
- M2 不引入聚类、评分、点评、推送。

## 16. 交付物

- PostgreSQL migration。
- Redis key helper。
- Source model / repository / service。
- FetchRun model / repository / service。
- RawItem model / repository / service。
- SourceHealth model / repository / service。
- FetcherPool。
- AihotApiFetcher。
- RssFetcher。
- RsshubFetcher。
- RawItemNormalizer。
- SSRFGuard。
- SchedulerService。
- API routes。
- fixtures。
- 单元测试和集成测试。
- README 更新，写清本地启动 PostgreSQL / Redis / worker 的方式。

## 17. 联调边界

- 前端只调用 `docs/contracts/collection-api.md` 定义的 `/api/sources`、`/api/fetch-runs`、`/api/raw-items`、`/api/source-health`。
- 前端不直接访问 RSS/RSSHub/AI HOT。
- M3 只能消费 `raw_items`，不能直接调用 source fetcher。
- 如果 contract 变更，先改 `docs/contracts/collection-api.md`，再改后端和前端。

## 18. 已知风险

- RSSHub route 质量和可用性不稳定，必须有主备和错误可见。
- 真实 RSS 字段差异大，normalizer 必须容忍字段缺失。
- SSRF 防护必须覆盖 DNS 解析和重定向，否则存在安全风险。
- 首次抓取可能写入大量历史数据，必须默认只入库不推送。
- SQLite 不适合验证最终 PostgreSQL 约束；集成测试应尽量使用真实 PostgreSQL 或兼容测试容器。
