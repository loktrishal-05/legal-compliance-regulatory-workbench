import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { ListState, PageHeader } from '../../../components/ui.jsx'
import { usePaged, useRequest, useResource } from '../../../hooks/useApi.js'
import { nextPage } from '../../../services/api.js'
import { legalPaths, query, shortHash } from '../shared/legalApi.js'
import { LegalProblem, LegalResource } from '../shared/LegalShared.jsx'
import { Citations, SubmitReview } from '../shared/WorkflowViews.jsx'
import { COMPLIANCE_STATES, displayTime, readableLabel } from '../shared/viewModel.js'
import { useWorkspace } from '../shared/workspace.js'

const RESOURCES = ['assessments', 'requirements', 'interpretations', 'controls', 'mappings', 'policies', 'policy-versions', 'evidence', 'evidence-versions', 'rules', 'findings', 'reevaluations']
const TARGETS = { assessments: 'assessment', interpretations: 'requirement_interpretation', 'evidence-versions': 'evidence_acceptance', rules: 'compliance_rule', findings: 'compliance_finding' }

export default function CompliancePage() {
  const { workspace } = useWorkspace()
  const paths = legalPaths(workspace.workspace_id)
  const [params, setParams] = useSearchParams()
  const selectedResource = RESOURCES.includes(params.get('resource')) ? params.get('resource') : 'assessments'
  const state = params.get('state') || ''
  const list = usePaged(query(paths.compliance(selectedResource), { limit: 50 }), nextPage.envelope)
  const [selected, setSelected] = useState(null)
  const items = list.items.filter(row => selectedResource !== 'assessments' || !state || row.status === state)
  return <>
    <PageHeader title="Compliance" description="Requirement → control → evidence → assessment. Stored states, current freshness and independent approval are separate dimensions; this is not a compliance certificate." />
    <div className="toolbar"><label>View<select value={selectedResource} onChange={e => { setSelected(null); setParams({ resource: e.target.value }) }}>{RESOURCES.map(value => <option key={value} value={value}>{readableLabel(value)}</option>)}</select></label>
      {selectedResource === 'assessments' && <label>Stored assessment state<select value={state} onChange={e => setParams({ resource: selectedResource, state: e.target.value })}><option value="">All six states</option>{COMPLIANCE_STATES.map(value => <option key={value} value={value}>{readableLabel(value)}</option>)}</select></label>}
      <button type="button" onClick={list.refresh}>Refresh</button><Link to="/app/legal/reviews">Independent review queue</Link></div>
    <section className="panel"><h2>{readableLabel(selectedResource)}</h2>
      <ListState list={list} empty="No permitted records" emptyMessage="This scope has no records of this type.">
        {items.length ? <div className="table-scroll"><table><thead><tr><th scope="col">Record</th><th scope="col">State / review</th><th scope="col">Recorded / expiry</th><th scope="col">Details</th></tr></thead><tbody>{items.map(row => <tr key={row.id}>
          <td>{row.title || row.text || row.reason || shortHash(row.id)}<small className="legal-record-id">{row.id}</small></td>
          <td><span className={`badge compliance-${row.status}`}>{readableLabel(row.status || row.review_state)}</span></td>
          <td>{displayTime(row.evaluated_at || row.created_at)}{row.expires_at && <p>Expires {displayTime(row.expires_at)}</p>}</td>
          <td><button type="button" aria-pressed={selected?.id === row.id} onClick={() => setSelected(row)}>Inspect {selectedResource === 'assessments' ? 'current projection' : 'record'}</button></td>
        </tr>)}</tbody></table></div> : <p>No loaded records match this state. Load more if available.</p>}
      </ListState>
    </section>
    {selected && <section className="panel" key={`${selectedResource}-${selected.id}`}><h2>Record details</h2>
      <p><code>{selected.id}</code></p><dl className="kv">{['requirement_id', 'control_id', 'policy_version_id', 'evidence_version_id', 'regulatory_version_id', 'owner_id', 'description', 'text', 'reason', 'source_sha256'].filter(key => selected[key]).map(key => <div key={key}><dt>{readableLabel(key)}</dt><dd>{selected[key]}</dd></div>)}</dl>
      {selectedResource === 'assessments' && <Assessment paths={paths} id={selected.id} />}
      <Citations items={selected.citations} />
      {selected.facts && <><h3>Evidence facts (proposed)</h3><dl className="kv">{Object.entries(selected.facts).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{JSON.stringify(value)}</dd></div>)}</dl></>}
      {selected.checks && <><h3>Deterministic rule checks</h3><ul>{selected.checks.map((check, i) => <li key={i}>{check.fact} {check.op} {JSON.stringify(check.value)}</li>)}</ul></>}
      {TARGETS[selectedResource] && selected.review_state !== 'approved' && <SubmitReview paths={paths} target={TARGETS[selectedResource]} row={selected} onSubmitted={list.refresh} />}
    </section>}
    <ProposeAssessment paths={paths} onCreated={list.refresh} />
    <p className="muted">Evidence uploads use <Link to="/app/legal/documents">Documents</Link>. Source interpretations, controls and evidence must be approved before they can establish a satisfied state.</p>
  </>
}

function Assessment({ paths, id }) {
  const resource = useResource(paths.assessmentCurrent(id))
  return <LegalResource resource={resource} what="assessment projection">{({ assessment, current }) => <>
    <dl className="kv"><dt>Stored state</dt><dd>{readableLabel(assessment.status)}</dd><dt>Current state</dt><dd>{readableLabel(current.current_status)}</dd><dt>Freshness</dt><dd>{current.freshness}</dd><dt>Review</dt><dd>{readableLabel(current.review_state)}</dd></dl>
    <h3>Reasons</h3><ul>{[...(assessment.result.reasons || []), ...(current.reasons || [])].map((reason, i) => <li key={i}>{typeof reason === 'string' ? reason : JSON.stringify(reason)}</li>)}</ul>
    <h3>Control and evidence map</h3>{assessment.inputs.components.length ? assessment.inputs.components.map(component => <section key={component.control_id} className="legal-statement"><h4>{component.control_title}</h4><p>{component.control_description}</p>
      <p>Rule revision <code>{shortHash(component.rule_version)}</code></p>
      {component.evidence.length ? component.evidence.map(evidence => <div key={evidence.evidence_id}><p>Evidence {shortHash(evidence.evidence_id)} · {evidence.accepted ? 'accepted' : 'not accepted'} · expires {displayTime(evidence.expires_at)}</p><Citations items={evidence.citations} /></div>) : <p>No mapped evidence — insufficient support must not be interpreted as failure.</p>}
    </section>) : <p>No approved control/rule components in this snapshot.</p>}
  </>}</LegalResource>
}

function ProposeAssessment({ paths, onCreated }) {
  const request = useRequest()
  const requirements = useResource(paths.compliance('requirements'))
  const applicability = useResource(paths.regulatory('applicability'))
  return <details className="panel"><summary>Evaluate a requirement from persisted inputs</summary><form onSubmit={async event => {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    if (await request.run(paths.compliance('assessments'), { method: 'POST', body: Object.fromEntries(form) })) onCreated()
  }}><fieldset className="toolbar" disabled={request.loading}>
    <label>Requirement<select name="requirement_id" required defaultValue=""><option value="">Select permitted requirement</option>{requirements.data?.items.map(row => <option key={row.id} value={row.id}>{row.title}</option>)}</select></label>
    <label>Applicability decision<select name="applicability_id" required defaultValue=""><option value="">Select scope decision</option>{applicability.data?.items.map(row => <option key={row.id} value={row.id}>{row.entity} · {row.product} · {row.state} · {row.effective_on}</option>)}</select></label><button type="submit">Create assessment proposal</button></fieldset></form>
    {request.error && <LegalProblem error={request.error} />}{requirements.error && <LegalProblem error={requirements.error} />}{applicability.error && <LegalProblem error={applicability.error} />}
    {request.data && <p role="status">Stored {readableLabel(request.data.status)}. Independent review is required.</p>}
  </details>
}
