import test from 'node:test'
import assert from 'node:assert/strict'
import { TERMS_REQUIRED_EVENT, apiRequest, getBackendHealth, nextPage } from './api.js'

test('a terms-gated 403 anywhere returns the user to terms acceptance', async (t) => {
  const events = []
  globalThis.window = new EventTarget()
  t.after(() => { delete globalThis.window })
  window.addEventListener(TERMS_REQUIRED_EVENT, event => events.push(event.type))
  t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({ detail: { code: 'terms_acceptance_required', version: '1.0' } }), { status: 403 }))
  await assert.rejects(apiRequest('/executions'), error => error.status === 403 && error.message === 'Accept the current terms to continue.')
  assert.deepEqual(events, [TERMS_REQUIRED_EVENT])
})

test('pagination follows each backend contract and stops at the last page', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response('[]', { headers: { 'X-Has-More': 'true', 'X-Next-Offset': '100', 'X-Sample-Size': '0' } }))
  const { data, meta } = await apiRequest('/verified-knowledge?limit=50', { meta: true })
  assert.deepEqual(data, [])
  // An empty knowledge page can still have more: the next offset comes from the header, not the item count.
  assert.equal(nextPage.header({ meta, path: '/verified-knowledge?limit=50' }), '/verified-knowledge?limit=50&offset=100')
  assert.equal(nextPage.envelope({ data: { has_more: true, next_offset: 50 }, path: '/executions?limit=50' }), '/executions?limit=50&offset=50')
  assert.equal(nextPage.envelope({ data: { has_more: false, next_offset: null }, path: '/executions' }), null)
  assert.equal(nextPage.offset({ meta: { hasMore: true }, path: '/knowledge-gaps?limit=100&offset=100' }), '/knowledge-gaps?limit=100&offset=200')
  assert.equal(nextPage.auditCursor({ meta: { hasMore: true }, items: [{ sequence_number: 90 }, { sequence_number: 41 }], path: '/audit/log?limit=100' }), '/audit/log?limit=100&before_sequence=41')
  assert.equal(nextPage.auditCursor({ meta: { hasMore: false }, items: [{ sequence_number: 1 }], path: '/audit/log' }), null)
})

test('requests use server cookies and preserve exact revision binding', async (t) => {
  let seen
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    seen = { url, ...options }
    return new Response(JSON.stringify({ decision: 'APPROVE' }))
  })
  const body = { decision: 'approve', expected_revision_id: 'exact-revision' }
  await apiRequest('/approvals/exact-revision/decision', { method: 'POST', body })
  assert.equal(seen.credentials, 'include')
  assert.equal(seen.cache, 'no-store')
  assert.deepEqual(JSON.parse(seen.body), body)
  assert.equal(seen.headers.Authorization, undefined)
})

test('backend authorization errors and readiness details survive', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({ detail: 'Self-approval is prohibited' }), { status: 403 }))
  await assert.rejects(apiRequest('/approvals/revision/decision'), error => error.status === 403 && error.message.includes('Self-approval'))
})

test('non-JSON errors do not crash parsing or produce fake success', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response('unavailable', { status: 503 }))
  await assert.rejects(apiRequest('/ready'), error => error.status === 503)
})

test('auth validation shows safe field messages without serializing the response', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({ detail: [{ msg: 'Enter a valid email address', loc: ['body', 'email'], type: 'value_error' }] }), { status: 422 }))
  await assert.rejects(apiRequest('/auth/signup'), error => error.message === 'Enter a valid email address' && error.status === 422)
})

test('empty successful response is rejected', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response(''))
  await assert.rejects(apiRequest('/query'), /empty or invalid JSON/)
})

test('health validates the actual service contract', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({ status: 'ok', service: 'other' })))
  await assert.rejects(getBackendHealth(), /Unexpected backend/)
})

test('health accepts the legal backend and refuses legacy or non-ready identities', async (t) => {
  const legal = { status: 'ok', service: 'legal-compliance-regulatory-workbench-backend' }
  t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify(legal)))
  assert.deepEqual(await getBackendHealth(), legal)
  for (const value of [{ ...legal, service: 'sovereign-agentic-workbench-backend' }, { ...legal, status: 'failed' }]) {
    t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify(value)))
    await assert.rejects(getBackendHealth(), /Unexpected backend/)
  }
})

test('timeouts surface uncertainty and do not retry submissions', async (t) => {
  let calls = 0
  t.mock.method(globalThis, 'fetch', (_url, { signal }) => new Promise((_resolve, reject) => {
    calls += 1
    signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
  }))
  await assert.rejects(apiRequest('/query', { method: 'POST', body: { query: 'question' }, timeout: 5 }), /Check current backend state/)
  assert.equal(calls, 1)
})
