import assert from 'node:assert/strict'
import test from 'node:test'
import { canDecide, citationHref, conflictCode, legalPaths, locatorLabel, nextOffsetPage, problemKind, query,
  uploadDocument } from './legalApi.js'

const WS = '11111111-1111-1111-1111-111111111111'

test('paths are workspace-scoped and encode every segment', () => {
  const p = legalPaths(WS)
  assert.equal(p.documents({ limit: 50, offset: 0 }), `/v1/workspaces/${WS}/documents?limit=50&offset=0`)
  assert.equal(p.spans('d', 'v', { limit: 200 }), `/v1/workspaces/${WS}/documents/d/versions/v/spans?limit=200`)
  assert.equal(p.decide('r/../x'), `/v1/workspaces/${WS}/reviews/r%2F..%2Fx/decisions`)
  assert.equal(p.redline('c', 'a', 'b'), `/v1/workspaces/${WS}/contracts/c/redline?from=a&to=b`)
  assert.equal(p.compliance('evidence-versions'), `/v1/workspaces/${WS}/compliance/evidence-versions`)
  assert.equal(p.extract('d', 'v', true), `/v1/workspaces/${WS}/documents/d/versions/v/extractions?ocr=true`)
})

test('query drops empty values', () => {
  assert.equal(query('/x', { a: '', b: null, c: undefined, d: 0, e: 'y z' }), '/x?d=0&e=y%20z')
})

test('offset paging follows has_more only', () => {
  assert.equal(nextOffsetPage({ data: { has_more: false }, path: '/d?limit=2' }), null)
  assert.equal(nextOffsetPage({ data: { has_more: true, limit: 2, offset: 4 }, path: '/d?limit=2&offset=4' }), '/d?limit=2&offset=6')
})

test('uniform deny, terms, conflicts and outages are classified without inventing state', () => {
  const err = (status, detail) => Object.assign(new Error('x'), { status, data: { detail } })
  assert.equal(problemKind(err(404, { code: 'legal_resource_unavailable' })), 'denied')
  assert.equal(problemKind(err(403, { code: 'terms_acceptance_required' })), 'terms')
  assert.equal(problemKind(err(409, { code: 'review_already_decided' })), 'conflict')
  assert.equal(conflictCode(err(409, { code: 'review_already_decided' })), 'review_already_decided')
  assert.equal(problemKind(err(429, { code: 'workspace_job_quota' })), 'busy')
  assert.equal(problemKind(err(503, null)), 'degraded')
  assert.equal(problemKind(new Error('timeout')), 'degraded')
  assert.equal(problemKind(null), null)
})

test('self-review and decided reviews are not offered in the UI', () => {
  assert.equal(canDecide({ requester_id: 'u1', status: 'pending' }, 'u1'), false)
  assert.equal(canDecide({ requester_id: 'u1', status: 'approved' }, 'u2'), false)
  assert.equal(canDecide({ requester_id: 'u1', status: 'escalated' }, 'u2'), true)
})

test('citations link to the exact stored span and locators are human readable', () => {
  assert.equal(citationHref({ document_id: 'd', version_id: 'v', span_id: 's' }), '/app/legal/source?document=d&version=v&span=s')
  assert.equal(citationHref({ span_id: 's' }), null)
  assert.equal(locatorLabel({ kind: 'page_region', page: 3, extraction_method: 'ocr' }), 'Page 3 (OCR)')
  assert.equal(locatorLabel({ kind: 'line', line: 7 }), 'Line 7')
})

test('upload sends raw bytes with metadata in the query and surfaces refusal codes', async () => {
  const calls = []
  const ok = async (url, init) => { calls.push({ url, init }); return { ok: true, json: async () => ({ document_id: 'd' }) } }
  const file = { name: 'msa.pdf' }
  assert.deepEqual(await uploadDocument(WS, file, { documentType: 'contract', classification: 'internal' }, ok), { document_id: 'd' })
  assert.match(calls[0].url, /documents\?filename=msa\.pdf&document_type=contract&classification=internal$/)
  assert.equal(calls[0].init.body, file)
  const refused = async () => ({ ok: false, status: 422, json: async () => ({ detail: { code: 'unsupported_format' } }) })
  await assert.rejects(uploadDocument(WS, file, { documentType: 'contract', classification: 'internal' }, refused),
    error => error.status === 422 && /unsupported_format/.test(error.message))
})

test('quote digest matches the server sha256 of the exact UTF-8 quote', async () => {
  const { sha256Hex } = await import('./legalApi.js')
  assert.equal(await sha256Hex('abc'), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
  assert.equal((await sha256Hex('Zahlung ü\n')).length, 64)
})
