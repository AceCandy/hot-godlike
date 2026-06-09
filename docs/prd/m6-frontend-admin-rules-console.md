# M6 前端管理后台与规则 Console 子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/admin-rules-api.md`
> 上游依赖：M2 Source Console、M3 Topic Console、M4 Assessment Console、M5 Commentary & Delivery Console
> 推荐实现客户端：前端 AI coding 客户端
> 技术栈决策：Vue 3 + Vite + Tailwind CSS。

## 1. 目标

实现 M6 阶段的 Admin Console，让管理员、审核员和运营人员能在一个工作台中查看 source、raw item、topic、assessment、background、commentary、subscription、channel、review queue、rule set、rerun request 和 audit log，并执行受权限控制的人工动作。

M6 前端不是营销页，不直接连接外部 webhook / bot / RSSHub / RSS / AI HOT，也不在浏览器保存或展示明文密钥。

## 2. 范围

### 2.1 In Scope

- 登录态检查和当前用户权限展示。
- 管理台壳层导航。
- Review Queue 列表和详情。
- Topic detail 工作区入口，聚合 M3-M5 只读信息。
- ReviewDecision 表单：approve / suppress / request changes / edit commentary / merge / split / rerun。
- AdminRuleSet 列表、详情、创建、编辑、暂停、归档和 preview。
- Subscription 管理表单。
- DeliveryChannel 管理表单。
- Channel secret 写入表单。
- Channel test dryRun / fake adapter 触发。
- RerunRequest 列表和详情。
- AuditLog 列表和资源详情页嵌入。
- User / Role 基础管理。
- 错误态、加载态、空状态。
- mock API 并行开发。
- 移动端基本适配。

### 2.2 Out of Scope

- 复杂 SSO 登录页。
- 生产级账户找回。
- 高级 BI 报表。
- 富文本卡片深度编辑器。
- 直接调用真实 webhook / bot URL。
- 直接调用 AI HOT、RSSHub、RSS 或 evidence URL 抓取接口。
- 在前端存储明文 secret、token、cookie。

## 3. 页面结构

### 3.1 Admin Shell

导航分区：

- Review。
- Topics。
- Sources。
- Rules。
- Subscriptions。
- Channels。
- Reruns。
- Audit。
- Users。

规则：

- 根据 `CurrentPrincipal.permissions` 隐藏不可用写入口。
- 禁止前端仅靠隐藏按钮做权限控制；后端仍必须返回 `FORBIDDEN`。
- 当前用户、角色和权限必须可查看。

### 3.2 Review Queue

展示字段：

- topic title。
- status。
- priority。
- reasons。
- assignedTo。
- updatedAt。
- traceId。

操作：

- 查看详情。
- approve。
- suppress。
- request changes。
- edit commentary。
- merge / split。
- rerun assessment / background / commentary。

规则：

- 所有写操作必须填写 reason。
- destructive / external side-effect 操作必须确认。
- 状态变化以 API envelope 为准，不做乐观成功。

### 3.3 Topic Detail 工作区

展示：

- M3 topic 和 members。
- M4 assessment、background pack、evidence、review flags。
- M5 commentary、rendered preview、delivery records。
- review decisions。
- audit logs。

规则：

- 不重新计算评分或点评。
- evidence URL 只作为可点击外链展示，不抓取。
- commentary edit 必须保留 evidence 区域和 warnings。

### 3.4 RuleSet 管理

展示字段：

- name。
- type。
- status。
- priority。
- version。
- updatedBy。
- updatedAt。

行为：

- 创建 draft。
- 编辑 draft。
- 编辑 active 时创建新 version。
- pause / activate / archive。
- preview rule。

规则：

- conditions / actions 使用结构化表单或 JSON editor，但禁止脚本。
- preview 不保存、不触发副作用。
- version conflict 必须显示。

### 3.5 Subscription 管理

展示和编辑：

- name。
- categories。
- includeKeywords / excludeKeywords。
- sourceAllowlist / sourceDenylist。
- minValueScore。
- deliveryMode。
- quietHours。
- maxItemsPerDay。
- enabled。

规则：

- 写操作必须有 reason。
- 前端不得把订阅规则传给外部模型。
- 0 次命中、0 次推送必须显示真实 0。

### 3.6 DeliveryChannel 管理

展示和编辑：

- type。
- name。
- maskedTarget。
- enabled。
- template。

secret 写入：

- 单独表单输入一次性 secret。
- 提交后清空输入框。
- 响应只展示 `maskedTarget` 和 `secretRef` 摘要。

规则：

- 不展示明文 webhook URL、bot token、email password。
- channel test 必须标注 dryRun / fake adapter。
- disabled channel 不能 test 或发送。

### 3.7 RerunRequest

展示字段：

- targetType。
- targetId。
- stage。
- status。
- reason。
- requestedBy。
- agentRunId。
- traceId。

规则：

- 手动重跑必须填写 reason。
- rerun 不显示为已覆盖历史结果；只显示新 run 或 queued request。

### 3.8 AuditLog

展示字段：

- actorId。
- actorRole。
- action。
- resourceType。
- resourceId。
- reason。
- redaction。
- createdAt。
- traceId。

规则：

- before / after ref 只显示脱敏摘要。
- 不展开 secret、token、cookie、Authorization header。
- audit log 不提供编辑或删除入口。

### 3.9 User / Role

展示字段：

- email。
- displayName。
- roles。
- status。
- lastLoginAt。

行为：

- 创建用户。
- 修改角色。
- 禁用 / 启用用户。

规则：

- 不能在 UI 中禁用最后一个 admin。
- role change 必须有 reason。

## 4. 组件建议

- `AdminShell`
- `AdminPermissionGate`
- `ReviewQueuePage`
- `ReviewDetailPanel`
- `ReviewDecisionForm`
- `TopicAdminWorkspace`
- `RuleSetList`
- `RuleSetEditor`
- `RuleSetPreviewPanel`
- `SubscriptionAdminForm`
- `DeliveryChannelAdminForm`
- `ChannelSecretForm`
- `RerunRequestList`
- `AuditLogList`
- `AuditDiffPreview`
- `AdminUsersPage`
- `AdminApiStateView`

## 5. API 使用

以 `docs/contracts/admin-rules-api.md` 为唯一 M6 管理契约。

前端调用：

```text
GET /api/admin/me
GET /api/admin/users
POST /api/admin/users
PATCH /api/admin/users/{userId}
GET /api/admin/roles
GET /api/admin/review-items
GET /api/admin/review-items/{reviewItemId}
POST /api/admin/review-decisions
GET /api/admin/review-decisions
POST /api/admin/topics/{topicId}/merge
POST /api/admin/topics/{topicId}/split
POST /api/admin/topics/{topicId}/suppress
POST /api/admin/topics/{topicId}/approve
GET /api/admin/rulesets
GET /api/admin/rulesets/{ruleSetId}
POST /api/admin/rulesets
PATCH /api/admin/rulesets/{ruleSetId}
POST /api/admin/rulesets/{ruleSetId}/preview
POST /api/admin/subscriptions
PATCH /api/admin/subscriptions/{subscriptionId}
POST /api/admin/delivery-channels
PATCH /api/admin/delivery-channels/{channelId}
POST /api/admin/delivery-channels/{channelId}/secret
POST /api/admin/delivery-channels/{channelId}/test
POST /api/admin/rerun-requests
GET /api/admin/rerun-requests
GET /api/admin/rerun-requests/{rerunRequestId}
GET /api/admin/audit-logs
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

前端类型以 `docs/contracts/admin-rules-api.md` 为唯一来源，至少覆盖：

- `AdminUser`
- `CurrentPrincipal`
- `Role`
- `Permission`
- `ReviewItem`
- `ReviewDecision`
- `AdminRuleSet`
- `RulePreviewResult`
- `ChannelSecretUpdate`
- `RerunRequest`
- `AuditLog`
- 统一 `Envelope<T>`
- 统一 `ApiError`
- cursor 分页 response

本地 UI 派生状态只允许保存：

- 当前选中 resource id。
- 当前筛选条件。
- 表单草稿。
- 最近一次 API envelope 的 traceId、warnings、error。

规则：

- 前端不得发明权限。
- 前端不得发明审核成功态。
- 前端不得保存明文 secret。

## 7. 状态机

ReviewItem：

```text
needs_review -> approved
needs_review -> suppressed
needs_review -> request_changes
request_changes -> needs_review
approved -> published
approved -> archived
suppressed -> archived
```

AdminRuleSet：

```text
draft -> active
active -> paused
paused -> active
active -> archived
paused -> archived
```

AdminUser：

```text
invited -> active
active -> disabled
disabled -> active
```

RerunRequest：

```text
queued -> running -> succeeded
queued -> running -> failed
queued -> cancelled
```

UI 规则：

- 成功态必须以 API 返回为准。
- `FORBIDDEN` 必须显示权限不足，不伪装为资源不存在。
- `REVIEW_STATE_CONFLICT` 必须提示刷新当前审核项。

## 8. Agent 输入输出

M6 前端不运行 Agent，只提交人工动作和规则配置。

展示输入：

- topic / assessment / background / commentary 引用。
- review reasons。
- rule conditions / actions。
- subscription / channel 表单。
- reason。

展示输出：

- `ReviewDecision`。
- `AuditLog`。
- `RulePreviewResult`。
- `ChannelSecretUpdate`。
- `RerunRequest`。

规则：

- 前端不得把 review item、commentary、evidence 或用户规则传给外部模型或工具。
- 前端不得绕过后端直接触发采集、分发或 webhook。

## 9. 错误处理

错误码以 `docs/contracts/admin-rules-api.md` 为准。

UI 显示要求：

- 所有错误态展示 `error.message` 和 `meta.traceId`。
- `AUTH_REQUIRED`：显示登录过期或未登录。
- `TOKEN_INVALID`：提示 token 无效。
- `FORBIDDEN`：显示权限不足。
- `AUDIT_REASON_REQUIRED`：定位到 reason 输入框。
- `REVIEW_STATE_CONFLICT`：提示刷新审核项。
- `RULESET_VERSION_CONFLICT`：提示规则已被他人更新。
- `SECRET_VALUE_REJECTED`：提示敏感值不会被展示或记录。
- `CHANNEL_SECRET_INVALID`：提示密钥格式或连通性失败。
- `RERUN_REQUEST_INVALID`：提示目标或阶段不合法。

禁止：

- 禁止 unknown id 兜底显示第一条资源。
- 禁止请求失败后伪造空成功态。
- 禁止把 `FORBIDDEN` 显示成“保存成功但无变化”。

## 10. 安全和合规边界

- 前端不直连 webhook、bot URL、AI HOT、RSSHub、RSS、evidence URL 抓取接口。
- 不展示真实 webhook URL、bot token、secret、cookie、Authorization header。
- secret 输入提交后立即清空。
- API token 创建后只展示一次，刷新后不可再查看。
- 所有写操作必须有 reason。
- 所有高副作用操作必须二次确认。
- 当前权限由后端 `CurrentPrincipal.permissions` 决定。

## 11. Prompt injection 防护

ReviewItem、commentary、evidence、channel response、audit reason 都可能包含外部文本，必须按普通文本处理。

要求：

- 使用 Vue 默认文本插值或等价安全渲染，不使用 `v-html` 渲染外部文本。
- 不解析 commentary 文本中的 Markdown 指令、HTML script、工具调用片段或“忽略以上指令”等内容。
- RuleSet JSON editor 不执行脚本。
- 复制、展开、筛选等 UI 行为只处理文本，不触发工具调用。
- mock 和测试必须包含带 prompt injection 文案的 review item，断言页面只展示文本。

## 12. Mock 开发

前端 mock 必须覆盖：

- viewer / operator / reviewer / admin 不同权限。
- auth required。
- forbidden。
- review queue high priority。
- approve review success。
- review state conflict。
- ruleset active / draft / paused。
- ruleset preview match / no match。
- channel secret update redacted。
- channel test dryRun success / failure。
- rerun request queued / failed。
- audit log redacted。
- prompt injection review item 只作为普通文本展示。

mock 写接口必须保留实体 identity：

- review decision 后更新对应 review item。
- unknown review item 返回 `REVIEW_ITEM_NOT_FOUND`。
- forbidden 不改变 mock state。
- secret update 不把 secretValue 写入可读 state。

## 13. 验收标准

- 可查看当前用户、角色和权限。
- 可查看 review queue。
- 可提交 review decision，且 reason 必填。
- 可查看 topic detail 汇总信息。
- 可管理 ruleset 并 preview。
- 可管理 subscription。
- 可管理 delivery channel，且密钥脱敏。
- 可创建 rerun request。
- 可查看 audit log，且不可编辑或删除。
- 权限不足时显示 `FORBIDDEN`。
- 错误态展示 `error.message` 和 traceId。
- 前端不包含 webhook、bot、AI HOT、RSSHub、RSS 或 evidence URL 直连 fetch。
- 移动端不出现主要内容重叠或横向溢出。
- prompt injection 样本文案只作为普通文本展示，不触发 HTML 渲染或工具调用。

## 14. 测试要求

- API client auth / query string / request body 测试。
- permission gate 测试。
- ReviewDecision reason required 测试。
- review state conflict 展示测试。
- RuleSet editor version conflict 测试。
- RuleSet preview no side effect 测试。
- channel secret redaction 测试。
- forbidden 展示测试。
- audit log redaction 测试。
- unknown id 错误测试。
- prompt injection 文本安全渲染测试。

## 15. 设计约束

- 工作台风格，信息密度优先。
- 不做营销式落地页。
- 列表在移动端可降级为卡片。
- 权限和状态必须比装饰更突出。
- 不使用颜色作为唯一状态表达。
- 长 URL、长标题、长 reason、长 commentary 必须换行，不造成横向溢出。
- destructive action 使用明确确认，不隐藏影响范围。
- audit 区域必须展示 trace id 和 reason。

## 16. 联调边界

- 后端未实现前，前端只使用 mock。
- 后端实现后，先联调 `GET /api/admin/me`，再联调 review queue，最后联调写操作和 audit。
- channel test 联调默认 fake adapter / dryRun。
- 真实联调不得调用生产 webhook。
- 如果 contract 发现缺口，先更新 `docs/contracts/admin-rules-api.md`，再更新前端和后端。

## 17. 迁移或兼容策略

- M6 前端必须新增 Admin Console，不破坏 M1-M5 页面。
- API client 新增 admin-rules client 模块；不得把 M6 字段混入 M5 commentary-distribution 类型。
- mock 数据应独立 reset，避免 M6 review / admin 写状态污染 M2-M5 mock。
- 后端未实现 M6 API 前，前端只能在 mock 模式开发，不伪造真实联调已完成。
- 如果 M6 contract 字段调整，先更新 `docs/contracts/admin-rules-api.md`，再同步类型、mock 和组件。

## 18. 已知风险

- 权限 UI 和后端 RBAC 不一致会造成误导，必须以后端 `FORBIDDEN` 为准。
- 密钥输入误展示会造成泄露，secret 表单必须单独处理。
- 审核状态冲突会导致误批准，必须展示并要求刷新。
- prompt injection review item 必须安全渲染。
- mock 写状态必须可 reset，否则测试会相互污染。
