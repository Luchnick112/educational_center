<template>
  <div class="table">
    <table>
      <thead>
        <tr>
          <th v-for="c in columns" :key="c.key" :class="c.className">{{ c.label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="rows.length === 0">
          <td class="muted" :colspan="columns.length">Немає даних</td>
        </tr>
        <tr
          v-for="(r, idx) in rows"
          :key="rowKey ? rowKey(r, idx) : idx"
          :class="{ clickable: !!onRowClick }"
          @click="onRowClick?.(r)"
        >
          <td v-for="c in columns" :key="c.key" :class="c.className">
            <span v-if="c.render">{{ c.render(r) }}</span>
            <span v-else>{{ (r as any)[c.key] }}</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts" generic="T extends Record<string, any>">
defineProps<{
  columns: Array<{ key: string; label: string; render?: (row: T) => string; className?: string }>
  rows: T[]
  rowKey?: (row: T, index: number) => string | number
  onRowClick?: (row: T) => void
}>()
</script>

<style scoped>
.clickable {
  cursor: pointer;
}
.clickable:hover td {
  background: var(--accent-hover);
}
</style>
