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
          <td v-for="c in columns" :key="c.key" :class="[c.className, c.cellClass?.(r)]">
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
  columns: Array<{ key: string; label: string; render?: (row: T) => string; className?: string; cellClass?: (row: T) => string }>
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
.status-scheduled span,
.status-completed span {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 650;
}
.status-scheduled span {
  color: #9a3412;
  background: #ffedd5;
  border: 1px solid #fed7aa;
}
.status-completed span {
  color: #166534;
  background: #dcfce7;
  border: 1px solid #bbf7d0;
}
</style>
