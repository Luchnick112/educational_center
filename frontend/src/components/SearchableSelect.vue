<template>
  <div ref="root" class="field searchable-select" @keydown.escape.stop="close">
    <span class="field__label">{{ label }}</span>
    <button
      class="input searchable-select__trigger"
      type="button"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="toggle"
    >
      <span>{{ selectedLabel }}</span>
      <span class="searchable-select__chevron" aria-hidden="true" />
    </button>

    <div v-if="open" class="searchable-select__menu">
      <input
        ref="searchInput"
        v-model="query"
        class="input searchable-select__search"
        type="search"
        placeholder="Пошук..."
        autocomplete="off"
        :aria-label="`Пошук: ${label}`"
      />
      <div class="searchable-select__options" role="listbox" :aria-label="label">
        <button
          v-for="(option, index) in filteredOptions"
          :key="`${option.value ?? 'null'}-${index}`"
          class="searchable-select__option"
          type="button"
          role="option"
          :aria-selected="option.value === modelValue"
          @click="select(option.value)"
        >
          {{ option.label }}
        </button>
        <div v-if="filteredOptions.length === 0" class="searchable-select__empty">Нічого не знайдено</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

type SelectValue = string | number | null
type SelectOption = { value: SelectValue; label: string }

const props = defineProps<{
  label: string
  modelValue: SelectValue
  options: SelectOption[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: SelectValue]
  change: []
}>()

const root = ref<HTMLElement | null>(null)
const searchInput = ref<HTMLInputElement | null>(null)
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

async function toggle() {
  open.value = !open.value
  query.value = ''
  if (open.value) {
    await nextTick()
    searchInput.value?.focus()
  }
}

function select(value: SelectValue) {
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
.searchable-select {
  position: relative;
  min-width: 0;
}

.searchable-select__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  text-align: left;
}

.searchable-select__trigger > span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.searchable-select__chevron {
  flex: 0 0 auto;
  width: 8px;
  height: 8px;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: translateY(-2px) rotate(45deg);
}

.searchable-select__menu {
  position: absolute;
  z-index: 30;
  top: calc(100% + 4px);
  right: 0;
  left: 0;
  min-width: 220px;
  padding: 6px;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  background: var(--surface);
  box-shadow: var(--shadow-lg);
}

.searchable-select__search {
  width: 100%;
  margin-bottom: 6px;
}

.searchable-select__options {
  max-height: 220px;
  overflow-y: auto;
}

.searchable-select__option {
  width: 100%;
  padding: 8px;
  border: 0;
  border-radius: 4px;
  color: inherit;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.searchable-select__option:hover,
.searchable-select__option[aria-selected='true'] {
  background: var(--surface-hover);
}

.searchable-select__empty {
  padding: 10px 8px;
  color: var(--muted);
  font-size: 13px;
}
</style>
