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
          <td v-for="c in columns" :key="c.key" :class="[c.className, c.cellClass?.(r)]" :data-label="c.label">
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

@media (max-width: 640px) {
  .table {
    overflow: visible;
    border: 0;
    border-radius: 0;
  }

  table,
  tbody,
  tr,
  td {
    display: block;
    width: 100%;
    min-width: 0;
  }

  table {
    border-collapse: separate;
  }

  thead {
    display: none;
  }

  tbody {
    display: grid;
    gap: 8px;
  }

  tr {
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--surface-soft);
    overflow: hidden;
  }

  tr.clickable:hover td {
    background: transparent;
  }

  tr.clickable:active {
    border-color: var(--accent-border);
    background: var(--accent-hover);
  }

  td {
    display: grid;
    grid-template-columns: minmax(92px, 36%) minmax(0, 1fr);
    gap: 10px;
    align-items: start;
    padding: 9px 10px;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
    overflow-wrap: anywhere;
  }

  td:last-child {
    border-bottom: 0;
  }

  td::before {
    content: attr(data-label);
    color: var(--muted);
    font-size: 12px;
    line-height: 1.35;
  }

  td.muted {
    display: block;
  }

  td.muted::before {
    content: none;
  }
}
</style>
