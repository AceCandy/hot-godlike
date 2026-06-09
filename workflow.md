# 热点情报系统开发 Workflow

> 版本：v0.8
> 最后更新：2026-06-09
> 适用项目：多 Agent 热点情报系统 / hot-godlike
> 强制性：后续开发必须按本文流程执行。任何 AI coding 客户端开始编码前，都必须先读取本文。
> 关系说明：`.trellis/workflow.md` 负责 Trellis 任务生命周期；本文负责本产品的 PRD、契约、阶段、前后端协作和验收流程。若两者冲突，先暂停并更新文档，不允许口头绕过。

## 1. 强制总原则

- `prd.md` 是完整产品范围，不是某一阶段的实现清单。
- `docs/prd/*` 是阶段实现边界。
- `docs/contracts/*` 是前后端、测试和多客户端协作边界。
- 先契约，后实现；先 PRD，后代码。
- 不允许跳过契约直接实现。
- 不允许前端直接调用 AI HOT。
- 不允许为了跑通加入 silent fallback、伪数据、无源新闻补充或假成功路径。
- 不允许使用模型训练记忆补新闻事实；所有热点事实必须来自可追溯源。
- 不允许把 M3-M7 brief 当成可直接开发的详细 PRD。
- 每个阶段完成后，文档、实现、测试、已知限制必须同步。

## 2. 每次开发启动流程

任一 AI coding 客户端接到开发任务后，必须按顺序执行：

1. 读取 `AGENTS.md`，确认仓库级规范。
2. 读取 `workflow.md`，确认本产品强制流程。
3. 读取 `prd.md`，确认完整产品范围。
4. 读取当前任务进度文件：`.trellis/tasks/<task-dir>/progress.md`。
5. 判断当前任务属于哪个阶段：M1-M7。
6. 读取该阶段的 contract 和阶段 PRD。
7. 如果该阶段只有 brief，没有详细 PRD，则只允许补文档，不允许写业务代码。
8. 明确本次客户端角色：后端、前端、契约、测试、运维、文档。
9. 给出本次改动计划和受影响文件。
10. 写测试、fixture 或 mock，再实现。
11. 跑对应验证命令。
12. 更新文档、已知限制和任务进度。

最低启动命令建议：

```bash
sed -n '1,260p' workflow.md
sed -n '1,220p' prd.md
```

进入 M1 后端：

```bash
sed -n '1,260p' docs/contracts/query-api.md
sed -n '1,260p' docs/prd/m1-backend-query-core.md
```

进入 M1 前端：

```bash
sed -n '1,260p' docs/contracts/query-api.md
sed -n '1,280p' docs/prd/m1-frontend-query-console.md
```

进入 M2 后端：

```bash
sed -n '1,320p' docs/contracts/collection-api.md
sed -n '1,320p' docs/prd/m2-backend-collection-core.md
sed -n '1,220p' .trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/progress.md
```

进入 M2 前端：

```bash
sed -n '1,320p' docs/contracts/collection-api.md
sed -n '1,260p' docs/prd/m2-frontend-source-console.md
sed -n '1,220p' .trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/progress.md
```

进入 M3 文档复核或编码前确认：

```bash
sed -n '1,360p' docs/contracts/clustering-api.md
sed -n '1,360p' docs/prd/m3-backend-clustering-trends.md
sed -n '1,300p' docs/prd/m3-frontend-topic-console.md
sed -n '1,260p' .trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/progress.md
```

进入 M4 文档复核或编码前确认：

```bash
sed -n '1,380p' docs/contracts/value-background-api.md
sed -n '1,380p' docs/prd/m4-backend-value-background.md
sed -n '1,320p' docs/prd/m4-frontend-assessment-console.md
sed -n '1,280p' .trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/progress.md
```

进入 M5 文档复核或编码前确认：

```bash
sed -n '1,420p' docs/contracts/commentary-distribution-api.md
sed -n '1,420p' docs/prd/m5-backend-commentary-distribution.md
sed -n '1,360p' docs/prd/m5-frontend-commentary-distribution-console.md
sed -n '1,300p' .trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/progress.md
```

进入 M6 文档复核或编码前确认：

```bash
sed -n '1,420p' docs/contracts/admin-rules-api.md
sed -n '1,420p' docs/prd/m6-backend-admin-rules.md
sed -n '1,380p' docs/prd/m6-frontend-admin-rules-console.md
sed -n '1,320p' .trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/progress.md
```

进入 M7 文档复核或编码前确认：

```bash
sed -n '1,420p' docs/contracts/eval-observability-api.md
sed -n '1,420p' docs/prd/m7-backend-eval-observability.md
sed -n '1,380p' docs/prd/m7-frontend-observability-console.md
sed -n '1,340p' .trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/progress.md
```

## 3. 文档层级

### 3.1 产品总 PRD

```text
prd.md
```

用途：

- 定义完整产品范围。
- 定义多 Agent 分工。
- 定义全局原则、验收标准、不做范围。
- 记录 AI HOT 与 HotPush 的事实依据和未验证范围。
- 不能替代阶段详细 PRD。

### 3.2 共享契约

```text
docs/contracts/*.md
```

用途：

- 定义 API、数据结构、错误码、分页、状态机、事件、fixture。
- 作为前端、后端、测试和不同 AI coding 客户端的唯一协作边界。
- 契约变更必须先于实现变更。

当前已具备：

```text
docs/contracts/query-api.md
docs/contracts/collection-api.md
docs/contracts/clustering-api.md
docs/contracts/value-background-api.md
docs/contracts/commentary-distribution-api.md
docs/contracts/admin-rules-api.md
docs/contracts/eval-observability-api.md
```

### 3.3 阶段详细 PRD

```text
docs/prd/m1-backend-query-core.md
docs/prd/m1-frontend-query-console.md
docs/prd/m2-backend-collection-core.md
docs/prd/m2-frontend-source-console.md
docs/prd/m3-backend-clustering-trends.md
docs/prd/m3-frontend-topic-console.md
docs/prd/m4-backend-value-background.md
docs/prd/m4-frontend-assessment-console.md
docs/prd/m5-backend-commentary-distribution.md
docs/prd/m5-frontend-commentary-distribution-console.md
docs/prd/m6-backend-admin-rules.md
docs/prd/m6-frontend-admin-rules-console.md
docs/prd/m7-backend-eval-observability.md
docs/prd/m7-frontend-observability-console.md
```

用途：

- 定义某阶段某端的可开发需求。
- 明确 In Scope / Out of Scope。
- 明确模块、页面、接口、测试、验收标准和联调边界。

### 3.4 阶段 brief / 路线 brief

```text
docs/prd/m2-collection-brief.md
docs/prd/m3-clustering-trends-brief.md
docs/prd/m4-value-background-brief.md
docs/prd/m5-commentary-distribution-brief.md
docs/prd/m6-admin-rules-brief.md
docs/prd/m7-eval-observability-brief.md
```

用途：

- 锁定方向、依赖、输入输出、关键决策和验收方向。
- 作为后续详细 PRD 的骨架。
- 不作为直接编码依据。

说明：

- M2 已从 brief 升级出详细 contract 和前后端子 PRD；M2 开发必须使用 `docs/contracts/collection-api.md`、`docs/prd/m2-backend-collection-core.md`、`docs/prd/m2-frontend-source-console.md`。
- `docs/prd/m2-collection-brief.md` 只保留为路线参考，不再作为 M2 直接编码依据。
- M3 已从 brief 升级出详细 contract 和前后端子 PRD；M3 编码前必须使用 `docs/contracts/clustering-api.md`、`docs/prd/m3-backend-clustering-trends.md`、`docs/prd/m3-frontend-topic-console.md`，并确认文档可作为开发依据。
- `docs/prd/m3-clustering-trends-brief.md` 只保留为路线参考，不再作为 M3 直接编码依据。
- M4 已从 brief 升级出详细 contract 和前后端子 PRD；M4 编码前必须使用 `docs/contracts/value-background-api.md`、`docs/prd/m4-backend-value-background.md`、`docs/prd/m4-frontend-assessment-console.md`，并确认文档可作为开发依据。
- `docs/prd/m4-value-background-brief.md` 只保留为路线参考，不再作为 M4 直接编码依据。
- M5 已从 brief 升级出详细 contract 和前后端子 PRD；M5 编码前必须使用 `docs/contracts/commentary-distribution-api.md`、`docs/prd/m5-backend-commentary-distribution.md`、`docs/prd/m5-frontend-commentary-distribution-console.md`，并确认文档可作为开发依据。
- `docs/prd/m5-commentary-distribution-brief.md` 只保留为路线参考，不再作为 M5 直接编码依据。
- M6 已从 brief 升级出详细 contract 和前后端子 PRD；M6 编码前必须使用 `docs/contracts/admin-rules-api.md`、`docs/prd/m6-backend-admin-rules.md`、`docs/prd/m6-frontend-admin-rules-console.md`，并确认文档可作为开发依据。
- `docs/prd/m6-admin-rules-brief.md` 只保留为路线参考，不再作为 M6 直接编码依据。
- M7 已从 brief 升级出详细 contract 和前后端子 PRD；M7 编码前必须使用 `docs/contracts/eval-observability-api.md`、`docs/prd/m7-backend-eval-observability.md`、`docs/prd/m7-frontend-observability-console.md`，并确认文档可作为开发依据。
- `docs/prd/m7-eval-observability-brief.md` 只保留为路线参考，不再作为 M7 直接编码依据。

## 4. 阶段顺序

必须按以下顺序推进：

```text
M0 PRD 与架构冻结
  -> M1 公开查询与种子源内核
  -> M2 采集基础设施
  -> M3 去重聚类与趋势
  -> M4 价值判断与背景补全
  -> M5 AI 点评与分发
  -> M6 管理后台与规则
  -> M7 评估与可观测
```

允许同一阶段内前后端并行。

禁止跨阶段抢先实现下游能力，例如：

- M1 不做数据库、多源采集、聚类、订阅、推送。
- M2 不做语义聚类和价值评分。
- M3 不做最终 AI 点评分发。
- M4 不做订阅推送。
- M5 不做完整管理后台。

## 5. 当前阶段可开发状态

| 阶段 | 状态 | 是否可直接开发 | 依据 |
|---|---|:---:|---|
| M0 | 已完成初版 | 否 | `prd.md` 已作为总纲 |
| M1 后端 | 已具备详细 PRD | 是 | `docs/contracts/query-api.md` + `docs/prd/m1-backend-query-core.md` |
| M1 前端 | 已具备详细 PRD | 是 | `docs/contracts/query-api.md` + `docs/prd/m1-frontend-query-console.md` |
| M2 后端 | 已具备详细 PRD | 是 | `docs/contracts/collection-api.md` + `docs/prd/m2-backend-collection-core.md` |
| M2 前端 | 已具备详细 PRD | 是 | `docs/contracts/collection-api.md` + `docs/prd/m2-frontend-source-console.md` |
| M3 | 已具备详细 PRD，待确认编码入口 | 待确认 | `docs/contracts/clustering-api.md` + `docs/prd/m3-backend-clustering-trends.md` + `docs/prd/m3-frontend-topic-console.md` |
| M4 | 已具备详细 PRD，待确认编码入口 | 待确认 | `docs/contracts/value-background-api.md` + `docs/prd/m4-backend-value-background.md` + `docs/prd/m4-frontend-assessment-console.md` |
| M5 | 已具备详细 PRD，待确认编码入口 | 待确认 | `docs/contracts/commentary-distribution-api.md` + `docs/prd/m5-backend-commentary-distribution.md` + `docs/prd/m5-frontend-commentary-distribution-console.md` |
| M6 | 已具备详细 PRD，待确认编码入口 | 待确认 | `docs/contracts/admin-rules-api.md` + `docs/prd/m6-backend-admin-rules.md` + `docs/prd/m6-frontend-admin-rules-console.md` |
| M7 | 已具备详细 PRD，待确认编码入口 | 待确认 | `docs/contracts/eval-observability-api.md` + `docs/prd/m7-backend-eval-observability.md` + `docs/prd/m7-frontend-observability-console.md` |

## 6. M1 开发流程

### 6.1 M1 总入口

M1 是当前可继续迭代开发的阶段之一。M2 也已具备详细 contract 和子 PRD，可以按第 7 节直接开发。

后端客户端必须读取：

```text
docs/contracts/query-api.md
docs/prd/m1-backend-query-core.md
```

前端客户端必须读取：

```text
docs/contracts/query-api.md
docs/prd/m1-frontend-query-console.md
```

如果前后端并行开发，双方都以 `docs/contracts/query-api.md` 为准，不以对方临时代码为准。

### 6.2 M1 契约优先规则

任何 M1 前后端改动都必须先对齐：

```text
docs/contracts/query-api.md
```

如果实现过程中发现契约缺口：

1. 先更新 `docs/contracts/query-api.md`。
2. 再同步更新后端 PRD 或前端 PRD。
3. 再更新 mock / fixture。
4. 最后改代码。

禁止出现“后端已经这么写了，前端先适配”的临时隐式契约。

### 6.3 M1 后端实现顺序

后端按以下顺序实现：

1. 项目结构和 FastAPI 应用入口。
2. 健康检查。
3. 统一 response envelope。
4. 错误码和 `ErrorMapper`。
5. `IntentRouter`。
6. `QueryPlanner`。
7. `AihotClient`，含 User-Agent、timeout、retry、ETag。
8. `ResponseNormalizer`。
9. `CacheStore`。
10. `GET /api/query/items`。
11. `GET /api/query/daily`。
12. `GET /api/query/dailies`。
13. `GET /api/query/help`。
14. 单元测试。
15. mock AI HOT 集成测试。
16. OpenAPI 自查。

后端完成标准：

- 所有 API 符合 `docs/contracts/query-api.md`。
- 所有响应使用统一 envelope。
- 所有 AI HOT 请求带 User-Agent。
- 不返回 AI HOT 原始响应。
- 上游错误映射为统一错误 envelope。
- ETag / cache 命中必须显式标注 `meta.cached=true`。
- 上游失败时不得把旧缓存伪装为最新数据。
- 测试不依赖实时新闻标题。

### 6.4 M1 前端实现顺序

前端按以下顺序实现：

1. 项目结构和基础样式。
2. API client。
3. mock response / fixture。
4. `QueryConsolePage`。
5. 顶部查询区。
6. 模式切换。
7. 分类筛选。
8. 时间窗筛选。
9. 动态结果列表。
10. 日报视图。
11. 日报归档视图。
12. 空状态、错误态、加载态、警告态。
13. 移动端适配。
14. 前后端联调。

前端完成标准：

- 不包含 AI HOT endpoint 常量。
- 所有字段来自 `docs/contracts/query-api.md`。
- mock 数据符合契约。
- 空摘要显示“该条暂无摘要”。
- 未知发布时间显示“发布时间未知”。
- 错误态展示 `error.message` 和 `traceId`。
- `error.retryable=true` 时展示重试入口。
- 移动端主要内容不重叠。

### 6.5 M1 联调规则

联调必须按顺序执行：

1. 后端启动。
2. 前端配置 `VITE_API_BASE_URL`。
3. 调用 `/api/query/help` 验证 base URL。
4. 调用 `/api/query/items` 验证默认精选。
5. 调用 `/api/query/items?mode=all` 验证全部动态。
6. 调用 `/api/query/daily` 验证日报。
7. 调用 `/api/query/dailies` 验证归档。
8. 验证错误态和 trace id。
9. 验证移动端展示。

联调发现问题时：

- 契约问题：先改 `docs/contracts/query-api.md`。
- 后端实现问题：后端修复并补测试。
- 前端展示问题：前端修复并补 mock / 组件测试。
- 上游 AI HOT 不可用：保留真实错误，不伪造成功。

## 7. M2 开发流程

### 7.1 M2 总入口

M2 是当前可直接开发阶段。M2 的目标是采集基础设施，不做 M3-M7 的聚类、价值判断、背景补全、AI 点评和分发。

后端客户端必须读取：

```text
docs/contracts/collection-api.md
docs/prd/m2-backend-collection-core.md
.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/progress.md
```

前端客户端必须读取：

```text
docs/contracts/collection-api.md
docs/prd/m2-frontend-source-console.md
.trellis/tasks/05-28-multi-agent-hot-intel-prd-hotpush/progress.md
```

如果前后端并行开发，双方都以 `docs/contracts/collection-api.md` 为准，不以对方临时代码为准。

### 7.2 M2 契约优先规则

任何 M2 前后端、worker、scheduler、repository、Redis、migration 改动都必须先对齐：

```text
docs/contracts/collection-api.md
```

如果实现过程中发现契约缺口：

1. 先更新 `docs/contracts/collection-api.md`。
2. 再同步更新 `docs/prd/m2-backend-collection-core.md` 或 `docs/prd/m2-frontend-source-console.md`。
3. 再更新 fixture / mock。
4. 最后改代码。

禁止出现“后端先临时返回，前端先临时适配”的隐式契约。

### 7.3 M2 后端实现顺序

M2 后端继续开发时，先读 `progress.md`，只做未完成项。已完成的 source CRUD、preview、manual fetch、fetch run / raw item / source health 查询、Redis key helper、retry 控制、Redis 锁适配器和 PostgreSQL migration 不重复实现。

后端按以下顺序推进剩余能力：

1. PostgreSQL repository 替换当前内存 repository。
2. Redis ETag / Last-Modified 持久同步。
3. Redis 源内 dedupe set 持久同步。
4. FetcherPool 与 RSS / RSSHub / AI HOT fetcher 完整化。
5. SourceHealth 连续失败、degraded、circuit_open 状态推进。
6. SchedulerService。
7. worker/API 同进程开发模式和可拆分边界。
8. mock RSS / RSSHub / AI HOT 集成测试。
9. OpenAPI 自查。

后端完成标准：

- 所有 API 符合 `docs/contracts/collection-api.md`。
- 所有响应使用统一 envelope。
- 不暴露 RSS、RSSHub、AI HOT 原始响应。
- 所有外部请求带 timeout、User-Agent、错误映射和 trace id。
- RSS/RSSHub/custom RSS 必须通过 SSRFGuard。
- disabled source 不参与 scheduler，也不可手动 fetch。
- requiresCookie source 在 M2 只保存配置，不执行抓取。
- 上游失败必须返回可见错误或 failed run，不伪造成功。
- 首次抓取只入库，不进入推送候选。
- 测试不依赖实时新闻标题。

### 7.4 M2 前端实现顺序

前端按以下顺序实现：

1. API client，严格使用 `docs/contracts/collection-api.md`。
2. mock response / fixture。
3. SourceConsole 入口。
4. Source 列表和筛选。
5. Source 创建 / 编辑表单。
6. Source preview 面板。
7. Source 启用 / 停用。
8. 手动 fetch 触发。
9. FetchRun 列表和详情。
10. RawItem 列表和详情入口。
11. SourceHealth 面板。
12. 空状态、错误态、加载态、警告态。
13. 移动端适配。
14. 前后端联调。

前端完成标准：

- 不包含 AI HOT、RSSHub、任意 RSS 直连 endpoint。
- 所有字段来自 `docs/contracts/collection-api.md`。
- mock 数据符合契约。
- preview 错误展示 `error.message` 和 `traceId`。
- disabled source 手动抓取展示明确错误。
- failed / partial_failed run 必须有明显状态。
- RawItem 缺摘要显示“该条暂无摘要”。
- 长 URL、长标题、移动端表格不横向溢出。

### 7.5 M2 联调规则

联调必须按顺序执行：

1. 后端启动。
2. 调用 `/api/sources` 验证 source list。
3. 调用 `/api/sources/preview` 验证 preview success / error。
4. 创建 RSSHub source。
5. 创建自定义 RSS source。
6. 启用 / 停用 source。
7. 手动触发 `/api/sources/{sourceId}/fetch`。
8. 查看 `/api/fetch-runs`。
9. 查看 `/api/raw-items`。
10. 查看 `/api/source-health`。
11. 验证 SSRF blocked、disabled source、source not found、upstream failed 等错误态。
12. 验证移动端展示。

联调发现问题时：

- 契约问题：先改 `docs/contracts/collection-api.md`。
- 后端实现问题：后端修复并补测试。
- 前端展示问题：前端修复并补 mock / 组件测试。
- 上游源不可用：保留真实错误，不伪造成功。

## 8. M3-M7 升级流程

M3/M4/M5/M6/M7 已完成文档升级，编码前还需要确认这些文档可作为开发依据。进入任一阶段前，如果发现 contract 或 PRD 缺口，必须先修正文档再编码。

### 8.1 升级输入

每次升级必须读取：

```text
prd.md
workflow.md
docs/prd/<stage>-*-brief.md
上一阶段实际实现与测试
```

如果涉及前后端，还必须读取上一阶段相关 contract。

### 8.2 升级输出

每个阶段至少产出：

```text
docs/contracts/<stage>-api.md
docs/prd/<stage>-backend-*.md
docs/prd/<stage>-frontend-*.md
```

如果阶段不涉及前端，可以不创建 frontend PRD，但必须在 brief 升级结果中明确说明原因。

如果阶段包含 worker、scheduler、pipeline、agent prompt、评估集，也需要单独写清交付边界。

M3 已产出：

```text
docs/contracts/clustering-api.md
docs/prd/m3-backend-clustering-trends.md
docs/prd/m3-frontend-topic-console.md
```

M4 已产出：

```text
docs/contracts/value-background-api.md
docs/prd/m4-backend-value-background.md
docs/prd/m4-frontend-assessment-console.md
```

M5 已产出：

```text
docs/contracts/commentary-distribution-api.md
docs/prd/m5-backend-commentary-distribution.md
docs/prd/m5-frontend-commentary-distribution-console.md
```

M6 已产出：

```text
docs/contracts/admin-rules-api.md
docs/prd/m6-backend-admin-rules.md
docs/prd/m6-frontend-admin-rules-console.md
```

M7 已产出：

```text
docs/contracts/eval-observability-api.md
docs/prd/m7-backend-eval-observability.md
docs/prd/m7-frontend-observability-console.md
```

### 8.3 详细 PRD 必须包含

- 目标。
- 背景和依赖。
- In Scope。
- Out of Scope。
- 用户故事或系统场景。
- 数据模型。
- API contract 或事件 contract。
- 状态机。
- Agent 输入输出。
- 错误处理。
- 安全和合规边界。
- Prompt injection 防护。
- 测试 fixture。
- 验收标准。
- 联调边界。
- 迁移或兼容策略。
- 已知风险。

### 8.4 升级门槛

满足以下条件后，才允许从“文档阶段”进入“编码阶段”：

- 详细 PRD 已写入 `docs/prd/`。
- contract 已写入 `docs/contracts/`。
- `prd.md` 的阶段索引已更新或确认无需更新。
- 待定问题已经关闭，或明确列为不阻塞项。
- 用户确认该阶段文档可作为开发依据。

## 9. 多 AI Coding 客户端分工

### 9.1 后端客户端

负责：

- 后端 PRD 对应代码。
- API、服务、任务、Agent pipeline、数据模型。
- 单元测试、集成测试、mock upstream。
- 后端 README / OpenAPI 自查。

不得负责：

- 未经契约定义的前端字段。
- 直接改前端 UI 来掩盖后端契约问题。

### 9.2 前端客户端

负责：

- 前端 PRD 对应页面和组件。
- API client。
- mock fixture。
- 空态、错态、加载态。
- 移动端和可用性。

不得负责：

- 直接调用 AI HOT。
- 自行推断后端未返回的新闻事实。
- 在 UI 中硬编码临时后端字段。

### 9.3 契约客户端

负责：

- 编写和维护 `docs/contracts/*`。
- 输出 request / response 示例。
- 维护错误码、枚举、状态机、fixture。
- 审核前后端是否出现隐式契约。

### 9.4 测试客户端

负责：

- 根据 PRD 和 contract 设计测试矩阵。
- 检查 mock 是否符合契约。
- 检查真实联调是否覆盖关键路径。
- 检查无 silent fallback、无伪数据、无无源事实。

## 10. 变更流程

任何影响前后端、数据模型、任务状态、Agent 输出、错误码、阶段边界的变更，必须按顺序执行：

1. 更新对应 `docs/contracts/*`。
2. 更新对应 `docs/prd/*`。
3. 必要时更新 `prd.md`。
4. 更新 mock / fixture。
5. 更新实现。
6. 更新测试。
7. 记录变更影响和已知限制。

小型文案、样式、内部重构不需要更新总 PRD，但不能改变契约和行为边界。

如果实现与文档冲突：

- 默认认为实现有问题。
- 若确认文档过时，先改文档并说明原因。
- 禁止只在聊天里说明“以代码为准”。

## 11. 测试与验收门槛

每个阶段完成前必须满足：

- 阶段 PRD 的验收标准全部通过。
- contract 与实现一致。
- 单元测试通过。
- 必要集成测试通过。
- 关键错误路径被覆盖。
- 没有无源事实、伪数据、隐藏降级。
- 文档已更新。
- 已记录已知限制和下一阶段依赖。

M1 后端最低验收：

```text
/api/query/help
/api/query/items
/api/query/daily
/api/query/dailies
```

M1 前端最低验收：

```text
精选查询
全部动态查询
分类筛选
关键词搜索
日报展示
日报归档
空态
错态
加载态
移动端
```

M2 后端最低验收：

```text
/api/sources
/api/sources/{sourceId}
/api/sources/preview
/api/sources/{sourceId}/fetch
/api/fetch-runs
/api/raw-items
/api/source-health
SSRFGuard
source lock
PostgreSQL migration
```

M2 前端最低验收：

```text
Source 列表
Source 创建 / 编辑
Source preview
Source 启停
手动 fetch
FetchRun 列表
RawItem 列表
SourceHealth 面板
空态 / 错态 / 加载态
移动端
```

## 12. 事实与数据边界

热点情报系统必须遵守：

- 新闻事实必须来自原文、AI HOT API、RSS、公开网页、官方声明或已记录来源。
- LLM 只能总结、分类、点评、判断价值，不能凭空补事实。
- 所有对外输出都要保留来源 URL 或来源标识。
- 摘要和点评必须与原文事实分层展示。
- 低置信度内容必须标注原因。
- 无法访问外部源时必须返回可见错误或待核验状态。

禁止：

- 用训练记忆补最新消息。
- 用缓存冒充最新数据。
- 把访问失败的外部源标成采集成功。
- 把模型推测写成事实。

## 13. 安全与合规边界

- 密钥不得明文出现在代码、日志、UI、测试 fixture。
- 外部源采集必须记录来源、抓取时间和访问方式。
- 对登录态、付费墙、隐私内容、敏感数据源不得绕过访问限制。
- Prompt injection 内容必须作为不可信输入处理。
- Agent 工具调用必须有超时、重试、错误记录和 trace id。
- 生产环境请求不得在测试中直接调用，除非用户明确授权。

## 14. 禁止事项

- 禁止前端绕过后端直接调用 AI HOT。
- 禁止未读取 M2 contract 和子 PRD 就直接做多源采集。
- 禁止在 M1 引入登录、数据库、订阅、推送。
- 禁止在 brief 未升级为详细 PRD 前实现 M3-M7 业务代码。
- 禁止使用训练记忆补新闻事实。
- 禁止缓存冒充最新数据。
- 禁止密钥明文出现在日志、UI 或测试 fixture。
- 禁止把无法访问的外部源伪造成成功。
- 禁止只改代码不改受影响契约。
- 禁止只改契约不改受影响测试。

## 15. Agent 开发门禁

实现任一 Agent 或 Agent-like 服务时，必须满足：

- 有明确输入、输出和失败语义。
- 有 trace id、source id、run id 或 topic id，可追踪执行链路。
- 外部工具调用必须有 timeout、retry、错误记录。
- LLM 输出必须区分事实、推断、点评和待核验内容。
- Prompt injection 内容必须按不可信输入处理。
- Agent 之间不得传递无来源事实。
- Agent 失败不得被下游伪装为成功。
- 每个 Agent 至少有单元测试或 fixture 覆盖正常路径和关键失败路径。

适用 Agent：

```text
采集 Agent
去重聚类 Agent
价值判断 Agent
背景补全 Agent
AI 点评 Agent
分发 Agent
```

## 16. 完成标识规则

每完成一个关键 workflow 项，必须把状态写入当前任务目录，不能只停留在聊天记录里。

推荐文件：

```text
.trellis/tasks/<task-dir>/progress.md
```

必须标识：

- 已完成的 PRD / contract / workflow 文档。
- 已完成的阶段入口判断。
- 已完成的实现模块。
- 已通过的测试或验证命令。
- 未完成的下一步。
- 明确禁止重复执行的事项。

每次更新完成标识时，至少写入：

```text
最后更新日期
当前阶段
已完成
下一步未完成
恢复规则
不要重复做
```

如果任务目录有 `task.json`，应同步把关键产物写入 `relatedFiles` 或 `notes`，方便后续恢复。

完成标识示例：

```markdown
- [x] 已创建 M1 查询 API 共享契约。
- [x] 已创建 M1 后端详细 PRD。
- [ ] M1 后端 FastAPI 查询内核尚未实现。
```

禁止：

- 禁止只在最终回复里说“已完成”但不更新任务文件。
- 禁止把未验证的事项标成 `[x]`。
- 禁止删除历史完成项来掩盖阶段变更；如果状态变化，新增说明。

## 17. 交付记录模板

每次阶段性交付时，在最终说明中至少包含：

```text
本次阶段：
读取文档：
修改文件：
验证命令：
通过项：
未验证项：
已知限制：
下一步：
```

如果是前后端并行交付，还必须说明：

```text
契约版本：
后端 base URL：
前端环境变量：
mock 与真实 API 差异：
联调阻塞项：
```

## 18. 后续阶段文档规划

推荐按以下顺序补齐详细 PRD：

1. M3 去重聚类与趋势：已补 `docs/contracts/clustering-api.md`、`docs/prd/m3-backend-clustering-trends.md`、`docs/prd/m3-frontend-topic-console.md`；编码前需要确认文档可作为开发依据。
2. M4 价值判断与背景补全：已补 `docs/contracts/value-background-api.md`、`docs/prd/m4-backend-value-background.md`、`docs/prd/m4-frontend-assessment-console.md`；编码前需要确认文档可作为开发依据。
3. M5 AI 点评与分发：已补 `docs/contracts/commentary-distribution-api.md`、`docs/prd/m5-backend-commentary-distribution.md`、`docs/prd/m5-frontend-commentary-distribution-console.md`；编码前需要确认文档可作为开发依据。
4. M6 管理后台与规则：已补 `docs/contracts/admin-rules-api.md`、`docs/prd/m6-backend-admin-rules.md`、`docs/prd/m6-frontend-admin-rules-console.md`；编码前需要确认文档可作为开发依据。
5. M7 评估与可观测：已补 `docs/contracts/eval-observability-api.md`、`docs/prd/m7-backend-eval-observability.md`、`docs/prd/m7-frontend-observability-console.md`；编码前需要确认文档可作为开发依据。

后续每补一个阶段，都必须同步更新本文件的“当前阶段可开发状态”。
