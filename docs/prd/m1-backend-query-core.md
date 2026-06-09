# M1 后端查询内核子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/query-api.md`
> 推荐实现客户端：后端 AI coding 客户端
> 技术栈决策：Python + FastAPI，公开只读 API，暂不引入数据库。

## 1. 目标

实现 M1 阶段的后端查询内核：把用户查询参数转换为 AI HOT 公开 API 请求，完成意图路由、参数构造、时间解析、分类映射、错误处理、ETag/cache、统一响应 envelope，并为前端提供稳定 API。

后端是 AI HOT 的唯一适配层。前端、CLI 或其他调用方不能直接依赖 AI HOT 字段。

## 2. 范围

### 2.1 In Scope

- `GET /api/query/items`
- `GET /api/query/daily`
- `GET /api/query/dailies`
- `GET /api/query/help`
- AI HOT client。
- IntentRouter / QueryPlanner。
- 中文时间窗解析。
- 分类映射。
- AI HOT response normalizer。
- ETag 与短期缓存。
- 统一错误 envelope。
- OpenAPI 自动文档。
- 单元测试与 mock 集成测试。

### 2.2 Out of Scope

- 登录、用户、权限。
- PostgreSQL schema。
- 多源采集入库。
- RSSHub、自定义 RSS 抓取。
- Topic 聚类、价值评分、背景补全、AI 点评。
- 推送、订阅、Webhook。
- 前端页面。

## 3. 模块设计

### 3.1 `IntentRouter`

职责：

- 将请求参数或自然语言 query 映射到查询意图。
- M1 API 以结构化参数为主，保留 `q`、`timePreset`、`category` 等字段。
- 不做大模型意图识别。

规则：

- `mode` 默认为 `selected`。
- 明确 `mode=all` 才查全部动态。
- `GET /api/query/daily` 只用于日报。
- `GET /api/query/items` 不自动改路由到日报。

测试：

- 默认请求走 selected。
- `mode=all` 透传 all。
- 非法 mode 返回 `BAD_REQUEST`。

### 3.2 `QueryPlanner`

职责：

- 构造 AI HOT endpoint、query params、headers。
- 转换 `timePreset` 为 ISO 8601 UTC `since`。
- 校验 take、cursor、q、category、since。
- 保留 cursor opaque，不解析。

AI HOT 请求头：

```http
User-Agent: hot-godlike-agent/0.1 (+contact-or-project-url)
```

items 映射：

| 本系统参数 | AI HOT 参数 |
|---|---|
| `mode` | `mode` |
| `category` | `category` |
| `q` | `q` |
| `since/timePreset` | `since` |
| `take` | `take` |
| `cursor` | `cursor` |

### 3.3 `AihotClient`

职责：

- 请求 AI HOT 公开 API。
- 设置 UA、超时、重试。
- 支持 ETag / If-None-Match。
- 将 304 映射为无新内容语义。
- 不把上游原始错误直接暴露给前端。

默认配置：

- timeout：10 秒。
- retry：最多 2 次，仅网络超时、429、503、5xx 可重试。
- retry backoff：指数退避。
- rate limit：本系统主动限制请求频率，远低于 AI HOT 声明的 `600 req/min/IP`。

### 3.4 `ResponseNormalizer`

职责：

- 将 AI HOT items 响应映射为 `QueryItemList`。
- 将 AI HOT daily 响应映射为 `DailyReport`。
- 将 AI HOT dailies 响应映射为 `DailyArchiveItem[]`。
- 缺失字段按契约返回 `null` 或空数组，不编造。

字段规则：

- `title/url/source/id` 缺失时该 item 标记为异常并跳过，同时写日志。
- `summary` 缺失时返回 `null`。
- `publishedAt` 缺失时返回 `null`。
- `category` 不在枚举内时返回 `null`。

### 3.5 `CacheStore`

M1 可使用内存缓存，后续替换为 Redis。

职责：

- 按 query key 保存 ETag。
- 保存最近一次成功响应的短期缓存。
- 缓存命中必须在 `meta.cached=true` 标注。
- 上游失败时不得把旧缓存伪装成最新结果。

query key 至少包含：

```text
endpoint + mode + category + since + q + take + cursor
```

### 3.6 `ErrorMapper`

职责：

- 将参数错误、上游错误、解析错误统一映射为契约错误码。
- 记录 trace id。
- 用户可见错误使用简体中文。

## 4. API 实现要求

以 `docs/contracts/query-api.md` 为准。后端必须实现：

```text
GET /api/query/items
GET /api/query/daily
GET /api/query/dailies
GET /api/query/help
```

所有响应必须使用：

```json
{
  "data": {},
  "meta": {},
  "error": null
}
```

## 5. 验收标准

- `GET /api/query/items` 默认返回 selected 查询结果。
- `GET /api/query/items?mode=all` 查询全部动态。
- `GET /api/query/items?category=paper&timePreset=7d` 生成合法 7 天内查询。
- `GET /api/query/items?q=a` 返回 `BAD_REQUEST`。
- `GET /api/query/daily` 查询最新日报。
- `GET /api/query/daily?date=2026-05-28` 查询指定日期日报。
- `GET /api/query/dailies?take=3` 返回日报归档列表。
- 所有请求都有 trace id。
- 所有 AI HOT 请求都有 User-Agent。
- 上游 403、404、429、503、超时、解析失败都有统一错误。
- 空结果返回空数组，不报错。
- 不出现无源事实补充。

## 6. 测试要求

### 6.1 单元测试

- 分类映射。
- 时间窗解析。
- QueryPlanner 参数构造。
- cursor opaque 透传。
- q 长度校验。
- take 范围校验。
- ErrorMapper。
- ResponseNormalizer 缺字段处理。

### 6.2 集成测试

使用 mock AI HOT server 或 httpx mock：

- items selected 成功。
- items all 成功。
- daily 成功。
- dailies 成功。
- 304 Not Modified。
- 403。
- 404 date not found。
- 429/503 retry。
- timeout retry。
- bad JSON。

测试不能断言真实新闻标题。

## 7. 交付物

- FastAPI 应用入口。
- 查询 API 路由。
- AI HOT client。
- router/planner/normalizer/cache/error 模块。
- OpenAPI 文档可访问。
- mock 测试数据。
- 单元测试和集成测试。
- README 或开发说明，写清如何运行后端和测试。

## 8. 联调边界

- 前端只能调用本系统 `/api/query/*`。
- 后端必须支持 CORS 开发配置。
- 前端 mock 数据必须来自 `docs/contracts/query-api.md`，不能自行设计新字段。
- 契约变更先改 `docs/contracts/query-api.md`，再改后端和前端。
