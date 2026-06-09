# M4 前端价值与背景 Console 子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/value-background-api.md`
> 上游依赖：M3 Topic Console
> 推荐实现客户端：前端 AI coding 客户端
> 技术栈决策：Vue 3 + Vite + Tailwind CSS。

## 1. 目标

实现 M4 阶段的轻量 Assessment Console，让管理员或开发者可以查看 topic 的价值评分、分项解释、背景包、证据来源、来源冲突和 review flags，并手动触发 assessment run。

M4 前端不是完整审核后台，不生成最终 AI 点评，不做订阅和分发。

## 2. 范围

### 2.1 In Scope

- Assessment 列表。
- Topic 最新 assessment 详情。
- 分项评分展示。
- recommendation / confidence / review flags 展示。
- BackgroundPack 详情。
- EvidenceSource 列表。
- FactConflict 列表。
- AssessmentRun 列表。
- 手动触发 assessment run。
- 错误态、加载态、空状态。
- 使用 mock API 并行开发。
- 移动端基本适配。

### 2.2 Out of Scope

- 最终 AI 点评生成。
- 点评编辑器。
- 分发推送。
- 完整人工审核后台。
- 权限和用户管理。
- 订阅规则配置。
- 直接抓取外部 URL。
- 直接调用 AI HOT、RSSHub 或 RSS。

## 3. 页面结构

M4 可在 Topic Console 旁增加“价值背景”入口，也可以在 topic detail 中增加 assessment tab。

### 3.1 Assessment 列表

展示字段：

- topic title。
- recommendation。
- valueScore。
- confidence。
- importance / freshness / credibility / propagation / userRelevance / noiseRisk。
- review flags count。
- updatedAt。
- 操作：查看详情、触发重评估。

筛选：

- recommendation。
- confidence。
- review flag status。
- q。

规则：

- `review`、`suppress` 必须有明显状态。
- `noiseRisk` 越高越危险，不得作为正向分展示。
- valueScore 不是事实真伪分。

### 3.2 Assessment 详情

展示：

- 总分和分项分。
- reasons。
- downrankReasons。
- recommendation。
- confidence。
- traceId。

行为：

- 点击 topic 可回到 M3 Topic Console。
- 错误态展示 `error.message` 和 traceId。

### 3.3 BackgroundPack 详情

展示：

- officialSourceStatus。
- originalSources。
- relatedSources。
- historicalContext。
- officialStatements。
- unresolvedQuestions。
- status。

规则：

- 未找到官方来源时显示“未找到官方来源”。
- background `partial` / `failed` 必须展示 failure reason。
- 不展示完整网页原文。

### 3.4 EvidenceSource 列表

展示字段：

- type。
- trust。
- title。
- url。
- sourceId。
- capturedAt。
- summary。
- fetchStatus。
- failureReason。

行为：

- 点击 URL 新窗口打开。
- `fetchStatus=failed` 明确展示失败原因。
- prompt injection 文案只作为普通文本展示。

### 3.5 FactConflict 列表

展示字段：

- claim。
- severity。
- evidenceIds。
- resolution。
- createdAt。

规则：

- unresolved conflict 必须有明显状态。
- 不在 UI 中擅自裁决冲突事实。

### 3.6 ReviewFlag 列表

展示字段：

- type。
- severity。
- reason。
- status。
- createdAt。

规则：

- M4 只展示和生成 flag，不实现完整审核处理。
- resolved/dismissed 操作留给 M6。

### 3.7 AssessmentRun 面板

展示字段：

- run id。
- trigger。
- status。
- startedAt / finishedAt。
- durationMs。
- topicCount。
- assessedCount。
- backgroundPackCount。
- reviewFlagCount。
- errorCode / errorMessage。

行为：

- 可手动触发 assessment run。
- 可选择 includeBackground。
- failed / partial_failed 用明显状态展示。
- 手动触发需要 reason。

## 4. 组件建议

- `AssessmentConsolePage`
- `AssessmentList`
- `AssessmentDetailPanel`
- `ScoreBreakdown`
- `BackgroundPackPanel`
- `EvidenceSourceList`
- `FactConflictList`
- `ReviewFlagList`
- `AssessmentRunPanel`
- `AssessmentStatusBadge`
- `ValueBackgroundApiStateView`

## 5. API 使用

以 `docs/contracts/value-background-api.md` 为唯一契约。

前端调用：

```text
POST /api/assessment-runs
GET /api/assessment-runs
GET /api/assessment-runs/{runId}
GET /api/value-assessments
GET /api/topics/{topicId}/assessment
GET /api/background-packs
GET /api/background-packs/{backgroundPackId}
GET /api/evidence-sources
GET /api/review-flags
GET /api/fact-conflicts
```

前端不得调用：

```text
https://aihot.virxact.com/*
RSSHub base URL
任意 RSS URL
任意 evidence URL 抓取接口
```

## 6. 数据模型

前端类型以 `docs/contracts/value-background-api.md` 为唯一来源，至少覆盖：

- `ValueAssessment`
- `AssessmentPolicy`
- `BackgroundPack`
- `EvidenceSource`
- `FactConflict`
- `ReviewFlag`
- `AssessmentRun`
- 统一 `Envelope<T>`
- 统一 `ApiError`
- cursor 分页 response

本地 UI 派生状态只允许保存：

- 当前选中 `topicId` / `assessmentId`。
- 当前筛选条件。
- 当前 run 表单输入。
- 最近一次 API envelope 的 `traceId`、`warnings`、`error`。

规则：

- 前端不得发明后端未返回的评分字段。
- valueScore / confidence 不能写成新闻真伪判断。
- `rank`、`hotScore`、`valueScore` 为 0 时必须显示真实 0，不和未知混淆。
- Evidence summary 只作为证据摘要，不是最终点评。

## 7. 状态机

Assessment recommendation：

```text
promote
normal
suppress
review
```

Background status：

```text
pending -> completed
pending -> partial
pending -> failed
```

ReviewFlag status：

```text
open -> resolved
open -> dismissed
```

AssessmentRun status：

```text
queued -> running -> succeeded
queued -> running -> partial_failed
queued -> running -> failed
queued -> cancelled
```

UI 规则：

- `review`、`suppress`、`open`、`partial_failed`、`failed` 必须有明显状态。
- `partial` background 不能显示为 completed。
- 状态变化只来自 API 响应；前端可以做 loading，但成功态必须以返回 envelope 为准。

## 8. Agent 输入输出

M4 前端不运行 Agent，只展示 ValueScorer / BackgroundResearcher 的输入输出。

展示输入：

- topic 引用。
- topic members / source trust 的摘要。
- assessment run 参数：`topicIds/since/take/includeBackground/dryRun/reason`。

展示输出：

- `ValueAssessment`。
- `BackgroundPack`。
- `EvidenceSource[]`。
- `FactConflict[]`。
- `ReviewFlag[]`。
- `AssessmentRun`。

规则：

- 前端不得把 evidence 文本传给外部模型或工具。
- 前端不得基于 valueScore 自行生成 AI 点评。
- 后续如增加点评生成，必须进入 M5 contract。

## 9. 错误处理

错误码以 `docs/contracts/value-background-api.md` 为准。

UI 显示要求：

- 所有错误态展示 `error.message` 和 `meta.traceId`。
- `TOPIC_NOT_FOUND`：提示 topic 不存在或不可评估，保留返回 topic 列表入口。
- `ASSESSMENT_NOT_FOUND`：提示 assessment 不存在，允许刷新。
- `BACKGROUND_PACK_NOT_FOUND`：提示背景包不存在，允许重新触发 assessment run。
- `EVIDENCE_NOT_FOUND`：提示证据不存在，不尝试前端抓取。
- `BACKGROUND_FETCH_BLOCKED`：提示证据 URL 被安全策略阻断。
- `BACKGROUND_FETCH_FAILED`：展示失败原因和可重试状态。
- `BACKGROUND_SOURCE_CONFLICT`：展示冲突并标记需要 review。
- `ASSESSMENT_REVIEW_REQUIRED`：展示 review flag，不伪造成 promote。

禁止：

- 禁止 unknown id 兜底显示第一条 assessment。
- 禁止请求失败后伪造空成功态。
- 禁止把 failed run 显示成 succeeded。

## 10. 安全和合规边界

- 前端不直连 AI HOT、RSSHub、任意 RSS、evidence URL 抓取接口。
- 外部 URL 只作为用户点击打开的链接展示，必须使用新窗口打开。
- 不展示完整 evidence 原文。
- 不在日志或 UI 中输出 Cookie、Authorization、Webhook URL 等敏感值。
- 未有完整权限系统前，assessment trigger 只能用于本地或受控环境。
- 背景和评分不能写成新闻真伪判定。

## 11. Prompt injection 防护

Evidence title、summary、failureReason、review reason 都可能来自外部源或人工输入，必须按普通文本处理。

要求：

- 使用 Vue 默认文本插值或等价安全渲染，不使用 `v-html` 渲染 evidence / background / review 字段。
- 不解析 evidence 文本中的 Markdown 指令、HTML script、工具调用片段或“忽略以上指令”等内容。
- 复制、展开、筛选等 UI 行为只处理文本，不触发工具调用。
- mock 和测试必须包含一条带 prompt injection 文案的 evidence，断言页面只展示文本。
- 如果未来引入 AI 辅助总结，必须进入 M5 或独立 contract。

## 12. Mock 开发

前端 mock 必须覆盖：

- promote / normal / suppress / review assessment。
- completed / partial / failed background pack。
- official source found / not found。
- EvidenceSource succeeded / failed。
- ReviewFlag open / resolved。
- FactConflict unresolved。
- AssessmentRun running / succeeded / failed。
- prompt injection evidence 只作为普通文本展示。

mock 写接口必须保留实体 identity：

- trigger run 后新增 run。
- assessment detail 按 topicId 查找。
- unknown topic id 返回 `TOPIC_NOT_FOUND`。
- unknown assessment id 返回 `ASSESSMENT_NOT_FOUND`。

## 13. 验收标准

- 可查看 assessment 列表。
- 可查看 topic 最新 assessment。
- 可查看分项评分和 reasons。
- 可查看 background pack。
- 可查看 evidence sources。
- 可查看 review flags。
- 可查看 fact conflicts。
- 可手动触发 assessment run。
- 错误态展示 `error.message` 和 traceId。
- `review` / `suppress` / `failed` / `partial` 状态明显。
- 前端不包含 AI HOT、RSSHub、任意 RSS 或 evidence URL 直连 fetch。
- 移动端不出现主要内容重叠或横向溢出。
- prompt injection 样本文案只作为普通文本展示，不触发 HTML 渲染或工具调用。

## 14. 测试要求

- API client query string / request body 测试。
- mock envelope shape 测试。
- ScoreBreakdown 展示测试。
- recommendation badge 测试。
- BackgroundPack officialSourceStatus 展示测试。
- EvidenceSource failed 展示测试。
- ReviewFlag open 展示测试。
- FactConflict unresolved 展示测试。
- unknown id 错误测试。
- prompt injection 文本安全渲染测试。

## 15. 设计约束

- 工作台风格，信息密度优先。
- 不做营销式落地页。
- 列表在移动端可降级为卡片。
- 状态必须比装饰更突出。
- 不使用颜色作为唯一状态表达。
- 长 URL、长标题、长 reason 必须换行，不造成横向溢出。
- 不把 valueScore 写成事实真伪评分。
- 背景区域必须标注证据 URL 和抓取状态。

## 16. 联调边界

- 后端未实现前，前端只使用 mock。
- 后端实现后，先联调 value assessments，再联调 background packs / evidence / flags。
- 真实联调不要求实时新闻内容，只断言 schema、状态和 UI 行为。
- 如果 contract 发现缺口，先更新 `docs/contracts/value-background-api.md`，再更新前端和后端。

## 17. 迁移或兼容策略

- M4 前端必须新增 Assessment Console，不破坏 M1 QueryConsole、M2 SourceConsole、M3 Topic Console。
- API client 可新增 value-background client 模块；不得把 M4 字段混入 M3 clustering 类型。
- mock 数据应独立 reset，避免 M4 run / assessment 测试污染 M3 topic mock。
- 后端未实现 M4 API 前，前端只能在 mock 模式开发，不伪造真实联调已完成。
- 如果 M4 contract 字段调整，先更新 `docs/contracts/value-background-api.md`，再同步类型、mock 和组件。

## 18. 已知风险

- M4 没有完整权限系统，真实生产前不能开放 assessment trigger API 给公网。
- 价值分容易被误解为事实真伪，UI 必须明确这是推荐价值判断。
- 背景包如果证据不足，必须显示 not_found / partial / failed，不能制造完整感。
- prompt injection evidence 必须安全渲染。
- mock 写状态必须可 reset，否则测试会相互污染。
