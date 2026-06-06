type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export class ApiError extends Error {
  status: number
  payload: unknown

  constructor(message: string, status: number, payload: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

function getApiBaseUrl() {
  const raw = (import.meta.env.VITE_API_URL as string | undefined) ?? ''
  return raw.replace(/\/+$/, '')
}

export function getAccessToken() {
  return localStorage.getItem('access') || ''
}

export function setTokens(tokens: { access: string; refresh: string }) {
  localStorage.setItem('access', tokens.access)
  localStorage.setItem('refresh', tokens.refresh)
}

export function clearTokens() {
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
}

async function refreshAccessToken(): Promise<string> {
  const refresh = localStorage.getItem('refresh')
  if (!refresh) throw new Error('No refresh token')

  const res = await fetch(`${getApiBaseUrl()}/api/users/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })

  const payload = await res.json().catch(() => ({}))
  if (!res.ok) throw new ApiError('Token refresh failed', res.status, payload)

  const access = (payload as any).access as string | undefined
  if (!access) throw new ApiError('Token refresh response missing access token', res.status, payload)
  localStorage.setItem('access', access)
  return access
}

export async function apiRequest<T>(
  path: string,
  opts?: {
    method?: HttpMethod
    body?: unknown
    auth?: boolean
    signal?: AbortSignal
  },
): Promise<T> {
  const method = opts?.method ?? 'GET'
  const auth = opts?.auth ?? true

  const url = path.startsWith('http') ? path : `${getApiBaseUrl()}${path.startsWith('/') ? '' : '/'}${path}`

  const headers: Record<string, string> = { Accept: 'application/json' }
  let body: BodyInit | undefined = undefined
  if (opts?.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(opts.body)
  }
  if (auth) {
    const access = getAccessToken()
    if (access) headers.Authorization = `Bearer ${access}`
  }

  const doFetch = async () =>
    fetch(url, {
      method,
      headers,
      body,
      signal: opts?.signal,
    })

  let res = await doFetch()

  // If access token expired, attempt one refresh and retry once.
  if (auth && res.status === 401 && localStorage.getItem('refresh')) {
    try {
      const newAccess = await refreshAccessToken()
      headers.Authorization = `Bearer ${newAccess}`
      res = await doFetch()
    } catch {
      // fall through and surface original 401 (or refresh failure)
    }
  }

  const payload = await res.json().catch(() => null)
  if (!res.ok) {
    throw new ApiError(`Request failed: ${method} ${path}`, res.status, payload)
  }
  return payload as T
}

