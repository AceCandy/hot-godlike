<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import ApiStateView from "./ApiStateView.vue";
import {
  createSource,
  disableSource,
  enableSource,
  fetchRawItems,
  fetchRuns as fetchFetchRuns,
  fetchSourceHealth,
  fetchSources,
  previewSource,
  triggerSourceFetch,
  updateSource,
} from "../lib/api";
import {
  buildSourceNameLookup,
  healthBySourceId,
  prependFetchRun,
  resolveSourceName,
  upsertSourceConfig,
} from "../lib/collectionViews";
import {
  createEmptySourceForm,
  sourceFormFromConfig,
  sourceFormTargetKind,
  switchSourceFormType,
  toSourceInput,
  type SourceFormState,
} from "../lib/sourceForm";
import {
  countSourceFilters,
  emptySourceFilters,
  filterSources,
  type SourceEnabledFilter,
  type SourceFilterState,
} from "../lib/sourceFilters";
import type {
  ApiError,
  FetchRun,
  FetchRunStatus,
  RawItem,
  SourceConfig,
  SourceHealth,
  SourcePreview,
  SourceStatus,
  SourceType,
  TrustLevel,
} from "../types/api";

const sources = ref<SourceConfig[]>([]);
const recentRuns = ref<FetchRun[]>([]);
const rawItems = ref<RawItem[]>([]);
const healthItems = ref<SourceHealth[]>([]);
const filters = ref<SourceFilterState>({ ...emptySourceFilters });
const sourceForm = ref<SourceFormState>(createEmptySourceForm());
const editingSourceId = ref<string | null>(null);
const previewResult = ref<SourcePreview | null>(null);
const actionError = ref<ApiError | null>(null);
const actionTraceId = ref("");
const actionMessage = ref("");
const loading = ref(false);
const actionLoading = ref(false);
const error = ref<ApiError | null>(null);
const traceId = ref("");

const typeLabels: Record<SourceType, string> = {
  aihot_api: "AI HOT API",
  aihot_rss: "AI HOT RSS",
  rss: "RSS",
  rsshub: "RSSHub",
};

const statusLabels: Record<SourceStatus, string> = {
  enabled: "正常",
  disabled: "停用",
  degraded: "降级",
  circuit_open: "熔断",
};

const trustLabels: Record<TrustLevel, string> = {
  high: "高",
  medium: "中",
  low: "低",
};

const enabledLabels: Record<SourceEnabledFilter, string> = {
  all: "全部启用状态",
  enabled: "已启用",
  disabled: "已停用",
};

const fetchRunLabels: Record<FetchRunStatus, string> = {
  queued: "排队",
  running: "运行中",
  succeeded: "成功",
  partial_failed: "部分失败",
  failed: "失败",
  cancelled: "已取消",
};

const rawItemLabels: Record<RawItem["status"], string> = {
  new: "新增",
  duplicate: "重复",
  ignored: "忽略",
  failed: "失败",
};

const filteredSources = computed(() => filterSources(sources.value, filters.value));
const activeFilterCount = computed(() => countSourceFilters(filters.value));
const empty = computed(() => !loading.value && !error.value && filteredSources.value.length === 0);
const enabledCount = computed(() => sources.value.filter((source) => source.enabled).length);
const issueCount = computed(
  () => sources.value.filter((source) => source.status === "degraded" || source.status === "circuit_open").length,
);
const sourceNames = computed(() => buildSourceNameLookup(sources.value));
const healthLookup = computed(() => healthBySourceId(healthItems.value));
const formTargetKind = computed(() => sourceFormTargetKind(sourceForm.value));
const categoryOptions = computed(() =>
  [...new Set(sources.value.map((source) => source.category).filter(Boolean))].sort(),
);

async function loadSources() {
  loading.value = true;
  error.value = null;
  const [sourceResponse, runResponse, rawItemResponse, healthResponse] = await Promise.all([
    fetchSources({ take: 100 }),
    fetchFetchRuns({ take: 10 }),
    fetchRawItems({ take: 10 }),
    fetchSourceHealth({ take: 20 }),
  ]);
  loading.value = false;
  traceId.value = sourceResponse.meta.traceId;
  error.value = sourceResponse.error ?? runResponse.error ?? rawItemResponse.error ?? healthResponse.error;
  sources.value = sourceResponse.data?.items ?? [];
  recentRuns.value = runResponse.data?.items ?? [];
  rawItems.value = rawItemResponse.data?.items ?? [];
  healthItems.value = healthResponse.data?.items ?? [];
}

function resetFilters() {
  filters.value = { ...emptySourceFilters };
}

function resetSourceForm() {
  sourceForm.value = createEmptySourceForm();
  editingSourceId.value = null;
  previewResult.value = null;
  actionError.value = null;
  actionTraceId.value = "";
  actionMessage.value = "";
}

function changeSourceType(event: Event) {
  const target = event.target as HTMLSelectElement;
  sourceForm.value = switchSourceFormType(sourceForm.value, target.value as SourceType);
}

function startEditSource(source: SourceConfig) {
  sourceForm.value = sourceFormFromConfig(source);
  editingSourceId.value = source.id;
  previewResult.value = null;
  actionError.value = null;
  actionTraceId.value = "";
  actionMessage.value = `正在编辑 ${source.name}`;
}

async function submitSourceForm() {
  actionLoading.value = true;
  actionError.value = null;
  actionMessage.value = "";
  const payload = toSourceInput(sourceForm.value);
  const response = editingSourceId.value
    ? await updateSource(editingSourceId.value, payload)
    : await createSource(payload);
  actionLoading.value = false;
  actionTraceId.value = response.meta.traceId;
  actionError.value = response.error;
  if (response.data) {
    actionMessage.value = editingSourceId.value ? "数据源已更新。" : "数据源已创建。";
    sources.value = upsertSourceConfig(sources.value, response.data);
    sourceForm.value = sourceFormFromConfig(response.data);
    editingSourceId.value = response.data.id;
  }
}

async function previewCurrentForm() {
  actionLoading.value = true;
  actionError.value = null;
  actionMessage.value = "";
  previewResult.value = null;
  const response = await previewSource(toSourceInput(sourceForm.value));
  actionLoading.value = false;
  actionTraceId.value = response.meta.traceId;
  actionError.value = response.error;
  previewResult.value = response.data;
  if (response.data) {
    actionMessage.value = "Preview 已返回样例。";
  }
}

async function previewExistingSource(source: SourceConfig) {
  sourceForm.value = sourceFormFromConfig(source);
  editingSourceId.value = source.id;
  await previewCurrentForm();
}

async function toggleSourceEnabled(source: SourceConfig) {
  actionLoading.value = true;
  actionError.value = null;
  actionMessage.value = "";
  const response = source.enabled ? await disableSource(source.id) : await enableSource(source.id);
  actionLoading.value = false;
  actionTraceId.value = response.meta.traceId;
  actionError.value = response.error;
  if (response.data) {
    actionMessage.value = response.data.enabled ? "数据源已启用。" : "数据源已停用。";
    sources.value = upsertSourceConfig(sources.value, response.data);
  }
}

async function fetchSourceNow(source: SourceConfig) {
  actionLoading.value = true;
  actionError.value = null;
  actionMessage.value = "";
  const response = await triggerSourceFetch(source.id, {
    idempotencyKey: `manual_${source.id}_${Date.now()}`,
    reason: "source console manual fetch",
  });
  actionLoading.value = false;
  actionTraceId.value = response.meta.traceId;
  actionError.value = response.error;
  if (response.data) {
    actionMessage.value = `手动抓取已完成：新增 ${response.data.newCount}，重复 ${response.data.duplicateCount}。`;
    recentRuns.value = prependFetchRun(recentRuns.value, response.data, 10);
  }
}

function formatTime(value: string | null): string {
  if (!value) {
    return "未抓取";
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

function sourceTarget(source: SourceConfig): string {
  return source.route ?? source.url ?? "内置";
}

function runStatusClass(status: FetchRunStatus): string {
  if (status === "succeeded") {
    return "status-enabled";
  }
  if (status === "failed" || status === "partial_failed") {
    return "status-circuit-open";
  }
  if (status === "running") {
    return "status-degraded";
  }
  return "status-disabled";
}

function rawItemStatusClass(status: RawItem["status"]): string {
  if (status === "new") {
    return "status-enabled";
  }
  if (status === "failed") {
    return "status-circuit-open";
  }
  return "status-disabled";
}

function sourceName(sourceId: string): string {
  return resolveSourceName(sourceId, sourceNames.value);
}

onMounted(() => {
  void loadSources();
});
</script>

<template>
  <section class="source-console" aria-label="数据源控制台">
    <header class="source-console-header">
      <div>
        <p class="eyebrow">M2 Collection Sources</p>
        <h2>数据源控制台</h2>
      </div>
      <dl class="source-stats" aria-label="数据源统计">
        <div>
          <dt>总数</dt>
          <dd>{{ sources.length }}</dd>
        </div>
        <div>
          <dt>启用</dt>
          <dd>{{ enabledCount }}</dd>
        </div>
        <div>
          <dt>异常</dt>
          <dd>{{ issueCount }}</dd>
        </div>
      </dl>
    </header>

    <section class="source-filter-bar" aria-label="数据源筛选">
      <label>
        <span>类型</span>
        <select v-model="filters.type" aria-label="数据源类型筛选">
          <option value="">全部类型</option>
          <option value="aihot_api">{{ typeLabels.aihot_api }}</option>
          <option value="aihot_rss">{{ typeLabels.aihot_rss }}</option>
          <option value="rss">RSS</option>
          <option value="rsshub">RSSHub</option>
        </select>
      </label>
      <label>
        <span>状态</span>
        <select v-model="filters.status" aria-label="数据源状态筛选">
          <option value="">全部状态</option>
          <option value="enabled">{{ statusLabels.enabled }}</option>
          <option value="disabled">{{ statusLabels.disabled }}</option>
          <option value="degraded">{{ statusLabels.degraded }}</option>
          <option value="circuit_open">{{ statusLabels.circuit_open }}</option>
        </select>
      </label>
      <label>
        <span>启停</span>
        <select v-model="filters.enabled" aria-label="数据源启停筛选">
          <option value="all">{{ enabledLabels.all }}</option>
          <option value="enabled">{{ enabledLabels.enabled }}</option>
          <option value="disabled">{{ enabledLabels.disabled }}</option>
        </select>
      </label>
      <label>
        <span>分类</span>
        <select v-model="filters.category" aria-label="数据源分类筛选">
          <option value="">全部分类</option>
          <option v-for="category in categoryOptions" :key="category" :value="category">
            {{ category }}
          </option>
        </select>
      </label>
      <button type="button" class="secondary-button" @click="resetFilters">
        清空<span v-if="activeFilterCount"> {{ activeFilterCount }}</span>
      </button>
      <button type="button" class="secondary-button" @click="loadSources">刷新</button>
    </section>

    <ApiStateView :loading="loading" :empty="empty" :error="error" :trace-id="traceId" @retry="loadSources" />

    <section v-if="!loading && !error" class="source-action-panel" aria-label="数据源操作">
      <div class="collection-panel-header">
        <div>
          <p class="eyebrow">Source Config</p>
          <h3>{{ editingSourceId ? "编辑数据源" : "创建数据源" }}</h3>
        </div>
        <button type="button" class="secondary-button" @click="resetSourceForm">新建</button>
      </div>

      <form class="source-form-grid" @submit.prevent="submitSourceForm">
        <label>
          <span>名称</span>
          <input v-model="sourceForm.name" type="text" maxlength="80" required />
        </label>
        <label>
          <span>类型</span>
          <select :value="sourceForm.type" aria-label="数据源表单类型" @change="changeSourceType">
            <option value="aihot_api">{{ typeLabels.aihot_api }}</option>
            <option value="aihot_rss">{{ typeLabels.aihot_rss }}</option>
            <option value="rss">RSS</option>
            <option value="rsshub">RSSHub</option>
          </select>
        </label>
        <label>
          <span>分类</span>
          <input v-model="sourceForm.category" type="text" required />
        </label>
        <label v-if="formTargetKind === 'url'" class="source-form-wide">
          <span>URL</span>
          <input v-model="sourceForm.url" type="url" required />
        </label>
        <label v-if="formTargetKind === 'route'" class="source-form-wide">
          <span>RSSHub route</span>
          <input v-model="sourceForm.route" type="text" required />
        </label>
        <div v-if="formTargetKind === 'builtin'" class="source-form-wide source-form-note">
          AI HOT API 使用后端内置入口。
        </div>
        <label>
          <span>抓取间隔</span>
          <input v-model.number="sourceForm.fetchIntervalMinutes" type="number" min="5" max="1440" required />
        </label>
        <label>
          <span>超时秒数</span>
          <input v-model.number="sourceForm.timeoutSeconds" type="number" min="5" max="60" required />
        </label>
        <label>
          <span>重试次数</span>
          <input v-model.number="sourceForm.retryCount" type="number" min="0" max="3" required />
        </label>
        <label>
          <span>并发</span>
          <input v-model.number="sourceForm.concurrencyLimit" type="number" min="1" max="5" required />
        </label>
        <label>
          <span>可信度</span>
          <select v-model="sourceForm.trustLevel">
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
          </select>
        </label>
        <label class="source-checkbox">
          <input v-model="sourceForm.enabled" type="checkbox" />
          <span>启用</span>
        </label>
        <label class="source-checkbox">
          <input v-model="sourceForm.requiresCookie" type="checkbox" />
          <span>需要 Cookie</span>
        </label>
        <div v-if="sourceForm.requiresCookie" class="source-form-wide source-form-note">
          M2 只保存配置，不执行 cookie 类 source 抓取。
        </div>
        <div class="source-form-actions">
          <button type="button" class="secondary-button" :disabled="actionLoading" @click="previewCurrentForm">
            Preview
          </button>
          <button type="submit" class="primary-button" :disabled="actionLoading">
            {{ editingSourceId ? "保存" : "创建" }}
          </button>
        </div>
      </form>

      <div v-if="actionMessage || actionError" class="action-feedback" :class="{ 'action-feedback-error': actionError }">
        <div>{{ actionError?.message ?? actionMessage }}</div>
        <div v-if="actionTraceId" class="trace-id">Trace: {{ actionTraceId }}</div>
      </div>

      <div v-if="previewResult" class="preview-panel" aria-label="Source preview">
        <div class="collection-panel-header">
          <div>
            <p class="eyebrow">Preview</p>
            <h3>{{ previewResult.source.name }}</h3>
          </div>
          <span class="trace-id">{{ previewResult.sampleItems.length }} 条</span>
        </div>
        <article v-for="item in previewResult.sampleItems" :key="item.url" class="collection-row">
          <a :href="item.url" target="_blank" rel="noreferrer" class="collection-title">
            {{ item.title }}
          </a>
          <div class="collection-subtitle">{{ item.publishedAt || "发布时间未知" }}</div>
          <p class="collection-snippet">{{ item.contentSnippet || "该条暂无摘要" }}</p>
        </article>
      </div>
    </section>

    <section v-if="!loading && !error && filteredSources.length" class="source-list" aria-label="数据源列表">
      <article v-for="source in filteredSources" :key="source.id" class="source-row">
        <div class="source-main">
          <div class="source-title-line">
            <h3>{{ source.name }}</h3>
            <span class="status-badge" :class="`status-${source.status.replace('_', '-')}`">
              {{ statusLabels[source.status] }}
            </span>
            <span class="status-badge" :class="source.enabled ? 'status-enabled' : 'status-disabled'">
              {{ source.enabled ? "启用" : "停用" }}
            </span>
          </div>
          <div class="source-target">{{ sourceTarget(source) }}</div>
          <div class="source-id">{{ source.id }}</div>
          <div v-if="healthLookup[source.id]?.lastErrorMessage" class="source-health-note">
            {{ healthLookup[source.id]?.lastErrorCode }} · {{ healthLookup[source.id]?.lastErrorMessage }}
          </div>
        </div>

        <dl class="source-fields">
          <div>
            <dt>类型</dt>
            <dd>{{ typeLabels[source.type] }}</dd>
          </div>
          <div>
            <dt>分类</dt>
            <dd>{{ source.category }}</dd>
          </div>
          <div>
            <dt>可信度</dt>
            <dd>{{ trustLabels[source.trustLevel] }}</dd>
          </div>
          <div>
            <dt>间隔</dt>
            <dd>{{ source.fetchIntervalMinutes }} 分钟</dd>
          </div>
          <div>
            <dt>上次抓取</dt>
            <dd>{{ formatTime(source.lastFetchedAt) }}</dd>
          </div>
        </dl>
        <div class="source-row-actions">
          <button type="button" class="secondary-button" @click="startEditSource(source)">编辑</button>
          <button type="button" class="secondary-button" @click="previewExistingSource(source)">预览</button>
          <button type="button" class="secondary-button" @click="toggleSourceEnabled(source)">
            {{ source.enabled ? "停用" : "启用" }}
          </button>
          <button type="button" class="secondary-button" @click="fetchSourceNow(source)">抓取</button>
        </div>
      </article>
    </section>

    <section v-if="!loading && !error" class="collection-monitor-grid" aria-label="采集只读监控">
      <section class="collection-panel" aria-label="最近抓取任务">
        <div class="collection-panel-header">
          <div>
            <p class="eyebrow">Fetch Runs</p>
            <h3>最近抓取</h3>
          </div>
          <span class="trace-id">{{ recentRuns.length }} 条</span>
        </div>
        <div v-if="recentRuns.length" class="collection-list">
          <article v-for="run in recentRuns" :key="run.id" class="collection-row">
            <div>
              <div class="collection-title">{{ sourceName(run.sourceId) }}</div>
              <div class="collection-subtitle">{{ run.id }} · {{ run.trigger }}</div>
            </div>
            <span class="status-badge" :class="runStatusClass(run.status)">
              {{ fetchRunLabels[run.status] }}
            </span>
            <dl class="collection-metrics">
              <div>
                <dt>抓取</dt>
                <dd>{{ run.fetchedCount }}</dd>
              </div>
              <div>
                <dt>新增</dt>
                <dd>{{ run.newCount }}</dd>
              </div>
              <div>
                <dt>重复</dt>
                <dd>{{ run.duplicateCount }}</dd>
              </div>
              <div>
                <dt>耗时</dt>
                <dd>{{ run.durationMs === null ? "运行中" : `${run.durationMs}ms` }}</dd>
              </div>
            </dl>
            <div v-if="run.errorMessage" class="collection-error">
              {{ run.errorCode }} · {{ run.errorMessage }}
            </div>
          </article>
        </div>
        <p v-else class="collection-empty">暂无抓取任务。</p>
      </section>

      <section class="collection-panel" aria-label="原始条目">
        <div class="collection-panel-header">
          <div>
            <p class="eyebrow">Raw Items</p>
            <h3>原始条目</h3>
          </div>
          <span class="trace-id">{{ rawItems.length }} 条</span>
        </div>
        <div v-if="rawItems.length" class="collection-list">
          <article v-for="item in rawItems" :key="item.id" class="collection-row">
            <div>
              <a :href="item.url" target="_blank" rel="noreferrer" class="collection-title">
                {{ item.title }}
              </a>
              <div class="collection-subtitle">{{ item.sourceName }} · {{ formatTime(item.fetchedAt) }}</div>
            </div>
            <span class="status-badge" :class="rawItemStatusClass(item.status)">
              {{ rawItemLabels[item.status] }}
            </span>
            <p class="collection-snippet">{{ item.summary || item.contentSnippet || "该条暂无摘要" }}</p>
          </article>
        </div>
        <p v-else class="collection-empty">暂无原始条目。</p>
      </section>

      <section class="collection-panel" aria-label="源健康状态">
        <div class="collection-panel-header">
          <div>
            <p class="eyebrow">Source Health</p>
            <h3>源健康</h3>
          </div>
          <span class="trace-id">{{ healthItems.length }} 条</span>
        </div>
        <div v-if="healthItems.length" class="collection-list">
          <article v-for="health in healthItems" :key="health.sourceId" class="collection-row">
            <div>
              <div class="collection-title">{{ sourceName(health.sourceId) }}</div>
              <div class="collection-subtitle">连续失败 {{ health.consecutiveFailures }} 次</div>
            </div>
            <span class="status-badge" :class="`status-${health.status.replace('_', '-')}`">
              {{ statusLabels[health.status] }}
            </span>
            <dl class="collection-metrics">
              <div>
                <dt>下次抓取</dt>
                <dd>{{ formatTime(health.nextFetchAt) }}</dd>
              </div>
              <div>
                <dt>成功</dt>
                <dd>{{ formatTime(health.lastSucceededAt) }}</dd>
              </div>
              <div>
                <dt>失败</dt>
                <dd>{{ formatTime(health.lastFailedAt) }}</dd>
              </div>
            </dl>
            <div v-if="health.lastErrorMessage" class="collection-error">
              {{ health.lastErrorCode }} · {{ health.lastErrorMessage }}
            </div>
          </article>
        </div>
        <p v-else class="collection-empty">暂无源健康记录。</p>
      </section>
    </section>
  </section>
</template>
