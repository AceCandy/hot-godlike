export function formatArchiveItemCount(value: number | null): string {
  return value === null ? "事件数未知" : `${value} 条`;
}
