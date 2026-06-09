# M5 前端点评与分发 Console 子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/commentary-distribution-api.md`
> 上游依赖：M4 Assessment Console
> 推荐实现客户端：前端 AI coding 客户端
> 技术栈决策：Vue 3 + Vite + Tailwind CSS。

## 1. 目标

实现 M5 阶段的轻量 Commentary & Delivery Console，让管理员或开发者可以查看 AI 点评、预览渲染消息、查看订阅匹配、查看分发渠道、手动触发 distribution run，并检查 delivery history / push trace。

M5 前端不是完整订阅管理后台，不编辑最终审核流程，不直接发送到未授权渠道。

## 2. 范围

### 2.1 In Scope

- TopicCommentary 列表和详情。
- brief / commentary / deep style 展示。
- RenderedMessage preview。
- Subscription 列表只读展示。
- DeliveryChannel 列表只读展示。
- DeliveryRecord 列表。
- PushTrace 列表。
- DistributionRun 列表。
- 手动触发 distribution run。
- 错误态、加载态、空状态。
- 使用 mock API 并行开发。
- 移动端基本适配。

### 2.2 Out of Scope

- 完整订阅编辑。
- 完整渠道密钥配置。
- 完整审核后台。
- 富文本卡片深度编辑。
- 直接调用 webhook / bot URL。
- 直接调用 AI HOT、RSSHub、RSS 或 evidence URL。

## 3. 页面结构

M5 可在 Assessment Console 旁增加“点评分发”入口，也可以在 topic detail 中增加 commentary / delivery tab。

### 3.1 Commentary 列表

展示字段：

- topic title。
- style。
- status。
- confidence。
- evidence count。
- warnings。
- updatedAt。
- 操作：查看详情、预览消息、触发分发。

规则：

- `needs_review` 和 `suppressed` 必须明显展示。
- evidence count 为 0 时不得显示 ready 状态。
- 低 confidence 有降调提示。

### 3.2 Commentary 详情

展示：

- what。
- whyImportant。
- impact。
- nextWatch。
- confidence。
- evidenceUrls。
- warnings。
- traceId。

规则：

- 每条 evidence URL 可点击新窗口打开。
- 不允许隐藏 warnings。
- 不把 commentary 当作已发送状态。

### 3.3 RenderedMessage Preview

展示：

- format。
- previewText。
- payloadRef。
- topic / commentary / subscription / channel 引用。

规则：

- preview 不发送。
- payloadRef 不展示 secret。
- JSON preview 可折叠展示，但不显示密钥。

### 3.4 Subscription 列表

展示字段：

- name。
- categories。
- includeKeywords / excludeKeywords。
- minValueScore。
- deliveryMode。
- quietHours。
- enabled。

规则：

- M5 只读展示，不编辑。
- 命中/跳过原因来自后端，不在前端自行推断。

### 3.5 DeliveryChannel 列表

展示字段：

- type。
- name。
- maskedTarget。
- enabled。
- template。

规则：

- 不展示 secretRef 的真实值。
- disabled channel 不能触发发送。

### 3.6 DeliveryRecord 列表

展示字段：

- topicId。
- subscriptionId。
- channelId。
- status。
- retryCount。
- errorCode / errorMessage。
- deliveredAt。
- traceId。

规则：

- failed / skipped / duplicate 必须明确原因。
- sent 不代表事实已被验证，只代表渠道发送成功。

### 3.7 PushTrace 列表

展示字段：

- adapter。
- responseStatus。
- durationMs。
- requestRef / responseRef。
- createdAt。

规则：

- requestRef / responseRef 不展开敏感字段。
- 不显示 webhook secret。

### 3.8 DistributionRun 面板

展示字段：

- run id。
- trigger。
- status。
- topicCount。
- commentaryCount。
- matchedSubscriptionCount。
- deliveryAttemptCount。
- sentCount。
- skippedCount。
- failedCount。
- errorCode / errorMessage。

行为：

- 可手动触发 distribution run。
- 可选择 style。
- 可选择 dryRun。
- failed / partial_failed 用明显状态展示。
- 手动触发需要 reason。

## 4. 组件建议

- `CommentaryDistributionPage`
- `CommentaryList`
- `CommentaryDetailPanel`
- `RenderedMessagePreview`
- `SubscriptionList`
- `DeliveryChannelList`
- `DeliveryRecordList`
- `PushTraceList`
- `DistributionRunPanel`
- `DeliveryStatusBadge`
- `CommentaryApiStateView`

## 5. API 使用

以 `docs/contracts/commentary-distribution-api.md` 为唯一契约。

前端调用：

```text
POST /api/distribution-runs
GET /api/distribution-runs
GET /api/topic-commentaries
GET /api/topic-commentaries/{commentaryId}
GET /api/subscriptions
GET /api/delivery-channels
POST /api/rendered-messages/preview
GET /api/delivery-records
GET /api/push-traces
```

前端不得调用：

```text
真实 webhook URL
bot token endpoint
https://aihot.virxact.com/*
RSSHub base URL
任意 RSS URL
任意 evidence URL 抓取接口
```

## 6. 数据模型

前端类型以 `docs/contracts/commentary-distribution-api.md` 为唯一来源，至少覆盖：

- `TopicCommentary`
- `Subscription`
- `DeliveryChannel`
- `RenderedMessage`
- `DeliveryRecord`
- `PushTrace`
- `DistributionRun`
- 统一 `Envelope<T>`
- 统一 `ApiError`
- cursor 分页 response

本地 UI 派生状态只允许保存：

- 当前选中 `topicId` / `commentaryId` / `deliveryRecordId`。
- 当前筛选条件。
- 当前 run 表单输入。
- 最近一次 API envelope 的 `traceId`、`warnings`、`error`。

规则：

- 前端不得生成 commentary 文案。
- 前端不得发明后端未返回的 delivery 状态。
- 0 次发送、0 次失败必须显示真实 0，不和未知混淆。

## 7. 状态机

Commentary status：

```text
draft -> ready
draft -> needs_review
ready -> archived
needs_review -> ready
ready -> suppressed
```

Delivery status：

```text
pending -> sent
pending -> failed
pending -> skipped
pending -> confirmed
```

DistributionRun status：

```text
queued -> running -> succeeded
queued -> running -> partial_failed
queued -> running -> failed
queued -> cancelled
```

UI 规则：

- `needs_review`、`suppressed`、`failed`、`skipped`、`partial_failed` 必须有明显状态。
- `preview` 不得显示成 sent。
- 状态变化只来自 API 响应；前端可以做 loading，但成功态必须以返回 envelope 为准。

## 8. Agent 输入输出

M5 前端不运行 Agent，只展示 CommentaryGenerator / Distributor 的输入输出。

展示输入：

- topic 引用。
- assessment / background / evidence 引用。
- subscription / channel 引用。
- distribution run 参数：`topicIds/subscriptionIds/channelIds/style/dryRun/reason`。

展示输出：

- `TopicCommentary`。
- `RenderedMessage`。
- `DeliveryRecord`。
- `PushTrace`。
- `DistributionRun`。

规则：

- 前端不得把 commentary 文本传给外部模型或工具。
- 前端不得绕过后端直接发送消息。
- 后续如增加人工编辑发布，必须进入 M6 contract。

## 9. 错误处理

错误码以 `docs/contracts/commentary-distribution-api.md` 为准。

UI 显示要求：

- 所有错误态展示 `error.message` 和 `meta.traceId`。
- `COMMENTARY_EVIDENCE_MISSING`：提示缺少 evidence，不能生成 ready commentary。
- `COMMENTARY_REVIEW_REQUIRED`：提示需要人工确认。
- `DELIVERY_DUPLICATE`：提示已发送或已排队，不重复发送。
- `DELIVERY_QUIET_HOURS`：提示命中免打扰并延后。
- `DELIVERY_CHANNEL_DISABLED`：提示渠道已停用。
- `DELIVERY_SECRET_MISSING`：提示密钥缺失，但不展示 secret。
- `DELIVERY_CHANNEL_FAILED`：展示失败原因和可重试状态。

禁止：

- 禁止 unknown id 兜底显示第一条 commentary。
- 禁止请求失败后伪造空成功态。
- 禁止把 failed delivery 显示成 sent。

## 10. 安全和合规边界

- 前端不直连 webhook、bot URL、AI HOT、RSSHub、RSS、evidence URL 抓取接口。
- 外部 URL 只作为用户点击打开的链接展示，必须使用新窗口打开。
- 不展示真实 webhook URL、bot token、secretRef 明文。
- dryRun / preview 不能显示为已发送。
- 未有完整权限系统前，distribution trigger 只能用于本地或受控环境。
- 点评不等于事实核验结论。

## 11. Prompt injection 防护

Commentary、evidence summary、channel response 都可能包含外部文本，必须按普通文本处理。

要求：

- 使用 Vue 默认文本插值或等价安全渲染，不使用 `v-html` 渲染 commentary / channel response。
- 不解析 commentary 文本中的 Markdown 指令、HTML script、工具调用片段或“忽略以上指令”等内容。
- 复制、展开、筛选等 UI 行为只处理文本，不触发工具调用。
- mock 和测试必须包含一条带 prompt injection 文案的 commentary，断言页面只展示文本。

## 12. Mock 开发

前端 mock 必须覆盖：

- brief / commentary / deep commentary。
- ready / needs_review / suppressed commentary。
- rendered preview。
- subscription enabled / disabled。
- channel enabled / disabled。
- delivery sent / failed / skipped / duplicate。
- push trace success / failed。
- distribution run running / succeeded / failed。
- prompt injection commentary 只作为普通文本展示。

mock 写接口必须保留实体 identity：

- trigger run 后新增 run。
- rendered preview 不新增 delivery record。
- duplicate delivery 返回 `DELIVERY_DUPLICATE` 或 skipped。
- unknown commentary id 返回 `COMMENTARY_NOT_FOUND`。

## 13. 验收标准

- 可查看 commentary 列表。
- 可查看 commentary 详情。
- 可查看 rendered preview，且 preview 不发送。
- 可查看 subscriptions。
- 可查看 delivery channels，且密钥脱敏。
- 可查看 delivery records。
- 可查看 push traces。
- 可手动触发 distribution run。
- 错误态展示 `error.message` 和 traceId。
- duplicate / failed / skipped 状态明确。
- 前端不包含 webhook、bot、AI HOT、RSSHub、RSS 或 evidence URL 直连 fetch。
- 移动端不出现主要内容重叠或横向溢出。
- prompt injection 样本文案只作为普通文本展示，不触发 HTML 渲染或工具调用。

## 14. 测试要求

- API client query string / request body 测试。
- mock envelope shape 测试。
- Commentary detail 展示测试。
- Rendered preview 不发送测试。
- Delivery status badge 测试。
- duplicate delivery 展示测试。
- delivery failed 展示测试。
- secret masked 展示测试。
- unknown id 错误测试。
- prompt injection 文本安全渲染测试。

## 15. 设计约束

- 工作台风格，信息密度优先。
- 不做营销式落地页。
- 列表在移动端可降级为卡片。
- 状态必须比装饰更突出。
- 不使用颜色作为唯一状态表达。
- 长 URL、长标题、长 commentary 必须换行，不造成横向溢出。
- 不把 sent 写成事实已验证。
- delivery 区域必须展示 trace id 和错误原因。

## 16. 联调边界

- 后端未实现前，前端只使用 mock。
- 后端实现后，先联调 commentaries，再联调 rendered preview，最后联调 fake adapter delivery。
- 真实联调不得调用生产 webhook。
- 如果 contract 发现缺口，先更新 `docs/contracts/commentary-distribution-api.md`，再更新前端和后端。

## 17. 迁移或兼容策略

- M5 前端必须新增 Commentary & Delivery Console，不破坏 M1/M2/M3/M4 页面。
- API client 可新增 commentary-distribution client 模块；不得把 M5 字段混入 M4 value-background 类型。
- mock 数据应独立 reset，避免 M5 delivery 测试污染 M4 assessment mock。
- 后端未实现 M5 API 前，前端只能在 mock 模式开发，不伪造真实联调已完成。
- 如果 M5 contract 字段调整，先更新 `docs/contracts/commentary-distribution-api.md`，再同步类型、mock 和组件。

## 18. 已知风险

- M5 没有完整权限系统，真实生产前不能开放 distribution trigger API 给公网。
- 真实 webhook / bot 发送有外部副作用，测试必须使用 fake adapter。
- 点评可能被误解为事实核验结论，UI 必须展示 evidence 和 confidence。
- prompt injection commentary 必须安全渲染。
- mock 写状态必须可 reset，否则测试会相互污染。
