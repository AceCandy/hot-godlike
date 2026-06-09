import { afterEach, describe, expect, it, vi } from "vitest";

import {
  mockCreateSource,
  mockDaily,
  mockDisableSource,
  mockEnableSource,
  mockFetchRuns,
  mockItems,
  mockPreviewSource,
  mockSourceHealth,
  mockSources,
  mockTriggerSourceFetch,
  resetMockApiState,
} from "./mockApi";
import { formatArchiveItemCount } from "./format";
afterEach(() => {
  resetMockApiState();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("query api helpers", () => {
  it("builds query strings without empty values", async () => {
    const { buildQueryString } = await import("./api");

    expect(
      buildQueryString({ mode: "selected", q: "", category: undefined, take: 50 }),
    ).toBe("?mode=selected&take=50");
  });

  it("mock items use the shared envelope shape", async () => {
    const response = await mockItems({ mode: "selected" });

    expect(response.error).toBeNull();
    expect(response.meta.source).toBe("aihot");
    expect(response.data?.items[0]?.url).toContain("https://");
  });

  it("mock empty query returns an empty list instead of an error", async () => {
    const response = await mockItems({ q: "empty" });

    expect(response.error).toBeNull();
    expect(response.data?.items).toHaveLength(0);
  });

  it("mock daily can represent a missing report error", async () => {
    const response = await mockDaily("2099-01-01");

    expect(response.data).toBeNull();
    expect(response.error?.code).toBe("UPSTREAM_NOT_FOUND");
    expect(response.error?.retryable).toBe(false);
  });

  it("mock items can represent retryable upstream failures", async () => {
    const response = await mockItems({ q: "unavailable" });

    expect(response.data).toBeNull();
    expect(response.error?.code).toBe("UPSTREAM_UNAVAILABLE");
    expect(response.error?.retryable).toBe(true);
  });

  it("mock items can represent bad upstream responses", async () => {
    const response = await mockItems({ q: "bad-json" });

    expect(response.data).toBeNull();
    expect(response.error?.code).toBe("UPSTREAM_BAD_RESPONSE");
    expect(response.error?.retryable).toBe(true);
  });

  it("formats missing archive counts as unknown instead of zero", () => {
    expect(formatArchiveItemCount(null)).toBe("事件数未知");
    expect(formatArchiveItemCount(0)).toBe("0 条");
    expect(formatArchiveItemCount(12)).toBe("12 条");
  });

  it("mock collection sources use the hot-godlike envelope shape", async () => {
    const response = await mockSources({ type: "rsshub", status: "enabled", take: 10 });

    expect(response.error).toBeNull();
    expect(response.meta.source).toBe("hot-godlike");
    expect(response.data?.items[0]?.type).toBe("rsshub");
    expect(response.data?.page.take).toBe(10);
  });

  it("source filters include type, status, enabled and category without empty values", async () => {
    const { buildSourceListQuery, filterSources } = await import("./sourceFilters");
    const response = await mockSources({ take: 10 });
    const filters = {
      type: "rss" as const,
      status: "disabled" as const,
      enabled: "disabled" as const,
      category: "ops",
    };

    expect(buildSourceListQuery(filters, 50)).toEqual({
      type: "rss",
      status: "disabled",
      enabled: false,
      category: "ops",
      take: 50,
    });
    expect(filterSources(response.data?.items ?? [], filters).map((item) => item.id)).toEqual([
      "src_disabled_rss",
    ]);
  });

  it("mock collection preview can represent source security errors", async () => {
    const response = await mockPreviewSource({
      name: "Blocked preview",
      type: "rsshub",
      category: "tech",
      url: null,
      route: "/blocked/private",
      enabled: true,
      fetchIntervalMinutes: 30,
      timeoutSeconds: 30,
      retryCount: 2,
      concurrencyLimit: 1,
      trustLevel: "medium",
      requiresCookie: false,
    });

    expect(response.data).toBeNull();
    expect(response.meta.source).toBe("hot-godlike");
    expect(response.error?.code).toBe("SOURCE_SSRF_BLOCKED");
    expect(response.error?.retryable).toBe(false);
  });

  it("mock collection health includes degraded and circuit states", async () => {
    const response = await mockSourceHealth({ take: 10 });

    expect(response.error).toBeNull();
    expect(response.data?.items.map((item) => item.status)).toContain("degraded");
    expect(response.data?.items.map((item) => item.status)).toContain("circuit_open");
  });

  it("collection view helpers resolve source names and latest health by source id", async () => {
    const { buildSourceNameLookup, healthBySourceId, prependFetchRun, resolveSourceName, upsertSourceConfig } =
      await import("./collectionViews");
    const sources = await mockSources({ take: 10 });
    const health = await mockSourceHealth({ take: 10 });
    const runs = await mockFetchRuns({ take: 10 });

    const sourceItems = sources.data?.items ?? [];
    const runItems = runs.data?.items ?? [];
    const names = buildSourceNameLookup(sourceItems);
    const healthLookup = healthBySourceId(health.data?.items ?? []);
    const updatedSource = { ...sourceItems[0], name: "Updated Hacker News" };
    const createdSource = { ...sourceItems[0], id: "src_created_local", name: "Created Local Source" };
    const manualRun = { ...runItems[0], id: "run_manual_new" };

    expect(resolveSourceName("src_rsshub_hn", names)).toBe("RSSHub Hacker News");
    expect(resolveSourceName("src_missing", names)).toBe("src_missing");
    expect(healthLookup.src_custom_rss?.status).toBe("degraded");
    expect(upsertSourceConfig(sourceItems, updatedSource)).toHaveLength(sourceItems.length);
    expect(upsertSourceConfig(sourceItems, updatedSource)[0].name).toBe("Updated Hacker News");
    expect(upsertSourceConfig(sourceItems, createdSource).map((item) => item.id)).toEqual([
      "src_created_local",
      ...sourceItems.map((item) => item.id),
    ]);
    expect(prependFetchRun(runItems, manualRun, 2).map((item) => item.id)).toEqual([
      "run_manual_new",
      runItems[0].id,
    ]);
  });

  it("source form helpers switch type-specific url and route fields", async () => {
    const { createEmptySourceForm, sourceFormFromConfig, sourceFormTargetKind, switchSourceFormType, toSourceInput } =
      await import("./sourceForm");
    const sources = await mockSources({ take: 10 });
    const blank = createEmptySourceForm();

    expect(blank.type).toBe("rsshub");
    expect(blank.url).toBe("");
    expect(blank.route).toBe("/hackernews/frontpage");
    expect(sourceFormTargetKind(blank)).toBe("route");

    const rss = switchSourceFormType({ ...blank, url: "https://example.com/feed.xml" }, "rss");
    expect(rss.route).toBe("");
    expect(sourceFormTargetKind(rss)).toBe("url");

    const rsshub = switchSourceFormType(rss, "rsshub");
    expect(rsshub.url).toBe("");
    expect(rsshub.route).toBe("/hackernews/frontpage");
    expect(toSourceInput({ ...rsshub, name: "HN", category: "tech" })).toMatchObject({
      type: "rsshub",
      url: null,
      route: "/hackernews/frontpage",
    });

    const aihotApi = switchSourceFormType(rsshub, "aihot_api");
    expect(sourceFormTargetKind(aihotApi)).toBe("builtin");
    expect(toSourceInput({ ...aihotApi, name: "AI HOT API", category: "ai" })).toMatchObject({
      type: "aihot_api",
      url: null,
      route: null,
    });

    expect(sourceFormFromConfig(sources.data!.items[0]).route).toBe("/hackernews/frontpage");
  });

  it("mock manual fetch can represent disabled source errors", async () => {
    const response = await mockTriggerSourceFetch("src_disabled_rss", {
      idempotencyKey: "manual-disabled",
    });

    expect(response.data).toBeNull();
    expect(response.error?.code).toBe("SOURCE_DISABLED");
    expect(response.error?.retryable).toBe(false);
  });

  it("mock source writes stay addressable after create", async () => {
    const created = await mockCreateSource({
      name: "Created Source",
      type: "rsshub",
      category: "tech",
      url: null,
      route: "/hackernews/frontpage",
      enabled: true,
      fetchIntervalMinutes: 30,
      timeoutSeconds: 30,
      retryCount: 2,
      concurrencyLimit: 1,
      trustLevel: "medium",
      requiresCookie: false,
    });

    const listed = await mockSources({ take: 10 });
    const disabled = await mockDisableSource(created.data!.id);
    const enabled = await mockEnableSource(created.data!.id);

    expect(created.data?.id).toBe("src_mock_created");
    expect(listed.data?.items.map((item) => item.id)).toContain("src_mock_created");
    expect(disabled.data).toMatchObject({
      id: "src_mock_created",
      enabled: false,
      status: "disabled",
    });
    expect(enabled.data).toMatchObject({
      id: "src_mock_created",
      enabled: true,
      status: "enabled",
    });
  });

  it("collection api helpers build query strings and JSON request bodies", async () => {
    vi.resetModules();
    const { buildQueryString, buildRequestInit } = await import("./api");

    const query = buildQueryString({ type: "rsshub", status: "enabled", take: 10 });
    const init = buildRequestInit("POST", {
      name: "RSSHub Hacker News",
      type: "rsshub",
      category: "tech",
      url: null,
      route: "/hackernews/frontpage",
      enabled: true,
      fetchIntervalMinutes: 30,
      timeoutSeconds: 30,
      retryCount: 2,
      concurrencyLimit: 1,
      trustLevel: "medium",
      requiresCookie: false,
    });

    expect(query).toBe("?type=rsshub&status=enabled&take=10");
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(String(init.body))).toMatchObject({
      type: "rsshub",
      route: "/hackernews/frontpage",
    });
  });
});
