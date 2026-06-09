import type { RawItem, RawItemQuery } from "../types/api";

export type RawItemFilterState = {
  sourceId: string;
  status: RawItem["status"] | "";
  q: string;
};

export const emptyRawItemFilters: RawItemFilterState = {
  sourceId: "",
  status: "",
  q: "",
};

export function buildRawItemQuery(filters: RawItemFilterState, take = 50): RawItemQuery {
  const sourceId = filters.sourceId.trim();
  const q = filters.q.trim();
  const query: RawItemQuery = { take };
  if (sourceId) {
    query.sourceId = sourceId;
  }
  if (filters.status) {
    query.status = filters.status;
  }
  if (q) {
    query.q = q;
  }
  return query;
}

export function countRawItemFilters(filters: RawItemFilterState): number {
  return [filters.sourceId.trim(), filters.status, filters.q.trim()].filter(Boolean).length;
}
