// Contracts: permitted contracts, deterministic analysis proposals with exact citations, redline, submit for review.
// Everything here is a proposal; acceptance happens only through the independent review queue.
import { useMemo, useState } from 'react'
import { EmptyState, PageHeader } from '../../../components/ui.jsx'
import { useRequest, useResource } from '../../../hooks/useApi.js'
import { legalPaths, shortHash } from '../shared/legalApi.js'
import { CitationLink, LegalProblem, LegalResource, ReviewBadge } from '../shared/LegalShared.jsx'
import { useWorkspace } from '../shared/workspace.js'

export function ContractsPage() {
  const { workspace } = useWorkspace()
  const paths = useMemo(() => legalPaths(workspace.workspace_id), [workspace.workspace_id])
  const contracts = useResource(paths.contracts)
  const [selected, setSelected] = useState(null)
  return <>
    <PageHeader title="Contracts" description="Clause, party, finding and obligation proposals cite exact stored source text. Nothing is accepted until an independent reviewer approves it." />
    <CreateContract paths={paths} onCreated={contracts.refresh} />
    <section className="panel" aria-labelledby="contracts-title">
      <h2 id="contracts-title">Permitted contracts</h2>
      <LegalResource resource={contracts} empty="No contracts" emptyMessage="Register a contract from a received document version." what="contracts">{data =>
        <div className="table-scroll"><table>
          <thead><tr><th scope="col">Title</th><th scope="col">Versions</th><th scope="col">Open</th></tr></thead>
          <tbody>{data.items.map(contract => <tr key={contract.contract_id}>
            <td>{contract.title}</td><td>{contract.versions.length}</td>
            <td><div className="toolbar">{contract.versions.map((v, i) => <button key={v.contract_version_id} type="button"
              aria-pressed={selected?.version.contract_version_id === v.contract_version_id}
              onClick={() => setSelected({ contract, version: v })}>Version {i + 1}</button>)}</div></td>
          </tr>)}</tbody></table></div>}
      </LegalResource>
    </section>
    {selected && <AnalysisPanel key={selected.version.contract_version_id} paths={paths} {...selected} />}
    {selected && selected.contract.versions.length > 1 && <RedlinePanel key={`r-${selected.contract.contract_id}`} paths={paths} contract={selected.contract} />}
  </>
}

function CreateContract({ paths, onCreated }) {
  const [form, setForm] = useState({ document_id: '', version_id: '', title: '' })
  const request = useRequest()
  const submit = async event => {
    event.preventDefault()
    if (await request.run(paths.contracts, { method: 'POST', body: form })) onCreated()
  }
  return <details className="disclosure"><summary>Register a contract from a document version</summary>
    <form onSubmit={submit}><fieldset disabled={request.loading} className="toolbar">
      <label>Document ID<input required value={form.document_id} onChange={e => setForm({ ...form, document_id: e.target.value.trim() })} /></label>
      <label>Document version ID<input required value={form.version_id} onChange={e => setForm({ ...form, version_id: e.target.value.trim() })} /></label>
      <label>Title<input required maxLength={200} value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /></label>
      <button type="submit">Register</button>
    </fieldset></form>
    <div aria-live="polite">{request.error && <LegalProblem error={request.error} what="that document version" />}
      {request.data && <p>Registered “{request.data.title}”.</p>}</div>
  </details>
}

function Citations({ citations }) {
  return citations?.length ? <ul className="citations">{citations.map((c, i) => <li key={c.span_id || i}><CitationLink citation={c} /></li>)}</ul>
    : <span className="muted">No citation</span>
}

function AnalysisPanel({ paths, contract, version }) {
  const path = paths.analysis(contract.contract_id, version.contract_version_id)
  const stored = useResource(path)
  const run = useRequest()
  const analysis = run.data || stored.data
  const notYetAnalysed = stored.error?.status === 404 && !run.data
  return <section className="panel" aria-labelledby="analysis-title">
    <h2 id="analysis-title">Analysis · {contract.title}</h2>
    <div className="toolbar"><button type="button" disabled={run.loading} onClick={() => run.run(path, { method: 'POST', body: {} })}>
      {run.loading ? 'Analysing…' : 'Run deterministic analysis'}</button>
      <span className="muted small">Source SHA-256 <code>{shortHash(version.source_sha256)}</code></span></div>
    {run.error && <LegalProblem error={run.error} what="this contract version" />}
    {notYetAnalysed ? <EmptyState title="Not analysed yet" message="Run the deterministic analysis to create reviewable proposals." />
      : analysis ? <AnalysisBody paths={paths} analysis={analysis} />
        : <LegalResource resource={stored} what="this analysis">{() => null}</LegalResource>}
  </section>
}

function AnalysisBody({ paths, analysis }) {
  return <>
    <dl className="kv"><dt>Status</dt><dd><span className="badge">{analysis.status}</span> (review required)</dd>
      <dt>Profile</dt><dd>{analysis.profile_version} · rules {analysis.rule_version}</dd>
      <dt>Uncertainties</dt><dd>{analysis.uncertainties?.length ? analysis.uncertainties.join(', ') : 'None recorded'}</dd></dl>
    <h3>Parties</h3>
    {analysis.parties.length ? <ul>{analysis.parties.map((p, i) => <li key={i}>{p.name} <Citations citations={p.citations} /></li>)}</ul> : <p className="muted">No parties proposed.</p>}
    <h3>Clauses</h3>
    <div className="table-scroll"><table><thead><tr><th scope="col">#</th><th scope="col">Title</th><th scope="col">Type</th><th scope="col">Source</th></tr></thead>
      <tbody>{analysis.clauses.map(c => <tr key={c.clause_id}><td>{c.ordinal}</td><td>{c.title}</td><td>{c.clause_type}</td><td><Citations citations={c.citations} /></td></tr>)}</tbody></table></div>
    <h3>Findings</h3>
    {analysis.findings.length ? <div className="table-scroll"><table><thead><tr><th scope="col">Kind</th><th scope="col">Rationale</th><th scope="col">Source</th><th scope="col">Review</th></tr></thead>
      <tbody>{analysis.findings.map(f => <tr key={f.finding_id}><td>{f.kind}</td><td>{f.rationale}{f.absence_established === false && ' (absence not established: incomplete coverage)'}</td>
        <td><Citations citations={f.citations} /></td><td><SubmitReview path={paths.submitFinding(f.finding_id)} outcome={f.outcome} /></td></tr>)}</tbody></table></div>
      : <p className="muted">No findings proposed.</p>}
    <h3>Obligation proposals</h3>
    {analysis.obligations.length ? <div className="table-scroll"><table><thead><tr><th scope="col">Actor</th><th scope="col">Action</th><th scope="col">Deadline phrase</th><th scope="col">Uncertainties</th><th scope="col">Source</th><th scope="col">Review</th></tr></thead>
      <tbody>{analysis.obligations.map(o => <tr key={o.proposal_id}><td>{o.actor}</td><td>{o.obligation_type}: {o.action}</td>
        <td>{o.original_deadline_phrase || '—'} <span className="muted small">(date needs human confirmation)</span></td>
        <td>{o.uncertainties.join(', ') || 'None'}</td><td><Citations citations={o.citations} /></td>
        <td><SubmitReview path={paths.submitObligation(o.proposal_id)} outcome={o.outcome} /></td></tr>)}</tbody></table></div>
      : <p className="muted">No obligation proposals.</p>}
  </>
}

function SubmitReview({ path, outcome }) {
  const request = useRequest()
  if (request.data) return <ReviewBadge status={request.data.status} />
  return <>{outcome && outcome !== 'proposed' && <span className="badge">{outcome}</span>}
    <button type="button" disabled={request.loading} onClick={() => request.run(path, { method: 'POST' })}>Submit for review</button>
    {request.error && <LegalProblem error={request.error} what="this proposal" />}</>
}

function RedlinePanel({ paths, contract }) {
  const [range, setRange] = useState({ from: contract.versions[0].contract_version_id, to: contract.versions.at(-1).contract_version_id })
  const redline = useResource(range.from !== range.to ? paths.redline(contract.contract_id, range.from, range.to) : null)
  const options = contract.versions.map((v, i) => <option key={v.contract_version_id} value={v.contract_version_id}>Version {i + 1}</option>)
  return <section className="panel" aria-labelledby="redline-title">
    <h2 id="redline-title">Exact redline</h2>
    <div className="toolbar"><label>From<select value={range.from} onChange={e => setRange({ ...range, from: e.target.value })}>{options}</select></label>
      <label>To<select value={range.to} onChange={e => setRange({ ...range, to: e.target.value })}>{options}</select></label></div>
    {range.from === range.to ? <p className="muted">Choose two different versions.</p> : <LegalResource resource={redline} what="this redline">{data => <>
      {data.qualified_summary && <p className="muted">{typeof data.qualified_summary === 'string' ? data.qualified_summary : JSON.stringify(data.qualified_summary)}</p>}
      {(data.changes || []).length ? <ol>{data.changes.map((change, i) => <li key={i}><strong>{change.section_ref || change.section} · {change.kind}</strong>
        <pre className="diff">{(change.text_diff || []).join('\n')}</pre></li>)}</ol> : <p className="muted">No textual changes between these versions.</p>}
      <p className="muted small">Exact text differences only; similarity is not legal equivalence.</p>
    </>}</LegalResource>}
  </section>
}
