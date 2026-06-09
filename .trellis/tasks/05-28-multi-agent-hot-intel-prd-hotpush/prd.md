# 多 Agent 热点情报系统 PRD 修订任务

## Goal

把根目录 `prd.md` 从“AI HOT 公开数据查询 Agent”升级为“多 Agent 热点情报系统”的产品需求文档，并结合 `JackyST0/hotpush` 的采集、调度、过滤、推送、趋势能力作为基础设施参考。

## What I Already Know

- 用户希望系统由多类 Agent 组成：采集、去重聚类、价值判断、背景补全、AI 点评、分发。
- 现有 `prd.md` 已完成 AI HOT 网站能力盘点和 AI HOT API 查询 Agent 设计。
- `hotpush` 是 Python/FastAPI + Vue 的热点聚合推送平台，支持 RSSHub/RSS、多源热榜、定时抓取、规则过滤、AI 摘要、多渠道推送和趋势分析。
- `hotpush` 更适合作为“采集与分发基础设施”参考，不应被写成具备完整语义聚类/事实核验/多 Agent 编排。

## Requirements

- 更新根目录 `prd.md`，明确新产品定位为多 Agent 热点情报系统。
- 保留 AI HOT 作为可信种子数据源，不删除前一版实测事实。
- 新增 `hotpush` 参考研究与产品映射。
- 新增多 Agent 架构、职责边界、输入输出、状态流转。
- 新增多源采集、事件聚类、价值判断、背景补全、点评、分发等需求。
- 将 M1 拆成共享 API Contract、后端查询内核子 PRD、前端查询工作台子 PRD，便于不同 AI coding 客户端并行实现。
- 为 M2-M7 创建路线级 brief，保证后续阶段有方向但不过早锁死实现细节。
- 创建根目录 `workflow.md`，强制后续开发按阶段、契约和 PRD 流程推进。
- 明确不编造：`hotpush` 只作为已读仓库能力参考；未在仓库中确认的能力不能写成事实。

## Acceptance Criteria

- [x] `prd.md` 中有多 Agent 总体架构。
- [x] `prd.md` 中有 HotPush 可参考能力和不能照搬的边界。
- [x] `prd.md` 中有各 Agent 的职责、输入、输出、验收标准。
- [x] `prd.md` 中有事件簇数据模型或等价设计。
- [x] `prd.md` 中有完整范围的执行拆分，覆盖从种子源查询到多 Agent 情报系统。
- [x] 已创建 `docs/contracts/query-api.md`、`docs/prd/m1-backend-query-core.md`、`docs/prd/m1-frontend-query-console.md`。
- [x] 已创建 M2-M7 路线级 brief：采集、聚类趋势、价值背景、点评分发、管理后台、评估可观测。
- [x] 已创建 `workflow.md` 并在总 PRD 中引用。

## Research References

- [`research/hotpush-reference.md`](research/hotpush-reference.md) — HotPush 采集、缓存、规则、推送、趋势和 AI 摘要能力梳理。
