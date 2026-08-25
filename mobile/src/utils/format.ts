const roleLabels: Record<string, string> = {
  admin: 'Адміністратор',
  teacher: 'Викладач',
  student: 'Учень',
  parent: 'Батьки',
}

const statusLabels: Record<string, string> = {
  scheduled: 'Заплановано',
  completed: 'Завершено',
  cancelled: 'Скасовано',
  pending: 'Очікує',
  issued: 'Нараховано',
  paid: 'Сплачено',
  approved: 'Підтверджено',
}

export function roleLabel(role?: string) {
  return roleLabels[role ?? ''] ?? role ?? ''
}

export function statusLabel(status?: string) {
  return statusLabels[status ?? ''] ?? status ?? 'Невідомо'
}

export function formatDateTime(value?: string) {
  if (!value) return 'Дата не вказана'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('uk-UA', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function formatMoney(value?: string | number) {
  const amount = Number(value ?? 0)
  return new Intl.NumberFormat('uk-UA', { style: 'currency', currency: 'UAH', maximumFractionDigits: 2 }).format(
    Number.isFinite(amount) ? amount : 0,
  )
}
