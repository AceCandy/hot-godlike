import type { SourceConfig, SourceListQuery, SourceStatus, SourceType } from "../types/api";

export type SourceEnabledFilter = "all" | "enabled" | "disabled";

export type SourceFilterState = {
  type: SourceType | "";
  status: SourceStatus | "";
  enabled: SourceEnabledFilter;
  category: string;
};

export const emptySourceFilters: SourceFilterState = {
  type: "",
  status: "",
  enabled: "all",
  category: "",
};

export function buildSourceListQuery(filters: SourceFilterState, take = 50): SourceListQuery {
  const category = filters.category.trim();
  const query: SourceListQuery = { take };
  if (filters.type) {
    query.type = filters.type;
  }
  if (filters.status) {
    query.status = filters.status;
  }
  if (filters.enabled !== "all") {
    query.enabled = filters.enabled === "enabled";
  }
  if (category) {
    query.category = category;
  }
  return query;
}

export function filterSources(sources: SourceConfig[], filters: SourceFilterState): SourceConfig[] {
  const category = filters.category.trim();
  return sources.filter((source) => {
    if (filters.type && source.type !== filters.type) {
      return false;
    }
    if (filters.status && source.status !== filters.status) {
      return false;
    }
    if (filters.enabled !== "all" && source.enabled !== (filters.enabled === "enabled")) {
      return false;
    }
    if (category && source.category !== category) {
      return false;
    }
    return true;
  });
}

export function countSourceFilters(filters: SourceFilterState): number {
  return [
    filters.type,
    filters.status,
    filters.enabled === "all" ? "" : filters.enabled,
    filters.category.trim(),
  ].filter(Boolean).length;
}
