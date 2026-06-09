# M7 评估与可观测 API 共享契约

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 上游依赖：M1-M6 全链路能力、M6 admin auth / RBAC / audit
> 使用对象：M7 后端评估与可观测服务、M7 前端 Observability Console、CI、本地回归脚本、不同 AI coding 客户端
> 原则：M7 负责 eval、trace、metrics、cost、alert 和 replay；不得把缓存或局部样本冒充最新事实，不得在 trace / replay 中泄露 secret。

## 1. 目标

定义 M7 阶段的固定评估集、评估运行、回归失败、Agent trace、工具调用日志、指标、成本、告警和回放 API。后端按本文实现；前端按本文展示；CI 和本地命令按本文判断是否可进入后续发布。

M7 覆盖：

- 固定 eval fixture 版本管理。
- 路由、采集归一化、聚类、价值评分、背景证据、点评无源事实、分发去重和 prompt injection eval。
- Agent run trace 和 tool call log。
- token / cost 统计。
- 请求量、错误率、耗时、推送量 dashboard 数据。
- RegressionFailure 和 release gate。
- Agent run replay。
- AlertRule / AlertEvent。

## 2. 全局约定

### 2.1 Base URL

```text
http://localhost:8000/api
```

### 2.2 响应 envelope

沿用 M1-M6：

```json
{
  "data": {},
  "meta": {
    "traceId": "tr_20260609_000001",
    "source": "hot-godlike",
    "cached": false,
    "query": {},
    "warnings": []
  },
  "error": null
}
```

### 2.3 认证与权限

M7 API 默认复用 M6 admin auth / RBAC：

- 查看 eval / trace / metrics：需要 `audit:read` 或后续 `observability:read` 等价权限。
- 触发 eval / replay：需要 `rerun:trigger` 或后续 `observability:write` 等价权限。
- CI 可以使用 scoped API token；token 只存 hash。

### 2.4 分页

列表 API 使用 cursor 分页：

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

## 3. 枚举

### 3.1 EvalCaseType

```ts
type EvalCaseType =
  | "route"
  | "collection_normalization"
  | "clustering"
  | "value_assessment"
  | "background_evidence"
  | "commentary_grounding"
  | "distribution_dedupe"
  | "security_prompt_injection";
```

### 3.2 EvalRunStatus

```ts
type EvalRunStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "regression_failed"
  | "cancelled";
```

### 3.3 EvalResultStatus

```ts
type EvalResultStatus = "passed" | "failed" | "skipped";
```

### 3.4 TraceSpanStatus

```ts
type TraceSpanStatus = "running" | "succeeded" | "failed" | "cancelled";
```

### 3.5 AlertStatus

```ts
type AlertStatus = "open" | "acknowledged" | "resolved";
```

## 4. 数据结构

### 4.1 EvalSuite

```json
{
  "id": "suite_core_regression",
  "name": "Core Regression",
  "version": "2026-06-09.1",
  "caseTypes": ["route", "clustering", "commentary_grounding"],
  "fixtureRoot": "backend/tests/fixtures/eval",
  "requiredForRelease": true,
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:00Z"
}
```

规则：

- `version` 必须随 fixture 变更递增。
- required suite 失败时必须产生 `RegressionFailure`。

### 4.2 EvalCase

```json
{
  "id": "eval_route_today_ai_001",
  "suiteId": "suite_core_regression",
  "type": "route",
  "name": "今天 AI 圈有什么",
  "fixtureRef": "eval/route/today_ai.json",
  "input": {
    "query": "今天 AI 圈有什么"
  },
  "expected": {
    "intent": "daily_or_items",
    "mustUseServerSearch": false,
    "mustNotAssertLiveTitle": true
  },
  "tags": ["route", "zh"],
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:00Z"
}
```

规则：

- 真实 API smoke eval 不得断言具体新闻标题。
- 每个 expected 必须可机器判定。
- 外部文本 fixture 一律按不可信输入处理。

### 4.3 EvalRun

```json
{
  "id": "eval_run_20260609_001",
  "suiteId": "suite_core_regression",
  "suiteVersion": "2026-06-09.1",
  "trigger": "manual",
  "status": "succeeded",
  "startedAt": "2026-06-09T00:00:00Z",
  "finishedAt": "2026-06-09T00:00:30Z",
  "durationMs": 30000,
  "totalCount": 24,
  "passedCount": 24,
  "failedCount": 0,
  "skippedCount": 0,
  "regressionFailureCount": 0,
  "traceId": "tr_20260609_000001",
  "gitRef": null,
  "promptVersions": {
    "commentary_generator": "commentary.v1"
  }
}
```

### 4.4 EvalResult

```json
{
  "id": "eval_result_20260609_001",
  "evalRunId": "eval_run_20260609_001",
  "caseId": "eval_route_today_ai_001",
  "type": "route",
  "status": "passed",
  "score": 1.0,
  "assertions": [
    {
      "name": "intent",
      "status": "passed",
      "expected": "daily_or_items",
      "actual": "daily_or_items"
    }
  ],
  "outputRef": "eval/output/eval_result_20260609_001.json",
  "errorCode": null,
  "errorMessage": null,
  "traceId": "tr_20260609_000001",
  "createdAt": "2026-06-09T00:00:10Z"
}
```

### 4.5 RegressionFailure

```json
{
  "id": "regression_20260609_001",
  "evalRunId": "eval_run_20260609_002",
  "caseId": "eval_commentary_grounding_001",
  "severity": "blocker",
  "category": "commentary_grounding",
  "message": "点评缺少 evidence URL",
  "expectedRef": "eval/expected/commentary_grounding_001.json",
  "actualRef": "eval/output/eval_result_20260609_002.json",
  "status": "open",
  "createdAt": "2026-06-09T00:00:10Z",
  "traceId": "tr_20260609_000002"
}
```

`severity` 枚举：

```ts
type RegressionSeverity = "info" | "warning" | "blocker";
```

### 4.6 AgentRunTrace

```json
{
  "runId": "agent_run_20260609_001",
  "agentName": "commentary_generator",
  "trigger": "eval",
  "status": "succeeded",
  "inputRef": "agent/input/agent_run_20260609_001.json",
  "outputRef": "agent/output/agent_run_20260609_001.json",
  "traceId": "tr_20260609_000001",
  "startedAt": "2026-06-09T00:00:00Z",
  "finishedAt": "2026-06-09T00:00:05Z",
  "durationMs": 5000,
  "model": "gpt-4.1-mini",
  "promptVersion": "commentary.v1",
  "inputTokens": 1000,
  "outputTokens": 300,
  "estimatedCost": 0.01,
  "errorCode": null,
  "errorMessage": null
}
```

### 4.7 TraceSpan

```json
{
  "id": "span_20260609_001",
  "traceId": "tr_20260609_000001",
  "parentSpanId": null,
  "name": "CommentaryGenerator.generate",
  "kind": "agent",
  "status": "succeeded",
  "startedAt": "2026-06-09T00:00:00Z",
  "finishedAt": "2026-06-09T00:00:05Z",
  "durationMs": 5000,
  "attributes": {
    "topicId": "topic_20260603_abcd1234",
    "promptVersion": "commentary.v1"
  },
  "redaction": "secrets_masked"
}
```

### 4.8 ToolCallLog

```json
{
  "id": "tool_call_20260609_001",
  "traceId": "tr_20260609_000001",
  "spanId": "span_20260609_001",
  "toolName": "background_reader",
  "inputRef": "tool/input/tool_call_20260609_001.json",
  "outputRef": "tool/output/tool_call_20260609_001.json",
  "status": "succeeded",
  "durationMs": 300,
  "errorCode": null,
  "createdAt": "2026-06-09T00:00:01Z"
}
```

### 4.9 CostRecord

```json
{
  "id": "cost_20260609_001",
  "traceId": "tr_20260609_000001",
  "agentRunId": "agent_run_20260609_001",
  "agentName": "commentary_generator",
  "model": "gpt-4.1-mini",
  "inputTokens": 1000,
  "outputTokens": 300,
  "estimatedCost": 0.01,
  "currency": "USD",
  "createdAt": "2026-06-09T00:00:05Z"
}
```

### 4.10 MetricsSnapshot

```json
{
  "window": "24h",
  "startedAt": "2026-06-08T00:00:00Z",
  "finishedAt": "2026-06-09T00:00:00Z",
  "requestCount": 1000,
  "errorRate": 0.02,
  "p50DurationMs": 350,
  "p95DurationMs": 1200,
  "agentRunCount": 120,
  "deliveryCount": 80,
  "failedDeliveryCount": 2,
  "inputTokens": 120000,
  "outputTokens": 30000,
  "estimatedCost": 4.2,
  "traceId": "tr_20260609_000005"
}
```

### 4.11 AlertRule

```json
{
  "id": "alert_eval_regression_blocker",
  "name": "Eval regression blocker",
  "type": "eval_regression",
  "enabled": true,
  "conditions": {
    "severity": "blocker",
    "minCount": 1
  },
  "channels": ["admin_console"],
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:00Z"
}
```

### 4.12 AlertEvent

```json
{
  "id": "alert_event_20260609_001",
  "ruleId": "alert_eval_regression_blocker",
  "status": "open",
  "severity": "blocker",
  "message": "Core regression suite failed",
  "resourceType": "eval_run",
  "resourceId": "eval_run_20260609_002",
  "createdAt": "2026-06-09T00:00:10Z",
  "acknowledgedAt": null,
  "resolvedAt": null,
  "traceId": "tr_20260609_000002"
}
```

### 4.13 ReplayRequest

```json
{
  "id": "replay_20260609_001",
  "agentRunId": "agent_run_20260609_001",
  "mode": "dry_run",
  "status": "queued",
  "reason": "复现 eval failure",
  "requestedBy": "user_reviewer_001",
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:00Z",
  "traceId": "tr_20260609_000006"
}
```

Replay 规则：

- 默认 `dry_run`，不得触发真实外发。
- replay 必须使用原始 inputRef / fixtureRef 的快照，不重新抓取外部事实。
- replay 输出不得覆盖原 run。

## 5. API 端点

### 5.1 Eval suites / cases

```http
GET /api/eval-suites
GET /api/eval-suites/{suiteId}
GET /api/eval-cases?suiteId=suite_core_regression&type=route&take=50&cursor=opaque
```

### 5.2 Eval runs / results

```http
POST /api/eval-runs
GET /api/eval-runs?suiteId=suite_core_regression&status=succeeded&take=50&cursor=opaque
GET /api/eval-runs/{evalRunId}
GET /api/eval-results?evalRunId=eval_run_20260609_001&take=50&cursor=opaque
GET /api/regression-failures?status=open&take=50&cursor=opaque
```

`POST /api/eval-runs` 请求体：

```json
{
  "suiteId": "suite_core_regression",
  "caseTypes": ["route", "commentary_grounding"],
  "trigger": "manual",
  "reason": "prompt version changed",
  "dryRun": true
}
```

### 5.3 Agent run / trace

```http
GET /api/agent-runs?agentName=commentary_generator&status=failed&take=50&cursor=opaque
GET /api/agent-runs/{agentRunId}
GET /api/traces/{traceId}
GET /api/traces/{traceId}/spans
GET /api/tool-calls?traceId=tr_20260609_000001&take=50&cursor=opaque
```

### 5.4 Replay

```http
POST /api/replay-requests
GET /api/replay-requests?status=queued&take=50&cursor=opaque
GET /api/replay-requests/{replayRequestId}
```

### 5.5 Metrics / cost

```http
GET /api/metrics/summary?window=24h
GET /api/cost-records?agentName=commentary_generator&take=50&cursor=opaque
```

### 5.6 Alerts

```http
GET /api/alert-rules
POST /api/alert-rules
PATCH /api/alert-rules/{alertRuleId}
GET /api/alert-events?status=open&take=50&cursor=opaque
POST /api/alert-events/{alertEventId}/acknowledge
POST /api/alert-events/{alertEventId}/resolve
```

## 6. 错误码

| code | HTTP | retryable | 场景 |
|---|---:|:---:|---|
| `EVAL_SUITE_NOT_FOUND` | 404 | 否 | eval suite 不存在 |
| `EVAL_CASE_NOT_FOUND` | 404 | 否 | eval case 不存在 |
| `EVAL_RUN_NOT_FOUND` | 404 | 否 | eval run 不存在 |
| `EVAL_FIXTURE_VERSION_CONFLICT` | 409 | 否 | fixture version 与 suite version 不一致 |
| `EVAL_RUN_ALREADY_RUNNING` | 409 | 是 | 同 suite eval 正在运行 |
| `REGRESSION_FAILURE_NOT_FOUND` | 404 | 否 | regression failure 不存在 |
| `REGRESSION_FAILED` | 409 | 否 | required eval suite 失败 |
| `TRACE_NOT_FOUND` | 404 | 否 | trace 不存在 |
| `AGENT_RUN_NOT_FOUND` | 404 | 否 | agent run 不存在 |
| `REPLAY_REQUEST_NOT_FOUND` | 404 | 否 | replay request 不存在 |
| `REPLAY_UNSAFE_SIDE_EFFECT` | 409 | 否 | replay 试图触发真实外发或写操作 |
| `METRIC_RANGE_INVALID` | 400 | 否 | 指标时间窗口非法 |
| `ALERT_RULE_NOT_FOUND` | 404 | 否 | alert rule 不存在 |
| `ALERT_EVENT_NOT_FOUND` | 404 | 否 | alert event 不存在 |
| `GROUNDING_EVIDENCE_MISSING` | 409 | 否 | 点评或输出缺 evidence URL |
| `OBSERVABILITY_REDACTION_FAILED` | 500 | 否 | trace / log 脱敏失败 |
| `INTERNAL_ERROR` | 500 | 否 | 未知错误 |

## 7. 存储契约

M7 必须落 PostgreSQL 表：

- `eval_suites`
- `eval_cases`
- `eval_runs`
- `eval_results`
- `regression_failures`
- `agent_run_traces`
- `trace_spans`
- `tool_call_logs`
- `cost_records`
- `metrics_snapshots`
- `alert_rules`
- `alert_events`
- `replay_requests`

建议索引：

- `eval_runs(suite_id, status, started_at desc)`
- `eval_results(eval_run_id, status)`
- `regression_failures(status, severity, created_at desc)`
- `agent_run_traces(agent_name, status, started_at desc)`
- `trace_spans(trace_id, started_at)`
- `tool_call_logs(trace_id, created_at desc)`
- `cost_records(agent_name, created_at desc)`
- `alert_events(status, severity, created_at desc)`

## 8. 安全与合规

- trace / tool call / replay output 必须脱敏 secret、token、cookie、Authorization header、webhook URL。
- eval fixture 不得包含真实密钥或用户私密订阅。
- replay 默认 dryRun，不得触发生产 webhook、bot、email 或外部提交。
- 真实 API smoke eval 不断言具体新闻标题，只断言 schema、状态、来源和边界。
- metrics dashboard 必须标注时间窗口和数据范围。
- cost 只保存估算值，不作为账单事实。

## 9. Prompt Injection 防护

- eval fixture 中的外部文本只作为测试输入。
- trace viewer 不执行外部文本中的指令。
- replay 不读取 commentary / evidence 中的“忽略规则”“调用 webhook”等文本作为系统指令。
- security eval 必须覆盖 prompt injection、无源事实、敏感外发和结构化输出缺字段。

## 10. 测试 Fixture

必须提供：

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

Fixture 必须版本化，并记录 suite version。

## 11. 兼容边界

- M7 不修改 M1-M6 业务 contract 的核心 shape。
- M7 通过 inputRef / outputRef / traceId 关联上游资源。
- M7 不替代企业级 APM，只提供产品内必要 trace、eval 和 dashboard。
- 若需要新增 Agent prompt / model 字段，先更新对应上游 contract，再更新 M7。
