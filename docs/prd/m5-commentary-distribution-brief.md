# M5 AI 点评与分发 Brief

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 阶段性质：路线级 brief，进入 M5 开发前需升级为详细 PRD
> 上游依赖：M4 ValueAssessment、BackgroundPack
> 下游依赖：M6 管理后台、M7 可观测

## 1. 目标

基于证据包和价值判断生成可读热点点评，并按订阅和渠道规则分发。M5 关注“怎么表达”和“怎么不重复、不越权地发送”。

## 2. 范围

### In Scope

- TopicCommentary。
- 短版和长版点评。
- what / why / impact / next / confidence / evidence 结构。
- 订阅匹配。
- 至少一个群机器人渠道。
- Webhook JSON 输出。
- DeliveryRecord。
- 按 topic/subscription/channel 去重。
- 推送历史和失败原因。

### Out of Scope

- 完整多渠道矩阵。
- 富文本卡片深度定制。
- 大规模用户画像。
- 自动生成无证据事实。

## 3. 输入与输出

输入：

- HotTopicCluster。
- ValueAssessment。
- BackgroundPack。
- Subscription。
- DeliveryChannel。

输出：

- TopicCommentary。
- RenderedMessage。
- DeliveryRecord。
- PushTrace。

## 4. 关键决策

- 点评 Agent 只能基于 topic、assessment、background pack 生成。
- 低置信内容必须降调表达。
- 分发 Agent 不能改写事实。
- 外发前可配置人工确认。
- 所有渠道密钥脱敏展示和脱敏日志。

## 5. 验收标准

- 每条点评都有 evidence URL。
- 点评结构包含是什么、为什么重要、影响谁、后续看什么、置信度。
- 同一 topic 不会在同一 subscriber/channel 重复发送。
- Webhook payload 是机器可读 JSON。
- 发送失败有可追踪原因和重试策略。
- 推送内容不包含未授权密钥。

## 6. 进入详细 PRD 前要补齐

- TopicCommentary schema。
- 推送模板。
- 订阅匹配规则。
- channel adapter 接口。
- delivery 幂等键。
- Webhook 签名方案。
- 点评 eval fixture 和无源事实检查。
