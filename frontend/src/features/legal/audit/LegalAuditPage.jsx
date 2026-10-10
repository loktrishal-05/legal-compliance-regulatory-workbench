import { useState } from 'react'
import { PageHeader } from '../../../components/ui.jsx'
import { useRequest, useResource } from '../../../hooks/useApi.js'
import { legalPaths, shortHash } from '../shared/legalApi.js'
import { LegalProblem, LegalResource, ReviewBadge } from '../shared/LegalShared.jsx'
import { displayTime, readableLabel } from '../shared/viewModel.js'
import { useWorkspace } from '../shared/workspace.js'

const ids = value => value.split(/[\s,]+/).filter(Boolean)

export function LegalAuditPage() {
  const { workspace } = useWorkspace()
  const paths = legalPaths(workspace.workspace_id)
  return <>
    <PageHeader title="Legal audit and exports" description="Hash-chained legal audit events, as-of snapshots that keep recorded time separate from effective time, and integrity-verified evidence packs. Auditor or workspace administrator role required." />
    <Timeline paths={paths} />
    <Snapshot paths={paths} />
    <Exports paths={paths} />
  </>
}

function Timeline({ paths }) {
  const [eventType, setEventType] = useState('')
  const list = useResource(paths.audit({ event_type: eventType, limit: 200 }))
  return <section className="panel"><h2>Audit timeline</h2>
    <div className="toolbar"><label>Event type<select value={eventType} onChange={e => setEventType(e.target.value)}><option value="">All legal events</option>
      {['LEGAL_REVIEW_REQUESTED', 'LEGAL_REVIEW_DECIDED', 'LEGAL_ACTIVITY_RECORDED'].map(t => <option key={t} value={t}>{readableLabel(t.toLowerCase())}</option>)}</select></label>
      <button type="button" onClick={list.refresh}>Refresh</button></div>
    <LegalResource resource={list} empty="No visible audit events" emptyMessage="Events bound to documents you cannot read are hidden." what="the audit log">{data =>
      <div className="table-scroll"><table><thead><tr><th scope="col">#</th><th scope="col">Event</th><th scope="col">When</th><th scope="col">Action</th><th scope="col">Hash</th></tr></thead><tbody>{data.items.map(e => <tr key={e.sequence_number}>
        <td>{e.sequence_number}</td><td>{readableLabel(e.event_type.toLowerCase())}</td><td>{displayTime(e.occurred_at)}</td>
        <td>{readableLabel(e.payload?.action || e.payload?.decision || e.payload?.target_type || [e.payload?.domain, e.payload?.operation].filter(Boolean).join(' ') || '—')}</td><td><code>{shortHash(e.event_hash)}</code></td>
      </tr>)}</tbody></table></div>}</LegalResource>
  </section>
}

function Snapshot({ paths }) {
  const [asOf, setAsOf] = useState(null)
  const result = useResource(asOf && paths.snapshot(asOf))
  return <section className="panel"><h2>As-of snapshot</h2>
    <form className="toolbar" onSubmit={e => { e.preventDefault(); const v = new FormData(e.currentTarget).get('as_of'); if (v) setAsOf(new Date(v).toISOString()) }}>
      <label>Recorded as of<input type="datetime-local" name="as_of" required /></label><button type="submit">Reconstruct</button></form>
    {asOf && <LegalResource resource={result} what="this snapshot">{data => <div aria-live="polite">
      <p>As of {displayTime(data.as_of)} · last audit sequence {data.last_audit_sequence_as_of ?? 'none'}</p>
      <h3>Reviews ({data.reviews.length})</h3>{data.reviews.length ? <ul>{data.reviews.map(r => <li key={r.review_id}>{readableLabel(r.target_type)} <code>{shortHash(r.target_revision_sha256)}</code> <ReviewBadge status={r.state_as_of} /></li>)}</ul> : <p>No reviews recorded by then.</p>}
      <h3>Obligations ({data.obligations.length})</h3>{data.obligations.length ? <ul>{data.obligations.map(o => <li key={o.obligation_id}><code>{shortHash(o.obligation_id)}</code> · {o.confirmed_as_of ? `due ${displayTime(o.effective_due_at)}${o.due_by_as_of ? ' (already due)' : ''}` : 'deadline not yet confirmed'}</li>)}</ul> : <p>No visible obligations recorded by then.</p>}
    </div>}</LegalResource>}
  </section>
}

function Exports({ paths }) {
  const create = useRequest()
  const [exportId, setExportId] = useState(null)
  const detail = useResource(exportId && paths.exportItem(exportId))
  const done = data => data && setExportId(data.export_id)
  return <section className="panel"><h2>Evidence packs and exports</h2>
    <form onSubmit={async e => { e.preventDefault(); const f = new FormData(e.currentTarget)
      done(await create.run(paths.evidencePacks, { method: 'POST', body: { document_ids: ids(f.get('document_ids')), review_ids: ids(f.get('review_ids')) } })) }}>
      <fieldset className="toolbar" disabled={create.loading}><legend>Freeze an evidence pack</legend>
        <label>Document IDs (comma or space separated)<textarea name="document_ids" rows="2" /></label>
        <label>Review IDs<textarea name="review_ids" rows="2" /></label>
        <button type="submit">Create pack</button>
        <button type="button" onClick={async () => done(await create.run(`${paths.workspace}/exports/findings`, { method: 'POST' }))}>Export approved findings</button></fieldset></form>
    <form className="toolbar" onSubmit={e => { e.preventDefault(); setExportId(new FormData(e.currentTarget).get('export_id')) }}>
      <label>Open export ID<input name="export_id" required /></label><button type="submit">Verify</button></form>
    {create.error && <LegalProblem error={create.error} what="these records" />}
    {exportId && <LegalResource resource={detail} what="this export">{data => <div aria-live="polite">
      <p><strong>{readableLabel(data.kind)}</strong> · {displayTime(data.created_at)} · manifest <code>{shortHash(data.manifest_sha256)}</code></p>
      <p className={data.integrity_verified ? 'badge review-approved' : 'badge review-rejected'}>{data.integrity_verified ? 'Integrity verified: manifest hash matches' : 'Integrity FAILED: manifest does not match its hash'}</p>
      <a className="button" download={`${data.kind}-${data.export_id}.json`} href={`data:application/json;charset=utf-8,${encodeURIComponent(JSON.stringify(data.manifest, null, 2))}`}>Download manifest JSON</a>
      <p className="muted small">Objects you could not read were excluded from the pack, not counted.</p>
    </div>}</LegalResource>}
  </section>
}
