<template>
  <div class="json">
    <div class="json__header">
      <div class="json__title">{{ title }}</div>
      <button v-if="value" class="btn btn--ghost" type="button" @click="copy">Копіювати</button>
    </div>
    <pre v-if="value" class="json__pre">{{ pretty }}</pre>
    <div v-else class="muted">{{ emptyText }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title: string
  value: unknown | null
  emptyText?: string
}>()

const pretty = computed(() => JSON.stringify(props.value, null, 2))
const emptyText = computed(() => props.emptyText ?? 'Оберіть рядок, щоб побачити деталі')

async function copy() {
  if (!props.value) return
  try {
    await navigator.clipboard.writeText(pretty.value)
  } catch {
    // ignore (clipboard may be blocked in some contexts)
  }
}
</script>

<style scoped>
.json {
  display: grid;
  gap: 10px;
}
.json__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.json__title {
  font-weight: 650;
}
.json__pre {
  margin: 0;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.12);
  overflow: auto;
  max-height: 70vh;
  font-size: 12px;
  line-height: 1.35;
}
</style>
