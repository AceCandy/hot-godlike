export type Envelope<T> = {
  data: T | null;
  meta: {
    traceId: string;
    source: "aihot" | string;
    cached: boolean;
    query: Record<string, unknown>;
    warnings: string[];
  };
  error: ApiError | null;
};

export type ApiError = {
  code:
    | "BAD_REQUEST"
    | "UPSTREAM_FORBIDDEN"
    | "UPSTREAM_NOT_FOUND"
    | "UPSTREAM_RATE_LIMITED"
    | "UPSTREAM_UNAVAILABLE"
    | "UPSTREAM_TIMEOUT"
    | "UPSTREAM_BAD_RESPONSE"
    | "SOURCE_NOT_FOUND"
    | "SOURCE_DISABLED"
    | "SOURCE_COOKIE_REQUIRED"
    | "SOURCE_UNREACHABLE"
    | "SOURCE_TIMEOUT"
    | "SOURCE_BAD_RESPONSE"
    | "SOURCE_SSRF_BLOCKED"
    | "SOURCE_RATE_LIMITED"
    | "FETCH_RUN_NOT_FOUND"
    | "RAW_ITEM_NOT_FOUND"
    | "INTERNAL_ERROR";
  message: string;
  details: Record<string, unknown>;
  retryable: boolean;
};

export type CategoryValue =
  | "ai-models"
  | "ai-products"
  | "industry"
  | "paper"
  | "tip";

export type QueryMode = "selected" | "all";
export type TimePreset = "today" | "yesterday" | "24h" | "3d" | "7d";

export type QueryItem = {
  id: string;
  title: string;
  titleEn: string | null;
  url: string;
  source: string;
  publishedAt: string | null;
  summary: string | null;
  category: CategoryValue | null;
  tags: string[];
  score: number | null;
};

export type QueryItemList = {
  items: QueryItem[];
  page: {
    take: number;
    hasNext: boolean;
    nextCursor: string | null;
  };
  window: {
    label: string;
    since: string | null;
    timezone: string;
  };
};

export type DailyReport = {
  date: string;
  generatedAt: string | null;
  windowStart: string | null;
  windowEnd: string | null;
  lead: {
    title: string | null;
    leadParagraph: string | null;
  } | null;
  sections: Array<{
    label: string | null;
    items: Array<{
      title: string | null;
      summary: string | null;
      sourceName: string | null;
      sourceUrl: string | null;
    }>;
  }>;
  flashes: Array<{
    title: string | null;
    sourceName: string | null;
    sourceUrl: string | null;
    publishedAt: string | null;
  }>;
};

export type DailyArchiveItem = {
  date: string;
  weekday: string | null;
  title: string | null;
  itemCount: number | null;
};

export type HelpResponse = {
  examples: string[];
  categories: Array<{ label: string; value: CategoryValue }>;
  limits: string[];
};

export type ItemsQuery = {
  mode?: QueryMode;
  category?: CategoryValue;
  q?: string;
  since?: string;
  timePreset?: TimePreset;
  take?: number;
  cursor?: string;
};

export type Page<T> = {
  items: T[];
  page: {
    take: number;
    hasNext: boolean;
    nextCursor: string | null;
  };
};

export type SourceType = "aihot_api" | "aihot_rss" | "rss" | "rsshub";
export type SourceStatus = "enabled" | "disabled" | "degraded" | "circuit_open";
export type TrustLevel = "high" | "medium" | "low";

export type SourceConfig = {
  id: string;
  name: string;
  type: SourceType;
  category: string;
  url: string | null;
  route: string | null;
  enabled: boolean;
  status: SourceStatus;
  fetchIntervalMinutes: number;
  timeoutSeconds: number;
  retryCount: number;
  concurrencyLimit: number;
  trustLevel: TrustLevel;
  requiresCookie: boolean;
  firstFetchMode: "ingest_only";
  etag: string | null;
  lastModified: string | null;
  lastFetchedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type SourceInput = {
  name: string;
  type: SourceType;
  category: string;
  url: string | null;
  route: string | null;
  enabled: boolean;
  fetchIntervalMinutes: number;
  timeoutSeconds: number;
  retryCount: number;
  concurrencyLimit: number;
  trustLevel: TrustLevel;
  requiresCookie: boolean;
};

export type SourceList = Page<SourceConfig>;

export type SourceListQuery = {
  type?: SourceType;
  status?: SourceStatus;
  enabled?: boolean;
  category?: string;
  take?: number;
  cursor?: string;
};

export type SourcePreview = {
  source: {
    name: string;
    type: SourceType;
    route: string | null;
  };
  sampleItems: Array<{
    title: string;
    url: string;
    publishedAt: string | null;
    contentSnippet: string | null;
  }>;
  warnings: string[];
};

export type FetchRunStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "partial_failed"
  | "failed"
  | "cancelled";

export type FetchRun = {
  id: string;
  sourceId: string;
  trigger: "manual" | "schedule" | "retry" | "preview";
  status: FetchRunStatus;
  startedAt: string;
  finishedAt: string | null;
  durationMs: number | null;
  fetchedCount: number;
  newCount: number;
  duplicateCount: number;
  ignoredCount: number;
  errorCode: string | null;
  errorMessage: string | null;
  traceId: string;
};

export type FetchRunList = Page<FetchRun>;

export type FetchRunQuery = {
  sourceId?: string;
  status?: FetchRunStatus;
  take?: number;
  cursor?: string;
};

export type RawItem = {
  id: string;
  sourceId: string;
  sourceName: string;
  title: string;
  url: string;
  normalizedUrl: string;
  publishedAt: string | null;
  fetchedAt: string;
  author: string | null;
  summary: string | null;
  contentSnippet: string | null;
  hotScore: string | number | null;
  rank: number | null;
  image: string | null;
  rawPayloadRef: string | null;
  status: "new" | "duplicate" | "ignored" | "failed";
};

export type RawItemList = Page<RawItem>;

export type RawItemQuery = {
  sourceId?: string;
  status?: RawItem["status"];
  q?: string;
  take?: number;
  cursor?: string;
};

export type SourceHealth = {
  sourceId: string;
  status: SourceStatus;
  lastSucceededAt: string | null;
  lastFailedAt: string | null;
  consecutiveFailures: number;
  nextFetchAt: string | null;
  circuitOpenedAt: string | null;
  degradedUntil: string | null;
  lastErrorCode: string | null;
  lastErrorMessage: string | null;
};

export type SourceHealthList = Page<SourceHealth>;

export type SourceHealthQuery = {
  sourceId?: string;
  status?: SourceStatus;
  take?: number;
  cursor?: string;
};

export type FetchSourceRequest = {
  idempotencyKey?: string;
  reason?: string;
};
