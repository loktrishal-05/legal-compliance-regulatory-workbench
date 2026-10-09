// Legal API client: every agent A/B/C endpoint under /v1/workspaces/{id} (shapes: docs/parallel/EVIDENCE_A|B|C.md).
// The server authorizes everything; nothing here decides permission, approval or legal state.
import { API_BASE_URL, apiRequest, withParam } from '../../../services/api.js'

const enc = encodeURIComponent

export function query(path, params = {}) {
  const entries = Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')
  return entries.length ? `${path}?${entries.map(([key, value]) => `${enc(key)}=${enc(value)}`).join('&')}` : path
}

export function legalPaths(workspaceId) {
  const ws = `/v1/workspaces/${enc(workspaceId)}`
  const doc = (d, v) => `${ws}/documents/${enc(d)}/versions/${enc(v)}`
  return {
    workspace: ws,
    // agent A — documents, jobs, sources, search, reviews, workflow, audit
    documents: params => query(`${ws}/documents`, params),
    upload: params => query(`${ws}/documents`, params),
    document: d => `${ws}/documents/${enc(d)}`,
    versions: d => `${ws}/documents/${enc(d)}/versions`,
    jobs: (d, v) => `${doc(d, v)}/jobs`,
    job: id => `${ws}/jobs/${enc(id)}`,
    extract: (d, v, ocr = false) => query(`${doc(d, v)}/extractions`, { ocr: ocr ? 'true' : undefined }),
    spans: (d, v, params) => query(`${doc(d, v)}/spans`, params),
    span: (d, v, s) => `${doc(d, v)}/spans/${enc(s)}`,
    original: (d, v) => `${doc(d, v)}/original`,
    projection: (d, v) => `${doc(d, v)}/projection`,
    proposeCorrection: (d, v, s) => `${doc(d, v)}/spans/${enc(s)}/corrections`,
    correction: (d, v, c) => `${doc(d, v)}/corrections/${enc(c)}`,
    decideCorrection: (d, v, c) => `${doc(d, v)}/corrections/${enc(c)}/decisions`,
    regionTranscription: (d, v) => `${doc(d, v)}/region-transcriptions`,
    search: (q, limit = 20) => query(`${ws}/search`, { q, limit }),
    reviews: params => query(`${ws}/reviews`, params),
    review: id => `${ws}/reviews/${enc(id)}`,
    decide: id => `${ws}/reviews/${enc(id)}/decisions`,
    obligations: params => query(`${ws}/obligations`, params),
    tasks: params => query(`${ws}/tasks`, params),
    notifications: params => query(`${ws}/notifications`, params),
    audit: params => query(`${ws}/audit`, params),
    snapshot: asOf => query(`${ws}/audit/snapshot`, { as_of: asOf }),
    evidencePacks: `${ws}/evidence-packs`,
    exportItem: id => `${ws}/exports/${enc(id)}`,
    // agent B — contracts, summaries, assistant
    contracts: `${ws}/contracts`,
    contractVersions: c => `${ws}/contracts/${enc(c)}/versions`,
    analysis: (c, cv) => `${ws}/contracts/${enc(c)}/versions/${enc(cv)}/analysis`,
    redline: (c, from, to) => query(`${ws}/contracts/${enc(c)}/redline`, { from, to }),
    obligationProposals: analysisId => query(`${ws}/obligation-proposals`, { analysis_id: analysisId }),
    submitObligation: id => `${ws}/obligation-proposals/${enc(id)}/review`,
    submitFinding: id => `${ws}/contract-findings/${enc(id)}/review`,
    summaries: `${ws}/summaries`,
    assistant: `${ws}/assistant/questions`,
    conversations: `${ws}/conversations`,
    // agent C — regulatory and compliance (envelope lists: items/has_more/next_offset)
    regulatory: resource => `${ws}/regulatory/${enc(resource)}`,
    compliance: resource => `${ws}/compliance/${enc(resource)}`,
    assessmentCurrent: id => `${ws}/compliance/assessments/${enc(id)}/current`,
  }
}

// Agent A lists return {items, has_more, limit, offset}: next page = offset + limit.
export const nextOffsetPage = ({ data, path }) => {
  if (!data?.has_more) return null
  const url = new URL(path, 'http://workbench.local')
  const limit = +(data.limit ?? url.searchParams.get('limit') ?? 50)
  return withParam(path, 'offset', (+(data.offset ?? url.searchParams.get('offset') ?? 0)) + limit)
}

export const newIdempotencyKey = () => globalThis.crypto?.randomUUID?.() ?? `k-${Date.now()}-${Math.random().toString(16).slice(2)}`

// Uniform-deny contract: unknown and forbidden objects look identical on purpose.
export function problemKind(error) {
  if (!error) return null
  const code = error.data?.detail?.code
  if (error.status === 404 && code === 'legal_resource_unavailable') return 'denied'
  if (error.status === 403 && code === 'terms_acceptance_required') return 'terms'
  if (error.status === 401) return 'session'
  if (error.status === 409) return 'conflict'
  if (error.status === 422) return 'invalid'
  if (error.status === 429) return 'busy'
  if (!error.status || error.status >= 500) return 'degraded'
  return 'error'
}

export const conflictCode = error => (typeof error?.data?.detail?.code === 'string' ? error.data.detail.code : null)

export const REVIEW_DECISIONS = ['approve', 'reject', 'request_changes', 'escalate']
export const REVIEW_STATUS = { pending: 'Pending', escalated: 'Escalated', approved: 'Approved', rejected: 'Rejected',
  changes_requested: 'Changes requested' }

// UI convenience only: the server rejects self-review regardless.
export const canDecide = (review, userId) => Boolean(review && userId && review.requester_id !== userId
  && ['pending', 'escalated'].includes(review.status))

export function citationHref(citation) {
  if (!citation?.document_id || !citation?.version_id) return null
  return query('/app/legal/source', { document: citation.document_id, version: citation.version_id, span: citation.span_id })
}

export function locatorLabel(locator) {
  if (!locator) return 'No locator'
  if (locator.kind === 'line') return `Line ${locator.line}`
  if (locator.kind === 'paragraph') return `Paragraph ${locator.paragraph}`
  if (locator.kind === 'page_region') return `Page ${locator.page}${locator.extraction_method === 'ocr' ? ' (OCR)' : ''}`
  return locator.kind
}

export const shortHash = value => (value ? `${value.slice(0, 12)}…` : '—')

export const JOB_TERMINAL = ['succeeded', 'failed', 'dead_letter']

export const legal = {
  get: (path, signal) => apiRequest(path, { signal }),
  post: (path, body = {}, signal) => apiRequest(path, { method: 'POST', body, signal }),
  patch: (path, body, signal) => apiRequest(path, { method: 'PATCH', body, signal }),
  remove: (path, signal) => apiRequest(path, { method: 'DELETE', signal }),
}

// Raw-body upload (the file IS the request body); bytes decide the format server-side.
export async function uploadDocument(workspaceId, file, { documentType, classification, matterId }, fetcher = fetch) {
  const path = legalPaths(workspaceId).upload({ filename: file.name, document_type: documentType, classification,
    matter_id: matterId })
  const response = await fetcher(`${API_BASE_URL}${path}`, { method: 'POST', body: file, credentials: 'include',
    cache: 'no-store', headers: { Accept: 'application/json', 'Content-Type': 'application/octet-stream' } })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const error = new Error(data?.detail?.code ? `Upload refused: ${data.detail.code}` : `Upload failed (${response.status})`)
    error.status = response.status
    error.data = data
    throw error
  }
  return data
}
