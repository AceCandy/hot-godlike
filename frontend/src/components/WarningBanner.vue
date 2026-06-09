<script setup lang="ts">
defineProps<{
  warnings: string[];
}>();
</script>

<template>
  <div v-if="warnings.length" class="warning-banner">
    <span v-for="warning in warnings" :key="warning">{{ warning }}</span>
  </div>
</template>
