import { tokenStorage, type AuthTokens } from './tokenStorage'

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly payload: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '')
let refreshRequest: Promise<string> | null = null

function apiUrl(path: string) {
  if (/^https?:\/\//.test(path)) return path
  return `${apiBaseUrl}${path.startsWith('/') ? '' : '/'}${path}`
}

async function parsePayload(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) return response.json().catch(() => null)
  return response.text().catch(() => null)
}

async function refreshAccessToken(refresh: string): Promise<string> {
  if (!refreshRequest) {
    refreshRequest = (async () => {
      const response = await fetch(apiUrl('/api/users/token/refresh/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ refresh }),
      })
      const payload = (await parsePayload(response)) as { access?: string } | null
      if (!response.ok || !payload?.access) {
        await tokenStorage.clear()
        throw new ApiError('Сесію завершено. Увійдіть ще раз.', response.status, payload)
      }
      await tokenStorage.set({ access: payload.access, refresh })
      return payload.access
    })().finally(() => {
      refreshRequest = null
    })
  }
  return refreshRequest
}

export async function apiRequest<T>(
  path: string,
  options: {
    method?: HttpMethod
    body?: unknown
    auth?: boolean
    signal?: AbortSignal
  } = {},
): Promise<T> {
  const method = options.method ?? 'GET'
  const auth = options.auth ?? true
  const tokens = auth ? await tokenStorage.get() : null
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (tokens?.access) headers.Authorization = `Bearer ${tokens.access}`
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'

  const send = (authorization = headers.Authorization) => {
    const requestHeaders = { ...headers }
    if (authorization) requestHeaders.Authorization = authorization
    return fetch(apiUrl(path), {
      method,
      headers: requestHeaders,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
    })
  }

  let response = await send()
  if (auth && response.status === 401 && tokens?.refresh) {
    const access = await refreshAccessToken(tokens.refresh)
    response = await send(`Bearer ${access}`)
  }

  const payload = await parsePayload(response)
  if (!response.ok) {
    throw new ApiError(errorMessage(payload, `Помилка запиту (${response.status})`), response.status, payload)
  }
  return payload as T
}

export function errorMessage(payload: unknown, fallback = 'Не вдалося виконати запит') {
  if (payload && typeof payload === 'object') {
    const record = payload as Record<string, unknown>
    if (record.detail) return String(record.detail)
    return Object.entries(record)
      .map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(', ') : String(value)}`)
      .join('; ')
  }
  return typeof payload === 'string' && payload ? payload : fallback
}

export type { AuthTokens }
