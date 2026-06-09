# M2 采集基础设施 Brief

> 版本：v0.1
> 所属总 PRD：`prd.md`
> 阶段性质：路线级 brief，进入 M2 开发前需升级为详细 PRD
> 上游依赖：M1 查询 API、AI HOT client、统一错误 envelope
> 下游依赖：M3 去重聚类、M7 可观测

## 1. 目标

建设多源采集基础设施，让系统从“只读查询 AI HOT”扩展为“可配置、可调度、可观测地采集多个热点来源”。M2 的核心不是智能判断，而是稳定获得标准化 `RawItem`。

## 2. 范围

### In Scope

- SourceRegistry：管理 AI HOT API、AI HOT RSS、RSSHub route、自定义 RSS。
- RSS / RSSHub 抓取器。
- 自定义 RSS URL 校验和 sample preview。
- 源级配置：频率、超时、重试、并发、启停、trust level。
- 源级失败计数、熔断、降频。
- ETag / Last-Modified / 短期缓存。
- RawItem 归一化。
- 首次抓取只入库不推送。
- 采集 run 记录和基础日志。

### Out of Scope

- 跨源事件聚类。
- 价值判断。
- 背景补全。
- AI 点评。
- 外部分发。
- 完整管理后台，只需要能通过 API 或配置文件管理 source。

## 3. 输入与输出

输入：

- SourceConfig。
- 调度触发或手动触发。
- RSSHub 主备实例配置。

输出：

- RawItem。
- FetchRun。
- SourceHealth。
- 失败原因和 trace。

## 4. 关键决策

- 首批 source 类型：`aihot_api`、`rss`、`rsshub`。
- Redis 用于缓存、锁、去重集合；长期数据进 PostgreSQL。
- 首次抓取保护必须默认开启。
- 任意 URL 抓取必须有 SSRF 防护。
- Cookie 类 source 属于敏感配置，本阶段只预留，不默认实现。

## 5. 验收标准

- 可配置 AI HOT API、AI HOT RSS、一个 RSSHub route、一个自定义 RSS。
- 同一 source 重复抓取不会重复入库。
- 单个 source 失败不影响其他 source。
- 连续失败 source 会进入降频或熔断状态。
- 每条 RawItem 至少有 `id/title/url/source_id/fetched_at`。
- 采集 run 可查看 source、状态、耗时、新增条数、错误。

## 6. 进入详细 PRD 前要补齐

- PostgreSQL 表结构：sources、fetch_runs、raw_items、source_health。
- source 配置 API。
- RSSHub route 配置格式。
- RawItem 去重键和唯一约束。
- 采集任务调度方式：APScheduler 单 worker 还是 worker service。
- Redis key 设计。
- mock RSS fixture。
