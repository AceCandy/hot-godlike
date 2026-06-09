<script setup lang="ts">
import type { DailyArchiveItem } from "../types/api";
import { formatArchiveItemCount } from "../lib/format";

defineProps<{
  archives: DailyArchiveItem[];
}>();

defineEmits<{
  select: [date: string];
}>();
</script>

<template>
  <section class="archive-list">
    <button
      v-for="archive in archives"
      :key="archive.date"
      type="button"
      class="archive-row"
      @click="$emit('select', archive.date)"
    >
      <span>{{ archive.date }}</span>
      <span>{{ archive.weekday || "" }}</span>
      <strong>{{ archive.title || "AI HOT 日报" }}</strong>
      <span>{{ formatArchiveItemCount(archive.itemCount) }}</span>
    </button>
  </section>
</template>
