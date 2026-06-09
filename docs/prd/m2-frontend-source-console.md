# M2 前端数据源管理入口子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/collection-api.md`
> 上游依赖：M1 查询工作台
> 推荐实现客户端：前端 AI coding 客户端
> 技术栈决策：Vue 3 + Vite + Tailwind CSS。

## 1. 目标

实现 M2 阶段的轻量数据源管理入口，让管理员或开发者可以查看 source、创建/编辑 source、preview RSS/RSSHub、手动触发抓取、查看 fetch run、raw item 和 source health。

M2 前端不是完整管理后台，只服务采集基础设施验收和联调。

## 2. 范围

### 2.1 In Scope

- 数据源列表。
- 数据源创建 / 编辑表单。
- 数据源启停。
- Source preview。
- 手动触发 fetch。
- FetchRun 列表。
- RawItem 列表。
- SourceHealth 状态展示。
- 错误态、加载态、空状态。
- 使用 mock API 并行开发。
- 移动端基本适配。

### 2.2 Out of Scope

- 登录、权限、用户管理。
- 完整后台导航。
- 聚类、评分、背景包、点评、分发。
- Cookie 类 source 配置 UI。
- RSSHub route 自动发现。
- 复杂图表和趋势分析。
- 直接抓取外部 URL。

## 3. 页面结构

M2 可在 M1 查询工作台旁增加一个“数据源”入口，或独立创建 Source Console 页面。实现方式可按项目实际路由决定。

### 3.1 Source 列表

展示字段：

- 名称。
- 类型。
- 分类。
- enabled。
- status。
- trustLevel。
- fetchIntervalMinutes。
- lastFetchedAt。
- 操作：编辑、启用/停用、预览、抓取。

筛选：

- type。
- status。
- enabled。
- category。

### 3.2 Source 表单

字段：

- name。
- type。
- category。
- url。
- route。
- enabled。
- fetchIntervalMinutes。
- timeoutSeconds。
- retryCount。
- concurrencyLimit。
- trustLevel。
- requiresCookie。

行为：

- `rss` / `aihot_rss` 展示 URL 输入。
- `rsshub` 展示 route 输入。
- `aihot_api` 可使用内置默认 URL，不要求用户输入 URL。
- requiresCookie 打开时提示“M2 只保存配置，不执行抓取”。

### 3.3 Preview 区域

展示：

- sample item 标题。
- URL。
- publishedAt。
- contentSnippet。
- warnings。

行为：

- preview 不入库。
- preview 失败展示 `error.message` 和 trace id。

### 3.4 FetchRun 列表

展示字段：

- run id。
- source。
- trigger。
- status。
- startedAt / finishedAt。
- durationMs。
- fetchedCount。
- newCount。
- duplicateCount。
- ignoredCount。
- errorCode / errorMessage。

行为：

- 点击 run 可查看详情。
- failed / partial_failed 用明显状态展示。

### 3.5 RawItem 列表

展示字段：

- title。
- sourceName。
- url。
- publishedAt。
- fetchedAt。
- status。
- summary / contentSnippet。

规则：

- 点击标题新窗口打开原文。
- 不展示 raw payload。
- 缺摘要显示“该条暂无摘要”。

### 3.6 SourceHealth 面板

展示字段：

- status。
- consecutiveFailures。
- lastSucceededAt。
- lastFailedAt。
- nextFetchAt。
- degradedUntil。
- circuitOpenedAt。
- lastErrorCode / lastErrorMessage。

状态颜色：

- enabled：正常。
- disabled：中性。
- degraded：警告。
- circuit_open：错误。

## 4. 组件建议

- `SourceConsolePage`
- `SourceList`
- `SourceFormDrawer`
- `SourcePreviewPanel`
- `FetchRunList`
- `RawItemList`
- `SourceHealthPanel`
- `CollectionApiStateView`
- `StatusBadge`

## 5. API 使用

以 `docs/contracts/collection-api.md` 为唯一契约。

前端调用：

```text
GET /api/sources
POST /api/sources
PATCH /api/sources/{sourceId}
POST /api/sources/{sourceId}/enable
POST /api/sources/{sourceId}/disable
POST /api/sources/preview
POST /api/sources/{sourceId}/fetch
GET /api/fetch-runs
GET /api/raw-items
GET /api/source-health
```

前端不得调用：

```text
https://aihot.virxact.com/*
RSSHub base URL
任意 RSS URL
```

## 6. Mock 开发

前端 mock 必须覆盖：

- Source 列表有结果。
- Source 列表为空。
- 创建 source 成功。
- Source preview 成功。
- Source preview SSRF blocked。
- 手动 fetch 成功。
- 手动 fetch source disabled。
- FetchRun running / succeeded / failed。
- RawItem 有结果和空结果。
- SourceHealth enabled / degraded / circuit_open。

## 7. 验收标准

- 可查看 sources 列表。
- 可创建 RSSHub source。
- 可创建自定义 RSS source。
- 可 preview source，展示 sample items。
- preview 错误显示 `error.message` 和 trace id。
- 可启停 source。
- 可手动触发 fetch 并看到 FetchRun。
- 可查看 RawItem。
- 可查看 SourceHealth。
- 前端不包含 AI HOT、RSSHub、任意 RSS 直连 fetch。
- 移动端不出现主要内容重叠或横向溢出。

## 8. 测试要求

- API client query string / request body 测试。
- mock envelope shape 测试。
- 错误态测试。
- Source 表单 type 切换测试。
- SourceHealth 状态展示测试。

## 9. 设计约束

- 工作台风格，信息密度优先。
- 不做营销式落地页。
- 表格在移动端可降级为卡片。
- 状态必须比装饰更突出。
- 不使用颜色作为唯一状态表达。
- 长 URL 和长标题必须换行，不造成横向溢出。

## 10. 联调边界

- 后端未实现前，前端只使用 mock。
- 后端实现后，先联调 source list / preview，再联调 fetch run / raw items / health。
- 如果 contract 发现缺口，先更新 `docs/contracts/collection-api.md`，再更新前端和后端。

## 11. 已知风险

- M2 没有登录权限，真实生产前不能开放写 API 给公网。
- RSS preview 可能受上游速度影响，前端必须有 loading 和 timeout 友好提示。
- `itemCount`、`newCount` 等统计字段可能为 0，不能和未知值混淆。
