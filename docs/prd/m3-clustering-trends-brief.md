# M3 去重聚类与趋势 Brief

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 阶段性质：路线级 brief，进入 M3 开发前需升级为详细 PRD
> 上游依赖：M2 RawItem 与 FetchRun
> 下游依赖：M4 价值判断、M5 分发、M7 评估

## 1. 目标

把源内重复和跨源同一事件聚合成 `HotTopicCluster`，并记录基础热度/排名快照，为后续价值判断、背景补全、推送和趋势分析提供事件级对象。

## 2. 范围

### In Scope

- 源内去重。
- URL 归一化。
- 标题相似度候选。
- 72 小时时间窗候选。
- 相同 URL 自动合并。
- topic、topic_member、merge_history。
- 人工合并/拆分接口的后端能力。
- ranking / hot score snapshot。
- 首次抓取不推送的状态延续。

### Out of Scope

- LLM 难例判定的完整实现。
- embedding 聚类的生产级效果优化。
- 价值评分。
- 背景补全。
- 前端复杂趋势图。

## 3. 输入与输出

输入：

- RawItem。
- SourceConfig trust level。
- 历史 HotTopicCluster。

输出：

- HotTopicCluster。
- TopicMember。
- MergeHistory。
- TrendSnapshot。
- 聚类解释。

## 4. 关键决策

- URL 归一后完全一致自动合并。
- 标题相似只能产生候选，不单独自动合并。
- 不同事件不得仅因共享公司名合并。
- 超过 72 小时的同主体事件默认拆成不同发展阶段。
- 所有自动合并必须保留 merge reason。

## 5. 验收标准

- 同 URL 跨源条目合并到同一 topic。
- 重复抓取不会产生重复 topic member。
- 明显不同事件不因同一公司名误合并。
- 人工拆分后保留历史和原因。
- 每个 topic 有首次发现、最后更新、来源集合、成员列表。
- 趋势快照能记录 source、rank/hot score、captured_at。

## 6. 进入详细 PRD 前要补齐

- URL 归一化规则表。
- 标题相似算法和阈值。
- topic 状态机和数据库约束。
- merge/split API contract。
- TrendSnapshot 表结构。
- 聚类 eval fixture：正例、反例、边界例。
