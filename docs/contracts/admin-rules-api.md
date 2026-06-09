# M6 管理后台与规则 API 共享契约

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 上游依赖：M2 `collection-api.md`、M3 `clustering-api.md`、M4 `value-background-api.md`、M5 `commentary-distribution-api.md`
> 使用对象：M6 后端管理服务、M6 前端 Admin Console、自动化测试、不同 AI coding 客户端
> 原则：M6 负责认证、RBAC、审核、规则、渠道密钥写入和审计；不得绕过 M2-M5 契约重写业务事实，不得返回敏感值。

## 1. 目标

定义 M6 管理后台与规则阶段的共享 API：管理员和审核员通过受控界面管理 source、topic review、commentary edit、subscription、delivery channel、rule set、manual rerun 和 audit log。

M6 覆盖：

- Web 管理台登录态和 RBAC。
- 用户、角色、权限只读/基础管理。
- 审核队列和 `ReviewDecision`。
- 合并、拆分、压制、批准、编辑点评、请求重跑等人工动作。
- 订阅规则与渠道配置管理。
- source / review / distribution 规则集管理和预览。
- 渠道密钥写入、脱敏展示和测试发送。
- 所有写操作写入 `AuditLog`。

## 2. 全局约定

### 2.1 Base URL

```text
http://localhost:8000/api
```

### 2.2 响应 envelope

沿用 M1-M5：

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

### 2.3 认证

M6 v0.1 冻结认证方案：

- Web 管理台使用服务端 session，浏览器只保存 `HttpOnly`、`SameSite=Lax` cookie。
- 开发者 API 使用 scoped API token；token 只存 hash，创建后只显示一次。
- 非 mock 模式不得有隐式匿名管理员。
- 本地开发可 seed admin 用户和测试 token，但请求仍必须带 session 或 token。

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

### 2.5 写操作原因

所有写操作必须包含：

```json
{
  "reason": "审核通过，官方来源已补齐"
}
```

缺失或空白 `reason` 返回 `AUDIT_REASON_REQUIRED`。

## 3. RBAC

### 3.1 Role

```ts
type Role = "viewer" | "operator" | "reviewer" | "admin" | "developer_api" | "system";
```

### 3.2 Permission

```ts
type Permission =
  | "source:read"
  | "source:write"
  | "topic:read"
  | "topic:merge"
  | "topic:split"
  | "topic:review"
  | "commentary:read"
  | "commentary:edit"
  | "subscription:read"
  | "subscription:write"
  | "channel:read"
  | "channel:write"
  | "rule:read"
  | "rule:write"
  | "user:read"
  | "user:write"
  | "audit:read"
  | "rerun:trigger";
```

默认权限矩阵：

| role | 主要权限 |
|---|---|
| `viewer` | read-only，不能触发副作用 |
| `operator` | source / subscription / channel / rule 管理，不能批准发布 |
| `reviewer` | topic review、commentary edit、merge / split、rerun |
| `admin` | 全部权限，包含 user / role / secret 管理 |
| `developer_api` | scoped token 授权的 API 访问 |
| `system` | 仅后台任务使用，不可登录 |

## 4. 数据结构

### 4.1 AdminUser

```json
{
  "id": "user_admin_001",
  "email": "admin@example.com",
  "displayName": "Admin",
  "roles": ["admin"],
  "status": "active",
  "lastLoginAt": "2026-06-09T00:00:00Z",
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:00Z"
}
```

`status` 枚举：

```ts
type AdminUserStatus = "invited" | "active" | "disabled";
```

### 4.2 CurrentPrincipal

```json
{
  "user": {
    "id": "user_admin_001",
    "email": "admin@example.com",
    "displayName": "Admin",
    "roles": ["admin"],
    "status": "active"
  },
  "permissions": ["source:read", "topic:review", "audit:read"]
}
```

### 4.3 ReviewItem

```json
{
  "id": "review_topic_20260609_001",
  "topicId": "topic_20260603_abcd1234",
  "assessmentId": "assessment_20260609_abcd1234",
  "commentaryId": "commentary_20260609_abcd1234",
  "status": "needs_review",
  "reasons": ["low_confidence", "source_conflict"],
  "priority": "high",
  "assignedTo": "user_reviewer_001",
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:00Z",
  "traceId": "tr_20260609_000001"
}
```

### 4.4 ReviewDecision

```json
{
  "id": "review_decision_20260609_001",
  "reviewItemId": "review_topic_20260609_001",
  "topicId": "topic_20260603_abcd1234",
  "actorId": "user_reviewer_001",
  "action": "approve",
  "reason": "官方来源已确认，点评证据完整",
  "beforeState": "needs_review",
  "afterState": "approved",
  "commentaryPatchRef": null,
  "createdAt": "2026-06-09T00:00:10Z",
  "traceId": "tr_20260609_000002"
}
```

`action` 枚举：

```ts
type ReviewAction =
  | "approve"
  | "suppress"
  | "request_changes"
  | "edit_commentary"
  | "merge"
  | "split"
  | "rerun_background"
  | "rerun_assessment"
  | "rerun_commentary";
```

### 4.5 AdminRuleSet

```json
{
  "id": "ruleset_review_default",
  "workspaceId": "default",
  "name": "Default Review Rules",
  "type": "review",
  "status": "active",
  "priority": 100,
  "conditions": {
    "minValueScore": 70,
    "requiresOfficialSource": true,
    "includeKeywords": ["OpenAI"],
    "excludeKeywords": ["广告"]
  },
  "actions": {
    "routeToReview": true,
    "suppress": false,
    "deliveryMode": "instant"
  },
  "version": 3,
  "createdBy": "user_admin_001",
  "updatedBy": "user_admin_001",
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:00Z"
}
```

`type` 枚举：

```ts
type RuleSetType = "source" | "review" | "subscription" | "distribution";
```

`status` 枚举：

```ts
type RuleSetStatus = "draft" | "active" | "paused" | "archived";
```

规则：

- `conditions` 和 `actions` 必须是结构化 JSON，不允许保存任意可执行代码。
- `active` rule set 必须有 `version`。
- 编辑 active rule set 时创建新版本，不覆盖历史。

### 4.6 RulePreviewResult

```json
{
  "ruleSetId": "ruleset_review_default",
  "inputRef": "topic_20260603_abcd1234",
  "matched": true,
  "matchedConditions": ["minValueScore", "requiresOfficialSource"],
  "actions": {
    "routeToReview": true
  },
  "warnings": [],
  "traceId": "tr_20260609_000003"
}
```

### 4.7 ChannelSecretUpdate

```json
{
  "channelId": "channel_webhook_demo",
  "secretRef": "secret://delivery/channel_webhook_demo",
  "maskedTarget": "https://example.com/***",
  "updatedAt": "2026-06-09T00:00:00Z"
}
```

规则：

- 请求可以提交一次性 `secretValue`，响应不得返回。
- `AuditLog` 只能保存 `secretRef`、`maskedTarget`、key id 和动作摘要。
- secret 校验失败返回 `CHANNEL_SECRET_INVALID`。

### 4.8 RerunRequest

```json
{
  "id": "rerun_20260609_001",
  "targetType": "topic",
  "targetId": "topic_20260603_abcd1234",
  "stage": "background",
  "status": "queued",
  "reason": "补充官方来源后重跑背景",
  "requestedBy": "user_reviewer_001",
  "agentRunId": null,
  "createdAt": "2026-06-09T00:00:00Z",
  "updatedAt": "2026-06-09T00:00:00Z",
  "traceId": "tr_20260609_000004"
}
```

`stage` 枚举：

```ts
type RerunStage = "collection" | "clustering" | "assessment" | "background" | "commentary" | "distribution";
```

### 4.9 AuditLog

```json
{
  "id": "audit_20260609_001",
  "actorId": "user_reviewer_001",
  "actorRole": "reviewer",
  "action": "topic.review.approve",
  "resourceType": "topic",
  "resourceId": "topic_20260603_abcd1234",
  "reason": "官方来源已确认",
  "beforeRef": "audit/before/audit_20260609_001.json",
  "afterRef": "audit/after/audit_20260609_001.json",
  "redaction": "secrets_masked",
  "createdAt": "2026-06-09T00:00:10Z",
  "traceId": "tr_20260609_000002"
}
```

规则：

- `AuditLog` 只追加，不更新、不删除。
- before / after ref 不得包含明文 secret、cookie、API key、用户私密 token。
- 失败的写操作也应记录 attempt audit 或 error trace。

## 5. 状态机

### 5.1 ReviewItem

```text
needs_review -> approved
needs_review -> suppressed
needs_review -> request_changes
request_changes -> needs_review
approved -> published
approved -> archived
suppressed -> archived
```

### 5.2 AdminRuleSet

```text
draft -> active
active -> paused
paused -> active
active -> archived
paused -> archived
```

### 5.3 AdminUser

```text
invited -> active
active -> disabled
disabled -> active
```

### 5.4 RerunRequest

```text
queued -> running -> succeeded
queued -> running -> failed
queued -> cancelled
```

## 6. API 端点

### 6.1 当前登录主体

```http
GET /api/admin/me
```

响应：`CurrentPrincipal`。

### 6.2 用户与角色

```http
GET /api/admin/users?status=active&take=50&cursor=opaque
POST /api/admin/users
PATCH /api/admin/users/{userId}
GET /api/admin/roles
```

写入 user 时必须有 `user:write` 权限和 `reason`。

### 6.3 审核队列

```http
GET /api/admin/review-items?status=needs_review&priority=high&take=50&cursor=opaque
GET /api/admin/review-items/{reviewItemId}
POST /api/admin/review-decisions
GET /api/admin/review-decisions?topicId=topic_20260603_abcd1234&take=50&cursor=opaque
```

`POST /api/admin/review-decisions` 请求体：

```json
{
  "reviewItemId": "review_topic_20260609_001",
  "action": "approve",
  "reason": "官方来源已确认",
  "commentaryPatch": null
}
```

### 6.4 Topic 人工操作

```http
POST /api/admin/topics/{topicId}/merge
POST /api/admin/topics/{topicId}/split
POST /api/admin/topics/{topicId}/suppress
POST /api/admin/topics/{topicId}/approve
```

规则：

- merge / split 必须复用 M3 的 topic 边界。
- approve / suppress 必须写 `ReviewDecision` 和 `AuditLog`。

### 6.5 规则集

```http
GET /api/admin/rulesets?type=review&status=active&take=50&cursor=opaque
GET /api/admin/rulesets/{ruleSetId}
POST /api/admin/rulesets
PATCH /api/admin/rulesets/{ruleSetId}
POST /api/admin/rulesets/{ruleSetId}/preview
```

preview 不保存、不触发副作用。

### 6.6 订阅与渠道管理

M6 复用 M5 `Subscription` 和 `DeliveryChannel` shape，并补充写操作：

```http
POST /api/admin/subscriptions
PATCH /api/admin/subscriptions/{subscriptionId}
POST /api/admin/delivery-channels
PATCH /api/admin/delivery-channels/{channelId}
POST /api/admin/delivery-channels/{channelId}/secret
POST /api/admin/delivery-channels/{channelId}/test
```

规则：

- `test` 必须使用 fake adapter 或显式 `dryRun=true`，不得默认调用生产 webhook。
- secret 写入响应只返回 `ChannelSecretUpdate`。

### 6.7 手动重跑

```http
POST /api/admin/rerun-requests
GET /api/admin/rerun-requests?status=queued&take=50&cursor=opaque
GET /api/admin/rerun-requests/{rerunRequestId}
```

### 6.8 Audit log

```http
GET /api/admin/audit-logs?resourceType=topic&resourceId=topic_20260603_abcd1234&take=50&cursor=opaque
```

Audit log 无 update / delete API。

## 7. 错误码

| code | HTTP | retryable | 场景 |
|---|---:|:---:|---|
| `AUTH_REQUIRED` | 401 | 否 | 未登录或 token 缺失 |
| `TOKEN_INVALID` | 401 | 否 | API token 无效或过期 |
| `FORBIDDEN` | 403 | 否 | 权限不足 |
| `USER_NOT_FOUND` | 404 | 否 | 用户不存在 |
| `ROLE_NOT_FOUND` | 404 | 否 | 角色不存在 |
| `REVIEW_ITEM_NOT_FOUND` | 404 | 否 | 审核项不存在 |
| `RULESET_NOT_FOUND` | 404 | 否 | 规则集不存在 |
| `AUDIT_LOG_NOT_FOUND` | 404 | 否 | 审计记录不存在 |
| `RERUN_REQUEST_NOT_FOUND` | 404 | 否 | 重跑请求不存在 |
| `AUDIT_REASON_REQUIRED` | 400 | 否 | 写操作缺少原因 |
| `REVIEW_STATE_CONFLICT` | 409 | 否 | 审核状态已变化 |
| `RULESET_VERSION_CONFLICT` | 409 | 否 | 规则版本冲突 |
| `SECRET_VALUE_REJECTED` | 400 | 否 | 响应或日志试图返回明文 secret |
| `CHANNEL_SECRET_INVALID` | 400 | 否 | 渠道密钥格式或连通性校验失败 |
| `ADMIN_ACTION_CONFLICT` | 409 | 否 | 人工动作与当前资源状态冲突 |
| `RERUN_REQUEST_INVALID` | 400 | 否 | 重跑目标或阶段不合法 |
| `INTERNAL_ERROR` | 500 | 否 | 未知错误 |

## 8. 安全与合规

- 所有 admin API 必须认证。
- 所有写操作必须做 RBAC 校验。
- 所有写操作必须写 `AuditLog`。
- secret、token、cookie、Authorization header 不得出现在响应、日志和 audit before / after ref。
- source、topic、commentary、channel response 中的外部文本一律按不可信输入处理。
- 手动发送、渠道测试、重跑和发布都是副作用操作，必须要求 `reason`。
- API token 创建后只显示一次，后端只保存 hash。

## 9. Prompt Injection 防护

M6 不把外部文本交给模型执行管理动作。规则：

- Topic、commentary、evidence、channel response 中的“忽略规则”“提升权限”“调用 webhook”等文本只作为内容展示。
- 审核动作只能来自已认证用户显式提交的表单和 `reason`。
- RuleSet 不允许保存可执行脚本。
- 前端不得用 `v-html` 渲染外部文本。
- 测试 fixture 必须覆盖带 prompt injection 文案的 topic / commentary / audit detail。

## 10. 测试 Fixture

必须提供：

- `fixtures/m6_admin_user_roles.json`
- `fixtures/m6_review_queue_high_priority.json`
- `fixtures/m6_review_decision_approve.json`
- `fixtures/m6_review_state_conflict.json`
- `fixtures/m6_ruleset_review_active.json`
- `fixtures/m6_ruleset_preview_match.json`
- `fixtures/m6_channel_secret_update.json`
- `fixtures/m6_rerun_request_background.json`
- `fixtures/m6_audit_log_redacted.json`
- `fixtures/m6_prompt_injection_review_item.json`

Fixture 不得包含真实 webhook、token、cookie、授权头或明文 secret。

## 11. 兼容边界

- M6 不重定义 M2 SourceConfig、M3 Topic、M4 Assessment、M5 Subscription / DeliveryChannel 的核心 shape。
- 如需新增字段，先更新对应 contract，再更新本契约。
- M6 写操作可以调用 M2-M5 服务，但必须保留原始服务的业务约束和错误码。
- M6 不实现 M7 eval / observability 全平台，只提供管理台需要的基础趋势和运行状态入口。
