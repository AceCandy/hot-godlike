# M3 去重聚类与趋势 API 共享契约

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 上游依赖：M2 `docs/contracts/collection-api.md`、统一 response envelope
> 使用对象：M3 后端去重聚类服务、M3 前端 Topic Console、自动化测试、不同 AI coding 客户端
> 原则：M3 只消费 M2 `RawItem` / `FetchRun` / `SourceConfig` / `SourceHealth`，不直接调用 source fetcher，不做 M4 价值评分、M5 AI 点评和分发。

## 1. 目标

定义 M3 阶段的热点主题、成员、合并拆分历史、趋势快照和聚类运行 API。后端按本文实现；前端按本文展示和触发；测试按本文构造 fixture。任何实现不得绕过 M2 `raw_items` 直接抓取 RSS/RSSHub/AI HOT。

M3 覆盖：

- 从 M2 `RawItem` 生成 `HotTopicCluster`。
- 同 `normalizedUrl` 跨源自动合并。
- 标题相似只生成候选或 `needs_review`，不单独自动合并。
- 人工 merge / split。
- `TopicMember` 幂等写入。
- `MergeHistory` 持久记录。
- `TrendSnapshot` 基础排名/热度快照。
- 聚类运行记录、错误码、trace。

## 2. 全局约定

### 2.1 Base URL

沿用 M1/M2：

```text
http://localhost:8000/api
```

### 2.2 响应 envelope

所有 API 仍使用统一 envelope：

```json
{
  "data": {},
  "meta": {
    "traceId": "tr_20260603_000001",
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
    "traceId": "tr_20260603_000001",
    "source": "hot-godlike",
    "cached": false,
    "query": {},
    "warnings": []
  },
  "error": {
    "code": "TOPIC_NOT_FOUND",
    "message": "热点主题不存在。",
    "details": {
      "topicId": "topic_20260603_abcd1234"
    },
    "retryable": false
  }
}
```

### 2.3 分页

M3 列表 API 使用 cursor 分页：

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
- 聚类候选默认时间窗为 72 小时，按 `RawItem.publishedAt ?? RawItem.fetchedAt` 计算。

## 3. 枚举

### 3.1 TopicStatus

```ts
type TopicStatus =
  | "candidate"
  | "clustered"
  | "needs_review"
  | "suppressed"
  | "archived";
```

说明：

- `candidate`：系统发现但聚类证据不足。
- `clustered`：规则确认的同一事件簇。
- `needs_review`：标题相似、主体相近、来源冲突或人工标记，需要审核。
- `suppressed`：M3 只允许人工压制，不做价值降权判断。
- `archived`：人工合并或拆分后不再作为活跃 topic 处理。

`assessed`、`approved`、`published` 属于 M4/M5/M6 下游状态，不在 M3 自动写入。

### 3.2 TopicMemberRole

```ts
type TopicMemberRole = "primary" | "supporting" | "duplicate" | "split_from";
```

### 3.3 MergeAction

```ts
type MergeAction =
  | "auto_merge"
  | "candidate"
  | "manual_merge"
  | "manual_split"
  | "suppress"
  | "restore";
```

### 3.4 MergeReason

```ts
type MergeReason =
  | "same_normalized_url"
  | "same_canonical_url"
  | "title_similarity_candidate"
  | "manual_same_event"
  | "manual_different_event"
  | "time_window_exceeded"
  | "shared_entity_only"
  | "source_conflict"
  | "other";
```

### 3.5 ClusteringRunStatus

```ts
type ClusteringRunStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "partial_failed"
  | "failed"
  | "cancelled";
```

## 4. 数据结构

### 4.1 HotTopicCluster

```json
{
  "id": "topic_20260603_abcd1234",
  "title": "OpenAI 发布新模型示例",
  "canonicalUrl": "https://example.com/openai-model",
  "primaryRawItemId": "raw_src_a_001",
  "primarySourceId": "src_aihot_api",
  "status": "clustered",
  "confidence": 0.98,
  "sourceIds": ["src_aihot_api", "src_github_blog"],
  "memberCount": 2,
  "firstSeenAt": "2026-06-03T00:00:00Z",
  "lastSeenAt": "2026-06-03T01:10:00Z",
  "lastMergedAt": "2026-06-03T01:10:00Z",
  "reviewReasons": [],
  "createdAt": "2026-06-03T00:00:01Z",
  "updatedAt": "2026-06-03T01:10:01Z"
}
```

字段规则：

- `id/title/canonicalUrl/primaryRawItemId/primarySourceId/status/firstSeenAt/lastSeenAt` 必须存在。
- `canonicalUrl` 使用首个 primary member 的 `normalizedUrl`；人工 merge 后可更新为 target topic 的代表链接。
- `confidence` 范围 0-1。
- 自动 URL 合并时 `confidence` 默认不低于 0.95。
- 标题相似候选不得把 `status` 写成 `clustered`，只能保持独立 topic 并记录 candidate history，或把相关 topic 标记为 `needs_review`。
- `sourceIds` 去重排序，来自成员 RawItem 的 `sourceId`。

### 4.2 TopicMember

```json
{
  "id": "member_20260603_001",
  "topicId": "topic_20260603_abcd1234",
  "rawItemId": "raw_src_a_001",
  "sourceId": "src_aihot_api",
  "role": "primary",
  "title": "OpenAI 发布新模型示例",
  "url": "https://example.com/openai-model?utm_source=rss",
  "normalizedUrl": "https://example.com/openai-model",
  "publishedAt": "2026-06-03T00:00:00Z",
  "fetchedAt": "2026-06-03T00:00:03Z",
  "addedAt": "2026-06-03T00:00:04Z",
  "mergeReason": "same_normalized_url"
}
```

字段规则：

- `topicId + rawItemId` 必须唯一。
- 同一个 `rawItemId` 在活跃 topic 中只能出现一次。
- `title/url/normalizedUrl/publishedAt/fetchedAt` 来自 M2 RawItem 快照，用于前端展示；不得编造缺失字段。
- `role=duplicate` 表示该成员是同 topic 内重复来源，不表示 M2 `RawItem.status=duplicate`。

### 4.3 MergeHistory

```json
{
  "id": "merge_20260603_001",
  "action": "auto_merge",
  "topicId": "topic_20260603_abcd1234",
  "sourceTopicId": null,
  "targetTopicId": "topic_20260603_abcd1234",
  "rawItemIds": ["raw_src_a_001", "raw_src_b_002"],
  "reason": "same_normalized_url",
  "reasonText": "normalizedUrl 完全一致，自动合并。",
  "confidence": 0.98,
  "actorType": "system",
  "actorId": null,
  "createdAt": "2026-06-03T01:10:01Z",
  "traceId": "tr_20260603_000001"
}
```

字段规则：

- 每次自动合并、候选生成、人工合并、人工拆分、压制、恢复都必须写历史。
- `action=candidate` 用于标题相似、共享主体、时间窗接近但不能自动合并的情况。
- `reasonText` 必须可展示给审核员，不能是空字符串。
- 人工动作必须写 `actorType="user"` 和 `actorId`。

### 4.4 TrendSnapshot

```json
{
  "id": "trend_20260603_001",
  "topicId": "topic_20260603_abcd1234",
  "rawItemId": "raw_src_a_001",
  "sourceId": "src_aihot_api",
  "rank": 3,
  "hotScore": "91",
  "sourceWeight": 1.0,
  "capturedAt": "2026-06-03T00:00:03Z",
  "createdAt": "2026-06-03T00:00:04Z"
}
```

字段规则：

- M3 只记录来源自身提供的 `rank` / `hotScore` 快照，不计算 M4 价值分。
- `rank` 和 `hotScore` 均可为空；两者都为空时仍可记录出现快照，但前端必须标为“无排名/热度数据”。
- 趋势结论只能表述为“系统已采集范围内的出现/排名变化”，不能表述为全网真实热度。

### 4.5 ClusteringRun

```json
{
  "id": "cluster_run_20260603_000001",
  "trigger": "manual",
  "status": "succeeded",
  "startedAt": "2026-06-03T01:00:00Z",
  "finishedAt": "2026-06-03T01:00:04Z",
  "durationMs": 4000,
  "scannedRawItemCount": 20,
  "createdTopicCount": 6,
  "mergedMemberCount": 12,
  "candidateCount": 2,
  "snapshotCount": 18,
  "errorCode": null,
  "errorMessage": null,
  "traceId": "tr_20260603_000001"
}
```

`trigger` 枚举：

```ts
type ClusteringTrigger = "manual" | "schedule" | "retry";
```

## 5. 聚类规则

### 5.1 自动合并规则

自动合并只允许以下证据：

1. `RawItem.normalizedUrl` 非空且完全一致。
2. 人工已确认两个 topic 是同一事件，后续同 URL member 可按该 topic 归并。

自动合并必须：

- 写入 `TopicMember`。
- 更新 `HotTopicCluster.sourceIds/memberCount/lastSeenAt/lastMergedAt/updatedAt`。
- 写入 `MergeHistory(action=auto_merge, reason=same_normalized_url)`。
- 保持幂等，同一个 `rawItemId` 重跑不新增 member。

### 5.2 候选规则

标题相似、共享公司名、共享人物名、同时间窗、同 source category 只能生成候选：

- 不得把 raw item 自动加入已有 topic。
- 不得因为标题相似直接合并两个 topic。
- 必须写 `MergeHistory(action=candidate, reason=title_similarity_candidate | shared_entity_only | other)`。
- 至少一个相关 topic 应进入 `needs_review`，供人工 merge / split。

### 5.3 时间窗规则

- 默认候选窗口：72 小时。
- 超过 72 小时的同主体事件默认拆成不同发展阶段。
- 如果人工确认是同一事件，可以手动 merge，并写 `manual_same_event`。

### 5.4 人工 merge / split 规则

- 人工 merge 必须提供 reason。
- 人工 split 必须指定要移动的 `TopicMember.id` 集合，并提供新 topic 标题或使用 primary member 标题。
- merge / split 后必须保留原 history，不能删除旧 topic 或旧 member 记录。
- 被 merge 走全部活跃 member 的 source topic 状态改为 `archived`。

## 6. 错误码

| code | HTTP | retryable | 场景 |
|---|---:|:---:|---|
| `BAD_REQUEST` | 400 | 否 | 参数格式错误 |
| `TOPIC_NOT_FOUND` | 404 | 否 | topic 不存在 |
| `TOPIC_MEMBER_NOT_FOUND` | 404 | 否 | topic member 不存在 |
| `RAW_ITEM_NOT_FOUND` | 404 | 否 | M2 raw item 不存在 |
| `CLUSTERING_RUN_NOT_FOUND` | 404 | 否 | clustering run 不存在 |
| `CLUSTER_MERGE_CONFLICT` | 409 | 否 | merge 目标冲突或跨状态不允许 |
| `CLUSTER_SPLIT_INVALID` | 400 | 否 | split 成员为空、成员不属于 topic 或会留下空 topic |
| `CLUSTER_REVIEW_REQUIRED` | 409 | 否 | 规则证据不足，必须人工确认 |
| `CLUSTERING_SOURCE_NOT_READY` | 409 | 是 | M2 RawItem / FetchRun 仍在写入或源数据不可用 |
| `INTERNAL_ERROR` | 500 | 否 | 未知错误 |

## 7. API 端点

### 7.1 触发聚类

```http
POST /api/clustering-runs
```

请求体：

```json
{
  "rawItemIds": ["raw_src_a_001"],
  "since": "2026-06-02T00:00:00Z",
  "take": 100,
  "dryRun": false,
  "idempotencyKey": "manual_cluster_20260603_001",
  "reason": "manual smoke"
}
```

响应：`ClusteringRun`

规则：

- `rawItemIds` 和 `since` 至少传一个；都不传时后端可使用默认未处理 raw item 窗口，但必须写入 `meta.query`。
- `take` 范围 1-500。
- `dryRun=true` 不写 topic/member/history/snapshot，只返回将要执行的 run 统计和 warnings。
- 同一 `idempotencyKey` 重复请求返回同一个或等价 run。

### 7.2 查询 clustering runs

```http
GET /api/clustering-runs?status=succeeded&take=50&cursor=opaque
```

响应：分页 `ClusteringRun[]`。

### 7.3 查询 clustering run 详情

```http
GET /api/clustering-runs/{runId}
```

响应：`ClusteringRun`

### 7.4 查询 topic 列表

```http
GET /api/topics?status=needs_review&sourceId=src_aihot_api&q=OpenAI&take=50&cursor=opaque
```

响应：分页 `HotTopicCluster[]`。

筛选：

- `status`
- `sourceId`
- `q`：标题搜索。
- `from` / `to`：按 `lastSeenAt` 时间窗筛选。

### 7.5 查询 topic 详情

```http
GET /api/topics/{topicId}
```

响应：

```json
{
  "topic": {},
  "members": [],
  "recentHistory": [],
  "recentTrendSnapshots": []
}
```

### 7.6 查询 topic members

```http
GET /api/topics/{topicId}/members?take=50&cursor=opaque
```

响应：分页 `TopicMember[]`。

### 7.7 人工 merge

```http
POST /api/topics/{targetTopicId}/merge
```

请求体：

```json
{
  "sourceTopicIds": ["topic_20260603_efgh5678"],
  "rawItemIds": [],
  "reason": "manual_same_event",
  "reasonText": "审核确认两条都是同一次模型发布。"
}
```

响应：

```json
{
  "topic": {},
  "movedMembers": [],
  "history": {}
}
```

规则：

- `sourceTopicIds` 和 `rawItemIds` 至少一个非空。
- 不允许把 `archived` topic 作为 target。
- 人工 merge 不做价值判断，不改变 M4/M5 下游产物。

### 7.8 人工 split

```http
POST /api/topics/{topicId}/split
```

请求体：

```json
{
  "memberIds": ["member_20260603_002"],
  "newTopicTitle": "另一个独立事件",
  "reason": "manual_different_event",
  "reasonText": "共享公司名但发布内容不同。"
}
```

响应：

```json
{
  "sourceTopic": {},
  "newTopic": {},
  "movedMembers": [],
  "history": {}
}
```

规则：

- `memberIds` 必须都属于 `topicId`。
- 不允许把原 topic 拆空；如果要完全归档，使用 merge 或 suppress。
- split 后两个 topic 都必须更新 `sourceIds/memberCount/firstSeenAt/lastSeenAt`。

### 7.9 压制 / 恢复 topic

```http
POST /api/topics/{topicId}/suppress
POST /api/topics/{topicId}/restore
```

请求体：

```json
{
  "reasonText": "人工确认是重复噪音或误聚类残留。"
}
```

响应：`HotTopicCluster`

规则：

- M3 suppress 只影响 Topic Console 展示和后续候选，不等同于 M4 价值降权。
- 所有动作必须写 `MergeHistory`。

### 7.10 查询 merge history

```http
GET /api/merge-history?topicId=topic_20260603_abcd1234&action=candidate&take=50&cursor=opaque
```

响应：分页 `MergeHistory[]`。

### 7.11 查询 trend snapshots

```http
GET /api/trend-snapshots?topicId=topic_20260603_abcd1234&sourceId=src_aihot_api&take=100&cursor=opaque
```

响应：分页 `TrendSnapshot[]`。

## 8. 存储契约

M3 必须落 PostgreSQL 表：

- `hot_topic_clusters`
- `topic_members`
- `merge_history`
- `trend_snapshots`
- `clustering_runs`

建议索引：

- `hot_topic_clusters(status, last_seen_at desc)`
- `hot_topic_clusters(canonical_url)`
- `topic_members(topic_id, added_at desc)`
- `topic_members(raw_item_id)` unique for active membership
- `topic_members(normalized_url)`
- `merge_history(topic_id, created_at desc)`
- `trend_snapshots(topic_id, captured_at desc)`
- `clustering_runs(status, started_at desc)`

可选 Redis key：

- `cluster:lock:run`：聚类运行全局锁。
- `topic:lock:{topic_id}`：人工 merge / split 互斥锁。

PostgreSQL unique constraint 是最终兜底；Redis 只能做并发控制和快速路径。

## 9. 安全与事实边界

- M3 不直接访问外部 URL。
- M3 不把 RawItem 文本作为系统 prompt 或工具指令执行。
- 标题相似、共享实体、embedding 相似在 M3 只做候选，不自动合并。
- 趋势只基于系统已采集范围，不代表全网真实热度。
- 人工 reason / reasonText 进入审计记录，不能被空值或默认值替代。
- 失败必须返回可见错误或 failed run，不允许伪造聚类成功。

## 10. Mock Fixture 要求

后端测试必须提供：

- same normalized URL 跨源 fixture。
- same company different event 反例 fixture。
- title similarity candidate fixture。
- 72 小时窗口内候选 fixture。
- 超过 72 小时不同发展阶段 fixture。
- manual merge fixture。
- manual split fixture。
- trend snapshot rank / hotScore fixture。

前端 mock 必须覆盖：

- topic 列表有结果 / 空结果。
- topic detail。
- members 列表。
- needs_review 候选。
- manual merge 成功 / 冲突。
- manual split 成功 / invalid。
- merge history。
- trend snapshots 有数据 / 无排名数据。
- clustering run succeeded / failed / running。

## 11. 非目标

M3 不包含：

- 直接调用 source fetcher。
- 新增采集源。
- M4 价值评分。
- 背景补全。
- AI 点评。
- 分发推送。
- 复杂前端趋势图。
- embedding 聚类生产级效果优化。
- LLM 难例判定完整实现。
- 登录、权限、多租户完整实现。
