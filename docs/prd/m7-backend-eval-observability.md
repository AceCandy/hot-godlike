# M7 后端评估与可观测子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/eval-observability-api.md`
> 上游依赖：M1-M6 全链路能力
> 推荐实现客户端：后端 / eval / observability AI coding 客户端
> 技术栈决策：Python + FastAPI + PostgreSQL；指标聚合可先用定时 job，Redis 只作为短期锁和缓存。

## 1. 目标

实现 M7 后端评估与可观测能力：固定 eval 集、eval run、regression failure、Agent run trace、tool call log、token / cost 统计、metrics snapshot、alert rule / event 和 agent run replay。

M7 的目标是防止多 Agent 系统在迭代中退化。M7 不自动判定新闻真实性，不替代企业级 APM，不执行真实生产外发 replay。

## 2. 背景与依赖

M1-M6 已提供：

- M1 query route 和 AI HOT seed source。
- M2 source / fetch / raw item / health。
- M3 topic clustering / merge / split / trend snapshot。
- M4 value assessment / background / evidence / review flag。
- M5 commentary / distribution / delivery trace。
- M6 admin auth / RBAC / review / audit。

M7 在此基础上新增：

- EvalSuite / EvalCase / EvalRun / EvalResult。
- RegressionFailure。
- AgentRunTrace / TraceSpan / ToolCallLog。
- CostRecord。
- MetricsSnapshot。
- AlertRule / AlertEvent。
- ReplayRequest。

## 3. 范围

### 3.1 In Scope

- `GET /api/eval-suites`
- `GET /api/eval-suites/{suiteId}`
- `GET /api/eval-cases`
- `POST /api/eval-runs`
- `GET /api/eval-runs`
- `GET /api/eval-runs/{evalRunId}`
- `GET /api/eval-results`
- `GET /api/regression-failures`
- `GET /api/agent-runs`
- `GET /api/agent-runs/{agentRunId}`
- `GET /api/traces/{traceId}`
- `GET /api/traces/{traceId}/spans`
- `GET /api/tool-calls`
- `POST /api/replay-requests`
- `GET /api/replay-requests`
- `GET /api/replay-requests/{replayRequestId}`
- `GET /api/metrics/summary`
- `GET /api/cost-records`
- `GET /api/alert-rules`
- `POST /api/alert-rules`
- `PATCH /api/alert-rules/{alertRuleId}`
- `GET /api/alert-events`
- `POST /api/alert-events/{alertEventId}/acknowledge`
- `POST /api/alert-events/{alertEventId}/resolve`
- PostgreSQL schema 和 migration。
- Eval fixture loader。
- Eval runner。
- Trace collector。
- Metrics aggregator。
- Cost recorder。
- Alert service。
- Replay service。
- 单元测试、集成测试、CI / 本地命令说明。

### 3.2 Out of Scope

- 企业级 APM 全量替代。
- 大规模在线 A/B 实验。
- 自动判定新闻真实性。
- 生产 webhook replay。
- 真实 API smoke 对实时新闻标题做断言。
- 把 cost estimate 当作正式账单。
- M1-M6 业务逻辑重写。

## 4. 用户故事 / 系统场景

### 4.1 Prompt 变更后运行 eval

开发者修改 commentary prompt 后触发 core regression suite。M7 运行 route、commentary grounding、distribution dedupe 等 eval；失败则写 `RegressionFailure`，状态为 `regression_failed`。

### 4.2 查看一次失败 trace

管理员打开 failed agent run，查看 trace span、tool call log、inputRef / outputRef、模型、promptVersion、token、耗时和错误原因。密钥和 webhook URL 已脱敏。

### 4.3 回放 Agent run

开发者对某个 agent run 发起 dryRun replay。M7 使用原 inputRef / fixtureRef 快照，不重新抓取外部事实，不触发真实外发，并写新的 replay trace。

### 4.4 监控成本和错误率

管理员查看 24h / 7d / 30d metrics，确认请求量、错误率、p95、token、成本估算、推送量。dashboard 必须标注时间窗口和数据范围。

### 4.5 告警 eval regression

required eval suite 失败时，AlertService 生成 blocker alert event。管理员可 acknowledge / resolve，但不能删除历史。

## 5. 模块设计

### 5.1 EvalFixtureLoader

职责：

- 读取版本化 fixture。
- 校验 fixture schema。
- 记录 suiteVersion。

规则：

- fixture version 不一致返回 `EVAL_FIXTURE_VERSION_CONFLICT`。
- fixture 不得包含 secret、token、cookie。

### 5.2 EvalRunner

职责：

- 创建 EvalRun。
- 调度各类 EvalAdapter。
- 汇总 EvalResult 和 RegressionFailure。

规则：

- 同 suite 正在运行时返回 `EVAL_RUN_ALREADY_RUNNING`。
- required suite 有 blocker failure 时状态为 `regression_failed`。

### 5.3 EvalAdapter

必须实现：

- `RouteEvalAdapter`
- `CollectionNormalizationEvalAdapter`
- `ClusteringEvalAdapter`
- `ValueAssessmentEvalAdapter`
- `BackgroundEvidenceEvalAdapter`
- `CommentaryGroundingEvalAdapter`
- `DistributionDedupeEvalAdapter`
- `PromptInjectionEvalAdapter`

规则：

- 真实 API smoke 不断言具体新闻标题。
- commentary grounding 必须检查 evidence URL。
- distribution dedupe 必须检查同 topic/subscription/channel 不重复。

### 5.4 TraceCollector

职责：

- 统一写 AgentRunTrace、TraceSpan、ToolCallLog。
- 提供 trace 查询。
- 做敏感字段脱敏。

规则：

- 脱敏失败返回 `OBSERVABILITY_REDACTION_FAILED`。
- trace 不得包含明文 secret。

### 5.5 CostRecorder

职责：

- 记录 model、promptVersion、inputTokens、outputTokens、estimatedCost。
- 按 agent / model / window 聚合。

规则：

- cost 是估算值，不是账单事实。
- 缺 token 时记录 warning，不伪造 0 以外的值。

### 5.6 MetricsAggregator

职责：

- 聚合 requestCount、errorRate、p50 / p95、agentRunCount、deliveryCount、token、estimatedCost。
- 生成 MetricsSnapshot。

规则：

- 所有 metrics 必须带时间窗口。
- 局部数据不得写成全网指标。

### 5.7 AlertService

职责：

- 管理 AlertRule。
- 根据 regression failure、错误率、成本阈值生成 AlertEvent。
- 支持 acknowledge / resolve。

规则：

- AlertEvent 只追加状态变化，不删除历史。
- blocker alert 不自动修复业务状态。

### 5.8 ReplayService

职责：

- 创建 ReplayRequest。
- 使用原 inputRef / fixtureRef 快照 dryRun replay。
- 写 replay trace。

规则：

- 默认 dryRun。
- 禁止生产 webhook / bot / email 外发。
- replay output 不覆盖原 run。

### 5.9 RetentionService

职责：

- 管理 eval output、trace、tool call log、cost record 的保留策略。
- 生成清理计划。

规则：

- 删除或归档前必须保留必要 audit 和 failure 证据。
- retention 策略变更进入 M6 audit。

## 6. 数据库 Schema

### 6.1 `eval_suites`

- `id` text primary key
- `name` text not null
- `version` text not null
- `case_types` jsonb not null
- `fixture_root` text not null
- `required_for_release` boolean not null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

### 6.2 `eval_cases`

- `id` text primary key
- `suite_id` text not null references eval_suites(id)
- `type` text not null
- `name` text not null
- `fixture_ref` text not null
- `input` jsonb not null
- `expected` jsonb not null
- `tags` jsonb not null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

### 6.3 `eval_runs`

- `id` text primary key
- `suite_id` text not null references eval_suites(id)
- `suite_version` text not null
- `trigger` text not null
- `status` text not null
- `started_at` timestamptz not null
- `finished_at` timestamptz null
- `duration_ms` integer null
- `total_count` integer not null default 0
- `passed_count` integer not null default 0
- `failed_count` integer not null default 0
- `skipped_count` integer not null default 0
- `regression_failure_count` integer not null default 0
- `trace_id` text not null
- `git_ref` text null
- `prompt_versions` jsonb not null

### 6.4 `eval_results`

- `id` text primary key
- `eval_run_id` text not null references eval_runs(id)
- `case_id` text not null references eval_cases(id)
- `type` text not null
- `status` text not null
- `score` numeric not null
- `assertions` jsonb not null
- `output_ref` text not null
- `error_code` text null
- `error_message` text null
- `trace_id` text not null
- `created_at` timestamptz not null

### 6.5 `regression_failures`

- `id` text primary key
- `eval_run_id` text not null references eval_runs(id)
- `case_id` text not null references eval_cases(id)
- `severity` text not null
- `category` text not null
- `message` text not null
- `expected_ref` text not null
- `actual_ref` text not null
- `status` text not null
- `created_at` timestamptz not null
- `trace_id` text not null

### 6.6 `agent_run_traces`

- `run_id` text primary key
- `agent_name` text not null
- `trigger` text not null
- `status` text not null
- `input_ref` text not null
- `output_ref` text null
- `trace_id` text not null
- `started_at` timestamptz not null
- `finished_at` timestamptz null
- `duration_ms` integer null
- `model` text null
- `prompt_version` text null
- `input_tokens` integer null
- `output_tokens` integer null
- `estimated_cost` numeric null
- `error_code` text null
- `error_message` text null

### 6.7 `trace_spans`

- `id` text primary key
- `trace_id` text not null
- `parent_span_id` text null
- `name` text not null
- `kind` text not null
- `status` text not null
- `started_at` timestamptz not null
- `finished_at` timestamptz null
- `duration_ms` integer null
- `attributes` jsonb not null
- `redaction` text not null

### 6.8 `tool_call_logs`

- `id` text primary key
- `trace_id` text not null
- `span_id` text not null
- `tool_name` text not null
- `input_ref` text not null
- `output_ref` text null
- `status` text not null
- `duration_ms` integer null
- `error_code` text null
- `created_at` timestamptz not null

### 6.9 `cost_records`

- `id` text primary key
- `trace_id` text not null
- `agent_run_id` text null
- `agent_name` text not null
- `model` text null
- `input_tokens` integer null
- `output_tokens` integer null
- `estimated_cost` numeric null
- `currency` text not null
- `created_at` timestamptz not null

### 6.10 `metrics_snapshots`

- `id` text primary key
- `window` text not null
- `started_at` timestamptz not null
- `finished_at` timestamptz not null
- `payload` jsonb not null
- `trace_id` text not null

### 6.11 `alert_rules`

- `id` text primary key
- `name` text not null
- `type` text not null
- `enabled` boolean not null
- `conditions` jsonb not null
- `channels` jsonb not null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

### 6.12 `alert_events`

- `id` text primary key
- `rule_id` text not null references alert_rules(id)
- `status` text not null
- `severity` text not null
- `message` text not null
- `resource_type` text not null
- `resource_id` text not null
- `created_at` timestamptz not null
- `acknowledged_at` timestamptz null
- `resolved_at` timestamptz null
- `trace_id` text not null

### 6.13 `replay_requests`

- `id` text primary key
- `agent_run_id` text not null
- `mode` text not null
- `status` text not null
- `reason` text not null
- `requested_by` text not null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null
- `trace_id` text not null

## 7. API 实现要求

以 `docs/contracts/eval-observability-api.md` 为准。

所有 API 必须：

- 使用统一 envelope。
- 生成 trace id。
- 复用 M6 admin auth / RBAC。
- 不返回明文 secret。
- 对外错误使用简体中文。
- eval / replay 写操作必须有 reason。
- replay 默认 dryRun。

## 8. 状态机

EvalRun：

```text
queued -> running -> succeeded
queued -> running -> failed
queued -> running -> regression_failed
queued -> cancelled
```

ReplayRequest：

```text
queued -> running -> succeeded
queued -> running -> failed
queued -> cancelled
```

AlertEvent：

```text
open -> acknowledged -> resolved
open -> resolved
```

## 9. Agent 输入输出

M7 不新增业务 Agent；M7 评估和回放会调用 M1-M6 的逻辑 Agent 或服务。

输入：

- `EvalSuite`
- `EvalCase`
- `AgentRunTrace`
- `TraceSpan`
- `ToolCallLog`
- `DeliveryRecord`
- `AuditLog`
- fixture

输出：

- `EvalRun`
- `EvalResult`
- `RegressionFailure`
- `MetricsSnapshot`
- `CostRecord`
- `AlertEvent`
- `ReplayRequest`

规则：

- eval input 必须来自 fixture 或已有 inputRef，不临时编造新闻事实。
- replay 不覆盖原 AgentRun。

## 10. 错误处理

必须实现 `docs/contracts/eval-observability-api.md` 的错误码。

错误映射：

- suite 不存在：`EVAL_SUITE_NOT_FOUND`
- fixture version 冲突：`EVAL_FIXTURE_VERSION_CONFLICT`
- 同 suite 正在运行：`EVAL_RUN_ALREADY_RUNNING`
- required eval 失败：`REGRESSION_FAILED`
- trace 不存在：`TRACE_NOT_FOUND`
- replay 试图触发副作用：`REPLAY_UNSAFE_SIDE_EFFECT`
- 指标窗口非法：`METRIC_RANGE_INVALID`
- 点评缺 evidence：`GROUNDING_EVIDENCE_MISSING`
- 脱敏失败：`OBSERVABILITY_REDACTION_FAILED`

## 11. 安全与合规

- eval fixture、trace、tool call、replay output 必须脱敏。
- replay 禁止生产 webhook / bot / email 外发。
- 真实 API smoke 只断言 schema / 状态 / 来源 / 边界，不断言具体新闻标题。
- cost 是估算值，不作为账单事实。
- dashboard 必须标注时间窗口和数据范围。
- 高风险内容 eval failure 不自动发布，进入 review 或 regression failure。

## 12. Prompt injection 防护

- eval fixture 中的 prompt injection 文本只作为测试输入。
- TraceCollector 不执行外部文本中的指令。
- ReplayService 不把 commentary / evidence 里的指令当系统提示。
- PromptInjectionEvalAdapter 覆盖无源事实、敏感外发、结构化输出缺字段。
- trace viewer 输出给前端前必须保持文本安全和敏感字段脱敏。

## 13. 测试 Fixture

必须创建：

- `fixtures/m7_eval_route_cases.json`
- `fixtures/m7_eval_collection_normalization.json`
- `fixtures/m7_eval_clustering_positive_negative.json`
- `fixtures/m7_eval_value_assessment.json`
- `fixtures/m7_eval_background_evidence.json`
- `fixtures/m7_eval_commentary_grounding.json`
- `fixtures/m7_eval_distribution_dedupe.json`
- `fixtures/m7_eval_prompt_injection.json`
- `fixtures/m7_trace_agent_run.json`
- `fixtures/m7_metrics_snapshot.json`
- `fixtures/m7_replay_dry_run.json`
- `fixtures/m7_alert_regression.json`

Fixture 不得包含真实 webhook、token、cookie、授权头或明文 secret。

## 14. 测试要求

### 14.1 单元测试

- EvalFixtureLoader version 校验。
- EvalRunner 状态机。
- RouteEvalAdapter。
- CollectionNormalizationEvalAdapter。
- Clustering 正反例。
- Commentary grounding evidence URL 检查。
- Distribution dedupe。
- Prompt injection eval。
- Trace redaction。
- Cost aggregation。
- Metrics window validation。
- Replay dryRun side-effect guard。
- Alert rule trigger。

### 14.2 集成测试

- 触发 core eval run 并生成 EvalResult。
- required suite failure 生成 RegressionFailure。
- trace 查询返回 spans 和 tool calls。
- replay request 默认 dryRun。
- metrics summary 返回时间窗口。
- alert acknowledge / resolve。
- OpenAPI 包含 M7 endpoints。
- 失败路径返回统一 envelope。

测试不能调用真实生产 webhook、真实第三方 bot、真实用户邮箱；真实 API smoke 不能断言具体新闻标题。

## 15. 验收标准

- 固定 eval suite 可运行。
- eval 覆盖 route、collection normalization、clustering、value assessment、background evidence、commentary grounding、distribution dedupe、prompt injection。
- required suite 失败会产生 RegressionFailure。
- 每个 AgentRun 有 trace id、输入输出引用、状态、耗时、错误、模型、promptVersion、token 和成本估算。
- 每次分发能追溯到 topic、commentary、delivery 和 evidence URL。
- trace / replay / tool call 输出不泄露 secret。
- metrics dashboard 数据有时间窗口。
- replay 默认 dryRun 且不覆盖原 run。
- CI 或本地命令能运行核心 eval。

## 16. 交付物

- PostgreSQL migration。
- EvalFixtureLoader。
- EvalRunner。
- EvalAdapter implementations。
- TraceCollector。
- CostRecorder。
- MetricsAggregator。
- AlertService。
- ReplayService。
- RetentionService。
- API routes。
- fixtures。
- 单元测试和集成测试。
- README 更新，写清本地 eval 命令和 CI gate。

## 17. 联调边界

- 前端只调用 `docs/contracts/eval-observability-api.md` 和 M6 admin auth。
- 后端 eval / replay 默认不调用生产外发渠道。
- 真实 API smoke 需保留真实错误，不伪造成功。
- 如果 contract 变更，先改 `docs/contracts/eval-observability-api.md`，再改后端和前端。

## 18. 迁移或兼容策略

- M7 migration 只新增 eval / trace / metrics / alert / replay 表，不修改 M1-M6 既有字段。
- 通过 `trace_id`、`run_id`、inputRef / outputRef 关联上游资源。
- 首次启用 M7 时可从已有 M1-M6 run 逐步回填 trace，但不能编造缺失成本或 token。
- contract 变更顺序固定为：先更新 `docs/contracts/eval-observability-api.md`，再更新后端 PRD / 前端 PRD，最后改实现和测试。

## 19. 已知风险

- Eval 太宽泛会变成摆设，必须有机器可判定断言。
- 真实 API smoke 如果断言实时标题会导致不稳定，必须只断言 schema 和边界。
- Trace / replay 泄露密钥风险高，脱敏失败必须阻断输出。
- Cost 估算可能不准，UI 不能当账单展示。
- Replay 如果触发真实外发会有外部副作用，必须默认 dryRun。
