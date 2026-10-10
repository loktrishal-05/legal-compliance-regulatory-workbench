import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { ListState, PageHeader } from '../../../components/ui.jsx'
import { usePaged, useRequest, useResource } from '../../../hooks/useApi.js'
import { nextPage } from '../../../services/api.js'
import { legalPaths, query, shortHash } from '../shared/legalApi.js'
import { LegalProblem, LegalResource } from '../shared/LegalShared.jsx'
import { Citations, SubmitReview } from '../shared/WorkflowViews.jsx'
import { displayTime, readableLabel } from '../shared/viewModel.js'
import { useWorkspace } from '../shared/workspace.js'

const RESOURCES = ['sources', 'documents', 'versions', 'changes', 'applicability', 'watchlists', 'campaigns']
const TARGETS = { sources: 'regulatory_source', changes: 'regulatory_change', applicability: 'regulatory_applicability' }
const label = row => row.name || row.title || (row.entity && `${row.entity} · ${row.product}`)
  || (row.from_version_id && `${shortHash(row.from_version_id)} → ${shortHash(row.to_version_id)}`) || shortHash(row.id)

export function RegulatoryPage() {
  const { workspace } = useWorkspace()
  const paths = legalPaths(workspace.workspace_id)
  const [params, setParams] = useSearchParams()
  const resource = RESOURCES.includes(params.get('resource')) ? params.get('resource') : 'sources'
  const list = usePaged(query(paths.regulatory(resource), { limit: 50 }), nextPage.envelope)
  const [selected, setSelected] = useState(null)
  return <>
    <PageHeader title="Regulatory intelligence" description="Governed source registry, exact version diffs and applicability proposals. Unconfigured feeds show “not monitored”, never “no change”; approval happens only in the independent review queue." />
    <div className="toolbar"><label>View<select value={resource} onChange={e => { setSelected(null); setParams({ resource: e.target.value }) }}>
      {RESOURCES.map(value => <option key={value} value={value}>{readableLabel(value)}</option>)}</select></label>
      <button type="button" onClick={list.refresh}>Refresh</button><Link to="/app/legal/reviews">Independent review queue</Link></div>
    <section className="panel"><h2>{readableLabel(resource)}</h2>
      <ListState list={list} empty="No permitted records" emptyMessage="This workspace has no regulatory records of this type yet.">
        <div className="table-scroll"><table><thead><tr><th scope="col">Record</th><th scope="col">State</th><th scope="col">Dates</th><th scope="col">Details</th></tr></thead>
          <tbody>{list.items.map(row => <tr key={row.id}>
            <td>{label(row)}<small className="legal-record-id">{row.id}</small></td>
            <td>{[...new Set([row.trust_state, row.review_state, row.state, row.freshness, row.monitoring].filter(Boolean))].map(value => <span key={value} className="badge">{readableLabel(value)}</span>)}</td>
            <td>{row.effective_from !== undefined ? `Effective ${row.effective_from || 'unknown'} → ${row.effective_until || 'open'}` : displayTime(row.created_at)}</td>
            <td><button type="button" aria-pressed={selected?.id === row.id} onClick={() => setSelected(row)}>Inspect</button></td>
          </tr>)}</tbody></table></div>
      </ListState></section>
    {selected && <section className="panel" key={selected.id} aria-live="polite"><h2>{label(selected)}</h2>
      <dl className="kv">{Object.entries(selected).filter(([, value]) => value !== null && typeof value !== 'object').map(([key, value]) => <div key={key}><dt>{readableLabel(key)}</dt><dd>{String(value)}</dd></div>)}</dl>
      {selected.reason && <p className="muted">{selected.reason}</p>}
      {selected.exact_diff && <><h3>Exact structural diff</h3>{selected.exact_diff.map((part, i) => <section key={i} className="legal-statement"><h4>Section {part.section_ref} · {readableLabel(part.kind)}</h4><pre className="diff">{(part.text_diff || []).join('\n')}</pre></section>)}</>}
      {selected.semantic_proposal && <><h3>Proposal ({selected.semantic_proposal.kind}) — review required</h3><p>{selected.semantic_proposal.text}</p><Citations items={selected.semantic_proposal.citations} />
        {!!selected.semantic_proposal.uncertainties?.length && <ul>{selected.semantic_proposal.uncertainties.map(u => <li key={u}>{u}</li>)}</ul>}</>}
      {selected.affected && <><h3>Impact campaign</h3>{selected.affected.length ? <ul>{selected.affected.map((item, i) => <li key={i}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>)}</ul> : <p>No affected requirements, controls, evidence or obligations recorded.</p>}</>}
      {TARGETS[resource] && selected.review_state !== 'approved' && <SubmitReview paths={paths} target={TARGETS[resource]} row={selected} onSubmitted={list.refresh} />}
    </section>}
    <AsOf paths={paths} />
    <Proposals paths={paths} onCreated={list.refresh} />
  </>
}

function AsOf({ paths }) {
  const [path, setPath] = useState(null)
  const result = useResource(path)
  return <details className="panel"><summary>Which version applied on a date?</summary>
    <form className="toolbar" onSubmit={e => { e.preventDefault(); setPath(query(`${paths.regulatory('versions')}/as-of`, Object.fromEntries(new FormData(e.currentTarget)))) }}>
      <label>Regulatory document ID<input name="regulatory_document_id" required /></label>
      <label>Effective on<input type="date" name="effective_on" required /></label>
      <button type="submit">Resolve</button></form>
    {path && <LegalResource resource={result} what="this regulatory document">{data => <div aria-live="polite"><p><span className="badge">{readableLabel(data.status)}</span> {data.version_id ? <code>{data.version_id}</code> : 'No single version resolved'}</p>
      {!!data.reasons?.length && <ul>{data.reasons.map(r => <li key={r}>{r}</li>)}</ul>}</div>}</LegalResource>}
  </details>
}

const FORMS = [
  ['sources', 'Register a source', [['name', 'Name'], ['jurisdiction', 'Jurisdiction'], ['authority_tier', 'Authority tier', 'unverified'], ['owner_id', 'Owner member ID']]],
  ['documents', 'Add a regulatory document', [['source_id', 'Approved source ID'], ['title', 'Title']]],
  ['versions', 'Bind an extracted version', [['regulatory_document_id', 'Regulatory document ID'], ['document_id', 'Document ID'], ['version_id', 'Version ID'], ['extraction_id', 'Extraction ID'], ['published_at', 'Published (YYYY-MM-DD)'], ['effective_from', 'Effective from (blank = unknown)', '', false], ['effective_until', 'Effective until', '', false]]],
  ['changes', 'Compute an exact change', [['from_version_id', 'From version ID'], ['to_version_id', 'To version ID']]],
  ['applicability', 'Propose applicability', [['regulatory_version_id', 'Regulatory version ID'], ['state', 'State', 'applicable'], ['jurisdiction', 'Jurisdiction'], ['entity', 'Entity'], ['product', 'Product'], ['business_unit', 'Business unit'], ['effective_on', 'Effective on (YYYY-MM-DD)'], ['rationale', 'Rationale']]],
  ['watchlists', 'Watch a source', [['source_id', 'Source ID'], ['max_age_days', 'Max age (days)', '7']]],
]

function Proposals({ paths, onCreated }) {
  const request = useRequest()
  return <details className="panel"><summary>Record a regulatory proposal</summary>
    {FORMS.map(([resource, title, fields]) => <form key={resource} onSubmit={async e => {
      e.preventDefault()
      const body = Object.fromEntries([...new FormData(e.currentTarget)].map(([k, v]) => [k, v === '' ? null : k === 'max_age_days' ? Number(v) : v]))
      if (await request.run(paths.regulatory(resource), { method: 'POST', body })) onCreated()
    }}><fieldset className="toolbar" disabled={request.loading}><legend>{title}</legend>
      {fields.map(([name, text, value = '', required = true]) => <label key={name}>{text}<input name={name} defaultValue={value} required={required} /></label>)}
      <button type="submit">Save proposal</button></fieldset></form>)}
    {request.error && <LegalProblem error={request.error} what="the referenced record" />}
    {request.data && <p role="status">Recorded <code>{request.data.id}</code>. Approval requires an independent reviewer.</p>}
  </details>
}
