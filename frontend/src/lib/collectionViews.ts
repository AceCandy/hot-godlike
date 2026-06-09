import type { FetchRun, SourceConfig, SourceHealth } from "../types/api";

export function buildSourceNameLookup(sources: SourceConfig[]): Record<string, string> {
  return Object.fromEntries(sources.map((source) => [source.id, source.name]));
}

export function resolveSourceName(sourceId: string, names: Record<string, string>): string {
  return names[sourceId] ?? sourceId;
}

export function healthBySourceId(items: SourceHealth[]): Record<string, SourceHealth> {
  return Object.fromEntries(items.map((item) => [item.sourceId, item]));
}

export function upsertSourceConfig(items: SourceConfig[], source: SourceConfig): SourceConfig[] {
  const existingIndex = items.findIndex((item) => item.id === source.id);
  if (existingIndex === -1) {
    return [source, ...items];
  }
  return items.map((item, index) => (index === existingIndex ? source : item));
}

export function prependFetchRun(items: FetchRun[], run: FetchRun, take: number): FetchRun[] {
  // 写接口返回的 run 是用户刚触发的结果，放在最前面并去重，避免 mock reload 冲掉反馈。
  return [run, ...items.filter((item) => item.id !== run.id)].slice(0, take);
}
