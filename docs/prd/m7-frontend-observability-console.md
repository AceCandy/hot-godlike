# M7 前端评估与可观测 Console 子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/eval-observability-api.md`
> 上游依赖：M6 Admin Console / auth / RBAC
> 推荐实现客户端：前端 AI coding 客户端
> 技术栈决策：Vue 3 + Vite + Tailwind CSS。

## 1. 目标

实现 M7 阶段的 Observability Console，让管理员、开发者和审核员能查看 eval suite、eval run、eval result、regression failure、Agent run trace、tool call log、metrics、cost、alert 和 replay request，用固定证据定位多 Agent 系统退化。

M7 前端不执行 eval 逻辑，不直接读取外部源，不调用真实 webhook / bot / email，不把 cost estimate 展示成账单事实。

## 2. 范围

### 2.1 In Scope

- EvalSuite 列表和详情。
- EvalCase 列表。
- 触发 EvalRun。
- EvalRun 列表和详情。
- EvalResult 断言详情。
- RegressionFailure 列表和详情。
- AgentRun 列表和详情。
- Trace viewer。
- ToolCallLog 列表。
- ReplayRequest 创建、列表和详情。
- Metrics summary dashboard。
- CostRecord 列表和聚合。
- AlertRule 列表、创建、编辑。
- AlertEvent 列表、acknowledge、resolve。
- 错误态、加载态、空状态。
- mock API 并行开发。
- 移动端基本适配。

### 2.2 Out of Scope

- 企业级 APM 全量 UI。
- 大规模在线 A/B 实验。
- 自动判定新闻真实性。
- 真实 webhook / bot / email replay。
- 直接调用 AI HOT、RSSHub、RSS 或 evidence URL 抓取接口。
- 展示明文 secret、token、cookie、Authorization header。

## 3. 页面结构

M7 可以作为 Admin Console 的“可观测”分区，也可以独立路由。

### 3.1 Overview Dashboard

展示：

- requestCount。
- errorRate。
- p50 / p95 duration。
- agentRunCount。
- deliveryCount。
- failedDeliveryCount。
- inputTokens / outputTokens。
- estimatedCost。
- open alerts。
- latest eval status。

规则：

- 必须展示时间窗口。
- 必须说明 cost 是估算值。
- 不把局部数据写成全网趋势。

### 3.2 Eval Suites

展示字段：

- name。
- version。
- caseTypes。
- requiredForRelease。
- updatedAt。

行为：

- 查看 cases。
- 触发 eval run。
- 选择 caseTypes。
- 填写 reason。
- dryRun 默认开启。

规则：

- required suite 失败必须明显展示。
- 真实 API smoke 不显示具体标题断言为必过条件。

### 3.3 Eval Run Detail

展示：

- status。
- suiteVersion。
- trigger。
- startedAt / finishedAt。
- total / passed / failed / skipped。
- regressionFailureCount。
- promptVersions。
- traceId。

展开：

- EvalResult assertion table。
- outputRef。
- errorCode / errorMessage。

规则：

- `regression_failed` 必须以 blocker 状态展示。
- failed result 必须可跳转到 RegressionFailure 和 Trace。

### 3.4 Regression Failures

展示字段：

- severity。
- category。
- message。
- caseId。
- evalRunId。
- status。
- createdAt。
- traceId。

规则：

- blocker failure 必须排在前面。
- expectedRef / actualRef 只展示脱敏摘要。
- 不把 failure 标记为 resolved，除非后端返回状态。

### 3.5 Agent Runs

展示字段：

- agentName。
- trigger。
- status。
- durationMs。
- model。
- promptVersion。
- inputTokens / outputTokens。
- estimatedCost。
- errorCode / errorMessage。
- traceId。

行为：

- 查看 trace。
- 创建 replay request。

规则：

- replay 默认 dryRun。
- failed run 不显示成 succeeded。
- cost 缺失显示未知，不伪造估算。

### 3.6 Trace Viewer

展示：

- traceId。
- span tree。
- tool calls。
- inputRef / outputRef。
- redaction status。
- duration waterfall。

规则：

- 不展开明文 secret、token、cookie、Authorization header。
- 外部文本只作为普通文本显示。
- 长文本可折叠但不能用 `v-html`。

### 3.7 Replay Requests

展示字段：

- agentRunId。
- mode。
- status。
- reason。
- requestedBy。
- traceId。

行为：

- 创建 dryRun replay。
- 查看 replay 结果。

规则：

- 非 dryRun replay 在 M7 v0.1 不提供 UI。
- replay 不显示为覆盖原 run。

### 3.8 Metrics / Cost

展示：

- 24h / 7d / 30d 窗口。
- request count。
- error rate。
- p95。
- token。
- estimated cost。
- delivery count。

规则：

- cost 展示为 estimated。
- 指标必须带时间窗口和数据范围。
- `METRIC_RANGE_INVALID` 明确展示。

### 3.9 Alerts

AlertRule：

- name。
- type。
- enabled。
- conditions。
- channels。

AlertEvent：

- severity。
- status。
- message。
- resourceType。
- resourceId。
- traceId。

行为：

- 创建 / 编辑 AlertRule。
- acknowledge。
- resolve。

规则：

- acknowledge / resolve 必须以 API 返回为准。
- 不删除 AlertEvent。

## 4. 组件建议

- `ObservabilityPage`
- `MetricsOverview`
- `EvalSuiteList`
- `EvalRunPanel`
- `EvalResultTable`
- `RegressionFailureList`
- `AgentRunList`
- `TraceViewer`
- `TraceSpanTree`
- `ToolCallLogList`
- `ReplayRequestPanel`
- `CostSummary`
- `AlertRuleEditor`
- `AlertEventList`
- `ObservabilityApiStateView`

## 5. API 使用

以 `docs/contracts/eval-observability-api.md` 为唯一 M7 契约。

前端调用：

```text
GET /api/eval-suites
GET /api/eval-suites/{suiteId}
GET /api/eval-cases
POST /api/eval-runs
GET /api/eval-runs
GET /api/eval-runs/{evalRunId}
GET /api/eval-results
GET /api/regression-failures
GET /api/agent-runs
GET /api/agent-runs/{agentRunId}
GET /api/traces/{traceId}
GET /api/traces/{traceId}/spans
GET /api/tool-calls
POST /api/replay-requests
GET /api/replay-requests
GET /api/replay-requests/{replayRequestId}
GET /api/metrics/summary
GET /api/cost-records
GET /api/alert-rules
POST /api/alert-rules
PATCH /api/alert-rules/{alertRuleId}
GET /api/alert-events
POST /api/alert-events/{alertEventId}/acknowledge
POST /api/alert-events/{alertEventId}/resolve
```

前端不得调用：

```text
真实 webhook URL
bot token endpoint
https://aihot.virxact.com/*
RSSHub base URL
任意 RSS URL
任意 evidence URL 抓取接口
浏览器本地 secret manager
```

## 6. 数据模型

前端类型以 `docs/contracts/eval-observability-api.md` 为唯一来源，至少覆盖：

- `EvalSuite`
- `EvalCase`
- `EvalRun`
- `EvalResult`
- `RegressionFailure`
- `AgentRunTrace`
- `TraceSpan`
- `ToolCallLog`
- `CostRecord`
- `MetricsSnapshot`
- `AlertRule`
- `AlertEvent`
- `ReplayRequest`
- 统一 `Envelope<T>`
- 统一 `ApiError`
- cursor 分页 response

本地 UI 派生状态只允许保存：

- 当前选中 suite / run / trace / alert。
- 当前筛选条件。
- 表单草稿。
- 最近一次 API envelope 的 traceId、warnings、error。

规则：

- 前端不得发明 eval passed 状态。
- 前端不得伪造 cost。
- 前端不得保存明文 secret。

## 7. 状态机

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

UI 规则：

- `regression_failed`、`failed`、`open blocker alert` 必须明显展示。
- 状态变化只来自 API 响应。
- replay 成功不代表原 run 被覆盖。

## 8. Agent 输入输出

M7 前端不运行 Agent，只展示 eval 和 trace 输入输出。

展示输入：

- eval suite / case / fixtureRef。
- agent inputRef。
- replay reason。
- alert conditions。

展示输出：

- eval result assertions。
- regression failure。
- trace spans。
- tool calls。
- metrics snapshot。
- cost records。
- alert events。
- replay request。

规则：

- 前端不得把 trace 或 fixture 内容传给外部模型或工具。
- 前端不得绕过后端直接执行 replay。

## 9. 错误处理

错误码以 `docs/contracts/eval-observability-api.md` 为准。

UI 显示要求：

- 所有错误态展示 `error.message` 和 `meta.traceId`。
- `EVAL_SUITE_NOT_FOUND`：提示 suite 不存在。
- `EVAL_FIXTURE_VERSION_CONFLICT`：提示 fixture 版本不一致。
- `EVAL_RUN_ALREADY_RUNNING`：提示同 suite 正在运行。
- `REGRESSION_FAILED`：提示 required suite 失败。
- `TRACE_NOT_FOUND`：提示 trace 不存在或已过保留期。
- `REPLAY_UNSAFE_SIDE_EFFECT`：提示 replay 被阻止，因为会触发真实副作用。
- `METRIC_RANGE_INVALID`：提示时间窗口非法。
- `GROUNDING_EVIDENCE_MISSING`：提示输出缺 evidence URL。
- `OBSERVABILITY_REDACTION_FAILED`：提示脱敏失败，禁止展示原始内容。

禁止：

- 禁止 unknown id 兜底显示第一条 run。
- 禁止请求失败后伪造空成功态。
- 禁止把 `regression_failed` 显示为 passed。

## 10. 安全和合规边界

- 前端不直连 webhook、bot URL、AI HOT、RSSHub、RSS、evidence URL 抓取接口。
- 不展示真实 webhook URL、bot token、secret、cookie、Authorization header。
- trace / tool call / replay output 只能展示后端已脱敏内容。
- replay 默认 dryRun；M7 v0.1 不提供真实外发 replay UI。
- metrics dashboard 必须标注时间窗口和数据范围。
- cost 显示为 estimated，不写成账单。

## 11. Prompt injection 防护

EvalCase、trace payload、tool output、commentary、evidence 都可能包含外部文本，必须按普通文本处理。

要求：

- 使用 Vue 默认文本插值或等价安全渲染，不使用 `v-html` 渲染外部文本。
- 不解析 trace 文本中的 Markdown 指令、HTML script、工具调用片段或“忽略以上指令”等内容。
- 复制、展开、筛选等 UI 行为只处理文本，不触发工具调用。
- mock 和测试必须包含 prompt injection trace / eval case，断言页面只展示文本。

## 12. Mock 开发

前端 mock 必须覆盖：

- eval suite required / optional。
- eval run queued / running / succeeded / failed / regression_failed。
- eval result passed / failed / skipped。
- regression failure blocker。
- agent run succeeded / failed。
- trace span tree。
- tool call success / failed。
- replay dryRun queued / succeeded / unsafe side effect blocked。
- metrics 24h / 7d / 30d。
- cost record missing token。
- alert open / acknowledged / resolved。
- prompt injection trace 只作为普通文本展示。

mock 写接口必须保留实体 identity：

- trigger eval 后新增 EvalRun。
- acknowledge / resolve 更新对应 AlertEvent。
- replay unsafe side effect 返回 `REPLAY_UNSAFE_SIDE_EFFECT`。
- unknown trace id 返回 `TRACE_NOT_FOUND`。

## 13. 验收标准

- 可查看 metrics overview。
- 可查看 eval suites 和 eval cases。
- 可触发 eval run。
- 可查看 eval run result 和 assertion。
- 可查看 regression failure。
- 可查看 agent run 和 trace span tree。
- 可查看 tool call log。
- 可创建 dryRun replay request。
- 可查看 cost record，且明确 estimated。
- 可管理 alert rule 和 alert event 状态。
- 错误态展示 `error.message` 和 traceId。
- 前端不包含 webhook、bot、AI HOT、RSSHub、RSS 或 evidence URL 直连 fetch。
- 移动端不出现主要内容重叠或横向溢出。
- prompt injection 样本文案只作为普通文本展示，不触发 HTML 渲染或工具调用。

## 14. 测试要求

- API client query string / request body 测试。
- EvalRun status badge 测试。
- EvalResult assertion table 测试。
- RegressionFailure blocker 展示测试。
- TraceViewer span tree 测试。
- ToolCallLog redaction 测试。
- Replay dryRun 表单测试。
- `REPLAY_UNSAFE_SIDE_EFFECT` 展示测试。
- Metrics window 测试。
- Cost estimated 文案测试。
- AlertEvent acknowledge / resolve 测试。
- prompt injection 文本安全渲染测试。

## 15. 设计约束

- 工作台风格，信息密度优先。
- 不做营销式落地页。
- 列表在移动端可降级为卡片。
- 失败、回归、告警必须比装饰更突出。
- 不使用颜色作为唯一状态表达。
- 长 trace、长 error、长 assertion 必须换行或折叠，不造成横向溢出。
- dashboard 数字必须带单位和时间窗口。
- cost 必须标注 estimated。

## 16. 联调边界

- 后端未实现前，前端只使用 mock。
- 后端实现后，先联调 eval suites，再联调 eval runs / results，最后联调 trace / replay / alerts。
- replay 联调默认 dryRun。
- 真实联调不得调用生产 webhook。
- 如果 contract 发现缺口，先更新 `docs/contracts/eval-observability-api.md`，再更新前端和后端。

## 17. 迁移或兼容策略

- M7 前端必须新增 Observability Console，不破坏 M1-M6 页面。
- API client 新增 eval-observability client 模块；不得把 M7 字段混入 M6 admin-rules 类型。
- mock 数据应独立 reset，避免 M7 eval / trace 写状态污染 M1-M6 mock。
- 后端未实现 M7 API 前，前端只能在 mock 模式开发，不伪造真实联调已完成。
- 如果 M7 contract 字段调整，先更新 `docs/contracts/eval-observability-api.md`，再同步类型、mock 和组件。

## 18. 已知风险

- Eval UI 如果只展示汇总会隐藏回归根因，必须提供 assertion detail。
- Trace / replay 有泄密风险，前端只能展示后端脱敏内容。
- Cost 估算容易被误解为账单，必须清晰标注 estimated。
- Prompt injection trace 必须安全渲染。
- mock 写状态必须可 reset，否则测试会相互污染。
