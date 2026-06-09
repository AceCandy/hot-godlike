# M6 后端管理后台与规则子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/admin-rules-api.md`
> 上游依赖：M2 collection、M3 clustering、M4 value/background、M5 commentary/distribution
> 推荐实现客户端：后端 / admin API AI coding 客户端
> 技术栈决策：Python + FastAPI + PostgreSQL；session 存储可用 PostgreSQL 或 Redis，API token 只保存 hash。

## 1. 目标

实现 M6 后端管理与规则能力：认证、RBAC、审核队列、人工审核决策、规则集、订阅与渠道管理写操作、渠道密钥写入、手动重跑和不可变审计日志。

M6 的目标是把 M2-M5 的后台能力产品化和可控化。M6 不重新实现采集、聚类、评分、背景补全、点评和分发算法，只通过受控 API 调用已有服务并记录人工动作。

## 2. 背景与依赖

上游已有能力：

- M2：SourceConfig、FetchRun、RawItem、SourceHealth。
- M3：HotTopicCluster、TopicMember、MergeHistory、TrendSnapshot。
- M4：ValueAssessment、BackgroundPack、EvidenceSource、ReviewFlag。
- M5：TopicCommentary、Subscription、DeliveryChannel、DeliveryRecord、PushTrace、DistributionRun。

M6 在此基础上新增：

- Admin session / API token。
- Role / Permission。
- ReviewItem / ReviewDecision。
- AdminRuleSet / RulePreviewResult。
- RerunRequest。
- AuditLog。
- Secret write boundary。

## 3. 范围

### 3.1 In Scope

- `GET /api/admin/me`
- `GET /api/admin/users`
- `POST /api/admin/users`
- `PATCH /api/admin/users/{userId}`
- `GET /api/admin/roles`
- `GET /api/admin/review-items`
- `GET /api/admin/review-items/{reviewItemId}`
- `POST /api/admin/review-decisions`
- `GET /api/admin/review-decisions`
- `POST /api/admin/topics/{topicId}/merge`
- `POST /api/admin/topics/{topicId}/split`
- `POST /api/admin/topics/{topicId}/suppress`
- `POST /api/admin/topics/{topicId}/approve`
- `GET /api/admin/rulesets`
- `GET /api/admin/rulesets/{ruleSetId}`
- `POST /api/admin/rulesets`
- `PATCH /api/admin/rulesets/{ruleSetId}`
- `POST /api/admin/rulesets/{ruleSetId}/preview`
- `POST /api/admin/subscriptions`
- `PATCH /api/admin/subscriptions/{subscriptionId}`
- `POST /api/admin/delivery-channels`
- `PATCH /api/admin/delivery-channels/{channelId}`
- `POST /api/admin/delivery-channels/{channelId}/secret`
- `POST /api/admin/delivery-channels/{channelId}/test`
- `POST /api/admin/rerun-requests`
- `GET /api/admin/rerun-requests`
- `GET /api/admin/rerun-requests/{rerunRequestId}`
- `GET /api/admin/audit-logs`
- PostgreSQL schema 和 migration。
- 单元测试、集成测试、OpenAPI 自查。

### 3.2 Out of Scope

- 复杂多租户计费。
- SSO / SAML / OAuth 企业集成。
- 完整 BI 报表。
- M7 eval / observability 平台。
- 绕过 M2-M5 contract 的直接表写。
- 所有第三方渠道深度卡片编辑器。
- 生产 webhook 真实发送 smoke。

## 4. 用户故事 / 系统场景

### 4.1 管理员登录并查看权限

管理员通过 session 登录管理台。后端返回 `CurrentPrincipal`，包含 user、roles 和 permissions。未登录请求返回 `AUTH_REQUIRED`。

### 4.2 审核员批准 topic

审核员打开 review item，确认 evidence 和 commentary 后提交 approve。后端校验 `topic:review` 权限，写 `ReviewDecision`、更新 review item 状态、写 `AuditLog`。

### 4.3 审核员编辑点评

审核员提交 commentary patch。后端不允许 patch 新增无 evidence claim；必须复用 M5 EvidenceGuard 或等价校验，写 patch ref 和 audit。

### 4.4 管理员更新规则集

管理员创建或修改 review rule set。active 规则改动必须创建新 version，不覆盖历史。preview 只返回匹配结果，不触发副作用。

### 4.5 管理员写入渠道密钥

管理员提交 webhook 或 bot token。后端写入 secret manager / encrypted secret store，响应只返回 `secretRef` 和 `maskedTarget`，audit 不记录明文 secret。

### 4.6 审核员发起重跑

审核员对某个 topic 发起 background rerun。后端创建 `RerunRequest`，调用既有任务入口或先写 queued 状态；失败必须保留真实错误。

## 5. 模块设计

### 5.1 AuthService

职责：

- 解析 session cookie 和 API token。
- 返回 `CurrentPrincipal`。
- 管理 token hash、过期时间和 scope。

规则：

- 非 mock 模式不得隐式匿名管理员。
- API token 只保存 hash。
- token 创建后只显示一次。

### 5.2 RbacService

职责：

- 维护 Role 到 Permission 的映射。
- 提供 `require_permission(permission)` dependency。
- 对每个 admin 写 API 做权限检查。

规则：

- 权限不足返回 `FORBIDDEN`。
- 系统任务 role 不可登录。

### 5.3 AdminUserService

职责：

- 管理 AdminUser 的创建、禁用、角色更新。
- 写操作产出 AuditLog。

规则：

- 禁用最后一个 admin 必须拒绝。
- 修改角色必须记录 before / after。

### 5.4 ReviewQueueService

职责：

- 从 M4 review flags、M5 needs_review commentary 和人工动作生成 `ReviewItem`。
- 查询 review queue。
- 防止并发审核状态冲突。

规则：

- 高影响低置信、来源冲突、缺官方来源、疑似敏感必须进入 review queue。
- 状态冲突返回 `REVIEW_STATE_CONFLICT`。

### 5.5 ReviewDecisionService

职责：

- 处理 approve / suppress / request_changes / edit_commentary / merge / split / rerun。
- 调用 M3/M4/M5 对应服务边界。
- 写 `ReviewDecision` 和 `AuditLog`。

规则：

- 所有 action 必须有 reason。
- edit commentary 必须通过 evidence 校验。
- merge / split 必须保留 M3 merge history。

### 5.6 RuleSetService

职责：

- 管理 `AdminRuleSet`。
- 支持 active rule versioning。
- 支持 preview。

规则：

- `conditions` / `actions` 是结构化 JSON，不执行脚本。
- preview 不保存、不触发副作用。
- active rule set 修改必须新建 version。

### 5.7 SecretService

职责：

- 接收一次性 secret value。
- 写入 secret manager 或 encrypted store。
- 返回 secretRef / maskedTarget。

规则：

- 不在响应、日志、audit 中返回明文 secret。
- 测试使用 fake secret store。

### 5.8 AdminSubscriptionChannelService

职责：

- 管理 M5 Subscription / DeliveryChannel 写操作。
- 调用 SecretService 写密钥。
- 支持 channel test。

规则：

- channel test 默认 fake adapter 或 `dryRun=true`。
- 真实生产 webhook 不在自动测试中调用。

### 5.9 RerunRequestService

职责：

- 创建和查询 `RerunRequest`。
- 将重跑请求映射到 M2-M5 对应任务入口。
- 记录 agentRunId / traceId。

规则：

- 不破坏历史结果，重跑必须产生新 run 或记录覆盖原因。
- 无效阶段返回 `RERUN_REQUEST_INVALID`。

### 5.10 AuditLogService

职责：

- 追加写 AuditLog。
- 生成 before / after ref。
- 脱敏敏感字段。

规则：

- AuditLog 不更新、不删除。
- 写操作失败也记录 attempt audit 或 error trace。

## 6. 数据库 Schema

### 6.1 `admin_users`

- `id` text primary key
- `email` text unique not null
- `display_name` text not null
- `roles` jsonb not null
- `status` text not null
- `password_hash` text null
- `last_login_at` timestamptz null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

### 6.2 `admin_api_tokens`

- `id` text primary key
- `user_id` text not null references admin_users(id)
- `token_hash` text not null
- `scopes` jsonb not null
- `status` text not null
- `expires_at` timestamptz null
- `last_used_at` timestamptz null
- `created_at` timestamptz not null

### 6.3 `admin_sessions`

- `id` text primary key
- `user_id` text not null references admin_users(id)
- `session_hash` text not null
- `expires_at` timestamptz not null
- `created_at` timestamptz not null
- `last_seen_at` timestamptz not null

### 6.4 `review_items`

- `id` text primary key
- `topic_id` text not null
- `assessment_id` text null
- `commentary_id` text null
- `status` text not null
- `reasons` jsonb not null
- `priority` text not null
- `assigned_to` text null references admin_users(id)
- `created_at` timestamptz not null
- `updated_at` timestamptz not null
- `trace_id` text not null

### 6.5 `review_decisions`

- `id` text primary key
- `review_item_id` text not null references review_items(id)
- `topic_id` text not null
- `actor_id` text not null references admin_users(id)
- `action` text not null
- `reason` text not null
- `before_state` text not null
- `after_state` text not null
- `commentary_patch_ref` text null
- `created_at` timestamptz not null
- `trace_id` text not null

### 6.6 `admin_rule_sets`

- `id` text primary key
- `workspace_id` text not null
- `name` text not null
- `type` text not null
- `status` text not null
- `priority` integer not null
- `conditions` jsonb not null
- `actions` jsonb not null
- `version` integer not null
- `created_by` text not null references admin_users(id)
- `updated_by` text not null references admin_users(id)
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

唯一约束：

- `workspace_id, type, name, version`

### 6.7 `rerun_requests`

- `id` text primary key
- `target_type` text not null
- `target_id` text not null
- `stage` text not null
- `status` text not null
- `reason` text not null
- `requested_by` text not null references admin_users(id)
- `agent_run_id` text null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null
- `trace_id` text not null

### 6.8 `audit_logs`

- `id` text primary key
- `actor_id` text not null
- `actor_role` text not null
- `action` text not null
- `resource_type` text not null
- `resource_id` text not null
- `reason` text not null
- `before_ref` text null
- `after_ref` text null
- `redaction` text not null
- `created_at` timestamptz not null
- `trace_id` text not null

索引：

- `audit_logs(resource_type, resource_id, created_at desc)`
- `audit_logs(actor_id, created_at desc)`
- `review_items(status, priority, updated_at desc)`
- `admin_rule_sets(workspace_id, type, status, priority)`

## 7. API 实现要求

以 `docs/contracts/admin-rules-api.md` 为准。

所有 admin API 必须：

- 使用统一 envelope。
- 生成 trace id。
- 校验认证。
- 校验 RBAC。
- 写操作校验 reason。
- 写操作写 AuditLog。
- 不返回明文 secret。
- 对外错误使用简体中文。

## 8. 状态机

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

RerunRequest：

```text
queued -> running -> succeeded
queued -> running -> failed
queued -> cancelled
```

## 9. Agent 输入输出

M6 不新增 LLM Agent。M6 的人工审核和规则配置会影响 M2-M5 Agent 的输入。

输入：

- `AdminUser`
- `CurrentPrincipal`
- `ReviewItem`
- `AdminRuleSet`
- `Subscription`
- `DeliveryChannel`
- `reason`

输出：

- `ReviewDecision`
- `AuditLog`
- `RulePreviewResult`
- `ChannelSecretUpdate`
- `RerunRequest`

规则：

- 模型不得决定 RBAC、secret、发布或外发。
- 后续如引入 AI 辅助审核建议，必须进入新 contract，并默认只读。

## 10. 错误处理

必须实现 `docs/contracts/admin-rules-api.md` 的错误码。

错误映射：

- 未登录：`AUTH_REQUIRED`
- token 无效：`TOKEN_INVALID`
- 权限不足：`FORBIDDEN`
- reason 缺失：`AUDIT_REASON_REQUIRED`
- 审核状态冲突：`REVIEW_STATE_CONFLICT`
- rule version 冲突：`RULESET_VERSION_CONFLICT`
- 明文 secret 泄露风险：`SECRET_VALUE_REJECTED`
- 渠道密钥无效：`CHANNEL_SECRET_INVALID`
- 重跑请求非法：`RERUN_REQUEST_INVALID`

## 11. 安全与合规

- 非 mock 模式所有 admin API 必须认证。
- 所有写 API 必须有 RBAC dependency。
- session cookie 必须 `HttpOnly`、`SameSite=Lax`；生产环境必须 `Secure`。
- API token 只保存 hash。
- 密码 hash 使用成熟算法，不能明文存储。
- secret、token、cookie、Authorization header 必须脱敏。
- AuditLog 不可更新删除。
- 生产环境禁用匿名 admin 和 fake secret。

## 12. Prompt injection 防护

- Topic title、raw item、commentary、evidence、channel response、audit reason 都按不可信文本处理。
- 后端不解析外部文本中的管理指令。
- RuleSet 不保存可执行代码。
- 审核 action 只能来自已认证用户请求体，不来自 commentary 文本。
- 测试覆盖 prompt injection review item 和 commentary patch。

## 13. 测试 Fixture

必须创建：

- `fixtures/m6_admin_user_roles.json`
- `fixtures/m6_auth_required.json`
- `fixtures/m6_forbidden_operator_review.json`
- `fixtures/m6_review_queue_high_priority.json`
- `fixtures/m6_review_decision_approve.json`
- `fixtures/m6_review_state_conflict.json`
- `fixtures/m6_ruleset_review_active.json`
- `fixtures/m6_ruleset_preview_match.json`
- `fixtures/m6_channel_secret_update.json`
- `fixtures/m6_rerun_request_background.json`
- `fixtures/m6_audit_log_redacted.json`
- `fixtures/m6_prompt_injection_review_item.json`

Fixture 不得包含真实 token、cookie、webhook、bot secret。

## 14. 测试要求

### 14.1 单元测试

- AuthService session / token 解析。
- RbacService 权限矩阵。
- reason required。
- ReviewDecision 状态机。
- RuleSet versioning。
- RuleSet preview no side effect。
- SecretService redaction。
- AuditLog redaction。
- RerunRequest stage validation。
- Prompt injection 文本安全处理。

### 14.2 集成测试

- 未登录访问 admin API 返回 `AUTH_REQUIRED`。
- 权限不足返回 `FORBIDDEN`。
- approve review 写 ReviewDecision 和 AuditLog。
- review state conflict 返回 `REVIEW_STATE_CONFLICT`。
- channel secret write 不返回明文 secret。
- channel test 使用 fake adapter / dryRun。
- rerun request queued 并可查询。
- OpenAPI 包含 M6 endpoints。

测试不能调用真实生产 webhook、真实第三方 bot 或真实用户邮箱。

## 15. 验收标准

- 管理员可查看当前 principal 和权限。
- 管理员可创建/禁用用户并写 audit。
- 审核员可查看 review queue 并提交 review decision。
- 合并/拆分/批准/压制必须记录 reason 和 audit。
- 规则集可创建、版本化、预览。
- 订阅和渠道可通过 admin API 管理。
- 渠道密钥不从响应、日志、audit 泄露。
- 手动重跑请求可创建并追踪状态。
- 所有写操作都有操作者、时间、旧值、新值和原因。
- prompt injection 样本文本不会触发管理动作。

## 16. 交付物

- PostgreSQL migration。
- AuthService。
- RbacService。
- AdminUser model / repository / service。
- ReviewItem model / repository / service。
- ReviewDecision model / repository / service。
- AdminRuleSet model / repository / service。
- SecretService / fake secret store。
- AdminSubscriptionChannelService。
- RerunRequest model / repository / service。
- AuditLog model / repository / service。
- API routes。
- fixtures。
- 单元测试和集成测试。
- README 更新，写清本地 seed admin / token 方式。

## 17. 联调边界

- 前端只调用 `docs/contracts/admin-rules-api.md` 和 M2-M5 已定义 API。
- M6 后端写操作必须通过服务层调用 M2-M5，不直接绕过业务校验写表。
- M6 channel test 在联调默认 fake adapter / dryRun，不调用生产 webhook。
- 如果 contract 变更，先改 `docs/contracts/admin-rules-api.md`，再改后端和前端。

## 18. 迁移或兼容策略

- M6 migration 只新增 admin / review / rules / rerun / audit 表，不修改 M2-M5 既有字段。
- 需要引用上游资源时使用 resource id，不强制增加上游外键；避免阻塞已有 migration。
- 首次启用 M6 时 seed 一个本地 admin 用户或一次性 setup token。
- 旧的 M2-M5 API 保持可用；M6 只增加 admin 写入口和 audit。
- contract 变更顺序固定为：先更新 `docs/contracts/admin-rules-api.md`，再更新后端 PRD / 前端 PRD，最后改实现和测试。

## 19. 已知风险

- 管理后台权限错误会造成越权发布或密钥泄露，RBAC 必须有测试覆盖。
- 审核和规则操作都是高副作用动作，reason / audit 不能省略。
- channel secret 泄露风险高，必须统一脱敏。
- rule set 如果支持任意脚本会带来 RCE 风险，M6 禁止可执行规则。
- M6 未完成生产级 SSO 前，不应暴露公网管理入口。
