# 执行进度标识

> 最后更新：2026-06-09
> 用途：记录已经完成和未完成的 workflow 项，避免后续恢复任务时重复判断。

## 当前结论

- 当前 Trellis 任务：`05-28-multi-agent-hot-intel-prd-hotpush`
- 当前任务状态：`in_progress`
- 当前产物类型：PRD / contract / workflow 文档任务 + M1/M2 后端前端实现 + M3/M4/M5/M6/M7 文档升级
- 当前可直接进入开发的阶段：M1 后端、M1 前端、M2 后端、M2 前端
- M3 当前状态：已从 brief 升级为详细 contract / 后端 PRD / 前端 PRD；业务编码前还需确认文档可作为开发依据
- M4 当前状态：已从 brief 升级为详细 contract / 后端 PRD / 前端 PRD；业务编码前还需确认文档可作为开发依据
- M5 当前状态：已从 brief 升级为详细 contract / 后端 PRD / 前端 PRD；业务编码前还需确认文档可作为开发依据
- M6 当前状态：已从 brief 升级为详细 contract / 后端 PRD / 前端 PRD；业务编码前还需确认文档可作为开发依据
- M7 当前状态：已从 brief 升级为详细 contract / 后端 PRD / 前端 PRD；业务编码前还需确认文档可作为开发依据
- 当前禁止直接编码的阶段：M3/M4/M5/M6/M7 未确认编码前；进入编码前必须先由用户确认对应文档可作为开发依据

## 已完成

- [x] 根目录 `prd.md` 已升级为多 Agent 热点情报系统总 PRD。
- [x] `prd.md` 已保留 AI HOT 实测事实和未验证范围。
- [x] `prd.md` 已加入 HotPush 参考能力和不可照搬边界。
- [x] `prd.md` 已加入采集、去重聚类、价值判断、背景补全、AI 点评、分发 Agent。
- [x] `prd.md` 已加入数据模型、Topic 生命周期、Agent Run 生命周期、API 资源面。
- [x] 已创建 `docs/contracts/query-api.md` 作为 M1 前后端共享契约。
- [x] 已创建 `docs/prd/m1-backend-query-core.md` 作为 M1 后端详细 PRD。
- [x] 已创建 `docs/prd/m1-frontend-query-console.md` 作为 M1 前端详细 PRD。
- [x] 已创建 M2-M7 路线级 brief。
- [x] 已创建根目录 `workflow.md` 并在 `prd.md` 中引用。
- [x] `workflow.md` 已明确每次开发启动流程、阶段顺序、M1/M2 可开发状态、M3-M7 升级门槛。
- [x] `workflow.md` 已加入完成标识规则，要求关键交付完成后更新任务目录进度文件。
- [x] `workflow.md` 已升级为 v0.3，补齐强制启动流程、M2 后端/前端开发流程、M2 联调规则、Agent 开发门禁和后续阶段文档规划。
- [x] M3 已按已确认方案从路线 brief 升级为详细文档：`docs/contracts/clustering-api.md`、`docs/prd/m3-backend-clustering-trends.md`、`docs/prd/m3-frontend-topic-console.md`。
- [x] M3 contract 已明确只消费 M2 `RawItem`，不直接调用 source fetcher；相同 `normalizedUrl` 自动合并，标题相似只生成候选或 `needs_review`。
- [x] M3 后端 PRD 已明确 `HotTopicCluster`、`TopicMember`、`MergeHistory`、`TrendSnapshot`、`ClusteringRun`、PostgreSQL schema、API、测试和联调边界。
- [x] M3 前端 PRD 已明确 Topic Console、成员、历史、趋势快照、manual merge/split、mock、移动端和错误态边界。
- [x] `prd.md` 已同步 M3 contract / 后端 PRD / 前端 PRD 索引，并把 M3 阶段说明从 route brief 扩展为详细文档引用。
- [x] `workflow.md` 已升级为 v0.4，补充 M3 文档复核入口、M3 contract / PRD 索引，以及“编码前需确认文档可作为开发依据”的门槛。
- [x] M3 后端 PRD 已按 `workflow.md` 8.3 补齐显式 `Prompt injection 防护`、prompt-injection fixture、迁移或兼容策略、对应测试与验收要求。
- [x] M3 前端 PRD 已按 `workflow.md` 8.3 补齐数据模型、状态机、Agent 输入输出、错误处理、安全和合规边界、Prompt injection 防护、测试 fixture、迁移或兼容策略。
- [x] M4 已按 workflow 从路线 brief 升级为详细文档：`docs/contracts/value-background-api.md`、`docs/prd/m4-backend-value-background.md`、`docs/prd/m4-frontend-assessment-console.md`。
- [x] M4 contract 已明确只消费 M3 topic/member/trend 和 M2 source trust；输出 `ValueAssessment`、`BackgroundPack`、`EvidenceSource`、`FactConflict`、`ReviewFlag`、`AssessmentRun`。
- [x] M4 contract 已明确评分必须有分项分和 reasons；高影响低置信、来源冲突、缺官方来源等进入 review；背景补全失败必须记录，不补写事实。
- [x] M4 后端 PRD 已按 `workflow.md` 8.3 覆盖目标、背景依赖、In/Out Scope、系统场景、数据模型/API、状态机、Agent 输入输出、错误处理、安全合规、Prompt injection 防护、测试 fixture、验收、联调、迁移兼容和风险。
- [x] M4 前端 PRD 已按 `workflow.md` 8.3 覆盖 Assessment Console、评分详情、背景包、证据、冲突、review flags、数据模型、状态机、Agent 输入输出、错误处理、安全合规、Prompt injection 防护、mock、验收、迁移兼容和风险。
- [x] `prd.md` 已同步 M4 contract / 后端 PRD / 前端 PRD 索引，并把 M4 阶段说明从路线 brief 扩展为详细文档引用。
- [x] `workflow.md` 已升级为 v0.5，补充 M4 文档复核入口、M4 contract / PRD 索引，以及“编码前需确认文档可作为开发依据”的门槛。
- [x] M5 已按 workflow 从路线 brief 升级为详细文档：`docs/contracts/commentary-distribution-api.md`、`docs/prd/m5-backend-commentary-distribution.md`、`docs/prd/m5-frontend-commentary-distribution-console.md`。
- [x] M5 contract 已明确只基于 M3 topic 和 M4 assessment / background / evidence 生成证据受限点评；输出 `TopicCommentary`、`Subscription`、`DeliveryChannel`、`RenderedMessage`、`DeliveryRecord`、`PushTrace`、`DistributionRun`。
- [x] M5 contract 已明确点评必须带 evidence URL；preview / dryRun 不发送；按 `topic_id + subscription_id + channel_id` 幂等去重；密钥只用 `secretRef` / `maskedTarget` 脱敏展示。
- [x] M5 后端 PRD 已按 `workflow.md` 8.3 覆盖 CommentaryInputReader、CommentaryGenerator、EvidenceGuard、SubscriptionMatcher、MessageRenderer、DeliveryDeduper、ChannelAdapter、WebhookAdapter、DistributionRunService、fake adapter 和测试边界。
- [x] M5 前端 PRD 已按 `workflow.md` 8.3 覆盖 Commentary & Delivery Console、Rendered preview、Subscription / Channel 只读展示、DeliveryRecord、PushTrace、DistributionRun、错误态、安全合规、Prompt injection 防护和 mock 边界。
- [x] `prd.md` 已同步 M5 contract / 后端 PRD / 前端 PRD 索引，并把 M5 阶段说明从路线 brief 扩展为详细文档引用。
- [x] `workflow.md` 已升级为 v0.6，补充 M5 文档复核入口、M5 contract / PRD 索引，以及“编码前需确认文档可作为开发依据”的门槛。
- [x] M6 已按 workflow 从路线 brief 升级为详细文档：`docs/contracts/admin-rules-api.md`、`docs/prd/m6-backend-admin-rules.md`、`docs/prd/m6-frontend-admin-rules-console.md`。
- [x] M6 contract 已明确认证、RBAC、`AdminUser`、`ReviewItem`、`ReviewDecision`、`AdminRuleSet`、`RerunRequest`、`AuditLog`、渠道密钥写入和脱敏边界。
- [x] M6 contract 已明确所有写操作必须有 reason 并写 `AuditLog`；非 mock 模式不得有隐式匿名管理员；RuleSet 不允许保存可执行脚本。
- [x] M6 后端 PRD 已按 `workflow.md` 8.3 覆盖 AuthService、RbacService、AdminUserService、ReviewQueueService、ReviewDecisionService、RuleSetService、SecretService、RerunRequestService、AuditLogService、PostgreSQL schema、错误处理、安全合规、Prompt injection 防护、测试 fixture、验收、联调、迁移兼容和风险。
- [x] M6 前端 PRD 已按 `workflow.md` 8.3 覆盖 Admin Console、Review Queue、Topic 工作区、RuleSet 管理、Subscription / Channel 管理、RerunRequest、AuditLog、User / Role、错误态、安全合规、Prompt injection 防护、mock、验收、迁移兼容和风险。
- [x] `prd.md` 已同步 M6 contract / 后端 PRD / 前端 PRD 索引，并把 M6 阶段说明从路线 brief 扩展为详细文档引用。
- [x] `workflow.md` 已升级为 v0.7，补充 M6 文档复核入口、M6 contract / PRD 索引，以及“编码前需确认文档可作为开发依据”的门槛。
- [x] M7 已按 workflow 从路线 brief 升级为详细文档：`docs/contracts/eval-observability-api.md`、`docs/prd/m7-backend-eval-observability.md`、`docs/prd/m7-frontend-observability-console.md`。
- [x] M7 contract 已明确 `EvalSuite`、`EvalCase`、`EvalRun`、`EvalResult`、`RegressionFailure`、`AgentRunTrace`、`TraceSpan`、`ToolCallLog`、`CostRecord`、`MetricsSnapshot`、`AlertRule`、`AlertEvent`、`ReplayRequest`。
- [x] M7 contract 已明确真实 API smoke 不断言具体新闻标题；replay 默认 dryRun，不触发真实外发；trace / tool call / replay output 必须脱敏 secret、token、cookie、Authorization header、webhook URL。
- [x] M7 后端 PRD 已按 `workflow.md` 8.3 覆盖 EvalFixtureLoader、EvalRunner、EvalAdapter、TraceCollector、CostRecorder、MetricsAggregator、AlertService、ReplayService、RetentionService、PostgreSQL schema、错误处理、安全合规、Prompt injection 防护、测试 fixture、验收、联调、迁移兼容和风险。
- [x] M7 前端 PRD 已按 `workflow.md` 8.3 覆盖 Observability Console、EvalSuite / EvalRun / EvalResult、RegressionFailure、AgentRun、TraceViewer、ReplayRequest、Metrics / Cost、Alert、错误态、安全合规、Prompt injection 防护、mock、验收、迁移兼容和风险。
- [x] `prd.md` 已同步 M7 contract / 后端 PRD / 前端 PRD 索引，并把 M7 阶段说明从路线 brief 扩展为详细文档引用。
- [x] `workflow.md` 已升级为 v0.8，补充 M7 文档复核入口、M7 contract / PRD 索引，以及“编码前需确认文档可作为开发依据”的门槛。
- [x] Phase 3.3 spec update 已完成：`.trellis/spec/guides/stage-doc-upgrade-thinking-guide.md` 已沉淀阶段 brief 升级为详细 contract / PRD 后的同步与验证清单，并已接入 `.trellis/spec/guides/index.md`。
- [x] `implement.jsonl` 已替换为真实上下文条目，不再只有种子 `_example`。
- [x] `check.jsonl` 已替换为真实检查上下文条目，不再只有种子 `_example`。
- [x] M1 后端已有 FastAPI 查询内核实现，包含 `/api/query/items`、`/api/query/daily`、`/api/query/dailies`、`/api/query/help`。
- [x] M1 后端已补齐 304 缓存命中返回和 `meta.cached=true`。
- [x] M1 后端已补齐 429 等可重试上游错误的重试路径。
- [x] M1 前端已有 Vue 查询工作台实现，包含精选/全部动态、分类、时间窗、日报、归档、状态展示。
- [x] M1 前端 mock 已补齐 404、503、timeout、bad response 等错误态。
- [x] 前端 Tailwind build 警告已清理。
- [x] M1 live AI HOT smoke 已通过：`items?take=1`、`daily`、`dailies?take=1` 均经本系统后端返回成功 envelope。
- [x] M1 OpenAPI 自查已通过：`/openapi.json` 包含 `/health` 和 `/api/query/*` 端点。
- [x] M1 浏览器联调已通过：默认精选列表、短关键词错误态、AI 日报、日报归档、归档点击进入指定日期日报。
- [x] M1 日报归档字段已修复：AI HOT `leadTitle` 映射为归档标题，星期由日期确定，缺失事件数显示“事件数未知”而不是 `0 条`。
- [x] M1 移动端横向溢出已修复，390px 视口下 items 和 archive 视图 `overflowX=false`。
- [x] M2 brief 已升级为可开发文档：`docs/contracts/collection-api.md`。
- [x] M2 后端详细 PRD 已创建：`docs/prd/m2-backend-collection-core.md`。
- [x] M2 前端详细 PRD 已创建：`docs/prd/m2-frontend-source-console.md`。
- [x] `workflow.md` 已更新 M2 后端 / 前端为可直接开发状态。
- [x] `prd.md` 子 PRD 拆分建议已加入 M2 contract 和子 PRD 索引。
- [x] M2 后端已按 TDD 启动核心契约层实现：`backend/tests/test_collection_core.py`。
- [x] M2 后端已实现 `SourceInput` 基础校验，覆盖类型、分类、抓取间隔、超时、重试、并发、RSS URL 和 RSSHub route。
- [x] M2 后端已实现 `SSRFGuard`，覆盖 HTTP(S) scheme、localhost、DNS 解析结果和内网 / loopback / link-local 等地址阻断。
- [x] M2 后端已实现 RSSHub feed URL 构造，并对最终 URL 执行 SSRF 校验。
- [x] M2 后端已实现 RawItem 基础标准化：title 清理、URL 标准化、tracking query 清理、rank 转换、`dedupeKey` 生成、缺失 title 时忽略。
- [x] M2 后端已补齐 collection 相关错误码：`SOURCE_*`、`FETCH_RUN_NOT_FOUND`、`RAW_ITEM_NOT_FOUND`。
- [x] M2 后端已按 TDD 实现 `/api/sources` 最小 API 闭环：创建、列表、详情、启用、停用、SSRF 错误和 source not found 错误 envelope。
- [x] M2 后端已加入 `InMemorySourceRepository` 作为 SourceRegistry/repository 边界的临时实现；后续仍需替换为 PostgreSQL repository。
- [x] M2 后端已按 TDD 实现 `PATCH /api/sources/{sourceId}`，支持基于现有 source 合并 Partial SourceInput、重新校验并更新 `updatedAt`。
- [x] M2 后端已按 TDD 实现 `POST /api/sources/preview`，preview 不入库，返回统一 envelope。
- [x] M2 后端已实现 `SourcePreviewer` 骨架，支持 RSSHub URL 构造、SSRF 校验、RSS/Atom XML 解析、最多 5 条 sample item、malformed XML 映射为 `SOURCE_BAD_RESPONSE`。
- [x] M2 后端已把 source API CORS method 从仅 GET 调整为全方法，避免前端调用 POST/PATCH 时被预检拦截。
- [x] M2 后端已按 TDD 实现 `POST /api/sources/{sourceId}/fetch` 手动抓取入口，支持 disabled source 错误和 idempotency key 复用。
- [x] M2 后端已实现 `InMemoryCollectionStore`，用于阶段性保存 FetchRun、RawItem、SourceHealth、源内 dedupe key 和 idempotency run 映射；后续仍需替换为 PostgreSQL/Redis。
- [x] M2 后端已实现 `CollectionRunner`，手动抓取后会生成 FetchRun、标准化 RawItem、统计 new/duplicate/ignored，并更新 SourceHealth。
- [x] M2 后端已实现 `GET /api/fetch-runs`、`GET /api/fetch-runs/{runId}`、`GET /api/raw-items`、`GET /api/raw-items/{rawItemId}`、`GET /api/source-health` 查询入口。
- [x] M2 后端已按 TDD 实现 Redis key helper，覆盖 `source:lock:{source_id}`、`source:etag:{source_id}`、`source:last_modified:{source_id}`、`source:dedupe:{source_id}`、`fetch_run:progress:{run_id}`。
- [x] M2 后端已实现 source lock TTL 预算计算，TTL 大于 source timeout + retry 总预算。
- [x] M2 后端已实现采集请求头构造，支持 `User-Agent`、`If-None-Match`、`If-Modified-Since`。
- [x] M2 后端已实现 retry 控制 helper，并让 `SourcePreviewer` 按 source `retryCount` 重试 retryable fetch 错误。
- [x] M2 后端已按 TDD 实现源级锁占用/释放边界：手动 fetch 前 acquire，成功或失败后 release，锁已占用时返回 `SOURCE_RATE_LIMITED` 且不执行抓取。
- [x] M2 后端已加入 `InMemorySourceLockStore` 作为 Redis `source:lock:{source_id}` 的阶段性实现；后续仍需替换为真实 Redis `SET NX EX` / release 逻辑。
- [x] M2 后端已按 TDD 实现 `RedisSourceLockStore`，使用 Redis `SET NX EX` 获取 `source:lock:{source_id}`，锁已存在时返回 `SOURCE_RATE_LIMITED`，release 时删除锁 key。
- [x] M2 后端已加入 Redis 锁配置入口：默认仍使用内存锁；设置 `USE_REDIS_LOCK=true` 时通过 `REDIS_URL` 创建 Redis 锁实现，缺少 redis 依赖时显式报错。
- [x] M2 后端 `pyproject.toml` 已声明 `redis>=5.0.0` 依赖。
- [x] M2 后端已按 TDD 创建 PostgreSQL migration：`backend/migrations/001_m2_collection_schema.sql`。
- [x] M2 PostgreSQL migration 已定义 `sources`、`fetch_runs`、`raw_items`、`source_health` 四张表，包含 PRD 要求字段、外键、partial unique index、raw item 去重约束和查询索引。
- [x] M2 后端已按 TDD 实现 `PostgresSourceRepository`，覆盖 source create / get / list / update / enable-disable 的 PostgreSQL row 到 contract shape 映射。
- [x] M2 后端已加入 PostgreSQL source repository 配置入口：默认仍使用内存 repository；设置 `USE_POSTGRES_SOURCE_REPOSITORY=true` 且提供 `DATABASE_URL` 或 `POSTGRES_DSN` 时启用 PostgreSQL source repository，缺少 psycopg 依赖时显式报错。
- [x] M2 后端 `pyproject.toml` 已声明 `psycopg[binary]>=3.2.0` 依赖。
- [x] README 已同步 M1/M2 文档入口、M2 阶段边界、PostgreSQL source repository 和 Redis source lock 的本地启用方式。
- [x] M2 后端已按 TDD 实现 `PostgresCollectionStore`，覆盖 FetchRun idempotency / start / finish / list / detail、RawItem 源内去重 / list / detail、SourceHealth success / failure / degraded 阈值映射。
- [x] M2 后端已加入 PostgreSQL collection store 配置入口：默认仍使用内存 store；设置 `USE_POSTGRES_COLLECTION_STORE=true` 且提供 `DATABASE_URL` 或 `POSTGRES_DSN` 时启用 PostgreSQL collection store，缺少 psycopg 依赖时显式报错。
- [x] README 已同步 PostgreSQL collection store 的本地启用方式。
- [x] M2 后端已按 TDD 实现 Redis ETag / Last-Modified 元数据存储：`InMemorySourceMetadataStore`、`RedisSourceMetadataStore`、`USE_REDIS_SOURCE_METADATA` 配置入口。
- [x] M2 后端默认采集 fetcher 已接入 Redis/内存 metadata store，抓取前使用 `If-None-Match` / `If-Modified-Since`，抓取后同步写回 metadata store 和 source repository 的 `etag`、`lastModified`、`lastFetchedAt` 字段。
- [x] M2 后端 `SourcePreviewer` 已支持带条件请求头抓取，并正确处理 `304 Not Modified`，避免解析空响应体。
- [x] README 已同步 Redis ETag / Last-Modified 元数据的本地启用方式。
- [x] M2 后端已按 TDD 实现 `SchedulerService` core：扫描 enabled source、按 `nextFetchAt` / `lastFetchedAt` / `fetchIntervalMinutes` 判断是否到期、用 `schedule` trigger 调用 `CollectionRunner`、通过 schedule idempotency key 避免同一窗口重复抓取。
- [x] M2 后端 `CollectionRunner.fetch_source` 已支持 `trigger` 参数，手动 API 默认仍为 `manual`，scheduler 调用为 `schedule`。
- [x] M2 后端 `InMemoryCollectionStore` / `PostgresCollectionStore` 已在 success / failure health 记录中维护 `nextFetchAt`，其中 `circuit_open` 默认 30 分钟后再调度。
- [x] README 已同步 scheduler core 当前边界：`app.state.scheduler_service.run_due_once()` 可用，但不会自动启动后台循环。
- [x] M2 后端已按 TDD 实现 APScheduler worker 生命周期管理：`SchedulerWorker` 用 interval job 调用 `SchedulerService.run_due_once()`，并通过 `max_instances=1` 避免同 worker 内扫描重叠。
- [x] M2 后端已加入 scheduler worker 配置入口：默认关闭；设置 `USE_SCHEDULER_WORKER=true` 后由 FastAPI lifespan 启动，并在应用关闭时释放。
- [x] M2 后端 `pyproject.toml` 已声明 `apscheduler>=3.11.0,<4.0.0` 依赖。
- [x] README 已同步 APScheduler worker 的本地启用方式和默认关闭边界。
- [x] M2 后端已按 TDD 实现 Redis 源内 dedupe set 持久同步：`RedisSourceDedupeStore` 使用 `source:dedupe:{source_id}` + `SADD` 做快速去重，`SREM` 支持保存失败时释放预占 key。
- [x] M2 后端 `CollectionRunner` 已接入可选 `source_dedupe_store`，默认不开启 Redis dedupe；显式启用后先走 Redis fast path，Redis 未命中后再进入 collection store，PostgreSQL unique constraint / 内存 store 负责 Redis 未覆盖路径的兜底去重。
- [x] M2 后端已加入 Redis dedupe 配置入口：设置 `USE_REDIS_SOURCE_DEDUPE=true` 且提供 `REDIS_URL` 时启用；默认仍不产生 Redis dedupe 副作用。
- [x] README 已同步 Redis 源内 dedupe set 的本地启用方式。
- [x] M2 后端已按 TDD 实现 `FetcherPool`：按 source type 分发，`aihot_api` 复用 M1 `AihotClient`，`aihot_rss` / `rss` / `rsshub` 复用 RSS/Atom feed fetcher。
- [x] M2 后端已实现 `AihotApiFetcher`，将 AI HOT items API 输出映射为 RawItem 输入，并把 M1 `UPSTREAM_*` 错误映射为 M2 `SOURCE_*` 错误。
- [x] M2 后端 `CollectionRunner` 默认采集链路已接入 `FetcherPool.fetch`；测试仍可通过 `source_item_fetcher` 注入覆盖，保留原有单元测试边界。
- [x] README 已同步 FetcherPool 当前分发边界。
- [x] M2 后端已按 TDD 完成 SourceHealth 策略收口：连续失败 3 次进入 `degraded`，使用 `fetchIntervalMinutes * 3` 的低频 `nextFetchAt` 并写入 `degradedUntil`；连续失败 5 次进入 `circuit_open`，默认 30 分钟 cooldown。
- [x] M2 后端 `CollectionRunner` 已把 SourceHealth status 同步回 SourceConfig `status`，失败进入 `degraded` / `circuit_open`，成功恢复为 `enabled`。
- [x] M2 后端 `SchedulerService` 已改为按 source `enabled` 布尔值扫描，再由 health `nextFetchAt` 控制调度窗口，避免 degraded source 因 SourceConfig `status=degraded` 被排除。
- [x] M2 contract / 后端 PRD 已同步 SourceHealth 具体策略：degraded 低频倍率、`degradedUntil`、circuit cooldown、成功恢复和 SourceConfig status 同步。
- [x] README 已同步 SourceHealth 阈值、低频抓取、circuit cooldown 和 source status 同步边界。
- [x] M2 后端已补齐 mock feed fixture 文件：`aihot-items.json`、`aihot-feed.xml`、`rsshub-hackernews.xml`、`custom-rss.xml`、`malformed-rss.xml`、`duplicate-rss.xml`。
- [x] M2 后端已补 RSS / RSSHub API 集成测试：通过真实 `FetcherPool` + 注入式 `SourcePreviewer` mock 上游，覆盖 raw item 写入、ETag / Last-Modified 回写、RSSHub route URL 构造和 malformed RSS failed run / health。
- [x] M2 后端已补 OpenAPI 自查测试，确认 `/api/sources`、`/api/fetch-runs`、`/api/raw-items`、`/api/source-health` 等 M2 collection 端点在 `/openapi.json` 中存在。
- [x] M2 前端已按 TDD 完成 collection API 数据层第一块：补齐 Source / FetchRun / RawItem / SourceHealth 类型、collection API client、JSON request helper 和 mock collection envelope。
- [x] M2 前端 mock 已覆盖 source list、preview success / SSRF blocked、manual fetch success / disabled error、fetch runs running/succeeded/failed、raw items、source health enabled/degraded/circuit_open。
- [x] M2 前端已按 TDD 完成 SourceConsole 第一块 UI：新增“数据源”入口、SourceConsole 页面、source 列表和 type / status / enabled / category 筛选。
- [x] M2 前端 SourceConsole 已复用 collection API client / mock source 数据层，不直接 fetch AI HOT、RSSHub 或任意 RSS 外部 URL。
- [x] M2 前端 SourceConsole 已补齐筛选控件可访问名称，便于浏览器自动化和后续回归验证。
- [x] M2 前端已按 TDD 完成 SourceConsole 只读监控区：展示最近 FetchRun、RawItem 和 SourceHealth，sourceId 通过 source 列表映射为可读 source 名称。
- [x] M2 前端 SourceConsole 只读监控区已复用 `fetchRuns`、`fetchRawItems`、`fetchSourceHealth` API client 和 mock envelope，不引入外部源直连 fetch。
- [x] M2 前端已按 TDD 完成 SourceConsole 写操作：创建 / 编辑 source 表单、source preview、启停 source 和手动 fetch。
- [x] M2 前端 SourceConsole 写操作成功后会把返回的 SourceConfig / FetchRun 合并到本地列表，避免无状态刷新冲掉 mock 或真实后端的即时反馈。
- [x] M2 前端 mock source 写接口已改为可重置的内存状态：create 后的 source 可继续被 list / update / enable / disable / fetch 识别，未知 source id 返回 `SOURCE_NOT_FOUND`。
- [x] `.trellis/spec/frontend/quality-guidelines.md` 已沉淀前端 mock 写接口约束：写 mock 必须保留实体 identity，未知 id 不允许兜底返回第一条记录，并在测试后 reset 状态。
- [x] M2 前端已完成真实后端 SourceConsole smoke：非 mock 前端连接本地 FastAPI，读取真实 `/api/sources` 列表，并通过 UI 调用真实后端启停 source。
- [x] M1/M2 当前本地质量复核已通过：后端全量 pytest、后端 compileall、前端 Vitest、前端 `vue-tsc --noEmit` + Vite build、源码调试/TS suppression 扫描和 Trellis JSON/JSONL 解析均已验证。
- [x] M2 前端已完成真实后端 SourceConsole preview / manual fetch smoke：非 mock 前端连接本地 FastAPI，UI 创建 RSS source、Preview 返回样例、手动抓取生成 succeeded FetchRun，刷新后可看到 RawItem 和 SourceHealth。
- [x] M2 前端真实后端 SourceConsole preview / manual fetch 已完成桌面和移动端布局验收，未出现横向溢出。
- [x] Phase 3.3 spec update 已完成：`.trellis/spec/backend/quality-guidelines.md` 已沉淀真实 RSS/RSSHub smoke 前必须先通过 SSRFGuard 校验的规范。
- [x] M2 后端已完成 Redis 外部依赖 smoke：临时 Redis 验证 `RedisSourceLockStore`、`RedisSourceMetadataStore`、`RedisSourceDedupeStore` 的真实连接读写边界。
- [x] 后端 editable install blocker 已修复：`backend/pyproject.toml` 显式限定 setuptools 只发现 `app*` 包并排除 `migrations*`，`pip install -e 'backend[dev]'` 已通过。
- [x] Phase 3.3 spec update 已补充后端 packaging 约束：`.trellis/spec/backend/quality-guidelines.md` 已记录 flat layout 下必须排除 `migrations*`。

## 本轮验证记录

- [x] 2026-06-09 Phase 3.1 最终文档质量复核通过：M3-M7 contract / PRD 索引在 `prd.md`、`workflow.md`、`progress.md`、`task.json` 中均可检索；旧 brief-only 状态残留检查通过；本轮触达文档尾随空白检查通过；`task.json` / `implement.jsonl` / `check.jsonl` 解析通过；32 个 `task.json.relatedFiles` 路径均存在。
- [x] 2026-06-09 Trellis 当前任务复核通过：`/usr/bin/python3 ./.trellis/scripts/task.py current --source` 返回 `.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush`；`/usr/bin/python3 ./.trellis/scripts/get_context.py --mode phase --step 3.5 --platform codex` 返回 wrap-up reminder。
- [x] 2026-06-09 Phase 3.4 commit precheck 仍阻塞：`git status --porcelain` 和 `git rev-parse --show-toplevel` 均返回 `fatal: not a git repository (or any of the parent directories): .git`；当前目录无法执行 workflow 要求的提交计划，必须先确认真实 Git repository path 或外部提交方式。
- [x] 2026-06-09 Git 绑定复核通过：已在当前目录执行 `git init`，并把 `origin` 绑定到 `https://github.com/AceCandy/hot-godlike.git`；本地分支已设为 `main`；`git status --porcelain=v1 --untracked-files=all` 可正常列出待初始提交文件。Phase 3.4 已从“非 Git 仓库阻塞”推进到“等待用户确认初始提交计划”。
- [x] 2026-06-09 Phase 3.4 初始提交计划已给出：计划提交 `chore: initial project import`，覆盖当前所有非 ignored 项；按 workflow 需要用户回复 `行` / `ok` 后才能执行 `git add` / `git commit`。本轮未提交、未推送。
- [x] 2026-06-09 Phase 3.3 spec update 复核通过：新增 `.trellis/spec/guides/stage-doc-upgrade-thinking-guide.md`，覆盖 stage contract / PRD 升级后的 `prd.md`、`workflow.md`、`progress.md`、`task.json` 同步项、必跑验证项和 `/usr/bin/python3` Trellis 脚本 fallback 记录规则；`.trellis/spec/guides/index.md` 已加入入口。
- [x] 2026-06-09 Trellis 脚本 Python 入口复核：`python3` 当前指向 `/opt/homebrew/bin/python3`，执行 `.trellis/scripts/get_context.py` 时被系统策略拦截 Homebrew Python 3.14 动态库；`/usr/bin/python3` 可正常执行 `get_context.py --mode phase --step 3.1/3.3/3.4 --platform codex`。后续恢复若遇到同类错误，先用 `/usr/bin/python3` 跑 Trellis 脚本，不要擅自改 shell 环境。
- [x] 2026-06-09 M7 workflow 8.3 文档完整性复核通过：contract 覆盖目标、全局约定、枚举、数据结构、API 端点、错误码、存储契约、安全合规、Prompt injection 防护、测试 fixture 和兼容边界；后端 PRD 覆盖目标、背景依赖、In/Out Scope、系统场景、模块/API/数据模型、状态机、Agent 输入输出、错误处理、安全合规、Prompt injection 防护、测试 fixture、验收、联调、迁移兼容和风险；前端 PRD 覆盖对应 UI 侧必备项。
- [x] 2026-06-09 M7 新增文档索引检查通过：`prd.md`、`workflow.md`、`progress.md`、`task.json` 均能检索到 `docs/contracts/eval-observability-api.md`、`docs/prd/m7-backend-eval-observability.md`、`docs/prd/m7-frontend-observability-console.md`。
- [x] 2026-06-09 M7 当前状态残留检查通过：`workflow.md` / `progress.md` 中不再存在把 M7 仍描述为“仅有 brief、需整体升级”的旧恢复提示。
- [x] 2026-06-09 M7 核心边界扫查通过：`EvalSuite`、`EvalRun`、`EvalResult`、`RegressionFailure`、`AgentRunTrace`、`TraceSpan`、`ToolCallLog`、`CostRecord`、`MetricsSnapshot`、`AlertRule`、`ReplayRequest`、`REGRESSION_FAILED`、`REPLAY_UNSAFE_SIDE_EFFECT`、`GROUNDING_EVIDENCE_MISSING`、`真实 API smoke 不断言具体新闻标题`、`replay 默认 dryRun`、`Prompt injection` 等约束可检索。
- [x] 2026-06-09 `task.json` / `implement.jsonl` / `check.jsonl` / `task.json.relatedFiles` 解析与路径检查通过：30 个 relatedFiles 路径均存在。
- [x] 2026-06-09 M7 本轮触达文档尾随空白检查通过：`eval-observability-api.md`、M7 后端/前端 PRD、`prd.md`、`workflow.md`、`progress.md`、`task.json` 无尾随空白命中。
- [x] 2026-06-09 M7 Git 状态复核：`git rev-parse --show-toplevel` 仍返回 `fatal: not a git repository (or any of the parent directories): .git`；Phase 3.4 commit 继续保留 blocker。
- [x] 2026-06-09 M6 workflow 8.3 文档完整性复核通过：contract 覆盖目标、全局约定、RBAC、数据结构、状态机、API 端点、错误码、安全合规、Prompt injection 防护、测试 fixture 和兼容边界；后端 PRD 覆盖目标、背景依赖、In/Out Scope、系统场景、模块/API/数据模型、状态机、Agent 输入输出、错误处理、安全合规、Prompt injection 防护、测试 fixture、验收、联调、迁移兼容和风险；前端 PRD 覆盖对应 UI 侧必备项。
- [x] 2026-06-09 M6 新增文档索引检查通过：`prd.md`、`workflow.md`、`progress.md`、`task.json` 均能检索到 `docs/contracts/admin-rules-api.md`、`docs/prd/m6-backend-admin-rules.md`、`docs/prd/m6-frontend-admin-rules-console.md`。
- [x] 2026-06-09 M6 当前状态残留检查通过：`workflow.md` / `progress.md` 中不再存在把 M6 仍描述为“仅有 brief、需整体升级”的旧恢复提示。
- [x] 2026-06-09 M6 核心边界扫查通过：`AdminUser`、`ReviewDecision`、`AdminRuleSet`、`AuditLog`、`RerunRequest`、`RBAC`、`AUTH_REQUIRED`、`FORBIDDEN`、`AUDIT_REASON_REQUIRED`、`SECRET_VALUE_REJECTED`、`不允许保存可执行脚本`、`Prompt injection` 等约束可检索。
- [x] 2026-06-09 `task.json` / `implement.jsonl` / `check.jsonl` / `task.json.relatedFiles` 解析与路径检查通过：27 个 relatedFiles 路径均存在。
- [x] 2026-06-09 M6 本轮触达文档尾随空白检查通过：`admin-rules-api.md`、M6 后端/前端 PRD、`prd.md`、`workflow.md`、`progress.md`、`task.json` 无尾随空白命中。
- [x] 2026-06-09 M6 Git 状态复核：`git rev-parse --show-toplevel` 仍返回 `fatal: not a git repository (or any of the parent directories): .git`；Phase 3.4 commit 继续保留 blocker。
- [x] 2026-06-09 M5 workflow 8.3 文档完整性复核通过：contract 覆盖目标、全局约定、枚举、数据结构、点评生成、订阅匹配、Webhook payload、错误码、API 端点和存储契约；后端 PRD 覆盖目标、背景依赖、In/Out Scope、系统场景、模块/API/数据模型、状态机、Agent 输入输出、错误处理、安全合规、Prompt injection 防护、测试 fixture、验收、联调、迁移兼容和风险；前端 PRD 覆盖对应 UI 侧必备项。
- [x] 2026-06-09 M5 新增文档索引检查通过：`prd.md`、`workflow.md`、`progress.md`、`task.json` 均能检索到 `docs/contracts/commentary-distribution-api.md`、`docs/prd/m5-backend-commentary-distribution.md`、`docs/prd/m5-frontend-commentary-distribution-console.md`。
- [x] 2026-06-09 M5 当前状态残留检查通过：`workflow.md` / `progress.md` 中不再存在把 M5 仍描述为“仅有 brief、需整体升级”的旧恢复提示。
- [x] 2026-06-09 M5 核心边界扫查通过：`TopicCommentary`、`RenderedMessage`、`DeliveryRecord`、`PushTrace`、`DistributionRun`、`COMMENTARY_EVIDENCE_MISSING`、`DELIVERY_DUPLICATE`、`不新增无证据事实`、`dryRun`、`preview 不发送`、`Webhook 签名`、`Prompt injection` 等约束可检索。
- [x] 2026-06-09 `task.json` / `implement.jsonl` / `check.jsonl` / `task.json.relatedFiles` 解析与路径检查通过：24 个 relatedFiles 路径均存在。
- [x] 2026-06-09 M5 本轮触达文档尾随空白检查通过：`commentary-distribution-api.md`、M5 后端/前端 PRD、`prd.md`、`workflow.md`、`progress.md`、`task.json` 无尾随空白命中。
- [x] 2026-06-09 M5 Git 状态复核：`git rev-parse --show-toplevel` 仍返回 `fatal: not a git repository (or any of the parent directories): .git`；Phase 3.4 commit 继续保留 blocker。
- [x] 2026-06-09 M4 workflow 8.3 文档完整性复核通过：后端 PRD 覆盖目标、背景依赖、In/Out Scope、系统场景、数据模型/API、状态机、Agent 输入输出、错误处理、安全合规、Prompt injection 防护、测试 fixture、验收、联调、迁移兼容和风险；前端 PRD 覆盖对应 UI 侧必备项。
- [x] 2026-06-09 M4 新增文档索引检查通过：`prd.md`、`workflow.md`、`progress.md`、`task.json` 均能检索到 `docs/contracts/value-background-api.md`、`docs/prd/m4-backend-value-background.md`、`docs/prd/m4-frontend-assessment-console.md`。
- [x] 2026-06-09 M4 当前状态残留检查通过：`workflow.md` / `progress.md` 中不再存在把 M4 仍描述为“仅有 brief、需整体升级”的旧恢复提示。
- [x] 2026-06-09 M4 核心边界扫查通过：`ValueAssessment`、`BackgroundPack`、`EvidenceSource`、`FactConflict`、`ReviewFlag`、`AssessmentRun`、`不生成最终 AI 点评`、`不做分发`、`不自动判定新闻真实性`、`Prompt injection`、`BACKGROUND_FETCH_FAILED` 等约束可检索。
- [x] 2026-06-09 `task.json` / `implement.jsonl` / `check.jsonl` / `task.json.relatedFiles` 解析与路径检查通过：21 个 relatedFiles 路径均存在。
- [x] 2026-06-09 M4 本轮触达文档尾随空白检查通过：`value-background-api.md`、M4 后端/前端 PRD、`prd.md`、`workflow.md`、`progress.md`、`task.json` 无尾随空白命中。
- [x] 2026-06-09 M4 Git 状态复核：`git rev-parse --show-toplevel` 仍返回 `fatal: not a git repository`；Phase 3.4 commit 继续保留 blocker。
- [x] 2026-06-09 M3 workflow 8.3 文档完整性复核通过：后端 PRD 覆盖目标、背景依赖、In/Out Scope、系统场景、数据模型/API、状态机、Agent 输入输出、错误处理、安全合规、Prompt injection 防护、测试 fixture、验收、联调、迁移兼容和风险；前端 PRD 覆盖对应 UI 侧必备项。
- [x] 2026-06-09 `task.json` / `implement.jsonl` / `check.jsonl` / `task.json.relatedFiles` 解析与路径检查通过：18 个 relatedFiles 路径均存在。
- [x] 2026-06-09 M3 核心边界扫查通过：`normalizedUrl` 自动合并、标题相似只进候选或 `needs_review`、M3 不直接调用 source fetcher、前端不直连 AI HOT/RSSHub/RSS、Prompt injection 文本只作为普通字段处理。
- [x] 2026-06-09 本轮触达文档尾随空白检查通过：`clustering-api.md`、M3 后端/前端 PRD、`progress.md`、`task.json` 无尾随空白命中。
- [x] 2026-06-09 Git 状态复核：`git rev-parse --show-toplevel` 仍返回 `fatal: not a git repository`；Phase 3.4 commit 继续保留 blocker。
- [x] M3 文档落地文件存在性检查通过：`docs/contracts/clustering-api.md`、`docs/prd/m3-backend-clustering-trends.md`、`docs/prd/m3-frontend-topic-console.md`、`prd.md`、`workflow.md`、`progress.md`、`task.json` 均存在。
- [x] `task.json`：`python3 -m json.tool` 解析通过；`implement.jsonl` / `check.jsonl` 逐行 JSON 解析通过。
- [x] `task.json.relatedFiles` 引用检查通过：18 个 relatedFiles 路径均存在。
- [x] M3 当前状态残留检查通过：`workflow.md` / `progress.md` 中不再存在把 M3 仍描述为“仅有 brief、需整体升级”的旧恢复提示。
- [x] M3 核心边界扫查通过：新增文档和索引均能检索到 `normalizedUrl`、`标题相似只生成候选`、`needs_review`、`不直接调用 source fetcher` 等约束。
- [x] 本轮触达文档尾随空白检查通过：`clustering-api.md`、M3 后端/前端 PRD、`prd.md`、`workflow.md`、`progress.md`、`task.json` 无尾随空白命中。
- [x] Git 状态复核：`git rev-parse --show-toplevel` 仍返回 `fatal: not a git repository`；Phase 3.4 commit 继续保留 blocker。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_collection_core.py`：8 passed。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_sources_api.py`：5 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_sources_api.py backend/tests/test_source_preview.py`：9 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_collection_fetch_api.py`：3 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_fetch_control.py backend/tests/test_source_preview.py`：8 passed。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_source_lock.py`：2 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_fetch_control.py`：8 passed。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_migrations.py`：3 passed。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_postgres_source_repository.py`：2 passed。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_postgres_source_repository.py backend/tests/test_sources_api.py`：9 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_sources_api.py backend/tests/test_collection_fetch_api.py backend/tests/test_source_lock.py backend/tests/test_fetch_control.py backend/tests/test_migrations.py backend/tests/test_postgres_source_repository.py`：25 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_postgres_collection_store.py`：3 passed。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_postgres_collection_store.py backend/tests/test_postgres_source_repository.py backend/tests/test_collection_fetch_api.py backend/tests/test_sources_api.py backend/tests/test_migrations.py`：18 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_source_metadata.py backend/tests/test_source_preview.py backend/tests/test_fetch_control.py`：14 passed。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_source_metadata.py backend/tests/test_source_preview.py backend/tests/test_fetch_control.py backend/tests/test_postgres_source_repository.py`：17 passed。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_scheduler_service.py`：2 passed。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_scheduler_service.py backend/tests/test_collection_fetch_api.py backend/tests/test_postgres_collection_store.py backend/tests/test_source_metadata.py backend/tests/test_source_preview.py backend/tests/test_fetch_control.py`：23 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest`：57 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest`：59 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest`：62 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest`：66 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest`：68 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_scheduler_worker.py`：4 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_scheduler_service.py backend/tests/test_scheduler_worker.py`：6 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] 显式启用 worker 真实 smoke：`create_app(scheduler_worker_enabled=True)` + `TestClient` 进入/退出输出 `True / True / True / True`，确认 startup 启动 APScheduler，退出 lifespan 后释放。
- [x] `backend/.venv/bin/python -m pytest`：72 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_fetch_control.py backend/tests/test_collection_fetch_api.py backend/tests/test_collection_runner_dedupe.py`：15 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest`：76 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_fetcher_pool.py backend/tests/test_aihot_fetcher_integration.py backend/tests/test_source_metadata.py backend/tests/test_collection_fetch_api.py`：10 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest`：80 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `python3 -m compileall -q backend/app`：通过。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_scheduler_service.py backend/tests/test_postgres_collection_store.py backend/tests/test_postgres_source_repository.py backend/tests/test_collection_fetch_api.py backend/tests/test_collection_runner_dedupe.py`：13 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest`：81 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `python3 -m compileall -q backend/app`：通过。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_feed_fetcher_integration.py backend/tests/test_openapi_collection_contract.py`：4 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m pytest`：85 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `python3 -m compileall -q backend/app`：通过。
- [x] `frontend npm run test`：12 passed。
- [x] `frontend npm run build`：通过，无 Tailwind utility warning。
- [x] `frontend npm run test`：7 passed。
- [x] `frontend npm run build`：通过，无 Tailwind utility warning。
- [x] `frontend npm run test`：13 passed，覆盖 SourceConsole source filter helper。
- [x] `frontend npm run build`：通过，`vue-tsc --noEmit` 和 Vite build 均通过。
- [x] `agent-browser` SourceConsole 桌面验收：1280px 视口点击“数据源”后展示 3 条 mock source；筛选 `status=degraded` 后只剩 `Custom RSS`，布局指标 `rows=1`、`scrollWidth=1280`、`width=1280`，无横向溢出。
- [x] `agent-browser` SourceConsole 移动端验收：390px 视口保持 `status=degraded` 筛选后只剩 1 条 source，布局指标 `rows=1`、`scrollWidth=390`、`width=390`，无横向溢出。
- [x] `frontend npm run test`：14 passed，覆盖 collection view helper 的 source 名称映射和 SourceHealth sourceId lookup。
- [x] `frontend npm run build`：通过，`vue-tsc --noEmit` 和 Vite build 均通过。
- [x] `agent-browser` SourceConsole 只读监控区桌面验收：1280px 视口展示最近抓取 / 原始条目 / 源健康三块；指标 `sourceRows=3`、`runRows=3`、`rawRows=1`、`healthRows=3`、`scrollWidth=1280`、`width=1280`，无横向溢出；浏览器 errors 为空。
- [x] `agent-browser` SourceConsole 只读监控区移动端验收：390px 视口展示最近抓取 / 原始条目 / 源健康三块；指标 `sourceRows=3`、`runRows=3`、`rawRows=1`、`healthRows=3`、`scrollWidth=390`、`width=390`，无横向溢出。
- [x] `frontend npm run test`：16 passed，覆盖 SourceConsole 写操作所需的 source upsert、fetch run prepend，以及 mock create 后可继续启停的状态一致性。
- [x] `frontend npm run build`：通过，`vue-tsc --noEmit` 和 Vite build 均通过。
- [x] in-app Browser SourceConsole 写操作验收：`VITE_USE_MOCK=true` 下创建 `Browser Created Source` 后 source 列表为 4 条；停用后新建行自身变为停用；重新启用后手动抓取新增 `run_mock_manual · manual`；指标 `sourceRows=4`、`runRows=4`、`scrollWidth=519`、`width=519`，无横向溢出；浏览器 errors 为空。
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_sources_api.py backend/tests/test_collection_fetch_api.py`：11 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] 真实后端 SourceConsole smoke：本地 FastAPI `http://127.0.0.1:8000` + 非 mock 前端 `http://127.0.0.1:5175`；先通过后端 API 创建 `src_real_backend_seeded_source_f071c982`，前端 SourceConsole 展示 `sourceRows=1`、`totalStat=1`，UI 停用后新建行变为停用，UI 启用后恢复正常；指标 `scrollWidth=519`、`width=519`，浏览器 errors 为空。
- [x] `backend/.venv/bin/python -m pytest`：85 passed，1 个 FastAPI/Starlette 依赖弃用 warning。
- [x] `backend/.venv/bin/python -m compileall -q backend/app`：通过。
- [x] `frontend npm run test`：16 passed。
- [x] `frontend npm run build`：通过，`vue-tsc --noEmit` 和 Vite build 均通过；npm 仅提示有新版可用。
- [x] `rg -n "console\\.log|debugger|@ts-ignore|@ts-expect-error|\\bas any\\b" frontend/src backend/app backend/tests`：无命中。
- [x] `task.json`：`python3 -m json.tool` 解析通过；`implement.jsonl` / `check.jsonl` 逐行 JSON 解析通过。
- [x] `workflow.md`：已检查主标题编号，确认 M1/M2 可开发状态和 M3-M7 文档升级门槛一致。
- [x] 直接后端 Source preview smoke：`POST /api/sources/preview` 使用 `https://github.blog/feed/` 返回 5 条 sample item，`meta.source=hot-godlike`，`error=null`；`hnrss.org` 在当前网络解析到 `198.18.39.228` 并被 SSRFGuard 返回 `SOURCE_SSRF_BLOCKED`，符合安全边界。
- [x] 真实后端 SourceConsole preview / manual fetch smoke：本地 FastAPI `http://127.0.0.1:8000` + 非 mock 前端 `http://127.0.0.1:5175`；UI 创建 `src_github_blog_smoke_rss_edb9fde7`，Preview 展示 5 条 GitHub Blog sample item，手动抓取生成 `run_20260603043100_5dee3957`，`status=succeeded`、`fetchedCount=10`、`newCount=10`、`duplicateCount=0`；刷新后 UI 指标 `sourceRows=1`、`runRows=1`、`rawRows=9`、`healthRows=1`。
- [x] `agent-browser` SourceConsole 真实后端桌面验收：1280px 视口下 `scrollWidth=1265`、`width=1280`，无横向溢出；截图保存为 `.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/browser-sourceconsole-real-fetch-desktop.png`。
- [x] `agent-browser` SourceConsole 真实后端移动端验收：390px 视口下 `scrollWidth=375`、`width=390`、`hasHorizontalOverflow=false`，并展示真实后端 source/run/raw/health 数据；截图保存为 `.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/browser-sourceconsole-real-fetch-mobile.png`。
- [x] Phase 3.3 spec update：`.trellis/spec/backend/quality-guidelines.md` 增加 `External Feed Smoke Inputs Must Pass SSRFGuard`，要求真实 feed smoke 先校验候选 URL，记录 `SOURCE_SSRF_BLOCKED` 为安全边界，不允许绕过 SSRFGuard。
- [x] Phase 3.4 commit precheck：`git status --porcelain` 和 `git rev-parse --show-toplevel` 均返回 `fatal: not a git repository`，项目目录 `find ... -name .git` 无结果；本轮未执行提交，继续保留“当前工作区根目录不是 Git 仓库”的 blocker。
- [x] Redis 外部依赖 smoke：临时 Redis `redis://127.0.0.1:16379/0` 返回 `PONG`；Python smoke 通过真实 `Redis*.from_url` 验证 `source:lock:src_redis_smoke` 的 NX/TTL/rate-limit/release、`source:etag:src_redis_smoke` / `source:last_modified:src_redis_smoke` 的 set/get/delete，以及 `source:dedupe:src_redis_smoke` 的 SADD duplicate / SREM release。
- [x] 后端环境安装修复验证：修复前 `backend/.venv/bin/python -m pip install -e 'backend[dev]'` 失败于 `Multiple top-level packages discovered in a flat-layout: ['app', 'migrations']`；修复后同命令通过，并安装/识别 `redis 8.0.0`、`psycopg 3.3.4`、editable `hot-godlike-backend 0.1.0`。
- [x] 后端回归验证：`PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests` 结果 `85 passed, 1 warning`；`backend/.venv/bin/python -m compileall -q backend/app` 通过。
- [x] PostgreSQL 外部依赖 smoke precheck：本机存在 ServBay `postgres/initdb/pg_ctl/psql`，默认 `5432` 未监听；未执行 migration smoke，因为这会创建并迁移临时 PostgreSQL 数据库结构，需单独确认影响范围后再跑。
- [x] 浏览器截图已保存：
  - `.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/browser-desktop-items.png`
  - `.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/browser-desktop-error.png`
  - `.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/browser-desktop-daily.png`
  - `.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/browser-desktop-archive-fixed.png`
  - `.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/browser-desktop-archive-to-daily.png`
  - `.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/browser-mobile-items-fixed.png`
  - `.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/browser-mobile-archive-fixed.png`

## 下一步未完成

- [ ] 如果继续 M1 后端：可补主动 rate limit、结构化日志、更多异常日志；不是当前 M1 contract 的阻塞项。
- [ ] 如果继续 M1 前端：可补组件级自动化测试和更细移动端样式测试；当前浏览器验收已覆盖主路径。
- [ ] 如果继续 M2 后端开发：当前本地质量复核与真实 Redis 外部依赖 smoke 已通过；可按风险补真实 PostgreSQL 临时库 migration / repository / collection store smoke，或进入后续阶段前的收尾判断。
- [ ] 如果继续 M2 前端开发：当前 SourceConsole 写操作、真实后端 source list / enable-disable smoke、真实后端 preview / manual fetch smoke 和桌面/移动无横向溢出验收均已完成；后续可补组件级自动化测试或更细截图，不是当前阻塞项。
- [ ] 如果继续 M3：先由用户确认 `docs/contracts/clustering-api.md`、`docs/prd/m3-backend-clustering-trends.md`、`docs/prd/m3-frontend-topic-console.md` 可作为开发依据，再进入编码；不要跳过确认门槛。
- [ ] 如果继续 M4：先由用户确认 `docs/contracts/value-background-api.md`、`docs/prd/m4-backend-value-background.md`、`docs/prd/m4-frontend-assessment-console.md` 可作为开发依据，再进入编码；不要跳过确认门槛。
- [ ] 如果继续 M5：先由用户确认 `docs/contracts/commentary-distribution-api.md`、`docs/prd/m5-backend-commentary-distribution.md`、`docs/prd/m5-frontend-commentary-distribution-console.md` 可作为开发依据，再进入编码；不要跳过确认门槛。
- [ ] 如果继续 M6：先由用户确认 `docs/contracts/admin-rules-api.md`、`docs/prd/m6-backend-admin-rules.md`、`docs/prd/m6-frontend-admin-rules-console.md` 可作为开发依据，再进入编码；不要跳过确认门槛。
- [ ] 如果继续 M7：先由用户确认 `docs/contracts/eval-observability-api.md`、`docs/prd/m7-backend-eval-observability.md`、`docs/prd/m7-frontend-observability-console.md` 可作为开发依据，再进入编码；不要跳过确认门槛。
- [ ] 如果进入 workflow Phase 3.4 commit：当前目录已绑定新仓库 `https://github.com/AceCandy/hot-godlike.git`，先按 `git status --porcelain=v1 --untracked-files=all` 生成初始提交计划，等待用户一次性确认后再 `git add` / `git commit`；不要跳过确认直接提交或推送。

## 恢复规则

后续任一客户端恢复本任务时，先读取：

```text
workflow.md
prd.md
.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/progress.md
```

然后按目标阶段读取对应文件：

```text
M1 后端：docs/contracts/query-api.md + docs/prd/m1-backend-query-core.md
M1 前端：docs/contracts/query-api.md + docs/prd/m1-frontend-query-console.md
M2 后端：docs/contracts/collection-api.md + docs/prd/m2-backend-collection-core.md
M2 前端：docs/contracts/collection-api.md + docs/prd/m2-frontend-source-console.md
M3：docs/contracts/clustering-api.md + docs/prd/m3-backend-clustering-trends.md + docs/prd/m3-frontend-topic-console.md，编码前需确认文档可作为开发依据
M4：docs/contracts/value-background-api.md + docs/prd/m4-backend-value-background.md + docs/prd/m4-frontend-assessment-console.md，编码前需确认文档可作为开发依据
M5：docs/contracts/commentary-distribution-api.md + docs/prd/m5-backend-commentary-distribution.md + docs/prd/m5-frontend-commentary-distribution-console.md，编码前需确认文档可作为开发依据
M6：docs/contracts/admin-rules-api.md + docs/prd/m6-backend-admin-rules.md + docs/prd/m6-frontend-admin-rules-console.md，编码前需确认文档可作为开发依据
M7：docs/contracts/eval-observability-api.md + docs/prd/m7-backend-eval-observability.md + docs/prd/m7-frontend-observability-console.md，编码前需确认文档可作为开发依据
```

## 不要重复做

- 不要重新调研 AI HOT 和 HotPush，除非需要刷新 2026-05-28 之后的最新事实。
- 不要重建 M1 contract，除非实现发现契约缺口。
- 不要把 M3 brief 当作可开发详细 PRD；M3 已有详细文档，后续直接复核 `docs/contracts/clustering-api.md`、`docs/prd/m3-backend-clustering-trends.md`、`docs/prd/m3-frontend-topic-console.md`。
- 不要在用户确认 M3 文档可作为开发依据前直接写 M3 业务代码。
- 不要重复创建 M3 contract / 后端 PRD / 前端 PRD；本轮已完成文档升级，后续如发现缺口应在现有文件上修订。
- 不要把 M4 brief 当作可开发详细 PRD；M4 已有详细文档，后续直接复核 `docs/contracts/value-background-api.md`、`docs/prd/m4-backend-value-background.md`、`docs/prd/m4-frontend-assessment-console.md`。
- 不要在用户确认 M4 文档可作为开发依据前直接写 M4 业务代码。
- 不要重复创建 M4 contract / 后端 PRD / 前端 PRD；本轮已完成文档升级，后续如发现缺口应在现有文件上修订。
- 不要把 M5 brief 当作可开发详细 PRD；M5 已有详细文档，后续直接复核 `docs/contracts/commentary-distribution-api.md`、`docs/prd/m5-backend-commentary-distribution.md`、`docs/prd/m5-frontend-commentary-distribution-console.md`。
- 不要在用户确认 M5 文档可作为开发依据前直接写 M5 业务代码。
- 不要重复创建 M5 contract / 后端 PRD / 前端 PRD；本轮已完成文档升级，后续如发现缺口应在现有文件上修订。
- 不要把 M6 brief 当作可开发详细 PRD；M6 已有详细文档，后续直接复核 `docs/contracts/admin-rules-api.md`、`docs/prd/m6-backend-admin-rules.md`、`docs/prd/m6-frontend-admin-rules-console.md`。
- 不要在用户确认 M6 文档可作为开发依据前直接写 M6 业务代码。
- 不要重复创建 M6 contract / 后端 PRD / 前端 PRD；本轮已完成文档升级，后续如发现缺口应在现有文件上修订。
- 不要把 M7 brief 当作可开发详细 PRD；M7 已有详细文档，后续直接复核 `docs/contracts/eval-observability-api.md`、`docs/prd/m7-backend-eval-observability.md`、`docs/prd/m7-frontend-observability-console.md`。
- 不要在用户确认 M7 文档可作为开发依据前直接写 M7 业务代码。
- 不要重复创建 M7 contract / 后端 PRD / 前端 PRD；本轮已完成文档升级，后续如发现缺口应在现有文件上修订。
- 不要跳过 `workflow.md` 直接写代码。
- 不要把旧版 `workflow.md` 中“M1 是唯一当前可直接开发的阶段”的说法作为依据；v0.3 已修正为 M1/M2 均可按对应 contract 和子 PRD 开发。
- 不要重复实现 `PostgresSourceRepository`。
- 不要重复实现 `PostgresCollectionStore`。
- 不要重复实现 Redis ETag/Last-Modified 元数据同步。
- 不要重复实现 Redis 源内 dedupe set 持久同步。
- 不要重复实现 `FetcherPool` / `AihotApiFetcher` 基础分发链路。
- 不要重复实现 `SchedulerService` core。
- 不要重复实现 APScheduler worker 启动 / 生命周期管理。
- 不要重复实现 SourceHealth 策略收口；已覆盖 degraded 低频抓取、circuit cooldown、source status 同步和成功恢复。
- 不要重复补 mock RSS / RSSHub 集成测试或 M2 OpenAPI 自查；已新增 fixture 和对应测试。
- 不要重复实现 M2 前端 collection API client / mock 数据层；下一步直接消费这些方法做 SourceConsole UI。
- 不要重复实现 M2 前端 SourceConsole 页面入口、source 列表和 type / status / enabled / category 筛选。
- 不要重复实现 M2 前端 SourceConsole FetchRun / RawItem / SourceHealth 只读视图；写操作和真实后端 source list / enable-disable smoke 也已完成，下一步从 preview / manual fetch 真实联调、组件级自动化测试或更细多视口截图继续。
- 不要重复实现 M2 前端 SourceConsole 创建 / 编辑、preview、启停和手动 fetch 写操作；下一步真实联调应从 preview / manual fetch、组件级自动化测试或更细多视口截图继续。
- 不要重复做 M2 前端真实后端 source list / enable-disable smoke；下一步真实联调应从 preview / manual fetch、组件级自动化测试或更细多视口截图继续。
- 不要重复做 M2 前端真实后端 SourceConsole preview / manual fetch smoke；已覆盖 UI 创建 RSS source、Preview 样例、手动抓取 succeeded run、刷新后的 RawItem / SourceHealth 展示，以及桌面/移动端无横向溢出。
- 不要重复做 M2 后端 Redis 外部依赖 smoke；已用临时 Redis 覆盖 source lock、metadata 和 dedupe 的真实连接路径。除非 Redis 实现、依赖版本或环境配置变化，否则下一步应聚焦 PostgreSQL 临时库 smoke 或后续阶段文档升级。
- 不要删除 `backend/pyproject.toml` 的 `[tool.setuptools.packages.find]` 配置；否则 README 中的 `pip install -e '.[dev]'` / `pip install -e 'backend[dev]'` 会重新因为 `app` + `migrations` flat-layout 包发现失败。
- 不要重复跑 M1/M2 当前本地质量复核，除非代码、contract、测试或运行依赖发生变化；下一步质量相关工作应聚焦真实 PostgreSQL / Redis 外部依赖 smoke 或新增改动后的回归。
