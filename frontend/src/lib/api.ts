import {
  mockDaily,
  mockDailies,
  mockCreateSource,
  mockDisableSource,
  mockEnableSource,
  mockFetchRuns,
  mockHelp,
  mockItems,
  mockPreviewSource,
  mockRawItems,
  mockSourceHealth,
  mockSources,
  mockTriggerSourceFetch,
  mockUpdateSource,
} from "./mockApi";
import type {
  DailyArchiveItem,
  DailyReport,
  Envelope,
  FetchRun,
  FetchRunList,
  FetchRunQuery,
  FetchSourceRequest,
  HelpResponse,
  ItemsQuery,
  RawItemList,
  RawItemQuery,
  QueryItemList,
  SourceConfig,
  SourceHealthList,
  SourceHealthQuery,
  SourceInput,
  SourceList,
  SourceListQuery,
  SourcePreview,
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export function buildQueryString(params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export function buildRequestInit(method: RequestOptions["method"], body?: unknown): RequestInit {
  return {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  };
}

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
  source?: string;
};

export async function requestEnvelope<T>(path: string, options: RequestOptions = {}): Promise<Envelope<T>> {
  const { method = "GET", body, source = "aihot" } = options;
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, buildRequestInit(method, body));
    const responseBody = (await response.json()) as Envelope<T>;
    return responseBody;
  } catch (error) {
    return {
      data: null,
      meta: {
        traceId: "frontend_network_error",
        source,
        cached: false,
        query: {},
        warnings: [],
      },
      error: {
        code: source === "hot-godlike" ? "SOURCE_UNREACHABLE" : "UPSTREAM_UNAVAILABLE",
        message: source === "hot-godlike" ? "无法连接采集服务，请确认后端已启动。" : "无法连接查询服务，请确认后端已启动。",
        details: { reason: error instanceof Error ? error.message : String(error) },
        retryable: true,
      },
    };
  }
}

export async function fetchItems(query: ItemsQuery): Promise<Envelope<QueryItemList>> {
  if (USE_MOCK) {
    return mockItems(query);
  }
  return requestEnvelope<QueryItemList>(`/query/items${buildQueryString(query)}`);
}

export async function fetchDaily(date?: string): Promise<Envelope<DailyReport>> {
  if (USE_MOCK) {
    return mockDaily(date);
  }
  return requestEnvelope<DailyReport>(`/query/daily${buildQueryString({ date })}`);
}

export async function fetchDailies(take = 30): Promise<Envelope<DailyArchiveItem[]>> {
  if (USE_MOCK) {
    return mockDailies();
  }
  return requestEnvelope<DailyArchiveItem[]>(`/query/dailies${buildQueryString({ take })}`);
}

export async function fetchHelp(): Promise<Envelope<HelpResponse>> {
  if (USE_MOCK) {
    return mockHelp();
  }
  return requestEnvelope<HelpResponse>("/query/help");
}

export async function fetchSources(query: SourceListQuery = {}): Promise<Envelope<SourceList>> {
  if (USE_MOCK) {
    return mockSources(query);
  }
  return requestEnvelope<SourceList>(`/sources${buildQueryString(query)}`, { source: "hot-godlike" });
}

export async function createSource(source: SourceInput): Promise<Envelope<SourceConfig>> {
  if (USE_MOCK) {
    return mockCreateSource(source);
  }
  return requestEnvelope<SourceConfig>("/sources", {
    method: "POST",
    body: source,
    source: "hot-godlike",
  });
}

export async function updateSource(sourceId: string, updates: Partial<SourceInput>): Promise<Envelope<SourceConfig>> {
  if (USE_MOCK) {
    return mockUpdateSource(sourceId, updates);
  }
  return requestEnvelope<SourceConfig>(`/sources/${sourceId}`, {
    method: "PATCH",
    body: updates,
    source: "hot-godlike",
  });
}

export async function enableSource(sourceId: string): Promise<Envelope<SourceConfig>> {
  if (USE_MOCK) {
    return mockEnableSource(sourceId);
  }
  return requestEnvelope<SourceConfig>(`/sources/${sourceId}/enable`, {
    method: "POST",
    source: "hot-godlike",
  });
}

export async function disableSource(sourceId: string): Promise<Envelope<SourceConfig>> {
  if (USE_MOCK) {
    return mockDisableSource(sourceId);
  }
  return requestEnvelope<SourceConfig>(`/sources/${sourceId}/disable`, {
    method: "POST",
    source: "hot-godlike",
  });
}

export async function previewSource(source: SourceInput): Promise<Envelope<SourcePreview>> {
  if (USE_MOCK) {
    return mockPreviewSource(source);
  }
  return requestEnvelope<SourcePreview>("/sources/preview", {
    method: "POST",
    body: source,
    source: "hot-godlike",
  });
}

export async function triggerSourceFetch(
  sourceId: string,
  request: FetchSourceRequest = {},
): Promise<Envelope<FetchRun>> {
  if (USE_MOCK) {
    return mockTriggerSourceFetch(sourceId, request);
  }
  return requestEnvelope<FetchRun>(`/sources/${sourceId}/fetch`, {
    method: "POST",
    body: request,
    source: "hot-godlike",
  });
}

export async function fetchRuns(query: FetchRunQuery = {}): Promise<Envelope<FetchRunList>> {
  if (USE_MOCK) {
    return mockFetchRuns(query);
  }
  return requestEnvelope<FetchRunList>(`/fetch-runs${buildQueryString(query)}`, { source: "hot-godlike" });
}

export async function fetchRawItems(query: RawItemQuery = {}): Promise<Envelope<RawItemList>> {
  if (USE_MOCK) {
    return mockRawItems(query);
  }
  return requestEnvelope<RawItemList>(`/raw-items${buildQueryString(query)}`, { source: "hot-godlike" });
}

export async function fetchSourceHealth(query: SourceHealthQuery = {}): Promise<Envelope<SourceHealthList>> {
  if (USE_MOCK) {
    return mockSourceHealth(query);
  }
  return requestEnvelope<SourceHealthList>(`/source-health${buildQueryString(query)}`, { source: "hot-godlike" });
}
