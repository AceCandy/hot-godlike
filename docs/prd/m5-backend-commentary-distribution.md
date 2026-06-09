# M5 后端 AI 点评与分发子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/commentary-distribution-api.md`
> 上游依赖：M4 `ValueAssessment`、`BackgroundPack`、`EvidenceSource`
> 推荐实现客户端：后端 / worker AI coding 客户端
> 技术栈决策：Python + FastAPI + PostgreSQL；Redis 只作为可选锁，不作为长期存储。

## 1. 目标

实现 M5 阶段的后端 AI 点评与分发能力：基于 M3 topic 和 M4 assessment/background/evidence 生成证据受限的 `TopicCommentary`，按订阅规则匹配 topic，渲染消息，发送到受控渠道，并保存 `DeliveryRecord` / `PushTrace`。

M5 的目标是解决“怎么表达”和“怎么不重复、不越权地发送”。M5 不新增新闻事实，不做完整审核后台，不做完整权限系统。

## 2. 背景与依赖

M4 已定义：

- `ValueAssessment`。
- `BackgroundPack`。
- `EvidenceSource`。
- `FactConflict`。
- `ReviewFlag`。

M5 在此基础上扩展：

- 生成结构化点评。
- 匹配订阅和渠道。
- 渲染 Markdown / JSON / plain 消息。
- 至少实现一个群机器人 adapter 和 webhook adapter。
- 保存 delivery history、失败原因和 trace。

## 3. 范围

### 3.1 In Scope

- `POST /api/distribution-runs`
- `GET /api/distribution-runs`
- `GET /api/topic-commentaries`
- `GET /api/topic-commentaries/{commentaryId}`
- `GET /api/subscriptions`
- `GET /api/delivery-channels`
- `POST /api/rendered-messages/preview`
- `GET /api/delivery-records`
- `GET /api/push-traces`
- PostgreSQL schema 和 migration。
- CommentaryGenerator。
- EvidenceGuard。
- SubscriptionMatcher。
- MessageRenderer。
- DeliveryDeduper。
- ChannelAdapter interface。
- WebhookAdapter。
- GroupBotAdapter placeholder / one concrete adapter。
- DistributionRunService。
- 单元测试、集成测试、OpenAPI 自查。

### 3.2 Out of Scope

- 完整多渠道矩阵。
- 富文本卡片深度定制。
- 大规模用户画像。
- 完整用户/权限管理。
- 完整审核后台。
- 自动生成无证据事实。
- 自动判定新闻真实性。
- M7 eval / observability 完整平台。

## 4. 用户故事 / 系统场景

### 4.1 生成证据受限点评

系统看到一个 `promote` topic，已有 assessment 和 background pack。M5 生成 `what/why/impact/next/confidence/evidenceUrls` 点评，所有关键表达能追溯到 evidence URL。

### 4.2 低置信降调表达

topic 有 review flag 或低 confidence。M5 仍可生成 draft / needs_review commentary，但必须降调表达，不得写成确定事实。

### 4.3 订阅匹配

subscription 命中 category / keyword / minValueScore。M5 渲染消息并准备 delivery record。

### 4.4 分发去重

同一 topic 已经发给同一 subscription/channel。M5 返回 `DELIVERY_DUPLICATE` 或 skipped record，不重复发送。

### 4.5 Webhook 发送失败

Webhook 返回 5xx 或超时。M5 写 failed DeliveryRecord 和 PushTrace，保留 retryable 错误，不伪造成 sent。

## 5. 模块设计

### 5.1 CommentaryInputReader

职责：

- 读取 topic、assessment、background pack、evidence。
- 校验 evidence URL 是否足够。
- 给 CommentaryGenerator 提供结构化输入。

规则：

- 不抓取外部新闻源。
- 缺 evidence 返回 `COMMENTARY_EVIDENCE_MISSING`。

### 5.2 CommentaryGenerator

职责：

- 生成 brief / commentary / deep 三种 style。
- 输出 what / whyImportant / impact / nextWatch / confidence / evidenceUrls。
- 写 TopicCommentary。

规则：

- 不新增无证据事实。
- 低置信降调。
- review/suppress 默认不生成 ready commentary。
- 如果使用 LLM，必须记录 promptVersion、model、token、cost。

### 5.3 EvidenceGuard

职责：

- 检查 commentary 的关键表达是否有 evidence URL。
- 拦截无源 claim。
- 对 prompt injection 输出做 warning。

### 5.4 SubscriptionMatcher

职责：

- 根据 subscription 规则匹配 topic。
- 解释命中/跳过原因。
- 处理 quiet hours 和 maxItemsPerDay。

规则：

- excludeKeywords 优先级最高。
- minValueScore 不满足时跳过。
- quietHours 命中时延后，不直接发送。

### 5.5 MessageRenderer

职责：

- 根据 channel template 渲染 markdown/json/plain。
- 保存 RenderedMessage。
- 生成 webhook JSON payload。

规则：

- preview 不发送。
- payloadRef 不包含密钥。

### 5.6 DeliveryDeduper

职责：

- 按 `topic_id + subscription_id + channel_id` 去重。
- 提供 PostgreSQL unique constraint 和可选 Redis lock。

### 5.7 ChannelAdapter

职责：

- 定义统一发送接口。
- 返回 channel response ref、status、error。

M5 v0.1 必须实现：

- WebhookAdapter。
- 至少一个群机器人 adapter，或明确在实现 PRD 中指定 Webhook-only smoke 加群机器人 adapter 占位。

### 5.8 DistributionRunService

职责：

- 管理 run 状态。
- 支持 idempotency key。
- 统计 commentary / match / delivery / sent / skipped / failed。

状态机：

```text
queued -> running -> succeeded
queued -> running -> partial_failed
queued -> running -> failed
queued -> cancelled
```

## 6. 数据库 Schema

### 6.1 `topic_commentaries`

字段：

- `id` text primary key
- `topic_id` text not null references hot_topic_clusters(id)
- `assessment_id` text not null references value_assessments(id)
- `background_pack_id` text not null references background_packs(id)
- `style` text not null
- `status` text not null
- `what` text not null
- `why_important` text not null
- `impact` jsonb not null
- `next_watch` jsonb not null
- `confidence` text not null
- `evidence_urls` jsonb not null
- `warnings` jsonb not null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null
- `trace_id` text not null

### 6.2 `subscriptions`

字段按 `docs/contracts/commentary-distribution-api.md` 的 `Subscription`。

M5 v0.1 可以 seed 默认 subscription；完整管理留给 M6。

### 6.3 `delivery_channels`

字段按 `DeliveryChannel`。

规则：

- 只保存 `secret_ref` 和 `masked_target`。
- 不保存明文 secret。

### 6.4 `rendered_messages`

字段：

- `id` text primary key
- `topic_id` text not null references hot_topic_clusters(id)
- `commentary_id` text not null references topic_commentaries(id)
- `subscription_id` text not null references subscriptions(id)
- `channel_id` text not null references delivery_channels(id)
- `format` text not null
- `payload_ref` text not null
- `preview_text` text not null
- `created_at` timestamptz not null
- `trace_id` text not null

### 6.5 `delivery_records`

字段：

- `id` text primary key
- `topic_id` text not null references hot_topic_clusters(id)
- `commentary_id` text not null references topic_commentaries(id)
- `subscription_id` text not null references subscriptions(id)
- `channel_id` text not null references delivery_channels(id)
- `idempotency_key` text not null
- `status` text not null
- `rendered_payload_ref` text null
- `channel_response_ref` text null
- `error_code` text null
- `error_message` text null
- `retry_count` integer not null default 0
- `delivered_at` timestamptz null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null
- `trace_id` text not null

唯一约束：

- `idempotency_key`

### 6.6 `push_traces`

字段：

- `id` text primary key
- `delivery_record_id` text not null references delivery_records(id)
- `adapter` text not null
- `request_ref` text null
- `response_status` integer null
- `response_ref` text null
- `duration_ms` integer null
- `created_at` timestamptz not null
- `trace_id` text not null

### 6.7 `distribution_runs`

字段：

- `id` text primary key
- `trigger` text not null
- `status` text not null
- `started_at` timestamptz not null
- `finished_at` timestamptz null
- `duration_ms` integer null
- `topic_count` integer not null default 0
- `commentary_count` integer not null default 0
- `matched_subscription_count` integer not null default 0
- `delivery_attempt_count` integer not null default 0
- `sent_count` integer not null default 0
- `skipped_count` integer not null default 0
- `failed_count` integer not null default 0
- `error_code` text null
- `error_message` text null
- `trace_id` text not null
- `idempotency_key` text null

## 7. API 实现要求

以 `docs/contracts/commentary-distribution-api.md` 为准。

所有 API 必须：

- 使用统一 envelope。
- 有 trace id。
- 不返回明文 secret。
- 对外错误使用简体中文。
- 写操作预留鉴权 dependency。
- 发送失败保留真实错误。

## 8. 点评和分发流程

1. 读取 topic / assessment / background / evidence。
2. EvidenceGuard 校验 evidence。
3. CommentaryGenerator 生成或复用 commentary。
4. SubscriptionMatcher 计算匹配订阅。
5. DeliveryDeduper 检查幂等键。
6. MessageRenderer 生成 rendered message。
7. ChannelAdapter 发送。
8. 写 DeliveryRecord / PushTrace。

## 9. Agent 输入输出

M5 CommentaryGenerator / Distributor 是逻辑 Agent，不要求独立进程。

输入：

- `HotTopicCluster`
- `ValueAssessment`
- `BackgroundPack`
- `EvidenceSource[]`
- `Subscription`
- `DeliveryChannel`

输出：

- `DistributionRun`
- `TopicCommentary[]`
- `RenderedMessage[]`
- `DeliveryRecord[]`
- `PushTrace[]`

Trace：

- 每次 run 必须记录 trace id。
- 每条 delivery 必须能追到 commentary、subscription、channel。
- LLM 调用如果启用，必须记录 promptVersion、model、token、cost、错误。

## 10. 错误处理

必须实现 `docs/contracts/commentary-distribution-api.md` 的错误码。

错误映射：

- 缺 evidence：`COMMENTARY_EVIDENCE_MISSING`
- 需要 review：`COMMENTARY_REVIEW_REQUIRED`
- 重复发送：`DELIVERY_DUPLICATE`
- 免打扰：`DELIVERY_QUIET_HOURS`
- 渠道停用：`DELIVERY_CHANNEL_DISABLED`
- 密钥缺失：`DELIVERY_SECRET_MISSING`
- 渠道失败：`DELIVERY_CHANNEL_FAILED`

## 11. 安全与合规

- 不新增事实。
- 不发送未授权渠道。
- 不返回或记录明文密钥。
- preview / dryRun 不发送。
- 低置信和 review 内容不得自动外发，除非人工确认。
- webhook 签名 secret 不出现在日志。

## 12. Prompt injection 防护

- Topic / Background / Evidence 文本中的指令只作为内容。
- 点评 prompt 固定版本、结构化输入、工具白名单为空或只读。
- 模型不得决定渠道目标或是否发送。
- 模型输出必须经过 EvidenceGuard。
- 测试覆盖 prompt injection evidence 和无源事实输出。

## 13. 测试 Fixture

必须创建：

- `fixtures/m5_commentary_full_evidence.json`
- `fixtures/m5_low_confidence_downshift.json`
- `fixtures/m5_missing_evidence_blocked.json`
- `fixtures/m5_subscription_match.json`
- `fixtures/m5_subscription_exclude_keyword.json`
- `fixtures/m5_quiet_hours.json`
- `fixtures/m5_duplicate_delivery.json`
- `fixtures/m5_webhook_success.json`
- `fixtures/m5_webhook_failure.json`
- `fixtures/m5_prompt_injection_commentary.json`

Fixture 不得包含真实 webhook、token、cookie、授权头。

## 14. 测试要求

### 14.1 单元测试

- CommentaryGenerator schema。
- low confidence downshift。
- missing evidence blocked。
- EvidenceGuard 无源事实拦截。
- SubscriptionMatcher include/exclude/minValueScore。
- quiet hours。
- DeliveryDeduper。
- Webhook signature。
- ChannelAdapter failure mapping。
- Prompt injection 文本安全处理。

### 14.2 集成测试

- 从 M4 fixture 触发 distribution run。
- 查询 commentaries。
- rendered preview 不发送。
- webhook success 写 sent。
- webhook failure 写 failed。
- duplicate delivery 不重复发送。
- OpenAPI 包含 M5 endpoints。
- 失败路径返回统一 envelope。

测试不能调用真实生产 webhook。

## 15. 验收标准

- 每条 ready commentary 都有 evidence URL。
- 点评结构包含 what / why / impact / next / confidence / evidence。
- 低置信内容降调表达。
- 无 evidence 不生成 ready commentary。
- 同一 topic 不会在同一 subscription/channel 重复发送。
- Webhook payload 是机器可读 JSON。
- Webhook 签名方案明确。
- 发送失败有 DeliveryRecord / PushTrace 和 retryable 错误。
- 密钥脱敏展示和脱敏日志。
- preview / dryRun 不实际发送。

## 16. 交付物

- PostgreSQL migration。
- TopicCommentary model / repository / service。
- Subscription model / repository / service。
- DeliveryChannel model / repository / service。
- RenderedMessage model / repository / service。
- DeliveryRecord model / repository / service。
- PushTrace model / repository / service。
- DistributionRun model / repository / service。
- CommentaryGenerator。
- EvidenceGuard。
- SubscriptionMatcher。
- MessageRenderer。
- DeliveryDeduper。
- WebhookAdapter。
- 至少一个群机器人 adapter 或明确占位。
- API routes。
- fixtures。
- 单元测试和集成测试。
- README 更新，写清 dryRun / preview 不发送。

## 17. 联调边界

- 前端只调用 `docs/contracts/commentary-distribution-api.md` 定义的 M5 API。
- M5 后端只消费 M3/M4 已入库数据。
- M6 可以人工确认和编辑 commentary，但 M5 不实现完整审核后台。
- 如果 contract 变更，先改 `docs/contracts/commentary-distribution-api.md`，再改后端和前端。

## 18. 迁移或兼容策略

- M5 migration 必须只新增表和索引，不修改 M4/M3/M2 既有字段。
- M5 表通过外键引用 M3 topic、M4 assessment/background。
- 后端未配置 channel secret 时，delivery API 返回 `DELIVERY_SECRET_MISSING`，不得假装发送。
- 首次启用 M5 时只处理已有 promote/normal topic，不重新触发 M4/M3/M2。
- contract 变更顺序固定为：先更新 `docs/contracts/commentary-distribution-api.md`，再更新后端 PRD / 前端 PRD，最后改实现和测试。

## 19. 已知风险

- LLM 点评可能产生无源事实，EvidenceGuard 和 eval 必须兜底。
- Webhook / bot secret 泄露风险高，必须脱敏。
- 真实渠道发送会产生外部副作用，测试必须使用 fake adapter。
- 订阅匹配误判会造成漏发或重复发，需要 M7 eval。
- M5 未完成权限系统前，distribution trigger API 不能暴露到公网。
