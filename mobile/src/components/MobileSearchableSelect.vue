<template>
  <div ref="root" class="mobile-field mobile-searchable-select" @keydown.escape.stop="close">
    <span>{{ label }}</span>
    <button
      class="mobile-control mobile-searchable-select__trigger"
      type="button"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="toggle"
    >
      <span>{{ selectedLabel }}</span>
      <span class="mobile-searchable-select__chevron" aria-hidden="true" />
    </button>

    <div v-if="open" class="mobile-searchable-select__menu">
      <input
        v-model="query"
        class="mobile-control mobile-searchable-select__search"
        type="search"
        placeholder="Пошук..."
        autocomplete="off"
        :aria-label="`Пошук: ${label}`"
      />
      <div class="mobile-searchable-select__options" role="listbox" :aria-label="label">
        <button
          v-for="option in filteredOptions"
          :key="option.value"
          class="mobile-searchable-select__option"
          type="button"
          role="option"
          :aria-selected="option.value === modelValue"
          @click="select(option.value)"
        >
          {{ option.label }}
        </button>
        <div v-if="filteredOptions.length === 0" class="mobile-searchable-select__empty">
          Нічого не знайдено
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { UserFilterOption } from '@/utils/userFilterOptions'

const props = defineProps<{
  label: string
  modelValue: string
  options: UserFilterOption[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  change: []
}>()

const root = ref<HTMLElement | null>(null)
const open = ref(false)
const query = ref('')

const selectedLabel = computed(() => (
  props.options.find((option) => option.value === props.modelValue)?.label
  || props.options[0]?.label
  || 'Оберіть значення'
))

const filteredOptions = computed(() => {
  const normalizedQuery = query.value.trim().toLocaleLowerCase('uk-UA')
  if (!normalizedQuery) return props.options
  return props.options.filter((option) => option.label.toLocaleLowerCase('uk-UA').includes(normalizedQuery))
})

function close() {
  open.value = false
  query.value = ''
}

function toggle() {
  open.value = !open.value
  query.value = ''
}

function select(value: string) {
  emit('update:modelValue', value)
  emit('change')
  close()
}

function onDocumentPointerDown(event: PointerEvent) {
  if (root.value && !root.value.contains(event.target as Node)) close()
}

onMounted(() => document.addEventListener('pointerdown', onDocumentPointerDown))
onBeforeUnmount(() => document.removeEventListener('pointerdown', onDocumentPointerDown))
</script>

<style scoped>
.mobile-searchable-select {
  position: relative;
  min-width: 0;
}

.mobile-searchable-select__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  text-align: left;
}

.mobile-searchable-select__trigger > span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-searchable-select__chevron {
  flex: 0 0 auto;
  width: 8px;
  height: 8px;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: translateY(-2px) rotate(45deg);
}

.mobile-searchable-select__menu {
  position: absolute;
  z-index: 50;
  top: calc(100% + 4px);
  right: 0;
  left: 0;
  min-width: 220px;
  padding: 6px;
  border: 1px solid var(--app-border);
  border-radius: 7px;
  background: #fff;
  box-shadow: 0 12px 28px rgba(24, 46, 40, 0.18);
}

.mobile-searchable-select__search {
  width: 100%;
  margin-bottom: 6px;
}

.mobile-searchable-select__options {
  max-height: 240px;
  overflow-y: auto;
}

.mobile-searchable-select__option {
  width: 100%;
  padding: 11px 10px;
  border: 0;
  border-radius: 5px;
  color: var(--app-ink);
  background: transparent;
  font: inherit;
  text-align: left;
}

.mobile-searchable-select__option:active,
.mobile-searchable-select__option[aria-selected='true'] {
  background: var(--app-soft);
}

.mobile-searchable-select__empty {
  padding: 12px 10px;
  color: var(--app-muted);
  font-size: 12px;
}
</style>
