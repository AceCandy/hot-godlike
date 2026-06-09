# M7 评估与可观测 Brief

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 阶段性质：路线级 brief，进入 M7 开发前需升级为详细 PRD
> 上游依赖：M1-M6 全链路能力
> 下游依赖：持续迭代和质量回归

## 1. 目标

建立多 Agent 系统的评估、追踪、日志、指标和回放能力，防止路由、采集、聚类、评分、点评、分发在迭代中退化。

## 2. 范围

### In Scope

- 固定 eval 集。
- 路由 eval。
- 采集归一化 eval。
- 聚类正反例 eval。
- 价值评分 eval。
- 背景补全证据检查。
- 点评无源事实检查。
- 分发去重 eval。
- Agent run trace。
- 工具调用日志。
- token 和成本统计。
- 错误率、耗时、请求量、推送量看板。
- Agent run 回放。

### Out of Scope

- 企业级 APM 全量替代。
- 大规模在线 A/B 实验。
- 自动判定新闻真实性。

## 3. 输入与输出

输入：

- AgentRun。
- FetchRun。
- DeliveryRecord。
- AuditLog。
- 固定 fixture。
- 线上运行样本。

输出：

- EvalReport。
- TraceView。
- MetricsDashboard。
- RegressionFailure。

## 4. 关键决策

- eval fixture 必须版本化。
- 真实 API smoke test 不能断言具体新闻标题。
- 所有对外输出必须能追溯到证据 URL。
- 模型或 prompt 变更必须跑 eval。
- 缓存内容不得冒充最新数据。

## 5. 验收标准

- 每个 Agent run 有 trace id、状态、输入输出引用、耗时、错误。
- 每次分发能追溯到 topic、commentary、delivery 和证据 URL。
- eval 能覆盖路由、聚类、评分、点评、分发关键路径。
- CI 或本地命令能运行核心 eval。
- 管理台能查看最近运行、失败原因和成本。
- 发现无源事实、重复推送、误聚类时 eval 失败。

## 6. 进入详细 PRD 前要补齐

- eval fixture 目录结构。
- EvalReport schema。
- trace 存储方案。
- 指标命名和 dashboard 范围。
- prompt/model 版本管理规则。
- CI 命令。
- 采样和数据保留策略。
