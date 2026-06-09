<script setup lang="ts">
import type { ApiError } from "../types/api";

defineProps<{
  loading: boolean;
  empty: boolean;
  error: ApiError | null;
  traceId?: string;
}>();

defineEmits<{
  retry: [];
}>();
</script>

<template>
  <div v-if="loading" class="state-panel">正在加载...</div>
  <div v-else-if="error" class="state-panel state-panel-error">
    <div>{{ error.message }}</div>
    <div v-if="traceId" class="trace-id">Trace: {{ traceId }}</div>
    <button v-if="error.retryable" class="secondary-button" type="button" @click="$emit('retry')">
      重试
    </button>
  </div>
  <div v-else-if="empty" class="state-panel">
    当前没有匹配内容，试试调整关键词、分类或时间窗。
  </div>
</template>
