import { ref } from 'vue'

export type ThemeName = 'dark' | 'light'

const storageKey = 'ui-theme'
const defaultTheme: ThemeName = 'dark'

export const currentTheme = ref<ThemeName>(readTheme())

function readTheme(): ThemeName {
  const saved = localStorage.getItem(storageKey)
  return saved === 'light' || saved === 'dark' ? saved : defaultTheme
}

function applyTheme(theme: ThemeName) {
  document.documentElement.dataset.theme = theme
}

export function setTheme(theme: ThemeName) {
  currentTheme.value = theme
  localStorage.setItem(storageKey, theme)
  applyTheme(theme)
}

export function toggleTheme() {
  setTheme(currentTheme.value === 'light' ? 'dark' : 'light')
}

export function initializeTheme() {
  applyTheme(currentTheme.value)
}
