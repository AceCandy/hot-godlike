# M4 价值判断与背景补全 Brief

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 阶段性质：路线级 brief，进入 M4 开发前需升级为详细 PRD
> 上游依赖：M3 HotTopicCluster
> 下游依赖：M5 AI 点评、M6 审核后台、M7 评估

## 1. 目标

对热点主题做可解释价值判断，并为高价值或高风险主题补齐证据和背景。M4 的输出必须让系统知道哪些 topic 值得展示、哪些需要人工 review、哪些应被压制。

## 2. 范围

### In Scope

- ValueAssessment。
- 重要性、新鲜度、可信度、传播强度、用户相关性、噪音风险评分。
- 推荐、正常、压制、review 四类建议。
- 背景包 BackgroundPack。
- 官方来源、关联来源、历史背景、未解决问题。
- 来源冲突标注。
- 高影响低置信进入 review。

### Out of Scope

- 生成最终 AI 点评。
- 外部分发。
- 完整人工审核前端。
- 自动判定新闻真实性。

## 3. 输入与输出

输入：

- HotTopicCluster。
- TopicMember。
- Source trust level。
- 用户规则或系统规则。

输出：

- ValueAssessment。
- BackgroundPack。
- ReviewFlag。
- 评分解释和背景证据 URL。

## 4. 关键决策

- 分项评分必须可解释。
- 二手媒体可作为关联来源，不单独支撑关键事实。
- 官方博客、论文、公告、GitHub release、监管文件优先级最高。
- 未找到官方来源时必须明确标注。
- 背景补全失败时保留失败原因，不补写事实。

## 5. 验收标准

- 每个 assessed topic 有总分、分项分、推荐理由。
- 标题党、营销、重复转述可以降权或进入 review。
- 高影响低置信、来源冲突、疑似敏感进入 review。
- 背景包至少区分原始来源、关联来源、历史背景。
- 关键事实有证据 URL。
- 低置信内容不能进入确定性表达链路。

## 6. 进入详细 PRD 前要补齐

- 评分权重和阈值。
- review/suppress/promote 状态转换规则。
- 背景补全抓取范围和最大 URL 数。
- 官方来源识别规则。
- 事实冲突标注 schema。
- 价值判断 eval fixture。
