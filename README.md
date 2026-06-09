# Hot Godlike

多 Agent 热点情报系统。当前实现遵循根目录 `workflow.md`，已进入 M1 / M2 可开发状态。

## 文档入口

- 总 PRD：`prd.md`
- 开发流程：`workflow.md`
- M1 API 契约：`docs/contracts/query-api.md`
- M1 后端 PRD：`docs/prd/m1-backend-query-core.md`
- M1 前端 PRD：`docs/prd/m1-frontend-query-console.md`
- M2 API 契约：`docs/contracts/collection-api.md`
- M2 后端 PRD：`docs/prd/m2-backend-collection-core.md`
- M2 前端 PRD：`docs/prd/m2-frontend-source-console.md`

## 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest
```

默认服务：

```text
http://localhost:8000
```

M2 默认仍使用内存 source repository、collection store 和 source lock，便于本地开发和测试。启用 PostgreSQL source repository：

```bash
USE_POSTGRES_SOURCE_REPOSITORY=true DATABASE_URL=postgresql://user:password@localhost:5432/hot_godlike uvicorn app.main:app --reload
```

启用 PostgreSQL collection store：

```bash
USE_POSTGRES_COLLECTION_STORE=true DATABASE_URL=postgresql://user:password@localhost:5432/hot_godlike uvicorn app.main:app --reload
```

启用 Redis source lock：

```bash
USE_REDIS_LOCK=true REDIS_URL=redis://localhost:6379/0 uvicorn app.main:app --reload
```

启用 Redis ETag / Last-Modified 元数据：

```bash
USE_REDIS_SOURCE_METADATA=true REDIS_URL=redis://localhost:6379/0 uvicorn app.main:app --reload
```

启用 Redis 源内 dedupe set：

```bash
USE_REDIS_SOURCE_DEDUPE=true REDIS_URL=redis://localhost:6379/0 uvicorn app.main:app --reload
```

启用 APScheduler 采集 worker：

```bash
USE_SCHEDULER_WORKER=true SCHEDULER_WORKER_INTERVAL_SECONDS=60 uvicorn app.main:app --reload
```

PostgreSQL migration 位于：

```text
backend/migrations/001_m2_collection_schema.sql
```

M2 scheduler core 已挂载到应用状态：

```text
app.state.scheduler_service.run_due_once()
```

默认不会自动启动后台循环；设置 `USE_SCHEDULER_WORKER=true` 后，应用 lifespan 会启动 APScheduler worker，并在应用关闭时释放。`SCHEDULER_WORKER_INTERVAL_SECONDS` 默认为 60。

M2 SourceHealth 策略已接入内存和 PostgreSQL collection store：连续失败 3 次进入 `degraded`，下一次抓取延后为 source `fetchIntervalMinutes` 的 3 倍，并写入 `degradedUntil`；连续失败 5 次进入 `circuit_open`，默认 30 分钟后再允许调度尝试恢复。`CollectionRunner` 会把 health status 同步到 SourceConfig `status`，成功抓取后恢复为 `enabled`；scheduler 按 `enabled` 布尔值扫描 source，再由 health `nextFetchAt` 控制 degraded / circuit_open 的调度窗口。

M2 默认采集链路通过 FetcherPool 分发：

```text
aihot_api -> M1 AihotClient
aihot_rss/rss/rsshub -> SourcePreviewer RSS/Atom fetcher
```

## 前端

```bash
cd frontend
npm install
npm run dev
npm run test
npm run build
```

本地 mock：

```bash
VITE_USE_MOCK=true npm run dev
```

默认后端地址：

```text
VITE_API_BASE_URL=http://localhost:8000/api
```

## 阶段边界

M1 不包含登录、数据库、多源采集、聚类、评分、背景补全、AI 点评、订阅和推送。

M2 只做采集基础设施：source、preview、manual fetch、fetch run、raw item、source health、PostgreSQL / Redis 基础边界。M2 不做跨源聚类、价值判断、背景补全、AI 点评和分发。

M3-M7 必须先把对应 brief 升级为详细 PRD 和 contract，再进入实现。
