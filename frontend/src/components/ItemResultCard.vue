<script setup lang="ts">
import type { QueryItem } from "../types/api";

defineProps<{
  item: QueryItem;
}>();

const categoryLabels: Record<string, string> = {
  "ai-models": "模型",
  "ai-products": "产品",
  industry: "行业",
  paper: "论文",
  tip: "技巧",
};
</script>

<template>
  <article class="item-card">
    <div class="item-card-header">
      <a :href="item.url" target="_blank" rel="noreferrer" class="item-title">
        {{ item.title }}
      </a>
      <span v-if="item.category" class="category-pill">
        {{ categoryLabels[item.category] ?? item.category }}
      </span>
    </div>
    <p class="item-summary">
      {{ item.summary || "该条暂无摘要" }}
    </p>
    <div class="item-meta">
      <span>{{ item.source }}</span>
      <span>{{ item.publishedAt || "发布时间未知" }}</span>
      <a :href="item.url" target="_blank" rel="noreferrer">原文</a>
    </div>
  </article>
</template>
