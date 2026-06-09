# M3 前端 Topic Console 子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/clustering-api.md`
> 上游依赖：M2 SourceConsole / RawItem 展示
> 推荐实现客户端：前端 AI coding 客户端
> 技术栈决策：Vue 3 + Vite + Tailwind CSS。

## 1. 目标

实现 M3 阶段的轻量 Topic Console，让管理员或开发者可以查看热点主题、成员条目、候选/待审原因、合并拆分历史和基础趋势快照，并执行人工 merge / split / suppress / restore。

M3 前端不是完整审核后台，不展示 M4 价值评分、M5 点评分发，也不做复杂趋势图。

## 2. 范围

### 2.1 In Scope

- Topic 列表。
- Topic 状态筛选。
- Topic 搜索。
- Topic 详情。
- TopicMember 列表。
- needs_review 候选提示。
- MergeHistory 列表。
- TrendSnapshot 基础表格。
- 手动触发 clustering run。
- ClusteringRun 列表。
- 人工 merge。
- 人工 split。
- suppress / restore。
- 错误态、加载态、空状态。
- 使用 mock API 并行开发。
- 移动端基本适配。

### 2.2 Out of Scope

- 价值评分展示。
- 背景包展示。
- AI 点评编辑。
- 分发推送。
- 完整权限系统。
- 复杂趋势图和多维分析图。
- 直接抓取外部 URL。
- 直接调用 AI HOT、RSSHub 或 RSS。

## 3. 页面结构

M3 可在 M2 “数据源”入口旁增加“热点主题”入口，或独立创建 Topic Console 页面。实现方式可按项目实际路由决定。

### 3.1 Topic 列表

展示字段：

- 标题。
- status。
- confidence。
- sourceIds / 来源数。
- memberCount。
- firstSeenAt。
- lastSeenAt。
- reviewReasons。
- 操作：查看详情、merge、split、suppress / restore。

筛选：

- status。
- sourceId。
- q。
- from / to。

规则：

- `needs_review` 必须有明显状态。
- `confidence` 只是聚类置信，不是价值评分。
- 长标题和 URL 必须换行，不能横向溢出。

### 3.2 Topic 详情

展示：

- topic 标题。
- canonicalUrl。
- primary source。
- firstSeenAt / lastSeenAt。
- status。
- confidence。
- sourceIds。
- memberCount。
- reviewReasons。

行为：

- 点击 canonicalUrl 新窗口打开原文。
- 显示 traceId / error message 的位置要稳定。
- 不展示 M2 raw payload。

### 3.3 TopicMember 列表

展示字段：

- role。
- title。
- sourceId。
- url。
- normalizedUrl。
- publishedAt。
- fetchedAt。
- mergeReason。

行为：

- 点击标题新窗口打开原文。
- 缺发布时间显示“发布时间未知”。
- 缺排名/热度不显示成 `0`。

### 3.4 MergeHistory 列表

展示字段：

- action。
- reason。
- reasonText。
- confidence。
- actorType / actorId。
- createdAt。
- traceId。

规则：

- `candidate` history 必须能让审核员看出为什么需要 review。
- 人工 merge / split 必须显示 reasonText。

### 3.5 TrendSnapshot 表格

展示字段：

- sourceId。
- rawItemId。
- rank。
- hotScore。
- capturedAt。

规则：

- rank / hotScore 缺失时显示“无排名/热度数据”。
- 页面文案必须限定为“系统已采集范围内”。
- M3 不做复杂趋势图；可以用轻量表格或简单时间线。

### 3.6 ClusteringRun 面板

展示字段：

- run id。
- trigger。
- status。
- startedAt / finishedAt。
- durationMs。
- scannedRawItemCount。
- createdTopicCount。
- mergedMemberCount。
- candidateCount。
- snapshotCount。
- errorCode / errorMessage。

行为：

- 可手动触发 clustering run。
- failed / partial_failed 用明显状态展示。
- 手动触发需要 reason。

### 3.7 人工 Merge

输入：

- targetTopicId。
- sourceTopicIds 或 rawItemIds。
- reason。
- reasonText。

行为：

- 默认从当前 topic 作为 target。
- reasonText 必填。
- 成功后刷新 target topic、source topic 列表、history。
- 冲突展示 `error.message` 和 traceId。

### 3.8 人工 Split

输入：

- topicId。
- memberIds。
- newTopicTitle。
- reason。
- reasonText。

行为：

- 至少选择 1 个 member。
- 不允许选择全部 member 导致原 topic 为空。
- 成功后展示 source topic 和 new topic。
- invalid 展示 `CLUSTER_SPLIT_INVALID` 对应错误。

## 4. 组件建议

- `TopicConsolePage`
- `TopicList`
- `TopicDetailPanel`
- `TopicMemberList`
- `MergeHistoryList`
- `TrendSnapshotTable`
- `ClusteringRunPanel`
- `TopicMergeDialog`
- `TopicSplitDialog`
- `TopicStatusBadge`
- `ClusteringApiStateView`

## 5. API 使用

以 `docs/contracts/clustering-api.md` 为唯一契约。

前端调用：

```text
POST /api/clustering-runs
GET /api/clustering-runs
GET /api/clustering-runs/{runId}
GET /api/topics
GET /api/topics/{topicId}
GET /api/topics/{topicId}/members
POST /api/topics/{targetTopicId}/merge
POST /api/topics/{topicId}/split
POST /api/topics/{topicId}/suppress
POST /api/topics/{topicId}/restore
GET /api/merge-history
GET /api/trend-snapshots
```

前端不得调用：

```text
https://aihot.virxact.com/*
RSSHub base URL
任意 RSS URL
```

## 6. 数据模型

前端类型以 `docs/contracts/clustering-api.md` 为唯一来源，至少需要覆盖以下 contract shape：

- `HotTopicCluster`
- `TopicMember`
- `MergeHistory`
- `TrendSnapshot`
- `ClusteringRun`
- 统一 `Envelope<T>`
- 统一 `ApiError`
- cursor 分页 response

本地 UI 派生状态只允许保存展示需要的字段：

- 当前选中 `topicId`。
- 当前筛选条件：`status/sourceId/q/from/to`。
- 当前 merge / split 表单输入。
- 最近一次 API envelope 的 `traceId`、`warnings`、`error`。

规则：

- 前端不得发明后端未返回的 topic 字段。
- `confidence` 只作为聚类置信，不转成价值评分。
- `rank` / `hotScore` 为空时展示“无排名/热度数据”，不得按 `0` 处理。
- `rawItemId`、`topicId`、`memberId` 必须保持原始字符串，不在 UI 中重新生成。

## 7. 状态机

Topic 状态以 contract 为准：

```text
candidate -> clustered
candidate -> needs_review
clustered -> needs_review
clustered -> suppressed -> clustered
candidate/clustered/needs_review -> archived
```

ClusteringRun 状态以 contract 为准：

```text
queued -> running -> succeeded
queued -> running -> partial_failed
queued -> running -> failed
queued -> cancelled
```

UI 规则：

- `needs_review`、`partial_failed`、`failed` 必须有明显状态。
- `suppressed` topic 默认仍可查看详情和 history，但不作为默认高亮内容。
- `archived` topic 只读展示，不提供 merge target 操作。
- 状态变化只来自 API 响应；前端可以做乐观 loading，但成功态必须以返回 envelope 为准。

## 8. Agent 输入输出

M3 前端不运行 Agent，只展示 Clusterer 逻辑 Agent 的输入输出。

展示输入：

- `RawItem` 引用：通过 `TopicMember.rawItemId`、title、url、sourceId 展示。
- 聚类触发参数：manual run 的 `rawItemIds/since/take/dryRun/reason`。

展示输出：

- `HotTopicCluster`。
- `TopicMember[]`。
- `MergeHistory[]`。
- `TrendSnapshot[]`。
- `ClusteringRun`。

规则：

- 前端不得把 RawItem 文本当成可执行指令。
- 前端不得把 topic title、reasonText、summary 传给外部模型或工具。
- 后续如增加 LLM 难例判定，需要新增独立 PRD / contract，不在 M3 Topic Console 内隐式实现。

## 9. 错误处理

错误码以 `docs/contracts/clustering-api.md` 为准。

UI 显示要求：

- 所有错误态展示 `error.message` 和 `meta.traceId`。
- `TOPIC_NOT_FOUND`：提示 topic 不存在或已被归档，并保留返回列表入口。
- `TOPIC_MEMBER_NOT_FOUND`：提示成员不存在，允许刷新 topic detail。
- `RAW_ITEM_NOT_FOUND`：提示上游 RawItem 不存在，不尝试重新抓取外部源。
- `CLUSTER_MERGE_CONFLICT`：保持 merge dialog 输入，展示冲突原因。
- `CLUSTER_SPLIT_INVALID`：保持 split 选择，提示非法成员或拆空 topic。
- `CLUSTER_REVIEW_REQUIRED`：提示需要人工确认，不伪造成自动合并成功。
- `CLUSTERING_SOURCE_NOT_READY`：提示 M2 数据仍不可用或写入中，允许稍后重试。

禁止：

- 禁止 unknown id 兜底显示第一条 topic。
- 禁止请求失败后伪造空成功态。
- 禁止把 failed run 显示成 succeeded。

## 10. 安全和合规边界

- 前端不直连 AI HOT、RSSHub、任意 RSS 或外部原文抓取接口。
- 外部 URL 只作为用户点击打开的链接展示，必须使用新窗口打开。
- 不展示 raw payload。
- 不在日志或 UI 中输出 Cookie、Authorization、Webhook URL 等敏感值。
- manual merge / split / suppress / restore 在未有完整权限系统前只能用于本地或受控环境。
- 趋势区域必须标注“系统已采集范围内”，避免被误解为全网真实热度。

## 11. Prompt injection 防护

Topic Console 展示的 title、url、reasonText、content snippet 都可能来自外部源或人工输入，必须按普通文本处理。

要求：

- 使用 Vue 默认文本插值或等价安全渲染，不使用 `v-html` 渲染 RawItem / Topic / MergeHistory 字段。
- 不解析 RawItem 文本中的 Markdown 指令、HTML script、工具调用片段或“忽略以上指令”等内容。
- 复制、展开、筛选等 UI 行为只处理文本，不触发工具调用。
- mock 和测试必须包含一条带 prompt injection 文案的 RawItem / Topic，断言页面只展示文本。
- 如果未来引入 AI 辅助审核，必须另起 contract，不能复用 Topic Console 的展示文本作为系统 prompt。

## 12. Mock 开发

前端 mock 必须覆盖：

- Topic 列表有结果。
- Topic 列表为空。
- `needs_review` topic。
- Topic 详情。
- TopicMember 列表。
- MergeHistory candidate / auto_merge / manual_merge / manual_split。
- TrendSnapshot 有 rank / hotScore。
- TrendSnapshot 无 rank / hotScore。
- ClusteringRun running / succeeded / failed。
- manual merge 成功。
- manual merge conflict。
- manual split 成功。
- manual split invalid。
- suppress / restore 成功。
- prompt injection 文案只作为普通文本展示。

mock 写接口必须保留实体 identity：

- merge 后 target topic 的 members 增加。
- source topic 被归档或成员减少。
- split 后创建 new topic。
- unknown topic id 返回 `TOPIC_NOT_FOUND`，不得兜底返回第一条 topic。

## 13. 验收标准

- 可查看 topic 列表。
- 可按 status / sourceId / q 筛选。
- 可查看 topic 详情。
- 可查看 topic members。
- 可查看 merge history。
- 可查看 trend snapshots。
- 可手动触发 clustering run。
- 可查看 clustering run 状态。
- 可人工 merge topic。
- 可人工 split topic。
- 可 suppress / restore topic。
- title similarity candidate / needs_review 有明显展示。
- 错误态展示 `error.message` 和 traceId。
- 前端不包含 AI HOT、RSSHub、任意 RSS 直连 fetch。
- 移动端不出现主要内容重叠或横向溢出。
- prompt injection 样本文案只作为普通文本展示，不触发 HTML 渲染或工具调用。

## 14. 测试要求

- API client query string / request body 测试。
- mock envelope shape 测试。
- Topic status badge 测试。
- needs_review 展示测试。
- merge 成功后本地状态同步测试。
- split 成功后本地状态同步测试。
- unknown topic id 错误测试。
- TrendSnapshot 缺 rank / hotScore 展示测试。
- prompt injection 文本安全渲染测试。

## 15. 设计约束

- 工作台风格，信息密度优先。
- 不做营销式落地页。
- 列表在移动端可降级为卡片。
- 状态必须比装饰更突出。
- 不使用颜色作为唯一状态表达。
- 长 URL 和长标题必须换行，不造成横向溢出。
- 不把聚类置信写成价值评分。
- 趋势区域必须标注数据范围是“系统已采集范围内”。

## 16. 联调边界

- 后端未实现前，前端只使用 mock。
- 后端实现后，先联调 topic list / detail，再联调 merge / split。
- 真实联调不要求实时新闻内容，只断言 schema、状态和 UI 行为。
- 如果 contract 发现缺口，先更新 `docs/contracts/clustering-api.md`，再更新前端和后端。

## 17. 迁移或兼容策略

- M3 前端必须新增 Topic Console，不破坏 M1 QueryConsole 和 M2 SourceConsole。
- API client 可新增 clustering client 模块；不得把 M3 字段混入 M2 collection 类型。
- mock 数据应独立 reset，避免 M3 merge / split 测试污染 M2 source mock。
- 后端未实现 M3 API 前，前端只能在 mock 模式开发，不伪造真实联调已完成。
- 如果 M3 contract 字段调整，先更新 `docs/contracts/clustering-api.md`，再同步类型、mock 和组件。

## 18. 已知风险

- M3 没有完整权限系统，真实生产前不能开放 merge / split API 给公网。
- 候选原因如果展示不清晰，会导致审核员误合并；前端必须展示 reasonText 和 source evidence。
- 趋势表格容易被误解为全网热度，页面必须限定数据范围。
- mock 写状态必须可 reset，否则测试会相互污染。
