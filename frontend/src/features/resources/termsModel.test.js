import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { DOCX_SHA256, TERMS_V1 } from './termsV1.js'
import { acceptBody, gateDecision, isVersionChanged, termsStatus } from './termsModel.js'

// Shape of GET /auth/terms/current (docs/terms_acceptance.md).
const ACKS = [{ id: 'advisory_only', text: 'I understand AI outputs are advisory only and must be independently verified.' },
  { id: 'no_equipment_control', text: 'I understand the AI cannot control plant equipment.' },
  { id: 'no_bypass', text: 'I will not attempt to bypass safety, access or audit controls.' },
  { id: 'audit_logging', text: 'I understand my application activity is recorded in the tamper-evident audit log.' }]
const current = (overrides = {}) => ({ version: '1.0', requires_acceptance: true, accepted_at: null, acknowledgements: ACKS, ...overrides })

test('in-app terms are generated from the exact downloadable v1.0 document', () => {
  const docx = readFileSync(new URL('../../../public/resources/sovereign-workbench-terms-v1.0.docx', import.meta.url))
  assert.equal(createHash('sha256').update(docx).digest('hex'), DOCX_SHA256)
  assert.equal(TERMS_V1.version, '1.0')
  assert.ok(TERMS_V1.sections.some(s => s.heading.startsWith('3. Acceptable Use')))
})

test('terms gate trusts only the server and never offers a skip', () => {
  assert.equal(gateDecision({ data: null, error: null }), 'loading')
  assert.equal(gateDecision({ data: current() }), 'accept')
  assert.equal(gateDecision({ data: current({ requires_acceptance: false, accepted_at: '2026-09-29T10:00:00Z' }) }), 'allow')
  assert.equal(gateDecision({ data: current({ version: '1.1' }) }), 'version-mismatch') // text not bundled: cannot be shown
  assert.equal(gateDecision({ data: current({ acknowledgements: [] }) }), 'error')
  assert.equal(gateDecision({ data: { version: '1.0', accepted: true } }), 'error') // unknown shape is never "accepted"
  assert.equal(gateDecision({ error: { status: 500 } }), 'error')
  assert.equal(gateDecision({ error: { status: 404 } }), 'unsupported')
  assert.equal(termsStatus(current({ requires_acceptance: 'no' })), null)
})

test('acceptance sends exactly the server-listed acknowledgements, all true', () => {
  assert.deepEqual(acceptBody('1.0', ACKS), { version: '1.0', acknowledgements: { advisory_only: true, no_equipment_control: true, no_bypass: true, audit_logging: true } })
  assert.equal(isVersionChanged({ status: 409, data: { detail: { code: 'terms_version_changed', version: '1.1' } } }), true)
  assert.equal(isVersionChanged({ status: 409, data: { detail: 'Conflict' } }), false)
})
