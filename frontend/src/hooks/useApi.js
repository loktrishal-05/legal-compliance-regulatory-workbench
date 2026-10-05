import { useCallback, useEffect, useRef, useState } from 'react'
import { apiRequest } from '../services/api.js'
import { capabilitiesFrom } from '../features/auth/authModel.js'

export function useRequest() {
  const [state, setState] = useState({ data: null, error: null, loading: false })
  const active = useRef(null)
  useEffect(() => () => active.current?.abort(), [])
  const run = useCallback(async (path, options) => {
    active.current?.abort()
    const controller = new AbortController()
    active.current = controller
    setState({ data: null, error: null, loading: true })
    try {
      const data = await apiRequest(path, { ...options, signal: controller.signal })
      if (!controller.signal.aborted) setState({ data, error: null, loading: false })
      return controller.signal.aborted ? null : data
    } catch (error) {
      if (!controller.signal.aborted) setState({ data: null, error, loading: false })
      return null
    }
  }, [])
  const reset = useCallback(() => {
    active.current?.abort()
    setState({ data: null, error: null, loading: false })
  }, [])
  return { ...state, run, reset }
}

export function useResource(path) {
  const request = useRequest()
  const { run } = request
  const [version, setVersion] = useState(0)
  useEffect(() => { if (path) run(path) }, [path, run, version])
  const refresh = useCallback(() => setVersion(v => v + 1), []) // stable, so it can be an effect dependency or listener
  return { ...request, refresh }
}

// Accumulates pages of a list route. `next` is one of api.nextPage; `more()` appends, `refresh()` restarts at page one.
export function usePaged(path, next) {
  const [state, setState] = useState({ items: [], nextPath: null, loading: false, error: null, loaded: false, asOf: null })
  const active = useRef(null)
  const load = useCallback(async (url, append) => {
    active.current?.abort()
    const controller = new AbortController()
    active.current = controller
    setState(value => ({ ...(append ? value : { items: [], nextPath: null, loaded: false, asOf: null }), loading: true, error: null }))
    try {
      const { data, meta } = await apiRequest(url, { signal: controller.signal, meta: true })
      if (controller.signal.aborted) return
      const items = Array.isArray(data) ? data : data?.items || []
      setState(value => ({ items: append ? [...value.items, ...items] : items, nextPath: next({ data, meta, items, path: url }),
        loading: false, error: null, loaded: true, asOf: data?.as_of || meta.asOf }))
    } catch (error) {
      if (!controller.signal.aborted) setState(value => ({ ...value, loading: false, error }))
    }
  }, [next])
  useEffect(() => { if (path) load(path, false); return () => active.current?.abort() }, [path, load])
  return { ...state, more: () => state.nextPath && load(state.nextPath, true), refresh: () => path && load(path, false) }
}

export function useAuthCapabilities() {
  const request = useResource('/auth/capabilities')
  return { ...capabilitiesFrom(request.data), loading: request.loading }
}
