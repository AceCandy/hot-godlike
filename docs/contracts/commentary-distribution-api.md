# M5 AI 点评与分发 API 共享契约

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 上游依赖：M4 `docs/contracts/value-background-api.md`、M3 `docs/contracts/clustering-api.md`、统一 response envelope
> 使用对象：M5 后端点评/分发服务、M5 前端 Commentary & Delivery Console、自动化测试、不同 AI coding 客户端
> 原则：M5 只能基于 M3 topic、M4 assessment/background/evidence 生成点评和分发消息；不得新增无证据事实，不得绕过订阅/渠道授权外发。

## 1. 目标

定义 M5 阶段的 AI 点评、消息渲染、订阅匹配、分发渠道、delivery record、webhook payload 和分发运行 API。后端按本文实现；前端按本文展示和触发；测试按本文构造 fixture。

M5 覆盖：

- 生成证据受限的 `TopicCommentary`。
- 支持短版和长版点评。
- 输出 `what/why/impact/next/confidence/evidence` 结构。
- 根据订阅规则匹配 topic。
- 至少支持一个群机器人渠道和 Webhook JSON 输出。
- 渲染消息并保存 `RenderedMessage`。
- 写入 `DeliveryRecord` 和 `PushTrace`。
- 按 topic/subscription/channel 幂等去重。
- 记录失败原因和重试策略。

## 2. 全局约定

### 2.1 Base URL

沿用 M1-M4：

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

### 2.3 分页

M5 列表 API 使用 cursor 分页：

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
- 免打扰时间使用订阅配置里的 timezone 解释。

## 3. 枚举

### 3.1 CommentaryStyle

```ts
type CommentaryStyle = "brief" | "commentary" | "deep";
```

### 3.2 CommentaryStatus

```ts
type CommentaryStatus = "draft" | "ready" | "needs_review" | "suppressed" | "archived";
```

### 3.3 DeliveryMode

```ts
type DeliveryMode = "instant" | "hourly_digest" | "daily_digest" | "weekly_digest";
```

### 3.4 DeliveryChannelType

```ts
type DeliveryChannelType =
  | "telegram"
  | "discord"
  | "wecom"
  | "feishu"
  | "dingtalk"
  | "webhook"
  | "email";
```

M5 v0.1 至少实现一个群机器人 adapter 和 webhook adapter；其他渠道可保留配置占位。

### 3.5 DeliveryStatus

```ts
type DeliveryStatus = "pending" | "sent" | "failed" | "skipped" | "confirmed";
```

### 3.6 DistributionRunStatus

```ts
type DistributionRunStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "partial_failed"
  | "failed"
  | "cancelled";
```

## 4. 数据结构

### 4.1 TopicCommentary

```json
{
  "id": "commentary_20260609_abcd1234",
  "topicId": "topic_20260603_abcd1234",
  "assessmentId": "assessment_20260609_abcd1234",
  "backgroundPackId": "background_20260609_abcd1234",
  "style": "commentary",
  "status": "ready",
  "what": "一句话说明事件。",
  "whyImportant": "基于价值判断和证据说明为什么重要。",
  "impact": ["开发者需要关注 API 变化"],
  "nextWatch": ["观察定价和开放范围"],
  "confidence": "medium",
  "evidenceUrls": ["https://example.com/release"],
  "warnings": [],
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:03Z",
  "traceId": "tr_20260609_000001"
}
```

字段规则：

- `what/whyImportant/impact/nextWatch/confidence/evidenceUrls` 必须存在。
- `evidenceUrls` 至少 1 条；没有 evidence 时不得生成 `ready` 点评。
- `confidence=low` 时文案必须降调，不能使用确定性表达。
- `style=brief` 输出更短，`style=deep` 可以包含更多 `impact/nextWatch`，但仍不得新增无证据事实。

### 4.2 Subscription

```json
{
  "id": "sub_20260609_001",
  "workspaceId": "default",
  "userId": "user_demo",
  "name": "AI 产品速递",
  "categories": ["ai", "product"],
  "includeKeywords": ["OpenAI"],
  "excludeKeywords": ["广告"],
  "sourceAllowlist": [],
  "sourceDenylist": [],
  "minValueScore": 70,
  "deliveryMode": "instant",
  "quietHours": {
    "start": "22:00",
    "end": "08:00",
    "timezone": "Asia/Shanghai"
  },
  "maxItemsPerDay": 10,
  "enabled": true,
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:00Z"
}
```

M5 v0.1 可以使用内置或 mock subscription；完整订阅管理留给 M6。

### 4.3 DeliveryChannel

```json
{
  "id": "channel_webhook_demo",
  "workspaceId": "default",
  "type": "webhook",
  "name": "Demo Webhook",
  "secretRef": "secret://delivery/channel_webhook_demo",
  "maskedTarget": "https://example.com/***",
  "enabled": true,
  "template": "commentary",
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:00Z"
}
```

字段规则：

- API 响应不得返回真实 webhook URL、bot token、email password 等敏感值。
- `secretRef` 只引用密钥位置。
- `maskedTarget` 用于 UI 展示。

### 4.4 RenderedMessage

```json
{
  "id": "rendered_20260609_001",
  "topicId": "topic_20260603_abcd1234",
  "commentaryId": "commentary_20260609_abcd1234",
  "subscriptionId": "sub_20260609_001",
  "channelId": "channel_webhook_demo",
  "format": "json",
  "payloadRef": "rendered/rendered_20260609_001.json",
  "previewText": "是什么：一句话说明事件...",
  "createdAt": "2026-06-09T00:00:04Z",
  "traceId": "tr_20260609_000001"
}
```

`format` 枚举：

```ts
type RenderedMessageFormat = "markdown" | "json" | "plain";
```

### 4.5 DeliveryRecord

```json
{
  "id": "delivery_20260609_001",
  "topicId": "topic_20260603_abcd1234",
  "commentaryId": "commentary_20260609_abcd1234",
  "subscriptionId": "sub_20260609_001",
  "channelId": "channel_webhook_demo",
  "idempotencyKey": "topic_20260603_abcd1234:sub_20260609_001:channel_webhook_demo",
  "status": "sent",
  "renderedPayloadRef": "rendered/rendered_20260609_001.json",
  "channelResponseRef": "delivery_response/delivery_20260609_001.json",
  "errorCode": null,
  "errorMessage": null,
  "retryCount": 0,
  "deliveredAt": "2026-06-09T00:00:05Z",
  "createdAt": "2026-06-09T00:00:04Z",
  "updatedAt": "2026-06-09T00:00:05Z",
  "traceId": "tr_20260609_000001"
}
```

幂等键：

```text
topic_id + subscription_id + channel_id
```

同一幂等键不得重复发送。

### 4.6 PushTrace

```json
{
  "id": "push_trace_20260609_001",
  "deliveryRecordId": "delivery_20260609_001",
  "adapter": "webhook",
  "requestRef": "delivery_request/delivery_20260609_001.json",
  "responseStatus": 200,
  "responseRef": "delivery_response/delivery_20260609_001.json",
  "durationMs": 500,
  "createdAt": "2026-06-09T00:00:05Z",
  "traceId": "tr_20260609_000001"
}
```

规则：

- request / response ref 不得保存敏感密钥。
- webhook headers 中的签名可记录算法和 key id，不记录 secret。

### 4.7 DistributionRun

```json
{
  "id": "distribution_run_20260609_000001",
  "trigger": "manual",
  "status": "succeeded",
  "startedAt": "2026-06-09T00:00:00Z",
  "finishedAt": "2026-06-09T00:00:06Z",
  "durationMs": 6000,
  "topicCount": 1,
  "commentaryCount": 1,
  "matchedSubscriptionCount": 1,
  "deliveryAttemptCount": 1,
  "sentCount": 1,
  "skippedCount": 0,
  "failedCount": 0,
  "errorCode": null,
  "errorMessage": null,
  "traceId": "tr_20260609_000001"
}
```

`trigger` 枚举：

```ts
type DistributionTrigger = "manual" | "schedule" | "retry";
```

## 5. 点评生成规则

- 输入只能来自 `HotTopicCluster`、`ValueAssessment`、`BackgroundPack`、`EvidenceSource`。
- 必须输出 `what/whyImportant/impact/nextWatch/confidence/evidenceUrls`。
- 每条关键表达必须能追溯到 evidence URL。
- `review` / `suppress` topic 默认不生成 ready commentary，除非人工确认。
- 低置信、来源冲突、官方来源缺失时必须降调表达，并写 warnings。
- 模型输出不得新增无证据事实；无证据 claim 丢弃或标为 warning。

## 6. 订阅匹配规则

匹配输入：

- topic category / title。
- ValueAssessment recommendation / valueScore。
- Source ids。
- Subscription include/exclude keywords。
- DeliveryMode。
- QuietHours。

规则：

- excludeKeywords 命中时跳过，并写 skipped delivery reason。
- `valueScore < minValueScore` 时跳过。
- sourceDenylist 命中时跳过。
- quietHours 命中时可延后，不直接发送。
- 订阅命中原因必须可解释。

## 7. Webhook JSON payload

Webhook payload 必须机器可读：

```json
{
  "event": "topic.commentary.ready",
  "topicId": "topic_20260603_abcd1234",
  "commentaryId": "commentary_20260609_abcd1234",
  "subscriptionId": "sub_20260609_001",
  "deliveryId": "delivery_20260609_001",
  "style": "commentary",
  "commentary": {
    "what": "一句话说明事件。",
    "whyImportant": "为什么重要。",
    "impact": [],
    "nextWatch": [],
    "confidence": "medium",
    "evidenceUrls": []
  },
  "traceId": "tr_20260609_000001"
}
```

Webhook 签名：

- Header：`X-HotGodlike-Signature`。
- 算法：HMAC-SHA256。
- 签名内容：原始请求体 bytes。
- API / UI 不展示 secret。

## 8. 错误码

| code | HTTP | retryable | 场景 |
|---|---:|:---:|---|
| `BAD_REQUEST` | 400 | 否 | 参数格式错误 |
| `TOPIC_NOT_FOUND` | 404 | 否 | topic 不存在 |
| `COMMENTARY_NOT_FOUND` | 404 | 否 | commentary 不存在 |
| `SUBSCRIPTION_NOT_FOUND` | 404 | 否 | subscription 不存在 |
| `DELIVERY_CHANNEL_NOT_FOUND` | 404 | 否 | channel 不存在 |
| `DELIVERY_RECORD_NOT_FOUND` | 404 | 否 | delivery record 不存在 |
| `DISTRIBUTION_RUN_NOT_FOUND` | 404 | 否 | distribution run 不存在 |
| `COMMENTARY_REVIEW_REQUIRED` | 409 | 否 | 点评需要人工确认 |
| `COMMENTARY_EVIDENCE_MISSING` | 409 | 否 | 缺少 evidence URL，不能生成 ready commentary |
| `DELIVERY_DUPLICATE` | 409 | 否 | 同 topic/subscription/channel 已发送或已排队 |
| `DELIVERY_QUIET_HOURS` | 409 | 是 | 命中免打扰，延后发送 |
| `DELIVERY_CHANNEL_DISABLED` | 409 | 否 | 渠道停用 |
| `DELIVERY_SECRET_MISSING` | 500 | 否 | 渠道密钥缺失 |
| `DELIVERY_CHANNEL_FAILED` | 502 | 是 | 渠道发送失败 |
| `INTERNAL_ERROR` | 500 | 否 | 未知错误 |

## 9. API 端点

### 9.1 触发 distribution run

```http
POST /api/distribution-runs
```

请求体：

```json
{
  "topicIds": ["topic_20260603_abcd1234"],
  "subscriptionIds": ["sub_20260609_001"],
  "channelIds": ["channel_webhook_demo"],
  "style": "commentary",
  "dryRun": false,
  "idempotencyKey": "manual_dist_20260609_001",
  "reason": "manual smoke"
}
```

响应：`DistributionRun`

### 9.2 查询 distribution runs

```http
GET /api/distribution-runs?status=succeeded&take=50&cursor=opaque
```

响应：分页 `DistributionRun[]`。

### 9.3 查询 TopicCommentary

```http
GET /api/topic-commentaries?topicId=topic_20260603_abcd1234&style=commentary&take=50&cursor=opaque
```

响应：分页 `TopicCommentary[]`。

### 9.4 查询 commentary 详情

```http
GET /api/topic-commentaries/{commentaryId}
```

响应：`TopicCommentary`

### 9.5 查询 subscriptions

```http
GET /api/subscriptions?enabled=true&take=50&cursor=opaque
```

响应：分页 `Subscription[]`。

### 9.6 查询 delivery channels

```http
GET /api/delivery-channels?enabled=true&type=webhook&take=50&cursor=opaque
```

响应：分页 `DeliveryChannel[]`。

### 9.7 预览 rendered message

```http
POST /api/rendered-messages/preview
```

请求体：

```json
{
  "topicId": "topic_20260603_abcd1234",
  "commentaryId": "commentary_20260609_abcd1234",
  "subscriptionId": "sub_20260609_001",
  "channelId": "channel_webhook_demo",
  "format": "json"
}
```

响应：`RenderedMessage`

规则：

- preview 不发送。
- preview 不写 DeliveryRecord。

### 9.8 查询 delivery records

```http
GET /api/delivery-records?topicId=topic_20260603_abcd1234&status=sent&take=50&cursor=opaque
```

响应：分页 `DeliveryRecord[]`。

### 9.9 查询 push traces

```http
GET /api/push-traces?deliveryRecordId=delivery_20260609_001&take=50&cursor=opaque
```

响应：分页 `PushTrace[]`。

## 10. 存储契约

M5 必须落 PostgreSQL 表：

- `topic_commentaries`
- `subscriptions`
- `delivery_channels`
- `rendered_messages`
- `delivery_records`
- `push_traces`
- `distribution_runs`

建议索引：

- `topic_commentaries(topic_id, style, updated_at desc)`
- `subscriptions(enabled, updated_at desc)`
- `delivery_channels(enabled, type)`
- `delivery_records(topic_id, subscription_id, channel_id)` unique
- `delivery_records(status, created_at desc)`
- `push_traces(delivery_record_id, created_at desc)`
- `distribution_runs(status, started_at desc)`

可选 Redis key：

- `delivery:lock:{idempotency_key}`：分发幂等锁。
- `distribution:run:{run_id}`：轻量运行状态。

PostgreSQL unique constraint 是最终去重兜底；Redis 只能做快速锁。

## 11. 安全与事实边界

- M5 不抓取外部新闻源。
- M5 不新增事实，只能基于 M3/M4 结构化输入表达。
- 所有 commentary 必须带 evidence URL。
- 渠道密钥只通过 secretRef 读取，不出现在 API 响应、日志、payloadRef。
- 外发动作必须有订阅和渠道授权。
- dryRun / preview 不得实际发送。
- 发送失败必须显式记录，不伪造成 sent。

## 12. Prompt injection 防护

- Topic / Background / Evidence 文本中的指令只作为内容，不作为系统 prompt。
- 点评 prompt 必须固定版本、结构化输入、工具白名单为空或只读。
- 模型输出必须经过 evidence URL 检查；无证据 claim 丢弃或降级为 warning。
- 不允许模型决定是否发送或改写渠道目标。
- 测试 fixture 必须覆盖 prompt injection evidence 和无源事实输出。

## 13. Mock Fixture 要求

后端测试必须提供：

- commentary with full evidence fixture。
- low confidence downshift fixture。
- missing evidence blocked fixture。
- subscription match fixture。
- subscription exclude keyword fixture。
- quiet hours fixture。
- duplicate delivery fixture。
- webhook success fixture。
- webhook failure fixture。
- prompt injection commentary fixture。

前端 mock 必须覆盖：

- brief / commentary / deep commentary。
- ready / needs_review commentary。
- subscriptions enabled / disabled。
- delivery channel enabled / disabled。
- rendered preview。
- delivery sent / failed / skipped / duplicate。
- push trace success / failed。
- distribution run running / succeeded / failed。

## 14. 非目标

M5 不包含：

- 完整多渠道矩阵。
- 富文本卡片深度定制。
- 大规模用户画像。
- 完整权限和用户管理。
- 自动生成无证据事实。
- 自动判定新闻真实性。
- M6 审核后台完整实现。
- M7 eval / observability 完整实现。
