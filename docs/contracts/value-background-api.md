# M4 价值判断与背景补全 API 共享契约

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 上游依赖：M3 `docs/contracts/clustering-api.md`、统一 response envelope
> 使用对象：M4 后端价值判断/背景补全服务、M4 前端 Assessment Console、自动化测试、不同 AI coding 客户端
> 原则：M4 只消费 M3 `HotTopicCluster` / `TopicMember` / `TrendSnapshot` 和 M2 source trust；不生成最终 AI 点评，不做分发，不自动判定新闻真伪。

## 1. 目标

定义 M4 阶段的价值判断、背景补全、证据、来源冲突、review flag 和运行记录 API。后端按本文实现；前端按本文展示和触发；测试按本文构造 fixture。任何实现不得把无证据推断写成事实，不得把背景补全失败伪造成成功。

M4 覆盖：

- 对 topic 做可解释分项评分。
- 输出 `promote` / `normal` / `suppress` / `review` 建议。
- 为高价值、高传播、高风险 topic 生成背景包。
- 记录官方来源、关联来源、历史背景、官方声明、未解决问题。
- 标注来源冲突和低置信原因。
- 生成 review flags，供 M6 审核后台继续处理。
- 保存 assessment / background run、错误、trace。

## 2. 全局约定

### 2.1 Base URL

沿用 M1-M3：

```text
http://localhost:8000/api
```

### 2.2 响应 envelope

所有 API 仍使用统一 envelope：

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

失败响应：

```json
{
  "data": null,
  "meta": {
    "traceId": "tr_20260609_000001",
    "source": "hot-godlike",
    "cached": false,
    "query": {},
    "warnings": []
  },
  "error": {
    "code": "ASSESSMENT_NOT_FOUND",
    "message": "价值判断结果不存在。",
    "details": {
      "assessmentId": "assessment_20260609_abcd1234"
    },
    "retryable": false
  }
}
```

### 2.3 分页

M4 列表 API 使用 cursor 分页：

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
- 背景补全的外部 evidence 抓取时间必须写入 `capturedAt`。

## 3. 枚举

### 3.1 AssessmentRecommendation

```ts
type AssessmentRecommendation = "promote" | "normal" | "suppress" | "review";
```

说明：

- `promote`：建议进入精选或后续点评候选。
- `normal`：保留普通展示，不主动提升。
- `suppress`：建议压制，不主动推送；不得删除 topic / raw item。
- `review`：需要人工审核。

### 3.2 AssessmentStatus

```ts
type AssessmentStatus = "draft" | "assessed" | "needs_review" | "suppressed" | "archived";
```

### 3.3 EvidenceType

```ts
type EvidenceType =
  | "original_source"
  | "official_statement"
  | "related_report"
  | "technical_doc"
  | "historical_context"
  | "community_discussion"
  | "unknown";
```

### 3.4 EvidenceTrust

```ts
type EvidenceTrust = "high" | "medium" | "low" | "unknown";
```

### 3.5 ReviewFlagType

```ts
type ReviewFlagType =
  | "high_impact_low_confidence"
  | "source_conflict"
  | "possible_marketing"
  | "possible_sensitive"
  | "missing_official_source"
  | "background_fetch_failed"
  | "manual_review_requested";
```

### 3.6 AssessmentRunStatus

```ts
type AssessmentRunStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "partial_failed"
  | "failed"
  | "cancelled";
```

## 4. 数据结构

### 4.1 ValueAssessment

```json
{
  "id": "assessment_20260609_abcd1234",
  "topicId": "topic_20260603_abcd1234",
  "status": "assessed",
  "recommendation": "promote",
  "valueScore": 82,
  "confidence": "medium",
  "importance": 90,
  "freshness": 80,
  "credibility": 75,
  "propagation": 70,
  "userRelevance": 85,
  "noiseRisk": 20,
  "reasons": ["官方来源明确", "多源报道", "对产品路线影响较大"],
  "downrankReasons": [],
  "reviewFlagIds": [],
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:02Z",
  "traceId": "tr_20260609_000001"
}
```

字段规则：

- `valueScore/importance/freshness/credibility/propagation/userRelevance/noiseRisk` 范围 0-100。
- `valueScore` 必须由分项分和权重计算，不能手写孤立总分。
- `reasons` 必须至少 1 条。
- `noiseRisk` 越高代表噪音越大；计算总分时应反向扣分。
- `confidence=low` 且 `importance` 高时，recommendation 必须为 `review`。

### 4.2 AssessmentPolicy

```json
{
  "id": "policy_default",
  "name": "Default M4 policy",
  "weights": {
    "importance": 0.25,
    "freshness": 0.15,
    "credibility": 0.2,
    "propagation": 0.15,
    "userRelevance": 0.15,
    "noiseRisk": -0.1
  },
  "thresholds": {
    "promote": 75,
    "normal": 45,
    "suppress": 25,
    "reviewConfidenceBelow": "medium"
  },
  "maxEvidenceUrls": 8,
  "maxHistoricalEvents": 5,
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:00Z"
}
```

M4 v0.1 可以先使用内置默认 policy；后续 M6 再做完整后台配置。

### 4.3 EvidenceSource

```json
{
  "id": "evidence_20260609_001",
  "topicId": "topic_20260603_abcd1234",
  "type": "official_statement",
  "trust": "high",
  "title": "Official model release note",
  "url": "https://example.com/release",
  "sourceId": "src_official_blog",
  "capturedAt": "2026-06-09T00:00:03Z",
  "summary": "官方发布说明摘要。",
  "fetchStatus": "succeeded",
  "failureReason": null
}
```

字段规则：

- `url` 必须为证据 URL，不能是无来源事实。
- `summary` 是证据摘要，不是最终 AI 点评。
- `fetchStatus=failed` 时必须写 `failureReason`。
- 官方来源缺失时不得伪造，应由 `BackgroundPack.officialSourceStatus` 标记。

### 4.4 BackgroundPack

```json
{
  "id": "background_20260609_abcd1234",
  "topicId": "topic_20260603_abcd1234",
  "status": "completed",
  "officialSourceStatus": "found",
  "originalSources": ["evidence_20260609_001"],
  "relatedSources": ["evidence_20260609_002"],
  "historicalContext": [
    {
      "title": "同产品上一版本发布",
      "url": "https://example.com/history",
      "occurredAt": "2026-05-01T00:00:00Z",
      "summary": "历史背景摘要。"
    }
  ],
  "officialStatements": ["evidence_20260609_001"],
  "unresolvedQuestions": ["定价细节尚未公布"],
  "conflictIds": [],
  "createdAt": "2026-06-09T00:00:03Z",
  "updatedAt": "2026-06-09T00:00:08Z",
  "traceId": "tr_20260609_000001"
}
```

`officialSourceStatus` 枚举：

```ts
type OfficialSourceStatus = "found" | "not_found" | "not_required" | "fetch_failed";
```

`status` 枚举：

```ts
type BackgroundStatus = "pending" | "completed" | "partial" | "failed";
```

### 4.5 FactConflict

```json
{
  "id": "conflict_20260609_001",
  "topicId": "topic_20260603_abcd1234",
  "claim": "发布时间存在冲突",
  "evidenceIds": ["evidence_20260609_001", "evidence_20260609_002"],
  "severity": "medium",
  "resolution": "unresolved",
  "createdAt": "2026-06-09T00:00:08Z"
}
```

规则：

- M4 只标注冲突，不擅自裁决事实真伪。
- `resolution=unresolved` 时必须生成 review flag。

### 4.6 ReviewFlag

```json
{
  "id": "review_20260609_001",
  "topicId": "topic_20260603_abcd1234",
  "assessmentId": "assessment_20260609_abcd1234",
  "type": "high_impact_low_confidence",
  "severity": "high",
  "reason": "影响较高但官方来源缺失。",
  "status": "open",
  "createdAt": "2026-06-09T00:00:08Z",
  "resolvedAt": null
}
```

`status` 枚举：

```ts
type ReviewFlagStatus = "open" | "resolved" | "dismissed";
```

### 4.7 AssessmentRun

```json
{
  "id": "assessment_run_20260609_000001",
  "trigger": "manual",
  "status": "succeeded",
  "startedAt": "2026-06-09T00:00:00Z",
  "finishedAt": "2026-06-09T00:00:09Z",
  "durationMs": 9000,
  "topicCount": 1,
  "assessedCount": 1,
  "backgroundPackCount": 1,
  "reviewFlagCount": 0,
  "errorCode": null,
  "errorMessage": null,
  "traceId": "tr_20260609_000001"
}
```

`trigger` 枚举：

```ts
type AssessmentTrigger = "manual" | "schedule" | "retry";
```

## 5. 评分规则

### 5.1 默认权重

默认权重以 `AssessmentPolicy` 为准：

- importance：0.25。
- freshness：0.15。
- credibility：0.20。
- propagation：0.15。
- userRelevance：0.15。
- noiseRisk：-0.10。

总分计算：

```text
valueScore = weighted_sum(importance, freshness, credibility, propagation, userRelevance, noiseRisk)
```

规则：

- 总分必须 clamp 到 0-100。
- 输出必须保留分项分和 reasons。
- 不允许只返回总分。

### 5.2 recommendation 阈值

- `valueScore >= 75` 且无 open high review flag：`promote`。
- `45 <= valueScore < 75`：`normal`。
- `valueScore < 25` 或命中明确噪音：`suppress`。
- 高影响低置信、来源冲突、疑似敏感、官方来源缺失但影响高：`review`。

### 5.3 背景补全触发

满足任一条件时触发背景补全：

- `recommendation=promote`。
- `recommendation=review`。
- `importance >= 80`。
- `propagation >= 75`。
- 用户或管理员手动请求。

## 6. 背景补全规则

- 默认最多处理 8 个 evidence URL。
- 单个 topic 最多记录 5 条历史背景。
- 官方博客、论文、公告、GitHub release、监管文件优先级最高。
- 二手媒体可作为关联来源，不单独支撑关键事实。
- 未找到官方来源时必须写 `officialSourceStatus=not_found` 并生成 review flag 或 warning。
- 背景抓取失败时写 `EvidenceSource.fetchStatus=failed` 和 failure reason，不补写事实。
- 来源冲突写 `FactConflict`，不由 AI 擅自裁决。

## 7. 错误码

| code | HTTP | retryable | 场景 |
|---|---:|:---:|---|
| `BAD_REQUEST` | 400 | 否 | 参数格式错误 |
| `TOPIC_NOT_FOUND` | 404 | 否 | M3 topic 不存在 |
| `ASSESSMENT_NOT_FOUND` | 404 | 否 | assessment 不存在 |
| `BACKGROUND_PACK_NOT_FOUND` | 404 | 否 | background pack 不存在 |
| `EVIDENCE_NOT_FOUND` | 404 | 否 | evidence source 不存在 |
| `ASSESSMENT_RUN_NOT_FOUND` | 404 | 否 | assessment run 不存在 |
| `ASSESSMENT_POLICY_INVALID` | 400 | 否 | 权重、阈值或规则非法 |
| `BACKGROUND_FETCH_BLOCKED` | 400 | 否 | evidence URL 被 SSRF / 合规策略拦截 |
| `BACKGROUND_FETCH_FAILED` | 502 | 是 | evidence URL 抓取失败 |
| `BACKGROUND_SOURCE_CONFLICT` | 409 | 否 | 来源冲突需要 review |
| `ASSESSMENT_REVIEW_REQUIRED` | 409 | 否 | 需要人工确认 |
| `INTERNAL_ERROR` | 500 | 否 | 未知错误 |

## 8. API 端点

### 8.1 触发 assessment run

```http
POST /api/assessment-runs
```

请求体：

```json
{
  "topicIds": ["topic_20260603_abcd1234"],
  "since": "2026-06-09T00:00:00Z",
  "take": 100,
  "includeBackground": true,
  "dryRun": false,
  "idempotencyKey": "manual_assess_20260609_001",
  "reason": "manual smoke"
}
```

响应：`AssessmentRun`

规则：

- `topicIds` 和 `since` 至少传一个。
- `take` 范围 1-200。
- `dryRun=true` 不写 assessment/background/evidence/review flag。
- 同一 `idempotencyKey` 重复请求返回同一个或等价 run。

### 8.2 查询 assessment runs

```http
GET /api/assessment-runs?status=succeeded&take=50&cursor=opaque
```

响应：分页 `AssessmentRun[]`。

### 8.3 查询 assessment run 详情

```http
GET /api/assessment-runs/{runId}
```

响应：`AssessmentRun`

### 8.4 查询 value assessments

```http
GET /api/value-assessments?topicId=topic_20260603_abcd1234&recommendation=review&take=50&cursor=opaque
```

响应：分页 `ValueAssessment[]`。

### 8.5 查询 topic 最新 assessment

```http
GET /api/topics/{topicId}/assessment
```

响应：

```json
{
  "assessment": {},
  "backgroundPack": {},
  "reviewFlags": [],
  "factConflicts": []
}
```

### 8.6 查询 background packs

```http
GET /api/background-packs?topicId=topic_20260603_abcd1234&status=completed&take=50&cursor=opaque
```

响应：分页 `BackgroundPack[]`。

### 8.7 查询 background pack 详情

```http
GET /api/background-packs/{backgroundPackId}
```

响应：

```json
{
  "backgroundPack": {},
  "evidenceSources": [],
  "factConflicts": []
}
```

### 8.8 查询 evidence sources

```http
GET /api/evidence-sources?topicId=topic_20260603_abcd1234&type=official_statement&take=50&cursor=opaque
```

响应：分页 `EvidenceSource[]`。

### 8.9 查询 review flags

```http
GET /api/review-flags?topicId=topic_20260603_abcd1234&status=open&take=50&cursor=opaque
```

响应：分页 `ReviewFlag[]`。

### 8.10 查询 fact conflicts

```http
GET /api/fact-conflicts?topicId=topic_20260603_abcd1234&take=50&cursor=opaque
```

响应：分页 `FactConflict[]`。

## 9. 存储契约

M4 必须落 PostgreSQL 表：

- `value_assessments`
- `assessment_policies`
- `background_packs`
- `evidence_sources`
- `fact_conflicts`
- `review_flags`
- `assessment_runs`

建议索引：

- `value_assessments(topic_id, updated_at desc)`
- `value_assessments(recommendation, updated_at desc)`
- `background_packs(topic_id, updated_at desc)`
- `evidence_sources(topic_id, type)`
- `review_flags(status, severity, created_at desc)`
- `fact_conflicts(topic_id, created_at desc)`
- `assessment_runs(status, started_at desc)`

可选 Redis key：

- `assessment:lock:run`：assessment run 全局锁。
- `topic:assessment:lock:{topic_id}`：单 topic assessment 互斥锁。

PostgreSQL 是最终事实源；Redis 只能做锁和短期运行状态。

## 10. 安全与事实边界

- M4 可以按受控规则抓取 evidence URL，但必须通过 SSRFGuard、timeout、User-Agent 和错误映射。
- M4 不新增采集 source，不绕过登录、付费墙、robots.txt、ToS 或平台限制。
- 外部网页内容按不可信输入处理，不作为系统 prompt 或工具指令。
- 背景补全失败必须显式记录，不得补写事实。
- 来源冲突必须标注，不由 AI 擅自裁决。
- LLM 如用于摘要或分类，只能基于 evidence 文本生成结构化摘要，不得新增无证据事实。
- 低置信内容不能进入确定性表达链路。

## 11. Prompt injection 防护

- Evidence HTML / Markdown / 文本中的指令只作为内容，不执行。
- 不把 evidence 原文拼接为系统 prompt；如果需要模型处理，必须使用固定 prompt version、工具白名单和结构化输入。
- 模型输出必须绑定 evidence URL；没有 evidence 支撑的 claim 丢弃或标为 unresolved。
- 测试 fixture 必须包含带 prompt injection 文案的 evidence，断言系统只记录文本和 warning。
- 外部内容不得触发新工具调用、网络请求、文件读写或密钥输出。

## 12. Mock Fixture 要求

后端测试必须提供：

- high value official source fixture。
- low credibility marketing fixture。
- high impact low confidence fixture。
- missing official source fixture。
- source conflict fixture。
- background fetch failed fixture。
- prompt injection evidence fixture。

前端 mock 必须覆盖：

- promote / normal / suppress / review assessment。
- completed / partial / failed background pack。
- official source found / not found。
- review flag open / resolved。
- fact conflict unresolved。
- assessment run running / succeeded / failed。

## 13. 非目标

M4 不包含：

- 最终 AI 点评生成。
- 分发推送。
- 完整审核后台。
- 订阅规则管理。
- 自动判定新闻真实性。
- 绕过外部站点限制。
- 大规模网页爬虫。
- M5/M6/M7 的权限、推送、eval 和可观测完整实现。
