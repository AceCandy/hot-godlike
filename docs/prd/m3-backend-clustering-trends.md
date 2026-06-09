# M3 后端去重聚类与趋势子 PRD

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 共享契约：`docs/contracts/clustering-api.md`
> 上游依赖：M2 `RawItem`、`FetchRun`、`SourceConfig`、`SourceHealth`
> 推荐实现客户端：后端 / worker AI coding 客户端
> 技术栈决策：Python + FastAPI + PostgreSQL；Redis 只作为可选锁，不作为长期存储。

## 1. 目标

实现 M3 阶段的后端去重聚类与趋势基础能力：读取 M2 已入库 `RawItem`，按规则生成 `HotTopicCluster`、`TopicMember`、`MergeHistory`、`TrendSnapshot`，并提供 Topic Console 所需 API。

M3 的目标是把原始条目升级为可审核、可追踪的事件级对象。M3 不直接抓取外部源，不做价值评分，不做背景补全，不生成 AI 点评，不推送。

## 2. 背景与依赖

M2 已完成或定义：

- Source Registry。
- FetchRun。
- RawItem。
- SourceHealth。
- RSS/RSSHub/AI HOT fetcher。
- 源内去重。
- PostgreSQL/Redis 外部依赖边界。

M3 在此基础上扩展：

- 从“源内 RawItem”变成“跨源事件 topic”。
- 使用 `normalizedUrl` 做确定性跨源合并。
- 使用标题相似、时间窗、共享主体做 review 候选，不自动合并。
- 保存人工 merge / split 历史。
- 保存基础趋势快照，供后续 M4/M5/M7 使用。

## 3. 范围

### 3.1 In Scope

- `POST /api/clustering-runs`
- `GET /api/clustering-runs`
- `GET /api/clustering-runs/{runId}`
- `GET /api/topics`
- `GET /api/topics/{topicId}`
- `GET /api/topics/{topicId}/members`
- `POST /api/topics/{targetTopicId}/merge`
- `POST /api/topics/{topicId}/split`
- `POST /api/topics/{topicId}/suppress`
- `POST /api/topics/{topicId}/restore`
- `GET /api/merge-history`
- `GET /api/trend-snapshots`
- PostgreSQL schema 和 migration。
- RawItem read repository。
- Topic repository。
- TopicMember repository。
- MergeHistory repository。
- TrendSnapshot repository。
- ClusteringRun repository。
- 规则聚类服务。
- 人工 merge / split 服务。
- 基础趋势快照服务。
- 单元测试、集成测试、OpenAPI 自查。

### 3.2 Out of Scope

- 直接调用 RSS/RSSHub/AI HOT fetcher。
- 新增采集源。
- M4 价值评分、噪音判断和推荐理由。
- 背景补全 Agent。
- AI 点评 Agent。
- 分发推送。
- 登录、权限、多租户完整实现。
- 复杂 embedding 聚类效果优化。
- LLM 难例判定完整实现。
- 前端复杂趋势图。

## 4. 用户故事 / 系统场景

### 4.1 相同 URL 跨源自动合并

系统看到两个 source 抓到同一 `normalizedUrl`。M3 创建或复用同一个 topic，把两个 raw item 写为 topic members，并记录 `MergeHistory(action=auto_merge, reason=same_normalized_url)`。

### 4.2 标题相似但不自动合并

系统看到两个标题都提到 OpenAI，但 URL 不同、发布时间接近。M3 不把它们自动合并，只创建候选历史或把相关 topic 标记为 `needs_review`，等待人工确认。

### 4.3 人工合并候选 topic

审核员确认两个候选 topic 是同一事件，调用 merge API。系统移动 members，归档 source topic，记录 `manual_merge` 历史。

### 4.4 人工拆分误聚类

审核员发现某个 topic 中有一条 member 属于另一事件，调用 split API。系统创建新 topic，移动 member，保留原 topic 和新 topic 的 history。

### 4.5 记录趋势快照

系统从 RawItem 的 `rank` / `hotScore` 写入 `TrendSnapshot`。前端只能展示“系统已采集范围内”的来源排名/热度变化。

## 5. 模块设计

### 5.1 RawItemReader

职责：

- 从 M2 `raw_items` 读取待聚类条目。
- 按 `rawItemIds`、`since`、`take` 查询。
- 返回 M2 contract shape，不暴露 raw payload。

规则：

- M3 只能读 M2 已入库数据。
- 缺失 `id/title/url/sourceId/fetchedAt` 的 RawItem 不参与聚类，run 计入 skipped 或 failed detail。
- 不能调用 `FetcherPool`、`SourcePreviewer` 或任何外部 URL fetcher。

### 5.2 TopicClusterer

职责：

- 执行规则优先聚类。
- 按 `normalizedUrl` 找现有 topic。
- 生成新 topic。
- 写 topic member。
- 写 merge history。
- 生成 title similarity candidate。

规则：

- `normalizedUrl` 完全一致才自动合并。
- 标题相似不能自动合并。
- 共享公司名、共享人物名、共享 source category 不能自动合并。
- 默认时间窗为 72 小时。
- 每次自动合并必须可解释。

### 5.3 TopicRepository

职责：

- 创建 topic。
- 查询 topic 列表和详情。
- 更新 topic 聚合字段。
- 设置 status。
- 归档被 merge 走全部成员的 source topic。

聚合字段：

- `sourceIds`
- `memberCount`
- `firstSeenAt`
- `lastSeenAt`
- `lastMergedAt`
- `confidence`
- `reviewReasons`

### 5.4 TopicMemberRepository

职责：

- 幂等写入 member。
- 查询 topic members。
- split / merge 时移动 member。
- 保证同一 raw item 不在多个活跃 topic 中重复出现。

规则：

- `topic_id + raw_item_id` unique。
- `raw_item_id` active membership unique。
- 移动 member 时写 updated timestamp。

### 5.5 MergeHistoryService

职责：

- 记录自动合并、候选、人工合并、人工拆分、压制、恢复。
- 查询 history。
- 为前端提供可读 reason。

规则：

- 历史不可物理删除。
- 人工动作必须记录 actor 和 reasonText。
- 系统动作必须记录 traceId。

### 5.6 ManualReviewService

职责：

- 人工 merge。
- 人工 split。
- suppress / restore topic。
- 校验冲突和空 topic。

规则：

- merge / split 必须在事务内完成。
- 不允许 split 后原 topic 为空。
- 不允许 archived topic 作为 merge target。
- 失败返回显式 contract error。

### 5.7 TrendSnapshotService

职责：

- 从 RawItem 的 `rank`、`hotScore`、`sourceId`、`fetchedAt` 生成快照。
- 查询 topic / source 维度快照。

规则：

- 不计算价值分。
- 不推断全网热度。
- rank/hotScore 缺失时仍可记录出现快照。

### 5.8 ClusteringRunService

职责：

- 管理 run 状态。
- 支持 idempotency key。
- 记录 scanned / created / merged / candidate / snapshot 计数。
- 记录 failed / partial_failed。

状态机：

```text
queued -> running -> succeeded
queued -> running -> partial_failed
queued -> running -> failed
queued -> cancelled
```

## 6. 数据库 Schema

### 6.1 `hot_topic_clusters`

字段：

- `id` text primary key
- `title` text not null
- `canonical_url` text not null
- `primary_raw_item_id` text not null references raw_items(id)
- `primary_source_id` text not null references sources(id)
- `status` text not null
- `confidence` numeric not null
- `source_ids` jsonb not null
- `member_count` integer not null default 0
- `first_seen_at` timestamptz not null
- `last_seen_at` timestamptz not null
- `last_merged_at` timestamptz null
- `review_reasons` jsonb not null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

索引：

- `hot_topic_clusters(status, last_seen_at desc)`
- `hot_topic_clusters(canonical_url)`
- `hot_topic_clusters(primary_source_id, last_seen_at desc)`

### 6.2 `topic_members`

字段：

- `id` text primary key
- `topic_id` text not null references hot_topic_clusters(id)
- `raw_item_id` text not null references raw_items(id)
- `source_id` text not null references sources(id)
- `role` text not null
- `title` text not null
- `url` text not null
- `normalized_url` text not null
- `published_at` timestamptz null
- `fetched_at` timestamptz not null
- `added_at` timestamptz not null
- `merge_reason` text not null
- `active` boolean not null default true

唯一约束：

- `topic_id + raw_item_id`
- `raw_item_id where active = true`

索引：

- `topic_members(topic_id, added_at desc)`
- `topic_members(normalized_url)`
- `topic_members(source_id, fetched_at desc)`

### 6.3 `merge_history`

字段：

- `id` text primary key
- `action` text not null
- `topic_id` text not null references hot_topic_clusters(id)
- `source_topic_id` text null references hot_topic_clusters(id)
- `target_topic_id` text null references hot_topic_clusters(id)
- `raw_item_ids` jsonb not null
- `reason` text not null
- `reason_text` text not null
- `confidence` numeric null
- `actor_type` text not null
- `actor_id` text null
- `created_at` timestamptz not null
- `trace_id` text not null

索引：

- `merge_history(topic_id, created_at desc)`
- `merge_history(action, created_at desc)`
- `merge_history(trace_id)`

### 6.4 `trend_snapshots`

字段：

- `id` text primary key
- `topic_id` text not null references hot_topic_clusters(id)
- `raw_item_id` text not null references raw_items(id)
- `source_id` text not null references sources(id)
- `rank` integer null
- `hot_score` text null
- `source_weight` numeric not null default 1
- `captured_at` timestamptz not null
- `created_at` timestamptz not null

唯一约束：

- `topic_id + raw_item_id + captured_at`

索引：

- `trend_snapshots(topic_id, captured_at desc)`
- `trend_snapshots(source_id, captured_at desc)`

### 6.5 `clustering_runs`

字段：

- `id` text primary key
- `trigger` text not null
- `status` text not null
- `started_at` timestamptz not null
- `finished_at` timestamptz null
- `duration_ms` integer null
- `scanned_raw_item_count` integer not null default 0
- `created_topic_count` integer not null default 0
- `merged_member_count` integer not null default 0
- `candidate_count` integer not null default 0
- `snapshot_count` integer not null default 0
- `error_code` text null
- `error_message` text null
- `trace_id` text not null
- `idempotency_key` text null

唯一约束：

- `idempotency_key where idempotency_key is not null`

## 7. API 实现要求

以 `docs/contracts/clustering-api.md` 为准。

所有 API 必须：

- 使用统一 envelope。
- 有 trace id。
- 不返回完整 raw payload。
- 对外错误使用简体中文。
- 写操作预留鉴权 dependency。
- 人工动作记录 actor 边界；M3 可先使用 dev actor，但不能静默为空。

## 8. 聚类算法要求

### 8.1 输入准备

1. 读取 RawItem。
2. 丢弃或记录缺失必要字段的 RawItem。
3. 使用 M2 `normalizedUrl`；如为空，生成新 candidate topic，不做自动合并。
4. 按 `publishedAt ?? fetchedAt` 排序，保证重跑稳定。

### 8.2 相同 URL 自动合并

1. 查找活跃 topic 中是否存在相同 `canonicalUrl` 或 active member `normalizedUrl`。
2. 有则写入 member。
3. 无则创建 topic。
4. 写入 auto merge history。
5. 更新 topic 聚合字段。

### 8.3 标题候选

1. 只在 72 小时窗口内查找标题相似 topic。
2. 相似度阈值先写成可配置常量。
3. 命中后只写 candidate history，并把相关 topic 置为 `needs_review`。
4. 不移动 member，不合并 topic。

### 8.4 人工 merge

1. 校验 target topic 活跃。
2. 锁定 target 和 source topics。
3. 移动 source topic active members 或指定 raw items。
4. 归档空 source topic。
5. 写 manual merge history。
6. 重算 target 聚合字段。

### 8.5 人工 split

1. 校验 member 全部属于 source topic。
2. 校验 split 后 source topic 不为空。
3. 创建 new topic。
4. 移动指定 members。
5. 写 manual split history。
6. 分别重算两个 topic。

## 9. Agent 输入输出

M3 Clusterer Agent 是逻辑 Agent，不要求独立 LLM。

输入：

- `RawItem[]`
- `SourceConfig.trustLevel`
- 历史 `HotTopicCluster`
- 历史 `TopicMember`
- `ClusteringTrigger`

输出：

- `ClusteringRun`
- `HotTopicCluster[]`
- `TopicMember[]`
- `MergeHistory[]`
- `TrendSnapshot[]`

Trace：

- 每次 run 必须记录 trace id。
- 每次自动合并和候选生成必须能追到 run。

## 10. 错误处理

必须实现 `docs/contracts/clustering-api.md` 的错误码。

错误映射：

- 参数错误：`BAD_REQUEST`
- topic 不存在：`TOPIC_NOT_FOUND`
- member 不存在：`TOPIC_MEMBER_NOT_FOUND`
- raw item 不存在：`RAW_ITEM_NOT_FOUND`
- run 不存在：`CLUSTERING_RUN_NOT_FOUND`
- merge 冲突：`CLUSTER_MERGE_CONFLICT`
- split 非法：`CLUSTER_SPLIT_INVALID`
- 证据不足：`CLUSTER_REVIEW_REQUIRED`
- M2 数据不可用：`CLUSTERING_SOURCE_NOT_READY`

## 11. 安全与合规

- M3 不执行外部 URL fetch。
- M3 不使用 LLM 处理外部文本。
- RawItem 标题、摘要、URL 作为不可信输入处理。
- 人工 reasonText 不得包含密钥或隐私数据；日志按普通用户输入处理。
- 不允许用训练记忆补新闻事实。
- 趋势说明必须标注“系统已采集范围内”。

## 12. Prompt injection 防护

M3 默认不调用 LLM，但仍必须把外部内容当作不可信输入处理，避免后续 M4/M5 复用 topic 时把注入文本带入模型上下文。

要求：

- RawItem 的 `title`、`summary`、`contentSnippet`、`author`、`url` 只作为数据字段存储和展示，不得作为系统指令、工具指令或 prompt 模板片段执行。
- `MergeHistory.reasonText` 是人工输入，只能作为审计说明，不得拼接进系统 prompt。
- Topic title 可以由 RawItem title 派生，但必须保持纯文本，不解析 HTML、Markdown 指令或工具调用格式。
- 后续如引入 LLM 难例判定，必须新增独立 contract / prompt version / eval fixture，并把输入限定为结构化字段和只读 evidence。
- 测试 fixture 需要覆盖包含“忽略以上指令”“调用工具”“泄露密钥”等文本的 RawItem，断言 M3 只保存和展示，不执行。

## 13. 测试 Fixture

必须创建：

- `fixtures/m3_same_url_cross_source.json`
- `fixtures/m3_same_company_different_events.json`
- `fixtures/m3_title_similarity_candidate.json`
- `fixtures/m3_time_window_boundary.json`
- `fixtures/m3_manual_merge.json`
- `fixtures/m3_manual_split.json`
- `fixtures/m3_trend_snapshots.json`
- `fixtures/m3_prompt_injection_raw_item.json`

Fixture 不得包含真实密钥、cookie、授权头。

## 14. 测试要求

### 14.1 单元测试

- RawItemReader 查询参数。
- same normalized URL 自动合并。
- 同 raw item 重跑幂等。
- 标题相似只生成 candidate / needs_review。
- 共享公司名不同事件不合并。
- 72 小时窗口边界。
- manual merge。
- manual split。
- suppress / restore。
- TrendSnapshot rank / hotScore 缺失处理。
- ClusteringRun idempotency。
- RawItem prompt injection 文本只作为普通字段处理。

### 14.2 集成测试

- 通过 M2 raw_items fixture 触发 clustering run。
- 查询 topics 列表和详情。
- 查询 members。
- 查询 merge history。
- 查询 trend snapshots。
- OpenAPI 包含 M3 endpoints。
- 失败路径返回统一 envelope。

测试不能断言实时新闻标题。

## 15. 验收标准

- 相同 `normalizedUrl` 跨源 RawItem 自动合并到同一 topic。
- 同一个 raw item 重跑不会产生重复 member。
- 标题相似不会自动合并，只生成 candidate 或 `needs_review`。
- 明显不同事件不因同一公司名误合并。
- 人工 merge 后 source topic 归档，target topic 成员和来源集合正确。
- 人工 split 后新旧 topic 成员、来源集合、时间字段正确。
- 每次自动合并、候选、人工操作都有 `MergeHistory`。
- 每个 topic 有首次发现、最后更新、来源集合、成员列表。
- 趋势快照记录 source、rank/hotScore、capturedAt。
- M3 不调用 source fetcher，不新增采集副作用。
- Prompt injection 样本文本不会触发工具调用、外部请求或系统指令执行。

## 16. 交付物

- PostgreSQL migration。
- Topic model / repository / service。
- TopicMember model / repository / service。
- MergeHistory model / repository / service。
- TrendSnapshot model / repository / service。
- ClusteringRun model / repository / service。
- RawItemReader。
- TopicClusterer。
- ManualReviewService。
- API routes。
- fixtures。
- 单元测试和集成测试。
- README 更新，写清 M3 只消费 M2 RawItem。

## 17. 联调边界

- 前端只调用 `docs/contracts/clustering-api.md` 定义的 M3 API。
- 前端可通过 M2 RawItem 链接查看原始条目，但不能直连外部源。
- M3 后端只读 M2 `raw_items`，不调用 fetcher。
- 如果 contract 变更，先改 `docs/contracts/clustering-api.md`，再改后端和前端。

## 18. 迁移或兼容策略

- M3 migration 必须只新增表和索引，不修改 M2 `sources`、`fetch_runs`、`raw_items`、`source_health` 既有字段。
- M3 表通过外键引用 M2 `raw_items.id` 和 `sources.id`；如果本地环境仍使用内存 store，M3 后端实现必须保持禁用或 mock 模式，不伪造 PostgreSQL 已启用。
- 首次启用 M3 时只处理已有 `raw_items`，不得重新触发 source fetch。
- `raw_item_id` active membership unique 是幂等兜底；重复 run 应复用或跳过已有 member。
- contract 变更顺序固定为：先更新 `docs/contracts/clustering-api.md`，再更新后端 PRD / 前端 PRD，最后改实现和测试。
- PostgreSQL migration smoke 会创建临时数据库结构，执行前需单独确认影响范围。

## 19. 已知风险

- 标题相似阈值容易误伤，M3 必须保守，只做 candidate。
- `normalizedUrl` 质量依赖 M2 normalizer；发现规则缺口时先更新 M2/M3 contract，再改实现。
- PostgreSQL migration smoke 会创建临时数据库结构，需要用户单独确认后执行。
- 趋势快照不能代表全网热度，只能代表系统采集范围。
- 未做权限前，人工 merge/split API 不能暴露到公网。
