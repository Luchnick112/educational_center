import { ref } from 'vue'

export function usePageData() {
  const loading = ref(false)
  const error = ref('')

  async function run(task: () => Promise<void>) {
    loading.value = true
    error.value = ''
    try {
      await task()
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : 'Не вдалося завантажити дані'
    } finally {
      loading.value = false
    }
  }

  return { loading, error, run }
}
