<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import ApiStateView from "./components/ApiStateView.vue";
import DailyArchiveList from "./components/DailyArchiveList.vue";
import DailyReportView from "./components/DailyReportView.vue";
import ItemResultCard from "./components/ItemResultCard.vue";
import SourceConsolePage from "./components/SourceConsolePage.vue";
import WarningBanner from "./components/WarningBanner.vue";
import { fetchDaily, fetchDailies, fetchHelp, fetchItems } from "./lib/api";
import type {
  ApiError,
  CategoryValue,
  DailyArchiveItem,
  DailyReport,
  HelpResponse,
  QueryItemList,
  QueryMode,
  TimePreset,
} from "./types/api";

type ViewMode = "items" | "daily" | "archive" | "sources";

const viewMode = ref<ViewMode>("items");
const itemMode = ref<QueryMode>("selected");
const category = ref<CategoryValue | "">("");
const timePreset = ref<TimePreset>("24h");
const keyword = ref("");
const dailyDate = ref("");

const items = ref<QueryItemList | null>(null);
const daily = ref<DailyReport | null>(null);
const archives = ref<DailyArchiveItem[]>([]);
const help = ref<HelpResponse | null>(null);
const warnings = ref<string[]>([]);
const error = ref<ApiError | null>(null);
const traceId = ref("");
const loading = ref(false);

const categoryOptions = computed(() => help.value?.categories ?? [
  { label: "模型", value: "ai-models" as const },
  { label: "产品", value: "ai-products" as const },
  { label: "行业", value: "industry" as const },
  { label: "论文", value: "paper" as const },
  { label: "技巧", value: "tip" as const },
]);

const empty = computed(() => {
  if (viewMode.value === "items") {
    return !loading.value && !error.value && !!items.value && items.value.items.length === 0;
  }
  if (viewMode.value === "archive") {
    return !loading.value && !error.value && archives.value.length === 0;
  }
  return false;
});

const pageTitle = computed(() => (viewMode.value === "sources" ? "数据源控制台" : "热点查询工作台"));
const pageSubtitle = computed(() =>
  viewMode.value === "sources" ? "M2 Collection Sources" : "AI HOT Seed Source",
);

async function loadHelp() {
  const response = await fetchHelp();
  if (response.data) {
    help.value = response.data;
  }
}

async function loadItems() {
  const trimmed = keyword.value.trim();
  if (trimmed.length === 1) {
    error.value = {
      code: "BAD_REQUEST",
      message: "关键词至少 2 个字符。",
      details: {},
      retryable: false,
    };
    return;
  }
  loading.value = true;
  error.value = null;
  viewMode.value = "items";
  const response = await fetchItems({
    mode: itemMode.value,
    category: category.value || undefined,
    q: trimmed || undefined,
    timePreset: timePreset.value,
    take: 50,
  });
  loading.value = false;
  traceId.value = response.meta.traceId;
  warnings.value = response.meta.warnings;
  error.value = response.error;
  items.value = response.data;
}

async function loadDaily(date?: string) {
  loading.value = true;
  error.value = null;
  viewMode.value = "daily";
  const selectedDate = date ?? (dailyDate.value.trim() || undefined);
  const response = await fetchDaily(selectedDate);
  loading.value = false;
  traceId.value = response.meta.traceId;
  warnings.value = response.meta.warnings;
  error.value = response.error;
  daily.value = response.data;
  if (selectedDate) {
    dailyDate.value = selectedDate;
  }
}

async function loadArchives() {
  loading.value = true;
  error.value = null;
  viewMode.value = "archive";
  const response = await fetchDailies(30);
  loading.value = false;
  traceId.value = response.meta.traceId;
  warnings.value = response.meta.warnings;
  error.value = response.error;
  archives.value = response.data ?? [];
}

function retry() {
  if (viewMode.value === "daily") {
    void loadDaily();
  } else if (viewMode.value === "archive") {
    void loadArchives();
  } else {
    void loadItems();
  }
}

onMounted(() => {
  void loadHelp();
  void loadItems();
});
</script>

<template>
  <main class="app-shell antialiased">
    <section class="toolbar" :class="{ 'toolbar-single': viewMode === 'sources' }">
      <div class="brand-block">
        <h1>{{ pageTitle }}</h1>
        <span>{{ pageSubtitle }}</span>
      </div>

      <form v-if="viewMode !== 'sources'" class="search-form" @submit.prevent="loadItems">
        <input v-model="keyword" type="search" placeholder="搜索关键词" aria-label="搜索关键词" />
        <button type="submit" class="primary-button">查询</button>
      </form>
    </section>

    <section class="control-panel">
      <div class="tabs" role="tablist" aria-label="查询模式">
        <button
          type="button"
          :class="{ active: viewMode === 'items' && itemMode === 'selected' }"
          @click="itemMode = 'selected'; loadItems()"
        >
          精选
        </button>
        <button
          type="button"
          :class="{ active: viewMode === 'items' && itemMode === 'all' }"
          @click="itemMode = 'all'; loadItems()"
        >
          全部动态
        </button>
        <button type="button" :class="{ active: viewMode === 'daily' }" @click="loadDaily()">
          AI 日报
        </button>
        <button type="button" :class="{ active: viewMode === 'archive' }" @click="loadArchives">
          日报归档
        </button>
        <button type="button" :class="{ active: viewMode === 'sources' }" @click="viewMode = 'sources'">
          数据源
        </button>
      </div>

      <div v-if="viewMode === 'items'" class="filters">
        <select v-model="category" aria-label="分类" @change="loadItems">
          <option value="">全部分类</option>
          <option v-for="option in categoryOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
        <select v-model="timePreset" aria-label="时间窗" @change="loadItems">
          <option value="today">今天</option>
          <option value="yesterday">昨天</option>
          <option value="24h">过去 24 小时</option>
          <option value="3d">最近 3 天</option>
          <option value="7d">最近 7 天</option>
        </select>
      </div>

      <div v-if="viewMode === 'daily'" class="filters">
        <input v-model="dailyDate" type="date" aria-label="日报日期" />
        <button type="button" class="secondary-button" @click="loadDaily()">查看日报</button>
      </div>
    </section>

    <template v-if="viewMode !== 'sources'">
      <WarningBanner :warnings="warnings" />
      <ApiStateView :loading="loading" :empty="empty" :error="error" :trace-id="traceId" @retry="retry" />
    </template>

    <section v-if="viewMode === 'items' && items && !error" class="results-grid">
      <ItemResultCard v-for="item in items.items" :key="item.id" :item="item" />
    </section>

    <DailyReportView v-if="viewMode === 'daily' && !error" :report="daily" />
    <DailyArchiveList
      v-if="viewMode === 'archive' && !error"
      :archives="archives"
      @select="loadDaily"
    />
    <SourceConsolePage v-if="viewMode === 'sources'" />
  </main>
</template>
