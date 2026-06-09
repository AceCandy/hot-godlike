# HotPush 参考研究

研究对象：`JackyST0/hotpush`
仓库地址：https://github.com/JackyST0/hotpush
研究日期：2026-05-28

## 结论

HotPush 可作为本项目“采集与分发基础设施”的参考，而不是完整的“多 Agent 热点情报系统”参考。它已经覆盖多源热榜/RSS 聚合、定时抓取、缓存、去重、规则过滤、多渠道推送、趋势快照和 AI 摘要，但没有看到完整的跨平台语义事件聚类、价值判断、背景补全、事实核验和多 Agent 编排能力。

## 可参考能力

- 数据源：内置微博热搜、知乎热榜、B 站热搜、V2EX、Hacker News、掘金、Linux DO、NodeSeek、少数派、豆瓣、联合早报、澎湃新闻等。
- 采集方式：主要通过 RSSHub 路由和普通 RSS URL 抓取，支持自建 RSSHub、备用 RSSHub 实例和自定义 RSS 源。
- 抓取实现：`RSSFetcher` 使用 `httpx` + `feedparser`，支持浏览器 UA、30 秒级超时、备用实例切换、每源最多取 50 条、并发抓取时用信号量限制并发。
- 数据模型：`HotItem` 包含 `id/title/url/hot_score/source/published/description/image`；`HotList` 包含 `source/source_name/items/updated_at/icon`。
- ID 策略：基于 `source_id + link/title` 生成 MD5 短 ID，适合源内去重，但不适合跨源语义聚类。
- 缓存与去重：Redis 缓存 `hotlist:{source}`，推送去重集合 `pushed:{source}`，MySQL `pushed_items` 作为持久备份。
- 趋势：抓取后保存排名快照，提供 ranking trend、item trend、platform stats、top items。
- 规则过滤：支持关键词包含、关键词排除、时间段限制、来源过滤。
- 定时：APScheduler 支持间隔抓取、手动触发、暂停/恢复、每日定时摘要。
- AI 摘要：通过 LiteLLM 支持 OpenAI、Claude、DeepSeek、Ollama 等，提供 brief、detailed、morning_briefing 三种摘要风格。
- 推送：支持 Telegram、Discord、企业微信、飞书、钉钉、Webhook、邮件，并支持推送历史、成功率和渠道统计。
- 前端：Vue 3 + Tailwind，包含公开热榜、数据源管理、规则管理、调度器、推送配置、趋势分析、用户管理。

## 本项目应吸收的设计

- 采集层先以 RSSHub + RSS + 已有公开 API 起步，不要一开始自研所有爬虫。
- 数据源配置需要统一 schema，区分内置源、自定义 RSS、热搜源、新闻源、社交源、指定网站源。
- 采集任务需要源级超时、失败重试、备用实例、并发上限和单源锁。
- 首次抓取默认只入库不推送，避免历史数据刷屏。
- 推送必须有去重状态，按订阅、渠道、主题分别记录。
- 趋势能力应从排名快照/热度快照开始，后续再叠加语义事件热度。
- AI 摘要不能替代价值判断、事实核验和背景补全，应作为最后的表达层。

## 本项目不能照搬的地方

- HotPush 的 ID 是源内去重，不足以识别跨平台同一事件；本项目需要事件指纹、embedding 或 LLM 辅助聚类。
- HotPush 的 AI 摘要基于热榜标题集合生成，容易缺背景；本项目需要背景补全 Agent 先拉原始来源、官方声明、历史上下文。
- HotPush 的规则过滤主要是关键词/时间/来源，不等同于价值判断；本项目需要价值判断 Agent 识别标题党、营销、八卦和重复噪音。
- HotPush 的推送以平台热榜更新为主；本项目推送对象应是“热点主题/事件簇”，不是单条原始 item。
- HotPush 是管理平台架构；本项目还需要 Agent trace、人工审核点、工具权限边界和评估集。

## 映射到本项目多 Agent

| 本项目 Agent | HotPush 可参考 | 本项目新增要求 |
|---|---|---|
| 采集 Agent | RSSHub、多实例、内置源、自定义 RSS、定时抓取 | 指定网站、社交平台、官方文档、增量抓取、源可信度 |
| 去重聚类 Agent | 源内 ID 去重、Redis/MySQL 推送去重 | 跨源事件聚类、事件指纹、embedding 相似度、簇合并/拆分 |
| 价值判断 Agent | 关键词规则过滤 | 多维评分、噪音识别、营销识别、标题党识别、领域偏好 |
| 背景补全 Agent | 无直接对应 | 原始来源、关联报道、官方声明、历史背景、技术文档 |
| AI 点评 Agent | LiteLLM 摘要风格 | 事实受限点评、影响对象、后续观察点、置信度 |
| 分发 Agent | 多渠道推送、推送历史、规则、定时摘要 | 按用户偏好/主题簇分发、订阅画像、渠道模板、人工确认 |
