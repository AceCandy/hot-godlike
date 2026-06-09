<script setup lang="ts">
import type { DailyReport } from "../types/api";

defineProps<{
  report: DailyReport | null;
}>();
</script>

<template>
  <section v-if="report" class="daily-view">
    <div class="daily-header">
      <div>
        <div class="eyebrow">AI HOT 日报</div>
        <h2>{{ report.date }}</h2>
      </div>
    </div>

    <div v-if="report.lead" class="daily-lead">
      <h3>{{ report.lead.title }}</h3>
      <p>{{ report.lead.leadParagraph }}</p>
    </div>

    <section v-for="section in report.sections" :key="section.label ?? 'section'" class="daily-section">
      <h3>{{ section.label }}</h3>
      <article v-for="item in section.items" :key="`${section.label}-${item.title}`" class="daily-item">
        <a v-if="item.sourceUrl" :href="item.sourceUrl" target="_blank" rel="noreferrer">
          {{ item.title }}
        </a>
        <span v-else>{{ item.title }}</span>
        <p>{{ item.summary || "该条暂无摘要" }}</p>
        <div class="item-meta">{{ item.sourceName || "来源未知" }}</div>
      </article>
    </section>
  </section>
</template>
