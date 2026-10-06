import { TERMS_V1 } from './termsV1.js'

export const TERMS_DOCUMENT = '/resources/sovereign-workbench-terms-v1.0.docx'
// Backend contract: docs/terms_acceptance.md (GET/POST /auth/terms/*).
export const TERMS_CURRENT = '/auth/terms/current'
export const TERMS_ACCEPT = '/auth/terms/accept'

// Acceptance state only ever comes from the server; nothing is remembered in the browser.
export function termsStatus(data) {
  if (!data || typeof data !== 'object' || typeof data.version !== 'string' || !data.version) return null
  if (typeof data.requires_acceptance !== 'boolean') return null
  const acknowledgements = Array.isArray(data.acknowledgements)
    ? data.acknowledgements.filter(a => typeof a?.id === 'string' && typeof a?.text === 'string') : []
  return { version: data.version, accepted: data.requires_acceptance === false, acknowledgements }
}

// Every acknowledgement the server listed, each literally true; no other fields (the backend rejects extras).
export const acceptBody = (version, acknowledgements) =>
  ({ version, acknowledgements: Object.fromEntries(acknowledgements.map(a => [a.id, true])) })

// 'unsupported' is a backend without the terms service (404): it cannot record consent and does not gate
// its APIs, so the Workbench does not pretend to. Any other failure keeps the Workbench locked.
export function gateDecision(request) {
  if (request.error) return request.error.status === 404 ? 'unsupported' : 'error'
  if (!request.data) return 'loading'
  const status = termsStatus(request.data)
  if (!status) return 'error'
  if (status.accepted) return 'allow'
  if (status.version !== TERMS_V1.version) return 'version-mismatch' // never accept text that was not shown
  return status.acknowledgements.length ? 'accept' : 'error'
}

export const isVersionChanged = error => error?.status === 409 && error?.data?.detail?.code === 'terms_version_changed'
