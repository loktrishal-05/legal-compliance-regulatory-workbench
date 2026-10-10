import { useState } from 'react'
import { Link } from 'react-router'
import { PageHeader } from '../../../components/ui.jsx'
import { useRequest, useResource } from '../../../hooks/useApi.js'
import { API_BASE_URL } from '../../../services/api.js'
import { legalPaths, query } from '../shared/legalApi.js'
import { LegalProblem, LegalResource, ReviewBadge } from '../shared/LegalShared.jsx'
import { SourceFacts } from '../shared/WorkflowViews.jsx'
import { useWorkspace } from '../shared/workspace.js'

export default function SummariesPage() {
  const { workspace } = useWorkspace()
  const paths = legalPaths(workspace.workspace_id)
  const summaries = useResource(paths.summaries)
  const documents = useResource(paths.documents({ limit: 100 }))
  const [documentId, setDocumentId] = useState('')
  const versions = useResource(documentId ? paths.versions(documentId) : null)
  const [sources, setSources] = useState([])
  const [selected, setSelected] = useState(null)
  const request = useRequest()
  return <>
    <PageHeader title="Summaries" description="Extractive views preserve source statements and conditions. Profiles change the view label, not legal meaning; audience rewriting and legal interpretation are not available yet." />
    <details className="panel"><summary>Generate a cited summary proposal</summary>
      <div className="toolbar"><label>Document<select value={documentId} onChange={e => setDocumentId(e.target.value)}><option value="">Choose a permitted source</option>{documents.data?.items.map(row => <option value={row.document_id} key={row.document_id}>{row.filename}</option>)}</select></label>
        <label>Version<select disabled={!documentId || versions.loading} value="" onChange={e => {
          if (e.target.value && !sources.some(row => row.version_id === e.target.value)) setSources([...sources, { document_id: documentId, version_id: e.target.value }])
        }}><option value="">Add source version</option>{versions.data?.items?.map(row => <option key={row.version_id} value={row.version_id}>{row.version_id.slice(0, 8)} · {row.status}</option>)}</select></label></div>
      {documents.error && <LegalProblem error={documents.error} />}{versions.error && <LegalProblem error={versions.error} />}
      <ul>{sources.map(row => <li key={row.version_id}>Source version <code>{row.version_id}</code> <button type="button" onClick={() => setSources(sources.filter(source => source.version_id !== row.version_id))}>Remove</button></li>)}</ul>
      <form onSubmit={async event => {
        event.preventDefault(); const form = Object.fromEntries(new FormData(event.currentTarget))
        const result = await request.run(paths.summaries, { method: 'POST', body: { ...form, sources } })
        if (result) { setSelected(result); summaries.refresh() }
      }}><fieldset className="toolbar" disabled={request.loading}><label>Profile<select name="profile">{['executive', 'detailed', 'clause', 'risk', 'obligation', 'action', 'change'].map(value => <option key={value}>{value}</option>)}</select></label>
        <label>Audience<select name="audience">{['legal', 'compliance', 'business', 'executive', 'auditor'].map(value => <option key={value}>{value}</option>)}</select></label><button type="submit" disabled={!sources.length || sources.length > 20}>Generate and submit for independent review</button></fieldset></form>
      {request.error && <LegalProblem error={request.error} what="these source versions" />}
    </details>
    <section className="panel"><h2>Permitted summaries</h2><p className="muted small">The API returns up to 200 recent permitted summaries.</p><LegalResource resource={summaries} empty="No cited summaries" what="summaries">{data =>
      <div className="table-scroll"><table><thead><tr><th scope="col">Profile</th><th scope="col">Audience</th><th scope="col">Review</th><th scope="col">Coverage</th><th scope="col">Action</th></tr></thead><tbody>{data.items.map(row => <tr key={row.summary_id}><td>{row.profile}</td><td>{row.audience}</td><td><ReviewBadge status={row.outcome} /></td><td>{row.coverage.covered_spans}/{row.coverage.total_spans} source spans</td><td><button type="button" onClick={() => setSelected(row)}>Read citations</button></td></tr>)}</tbody></table></div>}
    </LegalResource></section>
    {selected && <section className="panel"><h2>{selected.profile} summary · {selected.audience}</h2><ReviewBadge status={selected.outcome} /><p>Revision <code>{selected.revision_sha256}</code></p>
      <SourceFacts row={selected} />
      {!!selected.contradictions?.length && <p className="review-notice">Potential cross-source conflicts require review; source statements are preserved.</p>}
      <div className="toolbar">{selected.outcome === 'approved' ? ['pdf', 'docx', 'json'].map(format => <a className="button" key={format} href={API_BASE_URL + query(`${paths.summaries}/${selected.summary_id}/export`, { format })}>Download approved {format.toUpperCase()}</a>) : <p>Exports require independent approval. <Link to="/app/legal/reviews">Open review queue</Link>.</p>}</div>
    </section>}
  </>
}
