import type { SourceConfig, SourceInput, SourceType, TrustLevel } from "../types/api";

export type SourceFormState = {
  name: string;
  type: SourceType;
  category: string;
  url: string;
  route: string;
  enabled: boolean;
  fetchIntervalMinutes: number;
  timeoutSeconds: number;
  retryCount: number;
  concurrencyLimit: number;
  trustLevel: TrustLevel;
  requiresCookie: boolean;
};

const DEFAULT_RSSHUB_ROUTE = "/hackernews/frontpage";

export function createEmptySourceForm(overrides: Partial<SourceFormState> = {}): SourceFormState {
  return {
    name: "",
    type: "rsshub",
    category: "tech",
    url: "",
    route: DEFAULT_RSSHUB_ROUTE,
    enabled: true,
    fetchIntervalMinutes: 30,
    timeoutSeconds: 30,
    retryCount: 2,
    concurrencyLimit: 1,
    trustLevel: "medium",
    requiresCookie: false,
    ...overrides,
  };
}

export function sourceFormFromConfig(source: SourceConfig): SourceFormState {
  return createEmptySourceForm({
    name: source.name,
    type: source.type,
    category: source.category,
    url: source.url ?? "",
    route: source.route ?? "",
    enabled: source.enabled,
    fetchIntervalMinutes: source.fetchIntervalMinutes,
    timeoutSeconds: source.timeoutSeconds,
    retryCount: source.retryCount,
    concurrencyLimit: source.concurrencyLimit,
    trustLevel: source.trustLevel,
    requiresCookie: source.requiresCookie,
  });
}

export function sourceFormTargetKind(form: Pick<SourceFormState, "type">): "builtin" | "route" | "url" {
  if (form.type === "rsshub") {
    return "route";
  }
  if (form.type === "rss" || form.type === "aihot_rss") {
    return "url";
  }
  return "builtin";
}

export function switchSourceFormType(form: SourceFormState, type: SourceType): SourceFormState {
  const next = { ...form, type };
  const targetKind = sourceFormTargetKind(next);
  if (targetKind === "route") {
    return { ...next, url: "", route: next.route.trim() || DEFAULT_RSSHUB_ROUTE };
  }
  if (targetKind === "url") {
    return { ...next, route: "" };
  }
  return { ...next, url: "", route: "" };
}

export function toSourceInput(form: SourceFormState): SourceInput {
  const targetKind = sourceFormTargetKind(form);
  const url = form.url.trim();
  const route = form.route.trim();
  return {
    name: form.name.trim(),
    type: form.type,
    category: form.category.trim(),
    url: targetKind === "url" && url ? url : null,
    route: targetKind === "route" && route ? route : null,
    enabled: form.enabled,
    fetchIntervalMinutes: form.fetchIntervalMinutes,
    timeoutSeconds: form.timeoutSeconds,
    retryCount: form.retryCount,
    concurrencyLimit: form.concurrencyLimit,
    trustLevel: form.trustLevel,
    requiresCookie: form.requiresCookie,
  };
}
