# 采集数据独立页面

## Goal

把“我配置的数据源抓取到的数据”从数据源配置页中拆出来，新增顶层“采集数据”tab，让用户可以直接查看所有 source 入库后的 RawItem，并按数据源、状态和关键词筛选。

## What I already know

* 用户明确认可需要一个单独 tab 查看配置的数据源抓取到的数据。
* 当前前端已有顶层“数据源”tab，入口在 `frontend/src/App.vue`。
* 当前 `SourceConsolePage` 同时加载 source、fetch run、raw item、source health。
* 当前 RawItem 展示位于 `SourceConsolePage` 下半部分，容易被误认为只是数据源配置页附属信息。
* M2 前端 PRD 原本把 RawItem 列表纳入数据源管理入口。
* 现有 API 已支持 RawItem 查询，不需要新增后端接口。

## Decisions

* 新 tab 命名为“采集数据”，比“原始条目”更贴近用户理解。
* “采集数据”默认展示全部数据源最新 RawItem，用户确认该默认行为。
* 页面提供 source/status/q 筛选；时间范围如果后端契约暂不支持，本任务不强行扩接口。
* “数据源”tab 继续负责 source 配置、启停、预览、手动抓取和源健康。
* 采集数据页可以复用现有 `fetchRawItems`、`fetchSources` 和状态/时间展示逻辑。
* 2026-06-09 scope extension：没有配置 PostgreSQL 时，允许显式开启本地 SQLite 持久化；不能做成静默 fallback。

## Open Questions

* 暂无阻塞问题。

## Requirements (evolving)

* 新增顶层 tab：“采集数据”。
* 采集数据页默认展示全部数据源最新 RawItem 列表。
* RawItem 列表字段至少包括：标题、数据源名称、抓取时间、状态、摘要或片段、原文链接。
* 支持按数据源筛选。
* 支持按 RawItem status 筛选。
* 支持关键词搜索，对接 `q` 查询参数。
* 支持加载态、空状态、错误态和 trace id。
* 从“数据源”页移除或弱化 RawItem 列表，避免配置页承担数据浏览职责。
* 手动抓取完成后，用户能通过切换到“采集数据”tab 或刷新当前页面看到新入库内容。
* 支持 `STORAGE_MODE=local` 把 source、fetch run、RawItem 和 source health 写入本地 SQLite。
* 默认内存模式仍只用于开发和测试，重启后不保证数据存在。

## Acceptance Criteria (evolving)

* [x] 顶部 tab 中出现“采集数据”，并能切换到独立页面。
* [x] “采集数据”页面调用 `GET /api/raw-items` 显示 RawItem。
* [x] 页面可按 `sourceId`、`status`、`q` 过滤 RawItem。
* [x] 页面空结果时显示清晰空状态，不误报为错误。
* [x] API 失败时展示错误信息和 trace id。
* [x] “数据源”页面仍可创建、编辑、启停、预览和手动抓取 source。
* [x] 前端 mock 与测试覆盖新 tab 的主要数据加载和筛选行为。
* [x] `STORAGE_MODE=local` 持久化 source、fetch run、RawItem 和 source health。
* [x] 本地持久化模式通过测试覆盖重开后可读和 RawItem dedupe。

## Definition of Done (team quality bar)

* Tests added/updated (unit/integration where appropriate)
* Lint / typecheck / CI green
* Docs/notes updated if behavior changes
* Rollout/rollback considered if risky

## Out of Scope (explicit)

* 后端新增 RawItem 查询字段。
* Raw payload 全量展示。
* 聚类、评分、背景补全、AI 点评和分发。
* 复杂图表、趋势分析、批量操作。
* 登录、权限和多用户隔离。

## Technical Notes

* `frontend/src/App.vue` 当前 viewMode 包含 `items`、`daily`、`archive`、`sources`，可扩展 `collection` 或 `data` 模式。
* `frontend/src/components/SourceConsolePage.vue` 已有 RawItem 展示片段，可抽取或迁移到新组件。
* `frontend/src/lib/api.ts` 已有 `fetchRawItems(query)`，真实请求路径为 `/raw-items`。
* `docs/contracts/collection-api.md` 已定义 `GET /api/raw-items?sourceId=...&status=...&q=...&take=...`。
* `docs/prd/m2-frontend-source-console.md` 已定义 RawItem 展示字段和不展示 raw payload 的约束。
