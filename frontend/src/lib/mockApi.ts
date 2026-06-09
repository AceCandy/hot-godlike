import type {
  ApiError,
  DailyArchiveItem,
  DailyReport,
  Envelope,
  FetchRun,
  FetchRunList,
  FetchRunQuery,
  FetchSourceRequest,
  HelpResponse,
  ItemsQuery,
  RawItem,
  RawItemList,
  RawItemQuery,
  QueryItemList,
  SourceConfig,
  SourceHealth,
  SourceHealthList,
  SourceHealthQuery,
  SourceInput,
  SourceList,
  SourceListQuery,
  SourcePreview,
} from "../types/api";
import { filterSources, type SourceFilterState } from "./sourceFilters";

const warning = "摘要由 AI HOT 生成，关键事实请打开原文核对。";

function envelope<T>(
  data: T,
  query: Record<string, unknown> = {},
  source = "aihot",
  warnings: string[] = [warning],
): Envelope<T> {
  return {
    data,
    meta: {
      traceId: `tr_mock_${Date.now()}`,
      source,
      cached: false,
      query,
      warnings,
    },
    error: null,
  };
}

function errorEnvelope<T>(
  code: ApiError["code"],
  message: string,
  retryable: boolean,
  details: Record<string, unknown>,
  query: Record<string, unknown> = {},
  source = "aihot",
): Envelope<T> {
  return {
    data: null,
    meta: {
      traceId: `tr_mock_${Date.now()}`,
      source,
      cached: false,
      query,
      warnings: [],
    },
    error: {
      code,
      message,
      details,
      retryable,
    },
  };
}

export async function mockItems(query: ItemsQuery): Promise<Envelope<QueryItemList>> {
  const keyword = query.q?.toLowerCase();
  if (keyword === "forbidden") {
    return errorEnvelope(
      "UPSTREAM_FORBIDDEN",
      "数据源拒绝访问，请检查 User-Agent 或数据源访问限制。",
      false,
      { upstreamStatus: 403 },
      query,
    );
  }
  if (keyword === "unavailable") {
    return errorEnvelope(
      "UPSTREAM_UNAVAILABLE",
      "数据源暂时不可用，请稍后重试。",
      true,
      { upstreamStatus: 503 },
      query,
    );
  }
  if (keyword === "timeout") {
    return errorEnvelope(
      "UPSTREAM_TIMEOUT",
      "数据源请求超时，请稍后重试。",
      true,
      { upstreamStatus: null },
      query,
    );
  }
  if (keyword === "bad-json") {
    return errorEnvelope(
      "UPSTREAM_BAD_RESPONSE",
      "数据源响应异常。",
      true,
      { reason: "mock bad response" },
      query,
    );
  }
  if (keyword === "empty") {
    return envelope(
      {
        items: [],
        page: { take: query.take ?? 50, hasNext: false, nextCursor: null },
        window: { label: "过去 24 小时", since: null, timezone: "Asia/Shanghai" },
      },
      query,
    );
  }

  return envelope(
    {
      items: [
        {
          id: "mock-1",
          title: "OpenAI 发布新的 Agent 工具能力",
          titleEn: null,
          url: "https://example.com/openai-agent-tools",
          source: "AI HOT",
          publishedAt: "2026-05-29T01:20:00Z",
          summary: "这是一条用于前端开发的契约 mock 数据。",
          category: "ai-products",
          tags: ["Agent"],
          score: null,
        },
        {
          id: "mock-2",
          title: "一篇新的多模态模型论文引发讨论",
          titleEn: null,
          url: "https://example.com/paper",
          source: "AI HOT",
          publishedAt: null,
          summary: null,
          category: "paper",
          tags: [],
          score: null,
        },
      ],
      page: { take: query.take ?? 50, hasNext: false, nextCursor: null },
      window: { label: "过去 24 小时", since: null, timezone: "Asia/Shanghai" },
    },
    query,
  );
}

export async function mockDaily(date?: string): Promise<Envelope<DailyReport>> {
  if (date === "2099-01-01") {
    return errorEnvelope(
      "UPSTREAM_NOT_FOUND",
      "该日期暂无日报。",
      false,
      { upstreamStatus: 404 },
      { date },
    );
  }

  return envelope({
    date: date ?? "2026-05-29",
    generatedAt: "2026-05-29T00:00:00Z",
    windowStart: "2026-05-28T00:00:00Z",
    windowEnd: "2026-05-29T00:00:00Z",
    lead: {
      title: "AI HOT 日报",
      leadParagraph: "今日重点集中在模型能力、产品更新和开发者工具。",
    },
    sections: [
      {
        label: "产品发布/更新",
        items: [
          {
            title: "一个 AI 产品发布新版本",
            summary: "用于验证日报视图的 mock 摘要。",
            sourceName: "AI HOT",
            sourceUrl: "https://example.com/daily-item",
          },
        ],
      },
    ],
    flashes: [],
  });
}

export async function mockDailies(): Promise<Envelope<DailyArchiveItem[]>> {
  return envelope([
    { date: "2026-05-29", weekday: "星期五", title: "AI HOT 日报", itemCount: 12 },
    { date: "2026-05-28", weekday: "星期四", title: "AI HOT 日报", itemCount: 10 },
  ]);
}

export async function mockHelp(): Promise<Envelope<HelpResponse>> {
  return envelope({
    examples: ["今天 AI 圈有什么", "最近 OpenAI 有什么发布", "看一下今天的 AI 日报"],
    categories: [
      { label: "模型", value: "ai-models" },
      { label: "产品", value: "ai-products" },
      { label: "行业", value: "industry" },
      { label: "论文", value: "paper" },
      { label: "技巧", value: "tip" },
    ],
    limits: ["items 查询最长支持最近 7 天", "关键事实请打开原文核对"],
  });
}

export async function mockSources(query: SourceListQuery = {}): Promise<Envelope<SourceList>> {
  const filters: SourceFilterState = {
    type: query.type ?? "",
    status: query.status ?? "",
    enabled: query.enabled === undefined ? "all" : query.enabled ? "enabled" : "disabled",
    category: query.category ?? "",
  };
  const items = filterSources(mockSourceConfigs, filters);
  return collectionEnvelope(page(items, query.take ?? 50), query);
}

export async function mockCreateSource(source: SourceInput): Promise<Envelope<SourceConfig>> {
  const id = nextMockSourceNumber === 1 ? "src_mock_created" : `src_mock_created_${nextMockSourceNumber}`;
  nextMockSourceNumber += 1;
  const created = sourceFromInput(source, id);
  mockSourceConfigs = [created, ...mockSourceConfigs.filter((item) => item.id !== created.id)];
  return collectionEnvelope(created);
}

export async function mockUpdateSource(
  sourceId: string,
  updates: Partial<SourceInput>,
): Promise<Envelope<SourceConfig>> {
  const currentIndex = mockSourceConfigs.findIndex((item) => item.id === sourceId);
  if (currentIndex === -1) {
    return sourceNotFoundEnvelope<SourceConfig>(sourceId);
  }
  const current = mockSourceConfigs[currentIndex];
  const updated = {
    ...current,
    ...updates,
    status: updates.enabled === undefined ? current.status : updates.enabled ? "enabled" : "disabled",
    updatedAt: "2026-05-29T01:00:00Z",
  };
  mockSourceConfigs = mockSourceConfigs.map((item, index) => (index === currentIndex ? updated : item));
  return collectionEnvelope(updated);
}

export async function mockEnableSource(sourceId: string): Promise<Envelope<SourceConfig>> {
  const currentIndex = mockSourceConfigs.findIndex((item) => item.id === sourceId);
  if (currentIndex === -1) {
    return sourceNotFoundEnvelope<SourceConfig>(sourceId);
  }
  const updated = { ...mockSourceConfigs[currentIndex], enabled: true, status: "enabled" as const };
  mockSourceConfigs = mockSourceConfigs.map((item, index) => (index === currentIndex ? updated : item));
  return collectionEnvelope(updated);
}

export async function mockDisableSource(sourceId: string): Promise<Envelope<SourceConfig>> {
  const currentIndex = mockSourceConfigs.findIndex((item) => item.id === sourceId);
  if (currentIndex === -1) {
    return sourceNotFoundEnvelope<SourceConfig>(sourceId);
  }
  const updated = { ...mockSourceConfigs[currentIndex], enabled: false, status: "disabled" as const };
  mockSourceConfigs = mockSourceConfigs.map((item, index) => (index === currentIndex ? updated : item));
  return collectionEnvelope(updated);
}

export async function mockPreviewSource(source: SourceInput): Promise<Envelope<SourcePreview>> {
  if (source.route?.includes("blocked") || source.url?.includes("localhost")) {
    return collectionErrorEnvelope(
      "SOURCE_SSRF_BLOCKED",
      "数据源 URL 被安全策略拦截。",
      false,
      { reason: "mock_ssrf_blocked" },
    );
  }
  return collectionEnvelope({
    source: {
      name: source.name,
      type: source.type,
      route: source.route,
    },
    sampleItems: [
      {
        title: "Preview sample item",
        url: "https://example.com/source/preview",
        publishedAt: "2026-05-29T00:00:00Z",
        contentSnippet: "Preview sample summary",
      },
    ],
    warnings: [],
  });
}

export async function mockTriggerSourceFetch(
  sourceId: string,
  request: FetchSourceRequest = {},
): Promise<Envelope<FetchRun>> {
  const current = mockSourceConfigs.find((item) => item.id === sourceId);
  if (!current) {
    return sourceNotFoundEnvelope<FetchRun>(sourceId);
  }
  if (!current.enabled) {
    return collectionErrorEnvelope(
      "SOURCE_DISABLED",
      "数据源已停用，不能触发抓取。",
      false,
      { sourceId },
    );
  }
  return collectionEnvelope({
    id: "run_mock_manual",
    sourceId,
    trigger: "manual",
    status: "succeeded",
    startedAt: "2026-05-29T00:00:00Z",
    finishedAt: "2026-05-29T00:00:02Z",
    durationMs: 2000,
    fetchedCount: 2,
    newCount: 1,
    duplicateCount: 1,
    ignoredCount: 0,
    errorCode: null,
    errorMessage: null,
    traceId: request.idempotencyKey ?? "tr_mock_manual_fetch",
  });
}

export async function mockFetchRuns(query: FetchRunQuery = {}): Promise<Envelope<FetchRunList>> {
  let items = [...mockFetchRunItems];
  if (query.sourceId) {
    items = items.filter((item) => item.sourceId === query.sourceId);
  }
  if (query.status) {
    items = items.filter((item) => item.status === query.status);
  }
  return collectionEnvelope(page(items, query.take ?? 50), query);
}

export async function mockRawItems(query: RawItemQuery = {}): Promise<Envelope<RawItemList>> {
  let items = [...mockRawItemItems];
  if (query.sourceId) {
    items = items.filter((item) => item.sourceId === query.sourceId);
  }
  if (query.status) {
    items = items.filter((item) => item.status === query.status);
  }
  if (query.q) {
    items = items.filter((item) => item.title.toLowerCase().includes(query.q!.toLowerCase()));
  }
  return collectionEnvelope(page(items, query.take ?? 50), query);
}

export async function mockSourceHealth(query: SourceHealthQuery = {}): Promise<Envelope<SourceHealthList>> {
  let items = [...mockSourceHealthItems];
  if (query.sourceId) {
    items = items.filter((item) => item.sourceId === query.sourceId);
  }
  if (query.status) {
    items = items.filter((item) => item.status === query.status);
  }
  return collectionEnvelope(page(items, query.take ?? 50), query);
}

function collectionEnvelope<T>(data: T, query: Record<string, unknown> = {}): Envelope<T> {
  return envelope(data, query, "hot-godlike", []);
}

function collectionErrorEnvelope<T>(
  code: ApiError["code"],
  message: string,
  retryable: boolean,
  details: Record<string, unknown>,
): Envelope<T> {
  return errorEnvelope(code, message, retryable, details, {}, "hot-godlike");
}

function sourceNotFoundEnvelope<T>(sourceId: string): Envelope<T> {
  return collectionErrorEnvelope("SOURCE_NOT_FOUND", "数据源不存在。", false, { sourceId });
}

function page<T>(items: T[], take: number) {
  return {
    items: items.slice(0, take),
    page: {
      take,
      hasNext: items.length > take,
      nextCursor: null,
    },
  };
}

function sourceFromInput(source: SourceInput, id: string): SourceConfig {
  return {
    id,
    ...source,
    status: source.enabled ? "enabled" : "disabled",
    firstFetchMode: "ingest_only",
    etag: null,
    lastModified: null,
    lastFetchedAt: null,
    createdAt: "2026-05-29T00:00:00Z",
    updatedAt: "2026-05-29T00:00:00Z",
  };
}

const defaultMockSourceConfigs: SourceConfig[] = [
  {
    id: "src_rsshub_hn",
    name: "RSSHub Hacker News",
    type: "rsshub",
    category: "tech",
    url: null,
    route: "/hackernews/frontpage",
    enabled: true,
    status: "enabled",
    fetchIntervalMinutes: 30,
    timeoutSeconds: 30,
    retryCount: 2,
    concurrencyLimit: 1,
    trustLevel: "medium",
    requiresCookie: false,
    firstFetchMode: "ingest_only",
    etag: "etag-rsshub",
    lastModified: "Fri, 29 May 2026 00:10:00 GMT",
    lastFetchedAt: "2026-05-29T00:10:00Z",
    createdAt: "2026-05-29T00:00:00Z",
    updatedAt: "2026-05-29T00:10:00Z",
  },
  {
    id: "src_custom_rss",
    name: "Custom RSS",
    type: "rss",
    category: "tech",
    url: "https://example.com/custom/rss.xml",
    route: null,
    enabled: true,
    status: "degraded",
    fetchIntervalMinutes: 30,
    timeoutSeconds: 30,
    retryCount: 2,
    concurrencyLimit: 1,
    trustLevel: "medium",
    requiresCookie: false,
    firstFetchMode: "ingest_only",
    etag: null,
    lastModified: null,
    lastFetchedAt: "2026-05-29T00:00:00Z",
    createdAt: "2026-05-29T00:00:00Z",
    updatedAt: "2026-05-29T01:30:00Z",
  },
  {
    id: "src_disabled_rss",
    name: "Disabled RSS",
    type: "rss",
    category: "ops",
    url: "https://example.com/disabled/rss.xml",
    route: null,
    enabled: false,
    status: "disabled",
    fetchIntervalMinutes: 60,
    timeoutSeconds: 30,
    retryCount: 1,
    concurrencyLimit: 1,
    trustLevel: "low",
    requiresCookie: false,
    firstFetchMode: "ingest_only",
    etag: null,
    lastModified: null,
    lastFetchedAt: null,
    createdAt: "2026-05-29T00:00:00Z",
    updatedAt: "2026-05-29T00:00:00Z",
  },
];

let mockSourceConfigs = cloneSourceConfigs();
let nextMockSourceNumber = 1;

export function resetMockApiState() {
  mockSourceConfigs = cloneSourceConfigs();
  nextMockSourceNumber = 1;
}

function cloneSourceConfigs(): SourceConfig[] {
  return defaultMockSourceConfigs.map((source) => ({ ...source }));
}

const mockFetchRunItems: FetchRun[] = [
  {
    id: "run_mock_running",
    sourceId: "src_rsshub_hn",
    trigger: "schedule",
    status: "running",
    startedAt: "2026-05-29T00:12:00Z",
    finishedAt: null,
    durationMs: null,
    fetchedCount: 0,
    newCount: 0,
    duplicateCount: 0,
    ignoredCount: 0,
    errorCode: null,
    errorMessage: null,
    traceId: "tr_mock_running",
  },
  {
    id: "run_mock_succeeded",
    sourceId: "src_rsshub_hn",
    trigger: "manual",
    status: "succeeded",
    startedAt: "2026-05-29T00:00:00Z",
    finishedAt: "2026-05-29T00:00:02Z",
    durationMs: 2000,
    fetchedCount: 2,
    newCount: 1,
    duplicateCount: 1,
    ignoredCount: 0,
    errorCode: null,
    errorMessage: null,
    traceId: "tr_mock_succeeded",
  },
  {
    id: "run_mock_failed",
    sourceId: "src_custom_rss",
    trigger: "schedule",
    status: "failed",
    startedAt: "2026-05-29T01:00:00Z",
    finishedAt: "2026-05-29T01:00:04Z",
    durationMs: 4000,
    fetchedCount: 0,
    newCount: 0,
    duplicateCount: 0,
    ignoredCount: 0,
    errorCode: "SOURCE_BAD_RESPONSE",
    errorMessage: "数据源响应异常，无法解析。",
    traceId: "tr_mock_failed",
  },
];

const mockRawItemItems: RawItem[] = [
  {
    id: "raw_mock_1",
    sourceId: "src_rsshub_hn",
    sourceName: "RSSHub Hacker News",
    title: "Raw item from RSSHub",
    url: "https://example.com/raw/1",
    normalizedUrl: "https://example.com/raw/1",
    publishedAt: "2026-05-29T00:00:00Z",
    fetchedAt: "2026-05-29T00:00:03Z",
    author: null,
    summary: null,
    contentSnippet: "Raw item snippet",
    hotScore: null,
    rank: null,
    image: null,
    rawPayloadRef: null,
    status: "new",
  },
  {
    id: "raw_mock_2",
    sourceId: "src_custom_rss",
    sourceName: "Custom RSS",
    title: "Custom RSS failed raw item",
    url: "https://example.com/raw/2",
    normalizedUrl: "https://example.com/raw/2",
    publishedAt: null,
    fetchedAt: "2026-05-29T01:00:05Z",
    author: null,
    summary: "用于验证采集数据页筛选状态的 mock 数据。",
    contentSnippet: null,
    hotScore: null,
    rank: null,
    image: null,
    rawPayloadRef: null,
    status: "failed",
  },
];

const mockSourceHealthItems: SourceHealth[] = [
  {
    sourceId: "src_rsshub_hn",
    status: "enabled",
    lastSucceededAt: "2026-05-29T00:00:02Z",
    lastFailedAt: null,
    consecutiveFailures: 0,
    nextFetchAt: "2026-05-29T00:30:02Z",
    circuitOpenedAt: null,
    degradedUntil: null,
    lastErrorCode: null,
    lastErrorMessage: null,
  },
  {
    sourceId: "src_custom_rss",
    status: "degraded",
    lastSucceededAt: "2026-05-29T00:00:02Z",
    lastFailedAt: "2026-05-29T01:00:04Z",
    consecutiveFailures: 3,
    nextFetchAt: "2026-05-29T02:30:04Z",
    circuitOpenedAt: null,
    degradedUntil: "2026-05-29T02:30:04Z",
    lastErrorCode: "SOURCE_BAD_RESPONSE",
    lastErrorMessage: "数据源响应异常，无法解析。",
  },
  {
    sourceId: "src_circuit_open",
    status: "circuit_open",
    lastSucceededAt: "2026-05-29T00:00:02Z",
    lastFailedAt: "2026-05-29T01:20:04Z",
    consecutiveFailures: 5,
    nextFetchAt: "2026-05-29T01:50:04Z",
    circuitOpenedAt: "2026-05-29T01:20:04Z",
    degradedUntil: null,
    lastErrorCode: "SOURCE_TIMEOUT",
    lastErrorMessage: "数据源抓取超时，请稍后重试。",
  },
];
