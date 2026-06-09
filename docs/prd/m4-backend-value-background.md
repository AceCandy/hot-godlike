# M4 后端价值判断与背景补全子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/value-background-api.md`
> 上游依赖：M3 `HotTopicCluster`、`TopicMember`、`TrendSnapshot`
> 推荐实现客户端：后端 / worker AI coding 客户端
> 技术栈决策：Python + FastAPI + PostgreSQL；Redis 只作为可选锁，不作为长期存储。

## 1. 目标

实现 M4 阶段的后端价值判断与背景补全能力：读取 M3 topic / member / trend snapshot，生成可解释 `ValueAssessment`、`BackgroundPack`、`EvidenceSource`、`FactConflict`、`ReviewFlag` 和 `AssessmentRun`。

M4 的目标是让系统知道哪些 topic 值得后续展示/点评，哪些需要 review，哪些应压制。M4 不生成最终 AI 点评，不做分发，不自动判定新闻真实性。

## 2. 背景与依赖

M3 已定义：

- `HotTopicCluster`。
- `TopicMember`。
- `MergeHistory`。
- `TrendSnapshot`。
- Topic status 和 `needs_review`。

M4 在此基础上扩展：

- 对 topic 输出分项评分和总分。
- 根据来源信任、传播、时间、噪音风险输出推荐建议。
- 对高价值、高传播、高风险 topic 生成背景包。
- 记录官方来源缺失、来源冲突和背景抓取失败。
- 生成 review flag 给 M6 审核后台。

## 3. 范围

### 3.1 In Scope

- `POST /api/assessment-runs`
- `GET /api/assessment-runs`
- `GET /api/assessment-runs/{runId}`
- `GET /api/value-assessments`
- `GET /api/topics/{topicId}/assessment`
- `GET /api/background-packs`
- `GET /api/background-packs/{backgroundPackId}`
- `GET /api/evidence-sources`
- `GET /api/review-flags`
- `GET /api/fact-conflicts`
- PostgreSQL schema 和 migration。
- Topic read repository。
- AssessmentPolicy。
- ValueScorer。
- BackgroundResearcher。
- EvidenceFetcher。
- FactConflictDetector。
- ReviewFlagService。
- AssessmentRunService。
- 单元测试、集成测试、OpenAPI 自查。

### 3.2 Out of Scope

- 最终 AI 点评生成。
- 外部分发。
- 完整人工审核前端。
- 订阅规则管理。
- 自动判定新闻真实性。
- 新增 M2 source。
- 大规模网页爬虫。
- 绕过登录、付费墙或站点限制。
- 完整 LLM prompt/eval 平台。

## 4. 用户故事 / 系统场景

### 4.1 高价值官方发布

系统看到一个 topic 有官方来源、多源报道、传播明显。M4 输出高 importance / credibility / propagation，recommendation 为 `promote`，并生成包含官方来源和关联来源的背景包。

### 4.2 高影响低置信

系统看到一个 topic 影响很大，但只有低可信二手来源。M4 输出 `review`，生成 `high_impact_low_confidence` review flag，并标注官方来源缺失。

### 4.3 标题党或营销内容

系统看到 topic 文案明显营销、重复转述或低可信来源。M4 输出高 `noiseRisk`，recommendation 为 `suppress` 或 `review`，但不删除 topic。

### 4.4 来源冲突

两个来源对同一关键事实表达冲突。M4 生成 `FactConflict`，recommendation 改为 `review`，不由 AI 裁决谁真谁假。

### 4.5 背景抓取失败

Evidence URL 超时或被 SSRF / 合规策略阻断。M4 保留 failed evidence 和 failure reason，background pack 为 `partial` 或 `failed`，不补写事实。

## 5. 模块设计

### 5.1 TopicAssessmentReader

职责：

- 从 M3 读取 topic、members、trend snapshots。
- 读取 M2 source trust level。
- 为 ValueScorer 提供结构化输入。

规则：

- 不调用 M2 fetcher。
- 不直接抓取外部 RSS/RSSHub。
- topic 不存在返回 `TOPIC_NOT_FOUND`。

### 5.2 AssessmentPolicyService

职责：

- 提供默认评分权重。
- 校验权重和阈值。
- 供后续 M6 扩展可配置规则。

规则：

- M4 v0.1 使用内置默认 policy。
- policy 非法返回 `ASSESSMENT_POLICY_INVALID`。

### 5.3 ValueScorer

职责：

- 计算 importance / freshness / credibility / propagation / userRelevance / noiseRisk。
- 计算 valueScore。
- 生成 recommendation、confidence、reasons、downrankReasons。

规则：

- 必须输出分项分，禁止只输出总分。
- `noiseRisk` 高时必须降权。
- 高影响低置信必须进入 review。
- suppress 只表示不主动推送，不删除 topic。

### 5.4 BackgroundResearcher

职责：

- 判断是否需要背景补全。
- 选择 evidence URL。
- 调用 EvidenceFetcher。
- 生成 BackgroundPack。

规则：

- 默认最多 8 个 evidence URL。
- 官方来源优先。
- 未找到官方来源时明确标注。
- 抓取失败不补写事实。

### 5.5 EvidenceFetcher

职责：

- 对 evidence URL 做 SSRFGuard 校验。
- 执行 timeout、User-Agent、错误映射。
- 提取 title / url / summary / capturedAt / fetchStatus。

规则：

- 不绕过登录、付费墙、robots.txt、ToS 或平台限制。
- 外部内容只作为不可信文本。
- 被阻断返回 `BACKGROUND_FETCH_BLOCKED`。

### 5.6 FactConflictDetector

职责：

- 对同一 topic 的 evidence 标注显式冲突。
- 写入 FactConflict。

规则：

- 只标注冲突，不裁决真伪。
- unresolved conflict 必须生成 review flag。

### 5.7 ReviewFlagService

职责：

- 生成 review flags。
- 查询 open/resolved/dismissed flags。
- 为后续 M6 审核流提供输入。

规则：

- M4 可创建 flag，不做完整审核处理。
- resolved/dismissed 操作留给 M6。

### 5.8 AssessmentRunService

职责：

- 管理 run 状态。
- 支持 idempotency key。
- 记录 topicCount / assessedCount / backgroundPackCount / reviewFlagCount。
- 记录 failed / partial_failed。

状态机：

```text
queued -> running -> succeeded
queued -> running -> partial_failed
queued -> running -> failed
queued -> cancelled
```

## 6. 数据库 Schema

### 6.1 `value_assessments`

字段：

- `id` text primary key
- `topic_id` text not null references hot_topic_clusters(id)
- `status` text not null
- `recommendation` text not null
- `value_score` integer not null
- `confidence` text not null
- `importance` integer not null
- `freshness` integer not null
- `credibility` integer not null
- `propagation` integer not null
- `user_relevance` integer not null
- `noise_risk` integer not null
- `reasons` jsonb not null
- `downrank_reasons` jsonb not null
- `review_flag_ids` jsonb not null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null
- `trace_id` text not null

索引：

- `value_assessments(topic_id, updated_at desc)`
- `value_assessments(recommendation, updated_at desc)`

### 6.2 `assessment_policies`

字段：

- `id` text primary key
- `name` text not null
- `weights` jsonb not null
- `thresholds` jsonb not null
- `max_evidence_urls` integer not null
- `max_historical_events` integer not null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

### 6.3 `background_packs`

字段：

- `id` text primary key
- `topic_id` text not null references hot_topic_clusters(id)
- `status` text not null
- `official_source_status` text not null
- `original_sources` jsonb not null
- `related_sources` jsonb not null
- `historical_context` jsonb not null
- `official_statements` jsonb not null
- `unresolved_questions` jsonb not null
- `conflict_ids` jsonb not null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null
- `trace_id` text not null

### 6.4 `evidence_sources`

字段：

- `id` text primary key
- `topic_id` text not null references hot_topic_clusters(id)
- `type` text not null
- `trust` text not null
- `title` text not null
- `url` text not null
- `source_id` text null references sources(id)
- `captured_at` timestamptz not null
- `summary` text null
- `fetch_status` text not null
- `failure_reason` text null
- `created_at` timestamptz not null

### 6.5 `fact_conflicts`

字段：

- `id` text primary key
- `topic_id` text not null references hot_topic_clusters(id)
- `claim` text not null
- `evidence_ids` jsonb not null
- `severity` text not null
- `resolution` text not null
- `created_at` timestamptz not null

### 6.6 `review_flags`

字段：

- `id` text primary key
- `topic_id` text not null references hot_topic_clusters(id)
- `assessment_id` text null references value_assessments(id)
- `type` text not null
- `severity` text not null
- `reason` text not null
- `status` text not null
- `created_at` timestamptz not null
- `resolved_at` timestamptz null

### 6.7 `assessment_runs`

字段：

- `id` text primary key
- `trigger` text not null
- `status` text not null
- `started_at` timestamptz not null
- `finished_at` timestamptz null
- `duration_ms` integer null
- `topic_count` integer not null default 0
- `assessed_count` integer not null default 0
- `background_pack_count` integer not null default 0
- `review_flag_count` integer not null default 0
- `error_code` text null
- `error_message` text null
- `trace_id` text not null
- `idempotency_key` text null

唯一约束：

- `idempotency_key where idempotency_key is not null`

## 7. API 实现要求

以 `docs/contracts/value-background-api.md` 为准。

所有 API 必须：

- 使用统一 envelope。
- 有 trace id。
- 不返回完整 evidence 原文。
- 对外错误使用简体中文。
- 写操作预留鉴权 dependency。
- 不把失败包装成空成功态。

## 8. 评分与背景算法要求

### 8.1 输入准备

1. 读取 topic / members / trend snapshots。
2. 读取 source trust。
3. 读取默认 AssessmentPolicy。
4. 按 topic 更新时间排序，保证重跑稳定。

### 8.2 评分

1. 根据 topic 来源数、来源信任、传播快照、时间新鲜度计算分项分。
2. 根据标题党、营销词、低可信来源、重复转述计算 noiseRisk。
3. 按 policy 权重计算 valueScore。
4. 根据阈值和 review 条件生成 recommendation。
5. 写 ValueAssessment。

### 8.3 背景补全

1. 判断是否触发背景补全。
2. 从 topic member URL、官方域名规则、管理员配置候选中选择 evidence URL。
3. 对 URL 执行 SSRFGuard 和合规校验。
4. 抓取并提取 evidence summary。
5. 生成 BackgroundPack。
6. 标注 official source status、fact conflicts 和 unresolved questions。

### 8.4 Review flag

以下情况必须生成 review flag：

- 高 impact + low confidence。
- 来源冲突。
- 疑似营销。
- 疑似敏感。
- 高影响但缺官方来源。
- 背景补全失败影响关键事实。

## 9. Agent 输入输出

M4 ValueScorer / BackgroundResearcher 是逻辑 Agent，不要求独立进程。

输入：

- `HotTopicCluster`
- `TopicMember[]`
- `TrendSnapshot[]`
- Source trust level
- AssessmentPolicy

输出：

- `AssessmentRun`
- `ValueAssessment[]`
- `BackgroundPack[]`
- `EvidenceSource[]`
- `FactConflict[]`
- `ReviewFlag[]`

Trace：

- 每次 run 必须记录 trace id。
- 每个 assessment / background pack 必须能追到 run。
- LLM 调用如果启用，必须记录 promptVersion、model、token、cost、错误。

## 10. 错误处理

必须实现 `docs/contracts/value-background-api.md` 的错误码。

错误映射：

- 参数错误：`BAD_REQUEST`
- topic 不存在：`TOPIC_NOT_FOUND`
- assessment 不存在：`ASSESSMENT_NOT_FOUND`
- background pack 不存在：`BACKGROUND_PACK_NOT_FOUND`
- evidence 不存在：`EVIDENCE_NOT_FOUND`
- run 不存在：`ASSESSMENT_RUN_NOT_FOUND`
- policy 非法：`ASSESSMENT_POLICY_INVALID`
- background URL 被阻断：`BACKGROUND_FETCH_BLOCKED`
- background 抓取失败：`BACKGROUND_FETCH_FAILED`
- 来源冲突：`BACKGROUND_SOURCE_CONFLICT`
- 需要人工确认：`ASSESSMENT_REVIEW_REQUIRED`

## 11. 安全与合规

- Evidence URL 抓取必须执行 SSRFGuard。
- 禁止绕过登录、付费墙、robots.txt、ToS 或平台风控。
- 外部内容不得作为系统 prompt 或工具指令。
- Cookie、Authorization、Webhook URL 不得进入 evidence、日志或 fixture。
- 背景补全失败必须显式记录。
- 低置信内容不能进入确定性表达链路。

## 12. Prompt injection 防护

- Evidence HTML / Markdown / 文本中的指令只作为内容保存。
- 不使用 evidence 原文作为系统 prompt。
- 如果启用 LLM，必须使用固定 promptVersion、结构化输入和工具白名单。
- 模型输出必须逐条绑定 evidence URL；无 evidence claim 丢弃或标为 unresolved。
- 测试必须覆盖 prompt injection evidence。

## 13. 测试 Fixture

必须创建：

- `fixtures/m4_high_value_official_source.json`
- `fixtures/m4_low_credibility_marketing.json`
- `fixtures/m4_high_impact_low_confidence.json`
- `fixtures/m4_missing_official_source.json`
- `fixtures/m4_source_conflict.json`
- `fixtures/m4_background_fetch_failed.json`
- `fixtures/m4_prompt_injection_evidence.json`

Fixture 不得包含真实密钥、cookie、授权头。

## 14. 测试要求

### 14.1 单元测试

- AssessmentPolicy 权重校验。
- valueScore 分项和总分计算。
- recommendation 阈值。
- high impact low confidence 进入 review。
- marketing/noiseRisk 降权。
- missing official source 标记。
- source conflict 生成 FactConflict。
- background fetch failed 保留 failure reason。
- prompt injection evidence 只作为普通文本处理。
- AssessmentRun idempotency。

### 14.2 集成测试

- 从 M3 topic fixture 触发 assessment run。
- 查询 topic assessment。
- 查询 background pack detail。
- 查询 evidence sources。
- 查询 review flags。
- 查询 fact conflicts。
- OpenAPI 包含 M4 endpoints。
- 失败路径返回统一 envelope。

测试不能断言实时新闻事实。

## 15. 验收标准

- 每个 assessed topic 有总分、分项分、recommendation 和 reasons。
- 高影响低置信 topic 进入 review。
- 标题党、营销、重复转述可以 suppress 或 review。
- 背景包至少区分 original / related / historical / official / unresolved。
- 关键事实有 evidence URL。
- 官方来源缺失被明确标注。
- 来源冲突生成 FactConflict 和 ReviewFlag。
- 背景抓取失败保留 failure reason，不补写事实。
- Prompt injection 样本文本不会触发工具调用、外部请求或系统指令执行。

## 16. 交付物

- PostgreSQL migration。
- ValueAssessment model / repository / service。
- AssessmentPolicy model / service。
- BackgroundPack model / repository / service。
- EvidenceSource model / repository / service。
- FactConflict model / repository / service。
- ReviewFlag model / repository / service。
- AssessmentRun model / repository / service。
- ValueScorer。
- BackgroundResearcher。
- EvidenceFetcher。
- API routes。
- fixtures。
- 单元测试和集成测试。
- README 更新，写清 M4 不生成最终 AI 点评。

## 17. 联调边界

- 前端只调用 `docs/contracts/value-background-api.md` 定义的 M4 API。
- M4 后端只消费 M3/M2 已入库数据和受控 evidence URL。
- M5 只能消费 M4 `ValueAssessment` / `BackgroundPack`，不能把无证据文本当事实。
- 如果 contract 变更，先改 `docs/contracts/value-background-api.md`，再改后端和前端。

## 18. 迁移或兼容策略

- M4 migration 必须只新增表和索引，不修改 M3 / M2 既有字段。
- M4 表通过外键引用 M3 topic 和 M2 sources；如果 M3 未启用，M4 后端必须保持禁用或 mock 模式。
- 首次启用 M4 时只处理已有 topic，不重新触发 clustering 或 collection。
- 同一 topic 重跑 assessment 应生成新版本或更新 latest 指针，不能丢失旧 trace。
- contract 变更顺序固定为：先更新 `docs/contracts/value-background-api.md`，再更新后端 PRD / 前端 PRD，最后改实现和测试。

## 19. 已知风险

- 评分权重会影响推荐结果，需要 M7 eval 兜底。
- 背景补全抓取外部网页存在 SSRF、版权、ToS 和 prompt injection 风险。
- 官方来源识别规则容易漏判，必须允许显式标注 not_found。
- LLM 摘要可能产生无证据 claim，必须逐条绑定 evidence URL。
- M4 未完成权限系统前，assessment trigger API 不能暴露到公网。
