<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import ApiStateView from "./ApiStateView.vue";
import { fetchRawItems, fetchSources } from "../lib/api";
import {
  buildRawItemQuery,
  countRawItemFilters,
  emptyRawItemFilters,
  type RawItemFilterState,
} from "../lib/rawItemFilters";
import { sanitizeRawItemHtml } from "../lib/sanitizeHtml";
import type { ApiError, RawItem, SourceConfig } from "../types/api";

const sources = ref<SourceConfig[]>([]);
const rawItems = ref<RawItem[]>([]);
const filters = ref<RawItemFilterState>({ ...emptyRawItemFilters });
const loading = ref(false);
const error = ref<ApiError | null>(null);
const traceId = ref("");

const rawItemLabels: Record<RawItem["status"], string> = {
  new: "新增",
  duplicate: "重复",
  ignored: "忽略",
  failed: "失败",
};

const sourceOptions = computed(() => [...sources.value].sort((a, b) => a.name.localeCompare(b.name)));
const activeFilterCount = computed(() => countRawItemFilters(filters.value));
const empty = computed(() => !loading.value && !error.value && rawItems.value.length === 0);

async function loadCollectionData() {
  loading.value = true;
  error.value = null;
  const [sourceResponse, rawItemResponse] = await Promise.all([
    fetchSources({ take: 100 }),
    fetchRawItems(buildRawItemQuery(filters.value, 50)),
  ]);
  loading.value = false;
  traceId.value = rawItemResponse.meta.traceId || sourceResponse.meta.traceId;
  error.value = sourceResponse.error ?? rawItemResponse.error;
  sources.value = sourceResponse.data?.items ?? [];
  rawItems.value = rawItemResponse.data?.items ?? [];
}

function resetFilters() {
  filters.value = { ...emptyRawItemFilters };
  void loadCollectionData();
}

function formatTime(value: string | null): string {
  if (!value) {
    return "未知";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function rawItemStatusClass(status: RawItem["status"]): string {
  if (status === "new") {
    return "status-enabled";
  }
  if (status === "failed") {
    return "status-circuit-open";
  }
  if (status === "duplicate") {
    return "status-degraded";
  }
  return "status-disabled";
}

function rawItemPreviewHtml(item: RawItem): string {
  return sanitizeRawItemHtml(item.summary || item.contentSnippet || "该条暂无摘要");
}

onMounted(() => {
  void loadCollectionData();
});
</script>

<template>
  <section class="collection-data-page" aria-label="采集数据">
    <header class="source-console-header">
      <div>
        <p class="eyebrow">M2 Collection Data</p>
        <h2>采集数据</h2>
      </div>
      <dl class="source-stats" aria-label="采集数据统计">
        <div>
          <dt>当前列表</dt>
          <dd>{{ rawItems.length }}</dd>
        </div>
        <div>
          <dt>数据源</dt>
          <dd>{{ sources.length }}</dd>
        </div>
        <div>
          <dt>筛选</dt>
          <dd>{{ activeFilterCount }}</dd>
        </div>
      </dl>
    </header>

    <form class="raw-item-filter-bar" aria-label="采集数据筛选" @submit.prevent="loadCollectionData">
      <label>
        <span>数据源</span>
        <select v-model="filters.sourceId" aria-label="采集数据源筛选" @change="loadCollectionData">
          <option value="">全部数据源</option>
          <option v-for="source in sourceOptions" :key="source.id" :value="source.id">
            {{ source.name }}
          </option>
        </select>
      </label>
      <label>
        <span>状态</span>
        <select v-model="filters.status" aria-label="采集数据状态筛选" @change="loadCollectionData">
          <option value="">全部状态</option>
          <option value="new">{{ rawItemLabels.new }}</option>
          <option value="duplicate">{{ rawItemLabels.duplicate }}</option>
          <option value="ignored">{{ rawItemLabels.ignored }}</option>
          <option value="failed">{{ rawItemLabels.failed }}</option>
        </select>
      </label>
      <label class="raw-item-keyword">
        <span>关键词</span>
        <input v-model="filters.q" type="search" placeholder="搜索标题关键词" aria-label="采集数据关键词" />
      </label>
      <button type="submit" class="primary-button">查询</button>
      <button type="button" class="secondary-button" @click="resetFilters">
        清空<span v-if="activeFilterCount"> {{ activeFilterCount }}</span>
      </button>
      <button type="button" class="secondary-button" @click="loadCollectionData">刷新</button>
    </form>

    <ApiStateView
      :loading="loading"
      :empty="empty"
      :error="error"
      :trace-id="traceId"
      @retry="loadCollectionData"
    />

    <section v-if="!loading && !error && rawItems.length" class="raw-item-list" aria-label="采集数据列表">
      <article v-for="item in rawItems" :key="item.id" class="raw-item-row">
        <div class="raw-item-main">
          <a :href="item.url" target="_blank" rel="noreferrer" class="raw-item-title">
            {{ item.title }}
          </a>
          <div class="collection-subtitle">
            {{ item.sourceName }} · 抓取 {{ formatTime(item.fetchedAt) }}
          </div>
          <div class="raw-item-html-preview" v-html="rawItemPreviewHtml(item)"></div>
        </div>
        <div class="raw-item-side">
          <span class="status-badge" :class="rawItemStatusClass(item.status)">
            {{ rawItemLabels[item.status] }}
          </span>
          <dl class="raw-item-meta">
            <div>
              <dt>发布时间</dt>
              <dd>{{ formatTime(item.publishedAt) }}</dd>
            </div>
            <div>
              <dt>sourceId</dt>
              <dd>{{ item.sourceId }}</dd>
            </div>
            <div>
              <dt>rawItemId</dt>
              <dd>{{ item.id }}</dd>
            </div>
          </dl>
        </div>
      </article>
    </section>
  </section>
</template>
