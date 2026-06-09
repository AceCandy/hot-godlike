# 多 Agent 热点情报系统 PRD

> 版本：v0.3
> 采集日期：2026-05-28
> 目标站点：https://aihot.virxact.com/
> 外部参考：https://github.com/JackyST0/hotpush
> 文档性质：完整版 PRD，不按 MVP 裁剪范围；后续开发时可从本文拆分子 PRD 和阶段任务。
> 开发流程：后续实现必须遵循 `workflow.md`。
> 产出目的：基于 AI HOT 的公开能力和 HotPush 的开源采集/推送实现，设计一个可开发的“多 Agent 热点情报系统”。本文只把实测到、公开声明或源码确认的能力写成事实；无法验证的能力会明确标注。

## 1. 背景与目标

AI HOT 是一个中文 AI 资讯精选服务。公开页面说明其定位是“每天抓 AI 圈的新动静，用 AI 帮助筛掉噪声，把真正值得看的几条留下来”。站点同时提供网页浏览、RSS、REST API、Skill 四类公开入口，适合作为本系统的可信种子数据源。

本 PRD 的目标不是复刻 AI HOT 或 HotPush 的完整 UI，而是定义一个面向 Web、终端、聊天、企业群机器人和工作流的“多 Agent 热点情报系统”完整蓝图：由采集 Agent、去重聚类 Agent、价值判断 Agent、背景补全 Agent、AI 点评 Agent、分发 Agent 协同，把来自热搜、RSS、新闻源、社交平台和指定网站的碎片消息整理成可溯源、可评分、可推送的热点主题。本文后面的阶段拆分只表示开发顺序，不表示产品范围被裁剪。

## 2. 证据范围

### 2.1 实测页面

- `/`：精选信息流
- `/all`：全部 AI 动态
- `/daily`：最新 AI 日报
- `/daily/archive`：日报历史
- `/agent`：Skill / RSS / REST API 接入说明
- `/about`：关于页
- `/changelog`：更新日志
- `/feedback`：反馈表单
- `/submit`：信源提报与信源墙
- `https://login.virxact.com/login?...`：登录页

### 2.2 实测公开接口

- `GET /openapi.yaml`
- `GET /api/public/items?mode=selected&take=2`
- `GET /api/public/daily`
- `GET /api/public/dailies?take=3`
- `HEAD /feed.xml`
- `GET /aihot-skill/SKILL.md`

### 2.3 HotPush 参考范围

本次通过公开仓库 `JackyST0/hotpush` 的 README、文档、目录结构和关键源码梳理其能力，重点阅读：

- `README.md`
- `docs/getting-started.md`
- `docs/push-channels.md`
- `backend/.env.example`
- `docker-compose.yml`
- `backend/app/utils/sources.py`
- `backend/app/services/rss_fetcher.py`
- `backend/app/services/scheduler.py`
- `backend/app/services/push_service.py`
- `backend/app/services/ai_service.py`
- `backend/app/services/cache.py`
- `backend/app/models/schemas.py`
- `backend/app/routers/api.py`
- `backend/app/routers/sources.py`
- `backend/app/routers/rules.py`
- `backend/app/routers/scheduler.py`
- `backend/app/routers/trends.py`

### 2.4 未验证范围

- 登录后的收藏、内部反馈、内部信源提报等能力：登录页声明“登录后解锁收藏、反馈、信源提报等内部功能”，但本次没有企业飞书凭证，未进入验证。
- 后台抓取、评分、去重、聚类、审核流程：只从公开页面、OpenAPI 和更新日志推断接口契约，不把后台实现细节当作已验证事实。
- 内容真实性：AI HOT 自身声明“摘要由 LLM 生成，引用前请用 url 字段回原文核对”。Agent 必须保留原文链接，并提示关键结论以原文为准。
- HotPush 仓库中没有确认到完整的跨平台语义事件聚类、价值判断、背景补全和事实核验链路；这些是本系统新增设计，不应写成 HotPush 既有能力。

## 3. AI HOT 网站公开功能盘点

### 3.1 全局导航与主题

所有主要页面共享左侧导航：

- 精选
- 全部 AI 动态
- AI 日报
- Agent 接入
- 关于
- 更新日志
- 反馈
- 信源提报
- 登录

主题支持三态切换：

- 深色：默认选中
- 跟随系统
- 浅色

实测选择浅色后，浏览器 `localStorage` 写入 `aihot-theme=light`，并存在访客标识 `aihot_vid`。PRD 中不要求复刻视觉主题，但如果开发 Web 端，应保留用户偏好本地存储。

### 3.2 精选页 `/`

定位：AI 自动挑选的高价值内容。

实测功能：

- 默认展示精选信息流。
- 支持分类筛选：
  - 全部
  - 模型
  - 产品
  - 行业
  - 论文
  - 技巧
- 支持搜索标题/摘要，搜索结果通过 URL query 表达，例如 `?q=OpenAI&page=1`。
- 信息流按日期分组，例如 `5月28日`、`5月27日`。
- 日期分组支持收起/展开。实测点击“收起 5月28日”后，该日期条目隐藏，按钮变为“展开 5月28日”。
- 文章标题链接直接跳转原文。
- 卡片可展示来源、发布时间、精选标记、分数、摘要、标签、推荐理由、关联讨论等内容。
- 对 X 推文图片提供“查看大图 n/n”按钮。实测点击后出现弹窗，包含关闭按钮和图片。
- 对视频推文提供“打开原推播放视频”按钮，入口指向原推播放。
- 空结果态：搜索无匹配时显示“当前没有匹配的内容，试试调整搜索条件。”

对 Agent 的启发：

- 默认问题应优先走“精选”而不是“全部”，因为这是站点主菜单和降噪后的内容池。
- 输出应保留推荐理由、标签、来源、URL 和时间，方便用户判断是否继续阅读原文。
- Agent 不应把分数解释成绝对事实，只能作为排序/筛选信号。

### 3.3 全部 AI 动态 `/all`

定位：AI 相关资讯全量信息流。

实测功能：

- 支持频道筛选：
  - 全部
  - 一手信源
  - 资讯
  - 推文
- 支持同精选页一致的分类筛选：
  - 全部
  - 模型
  - 产品
  - 行业
  - 论文
  - 技巧
- 支持搜索标题/摘要，搜索后 URL 形如 `/all?q=OpenAI&page=1`。
- 支持分页。实测页面展示页码 `2`、`3`、末页 `50` 和“下一页”。更新日志说明“全部 AI 动态”由无限滚动改为翻页，声明为 `40 条/页 × 50 页上限`。
- 搜索、频道、分类会组合进 URL，例如 `/all?q=OpenAI&category=paper&page=1`。
- 空结果态与精选页一致。

对 Agent 的启发：

- 只有用户明确说“全部 / 完整 / 所有 / 全量”时，Agent 才应走全量池。
- 默认回答不应拉全量后自行 grep。站点已提供服务端关键词搜索，Agent 应优先用 API 的 `q` 参数。

### 3.4 AI 日报 `/daily`

定位：每天生成的 AI HOT 日报。

实测功能：

- 页面标题：AI HOT 日报。
- 左侧存在“日报历史”导航，显示最新一期和多日历史。
- 最新一期实测为 `2026-05-28`。
- 日报按板块组织，实测板块包括：
  - 产品发布/更新
  - 行业动态
  - 论文研究
  - 技巧与观点
- OpenAPI 说明日报固定 5 个 section label：
  - 模型发布/更新
  - 产品发布/更新
  - 行业动态
  - 论文研究
  - 技巧与观点
- 每条日报事件包含标题、摘要、来源名称、来源 URL。
- 页面底部存在“前一日”和“查看历史”入口。

对 Agent 的启发：

- 只有用户明确说“日报”时才走日报端点。
- 日报适合生成“每日成品简报”，不适合回答“过去 24 小时”这种滚动时间窗问题。

### 3.5 日报历史 `/daily/archive`

实测功能：

- 展示日报归档列表。
- 每条归档包含日期、星期、主标题和事件数。
- 实测列表包括 2026-05-28 到 2026-04-22 的多期日报。
- 页面侧栏按月份汇总，示例：`2026 年 5 月`、`2026 年 4 月`。

对 Agent 的启发：

- 用户问“有哪些日期有日报”“列一下最近日报”时，应先调用 `/api/public/dailies` 做 discovery。
- 用户指定日期时再调用 `/api/public/daily/{YYYY-MM-DD}`。

### 3.6 Agent 接入 `/agent`

定位：把 AI HOT 接进工作流，测试版。

公开说明：

- 匿名免费、无需 token。
- 支持三轨接入：
  - Skill：任意 Agent，SKILL.md 标准。
  - RSS：任意 RSS reader，零配置订阅。
  - REST API：开发者/自定义集成，OpenAPI 3.1。
- 使用须知：
  - 原文为准。
  - 合理使用。
  - 测试版，可能临时下线、调整接口或增加访问限制。

#### Skill Tab

实测内容：

- 安装入口：`https://aihot.virxact.com/aihot-skill/`
- 完整 Skill 文件：`https://aihot.virxact.com/aihot-skill/SKILL.md`
- GitHub 同步：`KKKKhazix/khazix-skills`
- 触发示例：
  - 今天 AI 圈有什么新东西
  - 看一下今天的 AI 日报
  - 最近 OpenAI 有什么发布
  - 看下精选条目
  - 最近一周的 AI 论文
  - AI 模型发布列表
  - 最近 3 天 AI 行业动态
  - AI 圈昨天发生了什么
- Skill 内部分流规则：
  - 默认宽问题走 `GET /api/public/items?mode=selected&since=<语义窗>`
  - 明确说“日报”走 `GET /api/public/daily` 或 `/daily/{date}`
  - 明确说“全部 / 完整 / 所有 / 全量”走 `GET /api/public/items?mode=all`
  - 分类问题走 `GET /api/public/items?mode=selected&category=...`
  - 时间窗问题走 `GET /api/public/items?mode=selected&since=ISO-8601`
  - 关键词搜索走 `GET /api/public/items?q=OpenAI`
  - 日期 discovery 走 `GET /api/public/dailies?take=N`

#### RSS Tab

实测内容：

- `https://aihot.virxact.com/feed.xml`
  - 名称：AI HOT — 精选
  - 内容：每日精编候选池，最新 50 条
- `https://aihot.virxact.com/feed/all.xml`
  - 名称：AI HOT — 全部 AI 动态
  - 内容：抓取的全部 AI 行业内容流，最新 50 条
- `https://aihot.virxact.com/feed/daily.xml`
  - 名称：AI HOT 日报
  - 内容：每天 08:00 北京时间发布的精编日报，最新 30 期
- RSS 2.0，UTF-8，`Content-Type: application/rss+xml`。
- 响应头支持 `ETag` 和 `Last-Modified`。实测 `/feed.xml` 返回 `HTTP/2 200`、`content-type: application/rss+xml; charset=utf-8`、`etag`、`last-modified`、`cache-control`。
- 推荐轮询频率：不低于 30 分钟。
- 站点声明 nginx 限流：`600 req/min/IP`。

#### REST API Tab

实测内容：

- OpenAPI：`https://aihot.virxact.com/openapi.yaml`
- 无需 token。
- 公开响应只暴露浏览器能看到的最终内容字段，评分、AI 标签、内部分类编号等不作为公开 API 字段。
- API 端点必须带 User-Agent；默认 curl UA 可能被 403。
- 端点：
  - `GET /api/public/items`
  - `GET /api/public/daily`
  - `GET /api/public/daily/{YYYY-MM-DD}`
  - `GET /api/public/dailies`

### 3.7 反馈 `/feedback`

实测功能：

- 匿名可用。
- 标题：说说你的想法。
- 内容输入框必填，显示 `0 / 2000` 计数。
- 联系方式选填。
- 未填写内容时“发送反馈”按钮禁用。
- 填写内容后按钮启用。
- 页面说明可反馈 bug、想法、吐槽和希望增加的功能。
- 更新日志说明提交后会发送到团队飞书群；本次未点击提交，避免产生真实反馈。

### 3.8 信源提报 `/submit`

实测功能：

- 匿名可用。
- 字段：
  - URL：必填
  - 信源名称：必填
  - 推荐理由：必填，页面显示 `0/15`，说明至少 15 字
  - 提报人：选填
- 表单未满足条件时“提报信源”按钮禁用。
- 填入 URL、信源名称和超过 15 字推荐理由后，按钮启用。
- 页面下方为“信源墙”，展示审核通过的信源卡片。
- 信源墙卡片包含：
  - 信源名称
  - 原始链接
  - 专属编号，例如 `N° 015`
  - 推荐理由
  - 提报人
  - 日期
- 实测可见信源示例包括 Artificial Intelligence News、The Verge、Dataguidance、lilianweng 博客、KreaAI 官方推特、MarkTechPost、TechCrunch、Cloudflare Blog、Ars Technica 等。
- 更新日志说明提报会经人工审核，通过后上墙并收录到正式抓取列表。
- 本次未点击提交，避免产生真实提报。

### 3.9 关于 `/about`

实测内容：

- 站点作者：数字生命卡兹克。
- 页面声明：
  - 这个站免费给大家用。
  - 每天抓 AI 圈的新动静。
  - 用 AI 帮助筛掉噪声。
  - 把真正值得看的几条留下来。
- 提供微信公众号“数字生命卡兹克”和飞书群“AI HOT 精选推送”的跟进入口。
- 页面文案：用心做的小项目，since 2026。

### 3.10 更新日志 `/changelog`

实测功能：

- 记录新功能、调整和下线。
- 实测条目覆盖：
  - 搜索不区分大小写。
  - 按天浏览增加日期吸顶和按天收起/展开。
  - 精选去重和引用上下文优化。
  - 信源提报开放和信源墙上线。
  - 手机端阅读适配上线。
  - 已读卡片自动置灰。
  - RSS 一键订阅。
  - 公众号爆文页不再公开。
  - 精选/全部增加分类筛选。
  - Agent 接入三轨上线。
  - 全部 AI 动态改翻页。
  - 主题切换。
  - X 图片代理与 webp 压缩。
  - 反馈页上线。

### 3.11 登录

实测登录页：

- 登录域名：`login.virxact.com`
- 页面标题：虚实传媒。
- 说明：员工与签约博主登录入口，普通访客无需登录即可继续浏览公开内容。
- 登录方式：
  - 虚实空际-飞书登录
  - 虚实传媒-飞书登录
  - 虚实传媒北京分公司-飞书登录
- 提供“暂不登录，返回 AIHot”。
- 页面声明登录后解锁收藏、反馈、信源提报等内部功能。

Agent 处理要求：

- 完整系统的公开能力不依赖 AI HOT 登录态。
- 不主动绕过登录或尝试内部接口。
- 如果用户要求收藏、内部信源管理等能力，Agent 应说明“需要登录态或后端授权，当前公开 API 不覆盖”。

### 3.12 HotPush 可参考能力

HotPush 是一个开源热点聚合推送平台，技术栈为 Python 3.11+ / FastAPI、Vue 3 / Vite / Tailwind CSS、MySQL、Redis、RSSHub。它对本项目最有参考价值的是“采集、调度、规则过滤、缓存去重、推送和趋势基础设施”。

确认到的能力：

- 公开热搜榜：未登录也可访问聚合热点。
- 数据源：内置微博热搜、知乎热榜、B 站热搜、V2EX、Hacker News、掘金、Linux DO、NodeSeek、少数派、豆瓣热映、豆瓣新书、联合早报、澎湃新闻等。
- 自定义 RSS：登录后可添加自定义 RSS 源，并提供 URL 格式和 RSS 可解析性校验。
- RSSHub 多实例：配置主 RSSHub 和备用实例，抓取失败时依次切换。
- 抓取器：`httpx` + `feedparser`，浏览器 UA，请求超时，单源最多取 50 条。
- 并发控制：批量抓取使用 `asyncio.Semaphore` 限制并发。
- 缓存：Redis 缓存热榜数据，默认 TTL 300 秒。
- 去重：按源记录已推送 item id；Redis 做快速集合判断，MySQL 做持久备份。
- 首次抓取保护：首次抓取会把历史条目标记为已推送，避免初次部署刷屏。
- 趋势快照：抓取后保存排名快照，用于排名变化、单条趋势、平台统计和高热条目查询。
- 规则过滤：关键词包含、关键词排除、时间段限制、来源过滤。
- 定时任务：APScheduler 支持间隔抓取、暂停/恢复、手动触发、每日定时摘要。
- AI 摘要：通过 LiteLLM 接入 OpenAI、Claude、DeepSeek、Ollama 等模型，支持简洁速递、详细分析、晨间简报三种风格。
- 推送渠道：Telegram、Discord、企业微信、飞书、钉钉、Webhook、邮件。
- 推送历史：记录历史推送、成功率、按渠道和来源统计。
- 部署：Docker Compose 包含 MySQL、Redis、后端、前端、RSSHub。

本项目应吸收的点：

- 采集层先以 RSSHub + RSS + 官方公开 API 起步，不要一开始自研所有爬虫。
- 数据源配置需要统一 schema，区分内置源、自定义 RSS、热搜源、新闻源、社交源、指定网站源。
- 采集任务必须具备源级超时、失败重试、备用实例、并发上限和单源锁。
- 首次抓取只入库不推送，避免历史数据刷屏。
- 推送必须按订阅、渠道、主题分别记录去重状态。
- 趋势能力先从排名快照/热度快照做起，后续再叠加语义事件热度。
- AI 摘要只作为表达层，不能替代价值判断、背景补全和事实核验。

不能照搬的点：

- HotPush 的 ID 策略更适合源内去重，不足以识别跨平台同一事件。
- HotPush 的规则过滤主要是关键词、时间、来源，不等同于价值判断。
- HotPush 的 AI 摘要主要基于热榜标题集合生成，不等同于背景补全后的情报点评。
- HotPush 的推送对象以单平台热榜更新为主；本系统推送对象应是“热点主题/事件簇”。
- HotPush 是管理平台架构；本系统还需要 Agent trace、工具权限边界、人工审核点和评估集。

## 4. 目标用户与核心场景

### 4.1 用户角色

1. AI 从业者：每天想快速知道模型、产品、论文、行业动态。
2. 创业者/产品经理：关注可转化为产品机会的 AI 动态。
3. 开发者：关注 Agent、MCP、模型 API、开源工具、工程实践。
4. 内容创作者：需要把热点整理成日报、周报、公众号选题或群消息。
5. 企业群机器人维护者：需要定时把精选热点推送到飞书、Slack、企业微信等渠道。

### 4.2 核心用户问题

- 今天 AI 圈有什么值得看？
- 最近 24 小时有哪些大新闻？
- 最近 OpenAI / Anthropic / Google / Qwen 有什么发布？
- 最近一周 AI 论文有哪些？
- 今天的 AI 日报是什么？
- 过去几天的日报有哪些？
- 看全部动态，不要只看精选。
- 只看模型、产品、行业、论文或技巧。
- 找某个关键词相关的动态。
- 把这些内容整理成可转发群消息。
- 每天固定时间推送简报。

## 5. 产品定位

热点消息 Agent 升级为“多 Agent 热点情报系统”。它不是通用新闻聊天机器人，也不是单纯热榜聚合页，而是一套把原始热点消息加工成“热点主题情报”的流水线。

### 5.1 一句话定位

持续采集全网热点信号，自动去重聚类、判断价值、补全背景、生成 AI 点评，并按用户偏好分发 AI、科技、商业、产品、政策等不同主题的热点情报。

### 5.2 产品原则

- 原文为准：每条结论必须带原文 URL 或来源 URL。
- 不编造：没有数据就说没有匹配，不补充训练记忆里的“新闻”。
- 事件优先：系统最终处理对象是“热点主题/事件簇”，不是孤立的单条资讯。
- 多源互证：优先保留同一事件的多个来源、原始来源和官方声明。
- 默认精选：宽问题默认走 `mode=selected`。
- 显式全量：只有用户明确要求全部/完整/所有/全量，才走 `mode=all`。
- 显式日报：只有用户明确要求日报，才走 daily。
- 服务端搜索：关键词查询走 `q` 参数，不拉一批到本地 grep。
- 采集克制：按源配置频率、并发、退避和缓存，避免对外部网站造成压力。
- 人机协同：高影响、低置信、可能敏感的热点进入人工确认队列。
- 可观测：记录每次意图识别、接口请求、状态码、ETag、条目数、摘要生成结果。
- 可评估：用固定查询集回归测试路由、字段、输出和错误处理。

### 5.3 多 Agent 分工

| Agent | 目标 | 主要输入 | 主要输出 |
|---|---|---|---|
| 采集 Agent | 定时获取全网热点信号 | 热搜源、RSS、新闻源、社交平台、指定网站、AI HOT API | 标准化 `RawItem` |
| 去重聚类 Agent | 把同一事件的碎片聚成主题 | `RawItem`、历史事件簇、URL/标题/embedding | `HotTopicCluster` |
| 价值判断 Agent | 判断热点是否值得进入精选/推送 | 事件簇、来源权重、传播速度、用户偏好 | 价值评分、噪音标签、推荐/降权原因 |
| 背景补全 Agent | 补齐事件来龙去脉 | 事件簇主链接、相关链接、官方文档、历史记录 | 背景包、证据列表、风险提示 |
| AI 点评 Agent | 生成短点评和观察点 | 事件簇、背景包、价值评分 | `what/why/impact/next` 点评 |
| 分发 Agent | 按用户偏好推送 | 热点主题、用户订阅、渠道配置、免打扰规则 | Markdown/卡片/Webhook/邮件推送 |

## 6. 完整功能需求

### FR-001 自然语言意图识别

Agent 必须把用户输入识别为以下意图之一：

| 意图 | 触发示例 | 数据入口 |
|---|---|---|
| 精选热点 | 今天 AI 圈有什么、最近 AI 有啥 | `/api/public/items?mode=selected` |
| 全部动态 | 全部 AI 动态、完整列表、所有消息 | `/api/public/items?mode=all` |
| 日报 | AI 日报、今天日报、5 月 28 日日报 | `/api/public/daily` 或 `/api/public/daily/{date}` |
| 日报归档 | 有哪些日报、最近几天日报 | `/api/public/dailies?take=N` |
| 分类查询 | 最近 AI 模型、AI 论文、行业动态 | `/api/public/items?category=...` |
| 关键词查询 | OpenAI 最近发了什么、Sora 相关 | `/api/public/items?q=...` |
| 组合查询 | 最近 3 天 OpenAI 论文 | `/api/public/items?mode=selected&q=OpenAI&category=paper&since=...` |
| 帮助 | 能查什么、怎么用 | 本地能力说明 |

验收标准：

- “今天 AI 圈有什么”不得走 `/api/public/daily`。
- “今天 AI 日报”必须走 `/api/public/daily`。
- “全部 AI 动态”必须显式 `mode=all`。
- “OpenAI 最近发的”必须使用 `q=OpenAI`。
- “最近一周 AI 论文”必须使用 `category=paper` 且带 7 天内 `since`。

### FR-002 时间窗口解析

Agent 必须支持常见中文时间表达：

- 今天
- 昨天
- 过去 24 小时
- 最近 3 天
- 最近一周
- 指定日期，例如 `2026-05-28`、`5 月 28 日`

规则：

- items API 的 `since` 必须是 ISO 8601 UTC。
- items API 最长只查最近 7 天；早于 7 天的历史需求应转到日报归档。
- 指定日报日期使用 `YYYY-MM-DD`。
- 当前用户时区按 Asia/Shanghai 处理。

验收标准：

- 用户说“最近 10 天动态”时，Agent 应说明 items 最长 7 天，并建议用日报历史补足更早日期。
- 用户说“昨天日报”时，Agent 应计算昨天日期并请求 `/api/public/daily/{date}`。

### FR-003 分类映射

Agent 必须维护分类映射：

| 用户说法 | API category | 日报 section |
|---|---|---|
| 模型、大模型、模型发布 | `ai-models` | 模型发布/更新 |
| 产品、工具、应用 | `ai-products` | 产品发布/更新 |
| 行业、融资、公司、监管 | `industry` | 行业动态 |
| 论文、研究、paper | `paper` | 论文研究 |
| 技巧、观点、教程、实践 | `tip` | 技巧与观点 |

验收标准：

- 用户说“AI 产品发布”映射到 `ai-products`。
- 用户说“技巧与观点”映射到 `tip`。
- 不支持多分类一次请求；多分类需求拆成多个串行请求。

### FR-004 REST API 拉取

Agent 必须通过公开 API 拉取数据。

必须包含请求头：

```http
User-Agent: hot-godlike-agent/0.1 (+contact-or-project-url)
```

AI HOT 端点：

```text
GET https://aihot.virxact.com/api/public/items
GET https://aihot.virxact.com/api/public/daily
GET https://aihot.virxact.com/api/public/daily/{YYYY-MM-DD}
GET https://aihot.virxact.com/api/public/dailies
```

items 参数：

| 参数 | 类型 | 默认 | 规则 |
|---|---|---|---|
| mode | `selected` / `all` | `selected` | 其他值 400 |
| category | enum | 无 | `ai-models`、`ai-products`、`industry`、`paper`、`tip` |
| since | ISO datetime | 服务端最多 7 天 | 未来时间 400 |
| take | integer | 50 | 1-100 |
| cursor | opaque string | 无 | 原样回传，不解析 |
| q | string | 无 | 关键词搜索，至少 2 字符才有意义，最长 200 |

验收标准：

- 默认 `take=50`，用户明确要求更多时用 cursor 翻页。
- cursor 必须视作黑盒。
- 单 IP 请求速率远低于 `600 req/min/IP`。
- 请求失败时不生成伪结果。

### FR-005 ETag 与缓存

Agent 定时轮询时必须支持 ETag。

规则：

- 每个 query 组合单独存一份 ETag。
- 下次同 query 请求带 `If-None-Match`。
- `304 Not Modified` 直接返回“暂无新内容”，不解析 body。
- RSS 和 items API 都支持缓存语义。

验收标准：

- 同一个 query 重复轮询时不会每次都完整解析 JSON。
- ETag key 至少包含 endpoint、mode、category、since、q、take、cursor。

### FR-006 输出热点简报

默认输出结构：

```markdown
## AI HOT 精选

时间窗：过去 24 小时
数据源：AI HOT /api/public/items?mode=selected

1. 标题
   - 来源：source
   - 时间：publishedAt
   - 分类：category
   - 摘要：summary
   - 原文：url

## 需要注意

- 摘要由 AI HOT 生成，关键事实请打开原文核对。
- 未匹配到的主题不代表行业内没有相关事件，只代表当前查询窗口内公开 API 没返回结果。
```

输出规则：

- 每条必须包含标题、来源、URL。
- `summary` 为 null 或空字符串时，不要编造摘要；可显示“该条暂无摘要”。
- `publishedAt` 为 null 时，不要猜时间；显示“发布时间未知”。
- `title_en` 为 null 时不显示英文标题。
- 对日报输出按 section 分组。
- 对关键词查询说明关键词和时间窗口。

验收标准：

- 任意输出都能追溯到 API 返回字段。
- 不出现“据我了解”“可能是”等无源新闻补充。

### FR-007 空结果与错误处理

必须处理：

- 空结果：提示用户调整关键词、分类或时间窗。
- 400：展示参数错误并尝试给出可修正建议。
- 403：提示需要有效 User-Agent。
- 404：日报不存在时说明该日期无日报。
- 429/503 rate limited：指数退避，提示稍后重试。
- 网络超时：最多重试 2 次，不重复提交写操作。
- JSON 解析失败：保留原始状态码和响应片段到日志，用户侧显示“数据源响应异常”。

验收标准：

- API 失败时 Agent 不输出旧缓存内容冒充最新内容，除非明确标注“来自缓存”。
- 限流时不并发重试。

### FR-008 反馈与信源提报引导

系统默认不直接自动提交反馈或信源，避免 Agent 代用户产生外部副作用。

Agent 可做：

- 引导用户打开 `/feedback` 提交反馈。
- 引导用户打开 `/submit` 提报信源。
- 帮用户草拟信源推荐理由，但最终提交必须由用户确认。

验收标准：

- 未经用户明确确认，不向 `/feedback` 或 `/submit` 发送 POST。
- 草拟信源推荐理由时提醒推荐理由至少 15 字。

### FR-009 多源采集 Agent

采集 Agent 必须支持多类来源，并把不同来源转换成统一 `RawItem`。

采集来源：

- AI HOT 公开 API：作为高质量 AI 资讯种子源。
- RSS / RSSHub：参考 HotPush，支持 RSSHub 主实例和备用实例。
- 自定义 RSS：用户可配置 URL、名称、分类、抓取频率。
- 指定网站 URL：先支持页面级抓取和正文抽取，不做大规模站点爬取。

完整来源分层：

- 热搜源：微博、知乎、B 站、Hacker News、V2EX、掘金等，优先通过 RSSHub 或公开 feed 接入。
- 新闻源：科技媒体、官方博客、公告页面。
- 社交平台：X、公众号等仅在合法、可访问、符合平台规则的前提下接入。

采集规则：

- 每个 source 必须有独立配置：`source_id/name/type/category/url/route/fetch_interval/timeout/retry/enabled/trust_level`。
- 每个 source 必须有抓取并发上限和超时。
- 支持源级失败计数和熔断；连续失败后降低频率。
- 首次抓取默认只入库不推送，避免历史内容刷屏。
- 原始响应不直接交给 LLM 执行，必须先抽取结构化字段。

验收标准：

- 至少可通过配置接入 AI HOT API、一个 RSSHub route、一个自定义 RSS。
- 抓取失败只影响该源，不影响其他源。
- 每条 `RawItem` 至少包含 `id/title/url/source_id/fetched_at`。
- 同一 source 重复抓取不会重复入库。

### FR-010 去重聚类 Agent

去重聚类 Agent 必须把跨平台同一事件聚合为热点主题。

聚类信号：

- URL 归一化：去除常见追踪参数，规范化域名和路径。
- 标题相似度：中英文标题、别名、简称。
- 时间窗口：默认同类事件在 72 小时内更容易合并。
- 来源关系：转发、引用、转载、官方原文。
- 语义向量：embedding 相似度用于跨语言、跨平台聚合。
- LLM 辅助判定：仅用于难例，必须记录输入、输出和置信度。

输出：

- `HotTopicCluster`：主题 ID、主标题、代表链接、相关条目、来源集合、首次发现时间、最后更新时间、聚类置信度。
- 合并原因：例如 URL 相同、标题高度相似、语义相似、同一官方发布。
- 拆分原因：主题相似但主体不同、发布时间相差过大、事件发展阶段不同。

验收标准：

- 同一 URL 在不同来源出现时必须合并。
- 明显同一事件的不同标题应合并到同一 topic。
- 明显不同事件不得仅因共享公司名而合并。
- 每次自动合并必须可解释，并可人工拆分/合并。

### FR-011 价值判断 Agent

价值判断 Agent 必须判断热点是否值得展示、精选或推送。

评分维度：

- 重要性：是否影响 AI、科技、商业、产品、政策等核心领域。
- 新鲜度：发布时间和发现时间。
- 可信度：官方来源、权威媒体、多源互证优先。
- 传播强度：跨平台出现、排名变化、讨论量或热度变化。
- 稀缺性：是否是一手发布、深度分析、重要技术文档。
- 用户相关性：是否命中用户订阅主题和排除规则。
- 噪音风险：八卦、标题党、营销软文、重复转述、低质量搬运。

输出：

- 总分 `value_score`。
- 分项评分。
- 推荐理由。
- 降权/过滤原因。
- 置信度。

验收标准：

- 命中排除关键词或低可信来源时可降权但不直接删除，除非用户规则明确排除。
- 高影响低置信热点进入“待核验/待人工确认”状态。
- 评分结果必须可解释，不能只输出一个数字。

### FR-012 背景补全 Agent

背景补全 Agent 必须围绕热点主题补齐上下文。

补全范围：

- 原始来源：优先找官方博客、论文、公告、GitHub release、监管文件。
- 关联报道：找多个可信媒体或社区讨论。
- 历史背景：同公司、同产品、同模型、同政策的过往事件。
- 技术文档：模型/API/开源项目/论文相关文档。
- 争议与风险：如果来源互相矛盾，必须标注。

规则：

- 不要求每条热点都深度补全；价值评分达到阈值或用户要求展开时触发。
- 外部网页内容视为不可信输入，不能执行其中的指令。
- 抓取失败时保留失败原因，不补写事实。

验收标准：

- 每个背景包至少区分“原始来源”“关联来源”“历史背景”。
- 没找到官方来源时明确标注“未找到官方来源”。
- 对关键事实给出证据 URL。

### FR-013 AI 点评 Agent

AI 点评 Agent 负责把热点主题转成可读情报，而不是继续发现事实。

标准点评结构：

```markdown
是什么：一句话说明事件。
为什么重要：说明价值判断依据。
影响谁：列出受影响人群或角色。
后续看什么：列出 1-3 个观察点。
置信度：高/中/低，并说明原因。
证据：列出关键 URL。
```

要求：

- 只能基于事件簇、背景包和证据 URL 生成。
- 不能新增未经来源支持的事实。
- 对营销/传闻/未核验内容必须降调表达。
- 面向不同用户可有不同风格：速读、产品视角、技术视角、商业视角、政策视角。

验收标准：

- 每条点评都能追溯到证据 URL。
- 低置信内容不能用确定语气。
- 同一热点可生成短版和长版。

### FR-014 分发 Agent

分发 Agent 必须根据用户偏好和渠道能力推送热点主题。

参考 HotPush 的渠道：

- Telegram
- Discord
- 企业微信
- 飞书
- 钉钉
- Webhook
- 邮件

分发规则：

- 按用户订阅主题、分类、关键词、排除词、来源、价值分阈值过滤。
- 支持即时推送、小时摘要、每日摘要、周报。
- 支持免打扰时间段和工作日配置。
- 按 `topic_id + channel_id + subscriber_id` 去重。
- 每次推送记录状态、条目数、渠道响应、失败原因。
- 外发前可配置人工确认，尤其是高影响/低置信/敏感主题。

验收标准：

- 推送内容以热点主题为单位，不以单条 raw item 刷屏。
- 同一主题不会在同一订阅渠道重复推送。
- Webhook payload 提供机器可读 JSON。
- 渠道密钥必须脱敏展示和脱敏日志。

### FR-015 订阅与偏好系统

系统必须支持用户按主题、关键词、分类、来源、价值阈值和渠道订阅热点情报。

能力：

- 用户可订阅 AI、科技、商业、产品、政策、论文、开源项目等主题流。
- 用户可维护关键词包含、关键词排除、来源 allowlist/denylist。
- 用户可配置输出长度：标题速览、短评版、深度版。
- 用户可配置时间窗口：即时、小时摘要、每日摘要、周报。
- 用户可配置免打扰时间、工作日、最大推送条数。
- 订阅规则必须有启用/暂停状态和最近一次匹配时间。

验收标准：

- 同一 `topic_id` 在同一 `subscriber_id + channel_id + subscription_id` 下不重复推送。
- 用户偏好只影响筛选、排序和输出风格，不允许改写原始事实。
- 订阅命中原因必须可解释，例如命中关键词、分类、来源或价值阈值。

### FR-016 Web 管理台

完整系统必须提供 Web 管理台，用于查看和干预多 Agent 流水线。

页面清单：

- 公开热点页：展示已发布热点主题、分类、来源、时间、短评和证据。
- 数据源管理：配置 AI HOT API、RSS、RSSHub route、自定义 RSS、指定网站和社交源。
- 原始条目列表：查看 `RawItem`、抓取批次、源响应、入库状态和失败原因。
- 热点主题列表：查看 `HotTopicCluster`、来源数量、分数、状态、更新时间。
- 热点详情页：展示成员条目、合并理由、背景包、点评、证据和推送记录。
- 合并/拆分工具：人工合并相同事件、拆分误聚类事件，并记录操作原因。
- 价值评分页：查看分项评分、推荐理由、降权原因和审核状态。
- 审核队列：处理低置信、高影响、敏感、来源冲突的主题。
- 背景包管理：查看原始来源、关联来源、官方声明、历史背景和未解决问题。
- 点评预览：查看不同输出风格，允许人工编辑后发布。
- 订阅与推送：配置用户订阅、渠道、模板、免打扰和分发规则。
- 推送历史：查看每次推送状态、渠道响应、失败原因和重试记录。
- 运行日志：查看 Agent run、工具调用、耗时、token、费用估算、错误。
- 趋势分析：按主题、来源、分类、关键词、时间窗口查看趋势。
- 用户与权限：管理管理员、审核员、普通用户和只读用户。

验收标准：

- 管理台所有写操作必须记录操作者、时间、旧值、新值和原因。
- 敏感配置如 Webhook URL、Cookie、API key 只脱敏展示。
- 人工审核操作必须能回溯到对应 topic、Agent run 和证据。

### FR-017 公开查询 Agent 与 API 服务

完整系统需要同时支持人类查询和机器集成。

能力：

- Chat/CLI 查询入口：支持自然语言问答、追问、转换成群消息。
- REST API：提供 sources、raw-items、topics、assessments、backgrounds、commentaries、subscriptions、deliveries、runs 等资源。
- OpenAPI：后端 API 必须导出 OpenAPI 文档。
- Webhook：外部系统可订阅 topic published、delivery failed、source failed 等事件。
- 导出：支持 Markdown、JSON、CSV 三种导出格式。

验收标准：

- API 响应必须使用结构化 schema，不返回只有自然语言的不可解析结果。
- 对外 API 必须有分页、排序、过滤和错误码规范。
- Chat/CLI 入口调用同一后端服务，不复制一套业务逻辑。

### FR-018 调度与任务编排

系统必须把采集、聚类、评分、补全、点评和分发作为可观测任务编排。

能力：

- 支持按 source interval 定时采集。
- 支持手动触发某个 source、某个 topic、某个 Agent 阶段重跑。
- 支持失败重试、指数退避、源级熔断、单源锁。
- 支持从 RawItem、TopicCluster、ValueAssessment、BackgroundPack 任一阶段恢复。
- 支持任务暂停、恢复、取消。
- 支持任务优先级：用户即时查询高于后台巡检。

验收标准：

- 每个 Agent run 都有 `run_id`、输入、输出、状态、耗时、错误和 trace。
- 一个 source 抓取失败不阻塞其他 source。
- 重跑不会破坏历史结果，必须产生新版本或记录覆盖原因。

### FR-019 趋势分析与情报洞察

趋势能力必须基于可说明的数据范围生成，不把局部数据冒充全网统计。

能力：

- 按 source 保存 ranking snapshot / hot score snapshot。
- 按 topic 保存传播时间线：首次发现、来源扩散、评分变化、推送时间。
- 按分类/关键词/来源统计热点数量、精选数量、推送数量。
- 支持“最近 24 小时 / 7 天 / 30 天”趋势视图。
- 支持主题热度变化提醒，例如快速上升、跨平台扩散、官方来源出现。
- 支持导出趋势报告。

验收标准：

- 每个趋势结论必须标注数据来源、时间窗口和覆盖范围。
- AI HOT items 超过 7 天的历史限制必须显式说明；更长分析只能基于本系统已采集入库的数据或日报归档。
- 趋势页面不能把标题数量统计写成“行业真实发生数量”。

### FR-020 权限、角色与审核工作流

完整系统必须区分访问、配置、审核、发布和系统管理权限。

角色：

- 访客：查看公开已发布热点。
- 登录用户：管理自己的订阅和推送渠道。
- 审核员：处理 review topic、编辑点评、批准发布。
- 管理员：管理数据源、规则、用户、渠道和系统配置。
- 系统任务：只能执行被授权的采集、评分、补全、分发工具。

审核状态：

- `candidate`：系统发现但未评分。
- `clustered`：已聚类。
- `assessed`：已评分。
- `needs_review`：需要人工审核。
- `approved`：审核通过。
- `published`：已公开或已分发。
- `suppressed`：被降权或过滤。
- `archived`：归档不再处理。

验收标准：

- 高影响低置信、来源冲突、疑似敏感、疑似营销的 topic 必须进入 review。
- 审核员可以批准、驳回、编辑点评、合并、拆分、要求重跑背景补全。
- 所有人工动作写入 audit log。

### FR-021 模型、工具与提示词治理

多 Agent 系统必须把 LLM 调用当成可测试、可观测、可替换的组件。

能力：

- 模型供应商通过配置接入，建议用 LiteLLM 或等价网关统一 OpenAI、Claude、DeepSeek、Ollama 等。
- 所有 LLM 输出必须优先使用结构化输出 schema。
- 每个 Agent 拥有独立 system prompt、工具白名单、输出 schema 和 eval cases。
- 工具调用必须最小授权：采集 Agent 不能直接发送外部推送，点评 Agent 不能修改数据源。
- 保存 prompt 版本、模型、输入 token、输出 token、费用估算、耗时和失败原因。
- 支持离线 mock 模式，测试不依赖真实模型返回。

验收标准：

- LLM 失败时不生成伪结果；可进入 review 或降级为规则输出，并明确标注。
- 结构化输出不通过校验时必须重试或进入人工处理。
- 每次 prompt 或模型版本变更必须跑固定 eval 集。

### FR-022 成本、配额与限流

系统必须可控地使用外部 API、RSSHub、LLM 和推送渠道。

能力：

- 每个 source 有频率、超时、重试、并发、每日最大请求数。
- 每个用户/工作区有查询频率、推送频率、LLM token 月预算。
- 每个 Agent 阶段有最大输入长度、最大补全来源数、最大重试次数。
- 后台批处理和即时查询使用不同优先级队列。
- 成本看板展示按模型、Agent、用户、source 的调用量和估算费用。

验收标准：

- 达到预算或限流时，系统明确拒绝或排队，不静默跳过。
- 管理员可以查看哪个 source、订阅或 Agent 消耗最多。
- 不允许无限分页、无限抓取、无限背景补全。

## 7. 完整功能域需求

### 7.1 定时推送

能力：

- 用户配置每日/每小时推送。
- 支持精选、分类、关键词或日报。
- 支持 ETag 防空跑。
- 支持飞书、Slack、企业微信、邮件等渠道。

验收标准：

- 60 秒级轮询必须带 ETag。
- 推送前按 `id` 去重。
- 同一条不会重复推送到同一频道。

### 7.2 个性化订阅

能力：

- 用户订阅关键词，例如 OpenAI、Claude、Qwen、MCP、RAG。
- 用户订阅分类。
- 用户设置排除关键词。
- 用户设置摘要长度。

验收标准：

- 个性化只影响结果选择和展示，不改写原始事实。
- 每个订阅配置有独立 ETag 和最后处理游标。

### 7.3 多轮追问

能力：

- 用户问“展开第 2 条”时，Agent 读取上一轮结果上下文。
- 用户问“只看论文”时，在上一轮时间窗基础上追加分类。
- 用户问“给我转成群消息”时，复用上一轮条目生成短版。

验收标准：

- 上下文必须保存 query、items id、URL 和时间窗。
- 如果上下文过期或不存在，要求重新查询。

### 7.4 原文核验

能力：

- 用户要求“核验这条”时，Agent 打开原文 URL 做二次阅读。
- 对 X、arXiv、博客、新闻站分别做最小抽取。
- 输出“AI HOT 摘要”和“原文核验摘要”的差异。

验收标准：

- 默认不批量抓原文，避免对外站造成压力。
- 无法访问原文时保留 AI HOT 摘要并标注未核验。

### 7.5 趋势分析

能力：

- 按 7 天内 items + 180 天内 dailies 做趋势观察。
- 统计关键词出现次数、来源分布、分类变化。

限制：

- items API 只覆盖最近 7 天；更长趋势只能基于日报归档标题和日报内容，不等价于全量明细。

验收标准：

- 趋势结论必须写清数据范围。
- 不把日报归档标题统计冒充全量行业统计。

## 8. Agent 架构设计

### 8.1 总体流水线

```text
定时触发 / 手动触发 / 用户查询
  -> 采集 Agent
      -> Source Registry
      -> Fetcher Pool
      -> RawItem Normalizer
      -> Raw Store
  -> 去重聚类 Agent
      -> URL/标题/时间/来源规则
      -> Embedding 相似度
      -> LLM 难例判定
      -> Topic Store
  -> 价值判断 Agent
      -> 重要性/新鲜度/可信度/传播强度/相关性/噪音风险
      -> Value Score
  -> 背景补全 Agent
      -> 原始来源
      -> 关联报道
      -> 历史背景
      -> 官方声明/技术文档
  -> AI 点评 Agent
      -> 是什么
      -> 为什么重要
      -> 影响谁
      -> 后续看什么
  -> 分发 Agent
      -> 用户偏好
      -> 渠道模板
      -> 去重状态
      -> 推送历史
```

### 8.2 模块职责

| 模块 | 职责 |
|---|---|
| SourceRegistry | 管理 AI HOT API、RSSHub route、自定义 RSS、指定网站、社交源配置 |
| FetcherPool | 按源抓取，处理 UA、超时、重试、备用实例、并发、锁和缓存 |
| RawNormalizer | 把不同来源响应转为统一 `RawItem` |
| RawStore | 保存原始条目、抓取批次、源状态、失败原因 |
| ClusterEngine | 做 URL 归一、标题相似、embedding 相似、LLM 难例判定 |
| TopicStore | 保存热点主题、事件簇成员、合并/拆分历史 |
| ValueScorer | 做重要性、新鲜度、可信度、传播强度、相关性、噪音风险评分 |
| BackgroundResearcher | 抓取原始来源、关联来源、官方声明、技术文档和历史背景 |
| CommentaryGenerator | 基于证据生成短评、影响面和后续观察点 |
| SubscriptionMatcher | 根据用户偏好筛选主题 |
| DistributionManager | 渲染并推送到 Telegram、Discord、飞书、企业微信、钉钉、Webhook、邮件 |
| AuditLog | 保存 Agent trace、工具调用、评分原因、推送状态 |
| Evaluator | 用固定样例回归采集、聚类、评分、点评和分发 |

### 8.3 HotPush 到本系统的映射

| HotPush 能力 | 本系统对应模块 | 采用方式 |
|---|---|---|
| RSSHub 主备实例 | FetcherPool | 直接吸收为采集基础能力 |
| 内置热榜源 | SourceRegistry | 转成可配置 source schema |
| 自定义 RSS 验证 | SourceRegistry / FetcherPool | 吸收 URL 校验和 sample item 预览 |
| Redis 热榜缓存 | RawStore / FetcherPool | 吸收源级缓存，但补充 ETag/Last-Modified |
| pushed_items 去重 | DistributionManager | 改为按 topic/subscriber/channel 去重 |
| ranking snapshot | TopicStore / TrendAnalyzer | 吸收快照思路，扩展到事件簇热度 |
| 关键词/时间/来源规则 | ValueScorer / SubscriptionMatcher | 作为硬规则和用户偏好规则 |
| LiteLLM 摘要 | CommentaryGenerator | 保留多模型接入，但输入必须是证据包 |
| 多渠道推送 | DistributionManager | 吸收渠道适配器和推送历史 |
| 用户和权限 | Admin Console | 完整后台管理能力 |

### 8.4 数据模型

```ts
type SourceType =
  | "aihot_api"
  | "rss"
  | "rsshub"
  | "hot_search"
  | "news_site"
  | "social"
  | "website";

type SourceConfig = {
  id: string;
  name: string;
  type: SourceType;
  category: string;
  url?: string;
  route?: string;
  enabled: boolean;
  fetchIntervalMinutes: number;
  timeoutSeconds: number;
  retryCount: number;
  trustLevel: "high" | "medium" | "low";
  requiresCookie?: boolean;
};

type RawItem = {
  id: string;
  sourceId: string;
  sourceName: string;
  title: string;
  url: string;
  normalizedUrl: string;
  publishedAt: string | null;
  fetchedAt: string;
  author?: string | null;
  summary?: string | null;
  contentSnippet?: string | null;
  hotScore?: string | null;
  rank?: number | null;
  image?: string | null;
  rawPayloadRef?: string | null;
};

type HotTopicCluster = {
  topicId: string;
  title: string;
  canonicalUrl: string;
  primarySourceId: string;
  rawItemIds: string[];
  sourceIds: string[];
  firstSeenAt: string;
  lastSeenAt: string;
  clusterConfidence: number;
  mergeReasons: string[];
  status: "candidate" | "selected" | "suppressed" | "needs_review" | "published";
};

type ValueAssessment = {
  topicId: string;
  valueScore: number;
  importance: number;
  freshness: number;
  credibility: number;
  propagation: number;
  userRelevance: number;
  noiseRisk: number;
  recommendation: "promote" | "normal" | "suppress" | "review";
  reasons: string[];
};

type BackgroundPack = {
  topicId: string;
  originalSources: Array<{ title: string; url: string; sourceId: string }>;
  relatedSources: Array<{ title: string; url: string; sourceId: string }>;
  historicalContext: string[];
  officialStatements: Array<{ title: string; url: string }>;
  unresolvedQuestions: string[];
};

type TopicCommentary = {
  topicId: string;
  what: string;
  whyImportant: string;
  impact: string[];
  nextWatch: string[];
  confidence: "high" | "medium" | "low";
  evidenceUrls: string[];
};

type Subscription = {
  id: string;
  workspaceId: string;
  userId: string;
  name: string;
  categories: string[];
  includeKeywords: string[];
  excludeKeywords: string[];
  sourceAllowlist: string[];
  sourceDenylist: string[];
  minValueScore: number;
  deliveryMode: "instant" | "hourly_digest" | "daily_digest" | "weekly_digest";
  quietHours?: { start: string; end: string; timezone: string };
  enabled: boolean;
};

type DeliveryChannel = {
  id: string;
  workspaceId: string;
  type: "telegram" | "discord" | "wecom" | "feishu" | "dingtalk" | "webhook" | "email";
  name: string;
  secretRef: string;
  enabled: boolean;
  template: "brief" | "commentary" | "deep";
};

type DeliveryRecord = {
  id: string;
  topicId: string;
  subscriptionId: string;
  channelId: string;
  status: "pending" | "sent" | "failed" | "skipped" | "confirmed";
  renderedPayloadRef?: string;
  channelResponse?: string;
  errorMessage?: string;
  deliveredAt?: string;
};

type AgentRun = {
  runId: string;
  agentName: "collector" | "clusterer" | "value_scorer" | "background_researcher" | "commentary_generator" | "distributor";
  trigger: "schedule" | "manual" | "user_query" | "retry" | "webhook";
  inputRef: string;
  outputRef?: string;
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled" | "needs_review";
  startedAt: string;
  finishedAt?: string;
  model?: string;
  promptVersion?: string;
  inputTokens?: number;
  outputTokens?: number;
  estimatedCost?: number;
  errorType?: string;
  errorMessage?: string;
};

type ReviewDecision = {
  id: string;
  topicId: string;
  reviewerId: string;
  action: "approve" | "suppress" | "merge" | "split" | "edit_commentary" | "rerun_background";
  reason: string;
  createdAt: string;
};

type TrendSnapshot = {
  id: string;
  sourceId: string;
  topicId?: string;
  rawItemId?: string;
  rank?: number | null;
  hotScore?: string | null;
  capturedAt: string;
};

type HotItem = {
  id: string;
  title: string;
  title_en: string | null;
  url: string;
  source: string;
  publishedAt: string | null;
  summary: string | null;
  category: "ai-models" | "ai-products" | "industry" | "paper" | "tip" | null;
};

type ItemList = {
  count: number;
  hasNext: boolean;
  nextCursor: string | null;
  items: HotItem[];
};

type DailyReport = {
  date: string;
  generatedAt: string;
  windowStart: string;
  windowEnd: string;
  lead: {
    title: string;
    leadParagraph: string;
  } | null;
  sections: Array<{
    label: "模型发布/更新" | "产品发布/更新" | "行业动态" | "论文研究" | "技巧与观点";
    items: Array<{
      title: string;
      summary: string;
      sourceUrl: string;
      sourceName: string;
    }>;
  }>;
  flashes: Array<{
    title: string;
    sourceName: string;
    sourceUrl: string;
    publishedAt: string | null;
  }>;
};
```

说明：

- 上述模型来自公开 API 和 OpenAPI 采样。
- `summary` 可能是 null 或空字符串。
- `publishedAt` 可能是 null。
- `category` 可能是 null。
- `id` 是字符串，不能当数字处理。
- `RawItem` / `HotTopicCluster` 是本系统新增模型，不是 AI HOT 或 HotPush 的既有公开 API。

### 8.5 Topic 生命周期

热点主题必须有明确状态机，避免 Agent 在不同阶段重复处理或错误发布。

```text
candidate
  -> clustered
  -> assessed
  -> needs_review
  -> approved
  -> published
  -> archived

assessed -> suppressed
needs_review -> suppressed
published -> archived
```

状态规则：

- `candidate`：采集入库后，尚未完成聚类。
- `clustered`：已进入事件簇，但未完成价值判断。
- `assessed`：已评分，可进入补全、点评或分发候选。
- `needs_review`：低置信、高影响、敏感、来源冲突或自动化失败。
- `approved`：人工或规则批准，可对外发布。
- `published`：已进入公开页或至少一次外部分发。
- `suppressed`：被规则、评分或人工操作压制，不对外分发。
- `archived`：不再参与主动推送，但保留查询和审计。

验收标准：

- 所有状态变化都必须有原因和触发者，触发者可以是系统 Agent 或人工用户。
- 从 `suppressed` 恢复必须人工确认。
- 已 `published` 的 topic 如果被拆分，必须保留旧链接或跳转关系，避免推送历史失效。

### 8.6 Agent Run 生命周期

每次 Agent 执行必须可追踪、可重放、可失败恢复。

```text
queued -> running -> succeeded
queued -> running -> failed -> queued
queued -> running -> needs_review
queued -> cancelled
```

记录要求：

- 输入引用：source id、topic id、raw item ids、订阅 id 或用户 query。
- 输出引用：新增 raw items、topic ids、assessment id、background pack id、commentary id、delivery id。
- 模型信息：模型名、prompt 版本、结构化 schema 版本。
- 工具信息：调用的 URL、状态码、耗时、重试次数、ETag 命中情况。
- 成本信息：token、费用估算、外部 API 调用次数。

验收标准：

- 任意一条对外推送都能追溯到对应 Agent run 和证据 URL。
- Agent run 失败时必须保存失败类型，不允许只写“未知错误”。
- 重跑必须生成新的 run，不覆盖旧 run。

### 8.7 后端 API 资源面

完整系统后端应围绕以下资源暴露 REST API，OpenAPI 是开发合同。

| 资源 | 典型能力 |
|---|---|
| `/sources` | 数据源 CRUD、启停、校验、抓取预览 |
| `/fetch-runs` | 抓取任务列表、详情、重试、取消 |
| `/raw-items` | 原始条目查询、过滤、查看 raw payload |
| `/topics` | 事件簇查询、详情、状态变更 |
| `/topics/{id}/members` | 成员增删、合并、拆分 |
| `/assessments` | 价值评分查询、重跑、解释 |
| `/background-packs` | 证据包查询、补全重跑 |
| `/commentaries` | 点评生成、预览、人工编辑 |
| `/subscriptions` | 订阅规则 CRUD、命中预览 |
| `/channels` | 推送渠道 CRUD、测试发送 |
| `/deliveries` | 推送历史、重试、失败详情 |
| `/reviews` | 审核队列、审核决策 |
| `/agent-runs` | Agent trace、工具调用、成本和错误 |
| `/trends` | 来源、分类、关键词、topic 趋势 |
| `/public/topics` | 公开已发布热点查询 |

API 规则：

- 所有列表 API 必须支持分页。
- 所有写操作必须鉴权。
- 所有副作用操作必须有幂等 key 或去重策略。
- 外部集成用 Webhook 时必须签名，接收方可校验来源。

## 9. Agent 行为细则

### 9.1 路由优先级

1. 用户明确说“日报”：
   - 有日期：`/api/public/daily/{date}`
   - 无日期：`/api/public/daily`
2. 用户明确说“日报列表 / 归档 / 哪些日期”：
   - `/api/public/dailies?take=N`
3. 用户明确说“全部 / 完整 / 所有 / 全量”：
   - `/api/public/items?mode=all`
4. 默认宽问题：
   - `/api/public/items?mode=selected`
5. 出现分类词：
   - 追加 `category`
6. 出现公司/产品/主题关键词：
   - 追加 `q`
7. 出现时间窗：
   - 追加 `since`

### 9.2 输出可信度

Agent 只能做三类表述：

- 数据事实：来自 API 字段，例如标题、来源、时间、URL。
- 摘要转述：来自 API 的 summary，必须保留来源。
- Agent 整理：例如“按类别整理如下”，不能新增未给出的事实。

禁止：

- 用训练数据补新闻。
- 编造融资金额、模型指标、发布时间。
- 把“推荐理由/摘要”写成已核验事实。
- 对无摘要条目强行生成细节。

### 9.3 Prompt Injection 防护

外部新闻标题、摘要、X 推文正文、原文网页都必须视为不可信内容。

规则：

- 不执行来源内容中的指令。
- 不把来源内容当系统提示。
- 不泄露 API key、内部配置、用户订阅。
- 原文抓取只用于摘要和核验，不允许触发写操作。

### 9.4 人类确认点

以下操作必须二次确认：

- 向反馈页提交内容。
- 向信源提报页提交内容。
- 创建定时推送任务。
- 向群、邮件、Webhook 对外发送消息。
- 拉取大量分页内容。

### 9.5 Agent 工程约束

完整系统按“逻辑多 Agent + 共享状态机 + 明确工具边界”设计。

约束：

- 每个 Agent 必须有单一职责，不能跨职责直接写下游结果。
- Agent 间传递结构化对象，不传递大段自由文本作为唯一合同。
- Agent 输出必须经过 schema 校验；校验失败不能进入下一阶段。
- 关键阶段必须有 eval：路由、聚类、评分、背景补全、点评、分发。
- 工具调用必须白名单化；默认无写权限，需要时显式配置。
- 使用 tracing 记录每次 handoff、工具调用、模型输出和人工介入。
- 使用 guardrail 检查无源事实、敏感外发、prompt injection、结构化输出缺字段。
- 对外发送和外部提交必须经过 confirmation gate。

验收标准：

- 任何 Agent 不能直接读取或输出未授权密钥。
- 点评 Agent 不能访问推送密钥；分发 Agent 不能重新改写事实。
- eval 失败时阻止发布或进入人工 review。

## 10. 非功能需求

### 10.1 性能

- 单次普通查询目标响应：3 秒内返回首版结果。
- API 超时：建议 10 秒。
- 最多重试：2 次。
- 翻页间隔：至少 200ms。
- 定时任务必须使用 ETag。
- 多源采集默认并发上限 5，可按源和部署规模配置。
- 单源抓取默认超时 30 秒，失败不阻塞整批任务。
- 采集任务应支持流式进度反馈，避免等待全部源完成才展示。

### 10.2 稳定性

- API 失败不影响帮助、配置、缓存查看等本地能力。
- 可配置备用读取 RSS，但 RSS 字段少于 API，必须标注来源差异。
- 缓存仅用于降级，不得冒充最新结果。
- RSSHub 应支持主备实例；主实例失败时自动尝试备用实例。
- 源级连续失败后进入降频或熔断状态，并在后台展示。
- 首次抓取不触发推送，避免历史数据刷屏。

### 10.3 安全

- 不存储用户敏感信息。
- 不要求 AI HOT 登录凭证。
- Webhook、飞书机器人等密钥必须通过环境变量或密钥管理配置。
- 日志脱敏：不记录完整 Webhook URL、授权头、用户私密关键词。
- 外部内容必须按不可信输入处理，不能作为系统提示或工具指令执行。
- Cookie 类采集配置必须按敏感信息存储和展示脱敏。
- 对外发送消息、提交反馈、提交信源、创建订阅等副作用操作必须有用户确认或管理员配置。

### 10.4 可观测性

每次 Agent 运行记录：

- trace id
- run id / job id
- 用户意图
- 规划 endpoint 和 query
- source id
- HTTP 状态码
- 是否命中 ETag/304
- 返回条目数
- 新增 raw item 数
- 聚类合并/拆分数量
- 价值评分分布
- 输出条目数
- 推送渠道结果
- 错误类型
- 耗时

### 10.5 可测试性

必须提供单元测试：

- 意图路由测试。
- 时间解析测试。
- 分类映射测试。
- API 参数构造测试。
- 空结果和错误响应测试。
- 输出溯源检查测试。
- source 配置校验测试。
- raw item 归一化测试。
- 聚类规则测试。
- 价值评分规则测试。
- 分发去重测试。

必须提供集成测试：

- 使用 mock API 验证完整流程。
- 可选使用真实 API smoke test，但不能依赖实时内容断言具体新闻标题。
- 使用 mock RSS/RSSHub feed 验证采集、入库、聚类、评分、推送去重。

### 10.6 可维护性

- 后端业务逻辑按 source、fetcher、normalizer、clusterer、scorer、researcher、commentary、delivery 分层。
- 前端页面按公开页、管理台、审核台、运行观测分区。
- Agent prompt、schema、eval case 必须版本化。
- 数据库迁移必须可回滚；重大字段变更需有迁移说明。
- 配置使用环境变量 + 数据库配置组合，敏感值不落普通日志。
- 核心流程必须有简体中文注释，尤其是聚类、评分、审核和分发去重。

### 10.7 合规与内容安全

- 不绕过登录、付费墙、平台风控或访问限制。
- 不保存不必要的个人信息。
- 不将用户私密关键词、订阅、渠道密钥发送给无关模型或工具。
- 对疑似隐私、政治、医疗、金融等高风险内容进入人工 review。
- 对外输出不宣称系统能验证新闻真伪，只能说明来源、证据和置信度。
- 对来源站点的 robots.txt、ToS、速率限制和版权边界保留人工配置入口。

### 10.8 备份与恢复

- 数据库需要定期备份，至少覆盖 source、raw item、topic、subscription、delivery、audit log。
- Redis 只作为缓存、锁、去重和短期状态，不能作为唯一长期存储。
- 推送记录、审核记录、合并/拆分历史必须持久化。
- 生产故障恢复后，定时任务应从 last successful cursor / ETag / snapshot 继续，不重复推送历史消息。

### 10.9 成本与容量

- LLM 调用按 Agent、模型、用户、工作区记录 token 和估算费用。
- 背景补全有最大 URL 数、最大正文长度和最大模型调用次数。
- 每个 source 有每日请求上限和失败熔断阈值。
- 每个订阅有每日最大推送条数。
- 管理台展示近 24 小时、7 天、30 天的请求量、失败率、token、推送量和平均耗时。

## 11. 评估集

初始查询 eval cases：

| 用户输入 | 期望路由 | 关键断言 |
|---|---|---|
| 今天 AI 圈有什么 | items selected | 不走 daily |
| 过去 24 小时 AI 大新闻 | items selected + since | since 为 ISO UTC |
| 看一下今天的 AI 日报 | daily latest | 输出按 section |
| 看 2026-05-28 的日报 | daily date | path 日期正确 |
| 最近 OpenAI 有什么发布 | items + q=OpenAI | 使用服务端 q |
| 最近一周 AI 论文 | items + category=paper + since | 不超过 7 天 |
| 全部 AI 动态 | items mode=all | 显式 mode=all |
| 最近 3 天行业动态 | items category=industry + since | 分类正确 |
| 哪些日期有日报 | dailies | 不请求 daily 正文 |
| 看全部论文和模型 | 多次 items | 不构造非法多分类 |
| 2099-01-01 日报 | daily date | 404 友好提示 |
| q=a | items q 单字符 | 提醒关键词过短或不搜索 |

输出质量 eval：

- 每条是否包含 URL。
- 是否出现无源事实。
- 是否标注空摘要。
- 是否正确说明数据窗口。
- 是否把“精选”和“全部”混淆。

多 Agent eval cases：

| 场景 | 输入 | 期望结果 |
|---|---|---|
| RSS 采集 | 一个包含 3 条 item 的 mock RSS | 生成 3 条 `RawItem`，字段完整 |
| 源内去重 | 同一 RSS 重复抓取 | 不重复入库，不重复推送 |
| 跨源聚类 | 两个来源标题不同但 URL 相同 | 合并为同一个 `HotTopicCluster` |
| 避免误聚类 | 两条都提到 OpenAI 但事件不同 | 不合并，给出拆分原因 |
| 首次抓取保护 | 新 source 第一次抓取 50 条 | 入库但不触发分发 |
| 价值判断 | 官方发布 + 多源报道 | 高可信、高价值，并输出理由 |
| 噪音过滤 | 标题党/营销词明显 | 降权或进入 review，并输出原因 |
| 背景补全 | 热点主题有官方来源 | 背景包包含 original source URL |
| 点评生成 | 输入 topic + background pack | 输出 what/why/impact/next/evidence |
| 分发去重 | 同一 topic 第二次触发 | 同一 subscriber/channel 不重复发送 |

## 12. 完整验收标准

完整系统完成必须满足：

1. 能回答精选热点、全部动态、日报、日报归档、分类、关键词、组合查询。
2. 默认宽问题走精选。
3. 所有 API 请求带 User-Agent。
4. 支持 ETag 缓存。
5. 支持 400/403/404/429/503/超时错误处理。
6. 输出每条热点包含标题、来源、URL。
7. 不把缓存或训练知识冒充最新新闻。
8. 支持至少 3 类采集源：AI HOT API、RSSHub route、自定义 RSS。
9. 采集结果统一归一为 `RawItem`。
10. 支持源内去重和首次抓取不推送。
11. 支持基础跨源聚类：相同 URL 合并、标题明显相似合并，并支持后续扩展 embedding/LLM 难例判定。
12. 支持基础价值判断：重要性、可信度、新鲜度、噪音风险和推荐理由。
13. 支持证据受限的 AI 点评输出。
14. 支持至少 1 个推送渠道和 Webhook JSON 输出。
15. 单元测试覆盖路由、时间、分类、API 参数、错误处理、采集归一化、聚类、评分、分发去重。
16. 集成 smoke test 不断言具体新闻内容，只断言 schema 和基础字段。
17. README 或帮助文档说明“原文为准、AI 摘要需核对”。
18. Web 管理台覆盖数据源、原始条目、热点主题、审核队列、订阅推送、运行日志和趋势分析。
19. 每个 Agent run 有 trace、输入输出引用、状态、错误、耗时、模型和成本记录。
20. Topic 生命周期和审核状态可追踪，可人工合并、拆分、批准、压制和重跑。
21. 所有外发动作按 topic/subscription/channel 去重，并记录 delivery history。
22. 后端提供 OpenAPI，核心资源 API 支持分页、过滤、错误码和鉴权。
23. 结构化输出、prompt 版本、工具白名单、eval cases 和 guardrail 必须落地。
24. 成本、配额、限流、源级熔断、备份恢复有明确配置和后台可视化。

## 13. 开发前决策清单

本节用于把完整版 PRD 转成可执行工程合同。这里不裁剪产品范围，而是给后续开发设定默认冻结决策：如果没有新的反向指令，后续子 PRD 和代码实现按本节执行。若后续要改这些决策，应先更新本文或对应子 PRD，再进入实现。

### 13.1 产品形态决策

- 完整范围包含 Web 管理台 + 后端 API + 后台任务 + Agent 查询入口 + 推送机器人。
- 未登录可看公开热点页；登录后管理数据源、事件簇、规则、订阅、推送和审核。
- 默认使用场景覆盖个人知识工作流、团队群推送、公开热点页、内部情报台。
- 角色固定为访客、登录用户、审核员、管理员、系统任务、开发者 API 调用方。
- 工程按单租户优先实现，但核心表预留 `workspace_id`，避免未来多租户重构。

### 13.2 技术栈决策

- 后端采用 Python + FastAPI。
- 前端采用 Vue 3 + Vite + Tailwind CSS，延续 HotPush 参考栈。
- 数据库采用 PostgreSQL，使用 JSONB 保存可回放 payload 引用和部分结构化扩展字段。
- Redis 用于缓存、分布式锁、去重集合、rate limit 和轻量任务状态。
- 后台任务先采用 APScheduler + worker service；需要高吞吐时升级 Celery/RQ，任务接口保持不变。
- RSSHub 作为 Docker Compose 服务提供，同时支持外部 RSSHub 主备实例。
- LLM 接入采用 LiteLLM 或等价网关抽象多 provider，默认实现使用 OpenAI。
- Embedding 作为聚类增强能力纳入完整范围；早期实现可先落表结构和接口，再启用模型。

### 13.3 数据源与采集合规决策

- 完整范围支持 AI HOT API、RSS、RSSHub route、自定义 RSS、指定网站、热搜源、新闻源、社交源。
- 任意 URL 抓取必须经过 SSRF 防护、协议限制、内网地址拦截和超时限制。
- Cookie 属于敏感配置，必须加密存储和脱敏展示。
- 默认只抓列表页和文章页正文，不做全站爬取。
- 首批内置源从 AI HOT API、AI HOT RSS、Hacker News、V2EX、知乎、微博、B 站、掘金、官方博客/RSS 中选择可合法访问源。
- 每个 source 必须配置频率、并发、User-Agent、超时、重试、熔断、trust level 和合规备注。
- robots.txt、站点 ToS、平台限制不由系统自动绕过；管理员可配置禁用或降频。

### 13.4 Agent 编排决策

- 完整 PRD 使用“逻辑多 Agent + 可观测流水线”定义；工程实现先用模块化服务和后台任务，不强制每个 Agent 独立进程。
- 每个 Agent 产物入库，支持从 RawItem、TopicCluster、ValueAssessment、BackgroundPack 任一阶段重跑。
- 需要人工审核队列，处理低置信、高影响、敏感、来源冲突的主题。
- 每个 Agent 必须有独立输入 schema、输出 schema、prompt 版本、工具白名单和 eval cases。
- 所有 Agent run 必须保存输入引用、输出引用、模型、耗时、token、费用估算和错误。

### 13.5 数据模型与 API 决策

- 后端必须提供 OpenAPI。
- 核心表围绕 source、raw item、topic cluster、assessment、background、commentary、subscription、delivery、audit log 设计。
- raw payload 可存对象存储或数据库 JSON 字段，至少保存可回放引用。
- 聚类历史必须保存，便于审核和回滚。
- 保存 embedding 向量字段或向量表；未启用 embedding 时字段可为空。
- 所有列表 API 必须有分页、排序、过滤；所有写 API 必须鉴权和审计。

### 13.6 聚类与评分决策

- URL 归一后完全一致自动合并。
- 标题相似和 embedding 相似只作为候选，需要时间窗和来源信号共同判断。
- LLM 只处理规则不确定的难例。
- 评分必须输出分项分数和解释，禁止只给总分。
- 初始时间窗按 72 小时处理；超出时间窗的同主体事件默认拆成不同发展阶段。
- 高影响低置信、来源冲突、疑似营销、疑似敏感进入 `needs_review`。
- suppress 只表示不主动推送，不删除原始条目和审计记录。

### 13.7 背景补全与事实边界决策

- 高价值、高传播、高风险主题必须背景补全。
- 官方博客、论文、公告、GitHub release、监管文件优先级最高。
- 二手媒体可作为关联来源，不单独支撑关键事实。
- 来源冲突必须标注，不由 AI 擅自裁决。
- 背景补全结果必须区分原始来源、关联报道、历史背景、官方声明、未解决问题。
- 原文快照保存为可选能力；至少保存抓取时间、URL、标题、正文摘要和失败原因。

### 13.8 UI 与管理后台决策

- 公开热点页。
- 数据源管理。
- 原始条目列表。
- 热点主题/事件簇列表。
- 事件簇详情与合并/拆分。
- 价值评分与审核队列。
- 背景包与证据管理。
- 点评预览与编辑。
- 订阅规则与推送渠道。
- 推送历史。
- 运行日志与 Agent trace。
- 趋势分析。
- 用户与权限。
- UI 风格按工作台产品处理，强调密度、可扫描、状态清晰，不做营销式落地页。
- 事件簇详情页是核心页面，必须同时展示成员条目、评分、证据、点评、审核和推送记录。

### 13.9 部署与运维决策

- 完整系统先提供 Docker Compose：backend、frontend、postgres、redis、rsshub、worker。
- 所有定时任务和 Agent run 都必须有 trace。
- LLM 调用必须记录模型、输入输出 token、费用估算、失败原因。
- 生产部署可后续扩展 Kubernetes，但不是首个工程合同。
- 数据库备份、日志保留、密钥管理、错误告警必须在完整范围内。

### 13.10 子 PRD 拆分建议

完整版 PRD 后续建议拆成以下子 PRD 执行；这些子 PRD 是实施顺序，不是缩小范围：

- M1 共享契约：`docs/contracts/query-api.md`。
- M1 后端子 PRD：`docs/prd/m1-backend-query-core.md`。
- M1 前端子 PRD：`docs/prd/m1-frontend-query-console.md`。
- M2 共享契约：`docs/contracts/collection-api.md`。
- M2 后端子 PRD：`docs/prd/m2-backend-collection-core.md`。
- M2 前端子 PRD：`docs/prd/m2-frontend-source-console.md`。
- M2 路线 brief：`docs/prd/m2-collection-brief.md`（已升级为上述 contract / 子 PRD，保留为路线来源）。
- M3 共享契约：`docs/contracts/clustering-api.md`。
- M3 后端子 PRD：`docs/prd/m3-backend-clustering-trends.md`。
- M3 前端子 PRD：`docs/prd/m3-frontend-topic-console.md`。
- M3 路线 brief：`docs/prd/m3-clustering-trends-brief.md`（已升级为上述 contract / 子 PRD，保留为路线来源）。
- M4 共享契约：`docs/contracts/value-background-api.md`。
- M4 后端子 PRD：`docs/prd/m4-backend-value-background.md`。
- M4 前端子 PRD：`docs/prd/m4-frontend-assessment-console.md`。
- M4 路线 brief：`docs/prd/m4-value-background-brief.md`（已升级为上述 contract / 子 PRD，保留为路线来源）。
- M5 共享契约：`docs/contracts/commentary-distribution-api.md`。
- M5 后端子 PRD：`docs/prd/m5-backend-commentary-distribution.md`。
- M5 前端子 PRD：`docs/prd/m5-frontend-commentary-distribution-console.md`。
- M5 路线 brief：`docs/prd/m5-commentary-distribution-brief.md`（已升级为上述 contract / 子 PRD，保留为路线来源）。
- M6 共享契约：`docs/contracts/admin-rules-api.md`。
- M6 后端子 PRD：`docs/prd/m6-backend-admin-rules.md`。
- M6 前端子 PRD：`docs/prd/m6-frontend-admin-rules-console.md`。
- M6 路线 brief：`docs/prd/m6-admin-rules-brief.md`（已升级为上述 contract / 子 PRD，保留为路线来源）。
- M7 共享契约：`docs/contracts/eval-observability-api.md`。
- M7 后端子 PRD：`docs/prd/m7-backend-eval-observability.md`。
- M7 前端子 PRD：`docs/prd/m7-frontend-observability-console.md`。
- M7 路线 brief：`docs/prd/m7-eval-observability-brief.md`（已升级为上述 contract / 子 PRD，保留为路线来源）。

## 14. 完整范围的执行拆分

以下阶段用于降低开发风险和验证复杂度，不表示只做阶段内能力。最终交付范围仍以本文完整 PRD 为准。

### M0：PRD 与架构冻结

- 冻结多 Agent 分工和完整产品边界。
- 冻结 AI HOT 是种子源，HotPush 是采集/分发参考。
- 建立 eval cases 和数据模型草案。

验收：`prd.md` 能直接指导后续开发，不把未验证能力写成事实。

### M1：公开查询与种子源内核

- 先按 `docs/contracts/query-api.md` 冻结前后端共享 API。
- 后端按 `docs/prd/m1-backend-query-core.md` 实现查询内核。
- 前端按 `docs/prd/m1-frontend-query-console.md` 实现查询工作台。
- 实现 IntentRouter。
- 实现 QueryPlanner。
- 实现 AihotClient。
- 实现基础 Markdown 输出。
- 支持日报、归档、分类、关键词。
- 完成 mock 测试。

验收：命令行输入“今天 AI 圈有什么”可返回 AI HOT 精选条目。

### M2：采集基础设施

- 路线级 brief：`docs/prd/m2-collection-brief.md`。
- 实现 SourceRegistry。
- 实现 RSS/RSSHub 抓取器。
- 支持自定义 RSS 校验。
- 实现源级超时、重试、并发上限、缓存。
- 实现 RawItem 归一化和 RawStore。

验收：可配置 AI HOT API、RSSHub route、自定义 RSS 三类来源并正常入库。

### M3：去重聚类与趋势

- 路线级 brief：`docs/prd/m3-clustering-trends-brief.md`。
- 共享契约：`docs/contracts/clustering-api.md`。
- 后端子 PRD：`docs/prd/m3-backend-clustering-trends.md`。
- 前端子 PRD：`docs/prd/m3-frontend-topic-console.md`。
- 消费 M2 `RawItem`，不直接调用 source fetcher。
- 实现同 `normalizedUrl` 跨源自动合并。
- 标题相似只生成候选或 `needs_review`，不单独自动合并。
- 支持人工 merge / split 并保留原因和历史。
- 保存 topic 和聚类历史。
- 记录系统已采集范围内的排名/热度快照。

验收：相同 URL 跨源合并为同一 topic，不同事件不因同一公司名误合并。

### M4：价值判断与背景补全

- 路线级 brief：`docs/prd/m4-value-background-brief.md`。
- 共享契约：`docs/contracts/value-background-api.md`。
- 后端子 PRD：`docs/prd/m4-backend-value-background.md`。
- 前端子 PRD：`docs/prd/m4-frontend-assessment-console.md`。
- 消费 M3 `HotTopicCluster`、`TopicMember` 和 `TrendSnapshot`，不重新触发采集或聚类。
- 实现可解释价值评分、分项分、recommendation 和 review flag。
- 实现背景补全 Agent 的原始来源、关联来源、历史背景、官方声明、未解决问题字段。
- 标注官方来源缺失、来源冲突和背景抓取失败，不自动判定新闻真实性。
- 不生成最终 AI 点评，不做分发。

验收：每个精选 topic 有可解释评分；高影响低置信 topic 进入 review。

### M5：AI 点评与分发

- 路线级 brief：`docs/prd/m5-commentary-distribution-brief.md`。
- 共享契约：`docs/contracts/commentary-distribution-api.md`。
- 后端子 PRD：`docs/prd/m5-backend-commentary-distribution.md`。
- 前端子 PRD：`docs/prd/m5-frontend-commentary-distribution-console.md`。
- 消费 M3 topic 和 M4 assessment / background / evidence，不重新触发采集、聚类或价值判断。
- 实现证据受限的点评生成。
- 实现订阅偏好匹配。
- 实现至少一个群机器人推送和 Webhook 推送。
- 实现推送历史和分发去重。
- preview / dryRun 不发送；同一 `topic_id + subscription_id + channel_id` 不重复发送。
- 不返回真实 webhook URL、bot token 或明文 secret；外部文本按不可信输入处理。

验收：同一 topic 不会在同一订阅渠道重复发送。

### M6：管理后台与规则

- 路线级 brief：`docs/prd/m6-admin-rules-brief.md`。
- 共享契约：`docs/contracts/admin-rules-api.md`。
- 后端子 PRD：`docs/prd/m6-backend-admin-rules.md`。
- 前端子 PRD：`docs/prd/m6-frontend-admin-rules-console.md`。
- 新增认证、RBAC、ReviewDecision、AdminRuleSet、RerunRequest 和 AuditLog，不绕过 M2-M5 契约重写业务事实。
- 数据源管理。
- 推送渠道管理。
- 关键词包含/排除。
- 时间段限制。
- 用户/角色权限。
- 趋势分析页。
- 所有写操作必须记录操作者、时间、旧值、新值和 reason。
- 密钥只写入 secret manager / encrypted store，API 和 UI 只展示 `secretRef`、`maskedTarget` 和脱敏摘要。

验收：管理员可配置 source、规则、调度、渠道并查看运行状态。

### M7：评估与可观测

- 路线级 brief：`docs/prd/m7-eval-observability-brief.md`。
- 共享契约：`docs/contracts/eval-observability-api.md`。
- 后端子 PRD：`docs/prd/m7-backend-eval-observability.md`。
- 前端子 PRD：`docs/prd/m7-frontend-observability-console.md`。
- 固定 eval fixture 必须版本化；真实 API smoke 不断言具体新闻标题。
- 固定 eval 集。
- trace 日志。
- 输出溯源检查。
- Agent 运行回放。
- 回归测试加入 CI。
- 记录 token / cost estimate、错误率、耗时、请求量、推送量和告警事件。
- replay 默认 dryRun，不触发真实 webhook、bot、email 或外部提交。

验收：每次改动可跑 eval，避免路由、聚类、评分和分发策略退化。

## 15. 不做范围

全版本默认不做：

- 无边界的全网爬虫；系统优先使用 RSSHub、RSS、公开 API 和明确配置的指定网站抓取。
- 绕过 AI HOT 登录。
- 自动提交反馈或信源。
- 无确认群发消息。
- 长期全量历史明细分析。
- 自动判定新闻真实性。
- 复刻 AI HOT Web UI。
- 绕过社交平台、新闻网站或 RSSHub 的访问限制。
- 把未核验传闻包装成确定新闻。
- 用 AI 摘要替代事实核验和背景补全。

## 16. 开发参考

### AI HOT 公开资料

- 站点首页：https://aihot.virxact.com/
- Agent 接入：https://aihot.virxact.com/agent
- OpenAPI：https://aihot.virxact.com/openapi.yaml
- Skill：https://aihot.virxact.com/aihot-skill/SKILL.md
- RSS 精选：https://aihot.virxact.com/feed.xml
- RSS 全部：https://aihot.virxact.com/feed/all.xml
- RSS 日报：https://aihot.virxact.com/feed/daily.xml

### HotPush 参考资料

- GitHub 仓库：https://github.com/JackyST0/hotpush
- README：https://github.com/JackyST0/hotpush/blob/main/README.md
- 快速开始：https://github.com/JackyST0/hotpush/blob/main/docs/getting-started.md
- 推送渠道：https://github.com/JackyST0/hotpush/blob/main/docs/push-channels.md
- 采集源配置：`backend/app/utils/sources.py`
- RSS 抓取：`backend/app/services/rss_fetcher.py`
- 定时任务：`backend/app/services/scheduler.py`
- 推送服务：`backend/app/services/push_service.py`
- AI 摘要：`backend/app/services/ai_service.py`
- 规则与趋势：`backend/app/routers/rules.py`、`backend/app/routers/trends.py`

### Agent 工程实践参考

- OpenAI Agents 指南：https://platform.openai.com/docs/guides/agents
- OpenAI Agents SDK / Tracing / Guardrails / Evals 资源入口：https://developers.openai.com/resources/
- OpenAI Structured Outputs：https://platform.openai.com/docs/guides/structured-outputs
- OpenAI Function Calling / Tools：https://platform.openai.com/docs/guides/function-calling

这些参考用于设计 Agent 的工具调用、结构化输出、追踪、评估和安全边界；具体数据契约仍以 AI HOT 的 OpenAPI 和实测接口为准。
