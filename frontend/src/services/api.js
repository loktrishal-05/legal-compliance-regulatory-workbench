// Same-origin by default (Vite proxy in development, site reverse proxy in production).
export const API_BASE_URL = (import.meta.env?.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')

// Protected APIs answer 403 with this code until the current terms version is accepted (docs/terms_acceptance.md).
export const TERMS_REQUIRED_EVENT = 'workbench-terms-required'

// Array routes carry their pagination in headers (X-Has-More, X-Next-Offset…); `meta: true` returns them.
export function pageMeta(headers) {
  const number = name => { const value = headers.get(name); return value == null || value === '' || !Number.isFinite(+value) ? null : +value }
  return { asOf: headers.get('X-As-Of'), sampleSize: number('X-Sample-Size'), hasMore: headers.get('X-Has-More') === 'true',
    nextOffset: number('X-Next-Offset'), scanLimit: number('X-Scan-Limit') }
}

export function withParam(path, key, value) {
  const url = new URL(path, 'http://workbench.local')
  url.searchParams.set(key, String(value))
  return url.pathname + url.search
}

// Next-page URL for each pagination style the backend uses; null means the last page was reached.
export const nextPage = {
  envelope: ({ data, path }) => data?.has_more && data.next_offset != null ? withParam(path, 'offset', data.next_offset) : null,
  // Knowledge scans may return an empty page that still has more: follow X-Next-Offset, never result length.
  header: ({ meta, path }) => meta?.hasMore && meta.nextOffset != null ? withParam(path, 'offset', meta.nextOffset) : null,
  offset: ({ meta, path }) => {
    if (!meta?.hasMore) return null
    const url = new URL(path, 'http://workbench.local')
    return withParam(path, 'offset', (+url.searchParams.get('offset') || 0) + (+url.searchParams.get('limit') || 100))
  },
  // Audit uses keyset pagination: the cursor is the last returned sequence number.
  auditCursor: ({ meta, items, path }) => meta?.hasMore && items.length ? withParam(path, 'before_sequence', items.at(-1).sequence_number) : null,
}

export async function apiRequest(path, { signal, method = 'GET', body, timeout = 30000, meta = false } = {}) {
  const controller = new AbortController()
  const abort = () => controller.abort()
  signal?.addEventListener('abort', abort, { once: true })
  if (signal?.aborted) controller.abort()
  const timer = setTimeout(abort, timeout)
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method, signal: controller.signal, credentials: 'include', cache: 'no-store',
      headers: { Accept: 'application/json', ...(body ? { 'Content-Type': 'application/json' } : {}) },
      ...(body ? { body: JSON.stringify(body) } : {}),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      const detail = data?.detail
      const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(item => item.msg).join(' ')
        : detail?.code === 'terms_acceptance_required' ? 'Accept the current terms to continue.' : `Request failed (${response.status})`
      const error = new Error(message)
      error.status = response.status
      error.data = data
      if (response.status === 401 && !['/auth/login', '/auth/me'].includes(path)) globalThis.window?.dispatchEvent(new Event('workbench-session-expired'))
      if (response.status === 403 && detail?.code === 'terms_acceptance_required') globalThis.window?.dispatchEvent(new Event(TERMS_REQUIRED_EVENT))
      throw error
    }
    if (data === null) throw new Error('Backend returned an empty or invalid JSON response.')
    return meta ? { data, meta: pageMeta(response.headers) } : data
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('Request cancelled or timed out. Check current backend state before retrying a submission.')
    throw error
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', abort)
  }
}

export async function getBackendHealth(signal) {
  const health = await apiRequest('/health', { signal, timeout: 5000 })
  if (health.status !== 'ok' || health.service !== 'sovereign-agentic-workbench-backend') {
    throw new Error('Unexpected backend health response')
  }
  return health
}
