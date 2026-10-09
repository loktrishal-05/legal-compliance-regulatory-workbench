// Documents: permitted list, governed upload (quarantine reasons visible), versions, durable extraction jobs.
import { useMemo, useState } from 'react'
import { Link } from 'react-router'
import { ListState, PageHeader } from '../../../components/ui.jsx'
import { usePaged, useRequest, useResource } from '../../../hooks/useApi.js'
import { API_BASE_URL } from '../../../services/api.js'
import { JOB_TERMINAL, legalPaths, newIdempotencyKey, nextOffsetPage, shortHash, uploadDocument } from '../shared/legalApi.js'
import { LegalProblem, LegalResource } from '../shared/LegalShared.jsx'
import { useWorkspace } from '../shared/workspace.js'

const CLASSIFICATIONS = ['public', 'internal', 'confidential', 'restricted']

export function DocumentsPage() {
  const { workspace } = useWorkspace()
  const paths = useMemo(() => legalPaths(workspace.workspace_id), [workspace.workspace_id])
  const [filters, setFilters] = useState({ status: '', classification: '', filename: '' })
  const [selected, setSelected] = useState(null)
  const list = usePaged(paths.documents({ limit: 50, ...filters }), nextOffsetPage)
  return <>
    <PageHeader title="Documents" description="Only documents you currently have access to are listed. Counts are never shown for items you cannot see." />
    <UploadPanel workspaceId={workspace.workspace_id} onUploaded={list.refresh} />
    <section className="panel" aria-labelledby="doc-list">
      <h2 id="doc-list">Permitted documents</h2>
      <form className="toolbar" onSubmit={event => event.preventDefault()} aria-label="Filter documents">
        <label>File name<input value={filters.filename} maxLength={255} onChange={e => setFilters({ ...filters, filename: e.target.value })} /></label>
        <label>Status<select value={filters.status} onChange={e => setFilters({ ...filters, status: e.target.value })}>
          <option value="">Any</option>{['received', 'quarantined', 'ready', 'needs_verification', 'failed'].map(s => <option key={s}>{s}</option>)}</select></label>
        <label>Classification<select value={filters.classification} onChange={e => setFilters({ ...filters, classification: e.target.value })}>
          <option value="">Any</option>{CLASSIFICATIONS.map(c => <option key={c}>{c}</option>)}</select></label>
      </form>
      <ListState list={list} empty="No permitted documents" emptyMessage="Upload a document or ask for access to an existing one.">
        <div className="table-scroll"><table>
          <caption className="muted small">Documents in {workspace.name}</caption>
          <thead><tr><th scope="col">File</th><th scope="col">Type</th><th scope="col">Classification</th><th scope="col">Status</th><th scope="col">Legal hold</th><th scope="col">Actions</th></tr></thead>
          <tbody>{list.items.map(doc => <tr key={doc.document_id}>
            <td>{doc.filename}</td><td>{doc.document_type}</td><td>{doc.classification}</td>
            <td><span className="badge">{doc.ingestion_status}</span></td><td>{doc.legal_hold ? 'Yes' : 'No'}</td>
            <td><button type="button" onClick={() => setSelected(doc.document_id)} aria-pressed={selected === doc.document_id}>Versions</button></td>
          </tr>)}</tbody></table></div>
      </ListState>
    </section>
    {selected && <VersionsPanel key={selected} paths={paths} documentId={selected} />}
  </>
}

function UploadPanel({ workspaceId, onUploaded }) {
  const [form, setForm] = useState({ documentType: 'contract', classification: 'internal', matterId: '' })
  const [file, setFile] = useState(null)
  const [state, setState] = useState({ busy: false, result: null, error: null })
  const submit = async event => {
    event.preventDefault()
    if (!file) return
    setState({ busy: true, result: null, error: null })
    try {
      const result = await uploadDocument(workspaceId, file, form)
      setState({ busy: false, result, error: null })
      onUploaded()
    } catch (error) {
      setState({ busy: false, result: null, error })
    }
  }
  return <section className="panel" aria-labelledby="upload-title">
    <h2 id="upload-title">Upload</h2>
    <p className="muted small">The server inspects the bytes, scans and may quarantine. Format is decided by content, not by the file name.</p>
    <form onSubmit={submit}>
      <fieldset disabled={state.busy} className="toolbar">
        <label>File<input type="file" required accept=".pdf,.docx,.txt" onChange={e => setFile(e.target.files?.[0] || null)} /></label>
        <label>Document type<input required pattern="[a-z][a-z0-9_]{1,49}" value={form.documentType} onChange={e => setForm({ ...form, documentType: e.target.value })} /></label>
        <label>Classification<select value={form.classification} onChange={e => setForm({ ...form, classification: e.target.value })}>
          {CLASSIFICATIONS.map(c => <option key={c}>{c}</option>)}</select></label>
        <label>Matter ID (optional)<input value={form.matterId} placeholder="UUID" onChange={e => setForm({ ...form, matterId: e.target.value.trim() })} /></label>
        <button type="submit">{state.busy ? 'Uploading…' : 'Upload'}</button>
      </fieldset>
    </form>
    <div aria-live="polite">
      {state.error && <LegalProblem error={state.error} what="the upload target" />}
      {state.result && <dl className="kv">
        <dt>Status</dt><dd><span className="badge">{state.result.status}</span>{state.result.duplicate && ' (existing version in this workspace)'}</dd>
        <dt>Quarantine reasons</dt><dd>{state.result.quarantine_reasons?.length ? state.result.quarantine_reasons.join(', ') : 'None'}</dd>
      </dl>}
    </div>
  </section>
}

function VersionsPanel({ paths, documentId }) {
  const versions = useResource(paths.versions(documentId))
  return <section className="panel" aria-labelledby="versions-title">
    <h2 id="versions-title">Versions</h2>
    <LegalResource resource={versions} empty="No versions" what="this document">{data =>
      <div className="table-scroll"><table>
        <thead><tr><th scope="col">Received</th><th scope="col">Format</th><th scope="col">Status</th><th scope="col">Source SHA-256</th><th scope="col">Quarantine reasons</th><th scope="col">Processing</th></tr></thead>
        <tbody>{data.items.map(v => <tr key={v.version_id}>
          <td>{new Date(v.created_at).toLocaleString()}</td><td>{v.format || '—'}</td><td><span className="badge">{v.status}</span></td>
          <td><code title={v.source_sha256}>{shortHash(v.source_sha256)}</code></td>
          <td>{v.quarantine_reasons.length ? v.quarantine_reasons.join(', ') : 'None'}</td>
          <td><VersionActions paths={paths} documentId={documentId} version={v} /></td>
        </tr>)}</tbody></table></div>}
    </LegalResource>
  </section>
}

function VersionActions({ paths, documentId, version }) {
  const submit = useRequest()
  const status = useRequest()
  const job = status.data || submit.data
  const quarantined = version.status === 'quarantined' || version.quarantine_reasons.length > 0
  const start = operation => submit.run(paths.jobs(documentId, version.version_id),
    { method: 'POST', body: { operation, idempotency_key: newIdempotencyKey() } })
  return <div className="toolbar">
    {quarantined ? <span className="muted small">Quarantined: processing and download are blocked.</span> : <>
      <button type="button" disabled={submit.loading} onClick={() => start('extract')}>{job?.state === 'failed' || job?.state === 'dead_letter' ? 'Retry extraction' : 'Extract'}</button>
      <Link className="button ghost" to={`/app/legal/source?document=${documentId}&version=${version.version_id}`}>Open source</Link>
      <a className="button ghost" href={`${API_BASE_URL}${paths.original(documentId, version.version_id)}`} download>Original</a>
    </>}
    {job && <span aria-live="polite" className="small">Job <span className="badge">{job.state}</span>
      {job.failure_code && ` · ${job.failure_code}`} · attempt {job.attempts}/{job.max_attempts}
      {!JOB_TERMINAL.includes(job.state) && <button type="button" className="ghost" onClick={() => status.run(paths.job(job.job_id))}>Refresh status</button>}
    </span>}
    {(submit.error || status.error) && <LegalProblem error={submit.error || status.error} what="this version" />}
  </div>
}
