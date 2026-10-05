import { useEffect, useState } from 'react'
import { usePaged, useRequest } from '../../hooks/useApi.js'
import { nextPage } from '../../services/api.js'
import { EmptyState, Icon, ListState, LoadingState, RequestProblem } from '../../components/ui.jsx'
import { humanizeEvent } from '../insights/insightsModel.js'

const STATUSES = ['PENDING', 'RUNNING', 'WAITING_APPROVAL', 'COMPLETED', 'REJECTED', 'INTERRUPTED', 'FAILED']
const TONE = { COMPLETED: 'ok', RUNNING: 'muted', PENDING: 'muted', WAITING_APPROVAL: 'warn', INTERRUPTED: 'warn', REJECTED: 'bad', FAILED: 'bad' }
const stamp = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })
const when = iso => iso ? stamp.format(Date.parse(iso)) : 'Not recorded'
const text = value => value == null || value === '' ? 'Not recorded' : String(value)

export const Chip = ({ tone, children }) => <span className="chip-status" data-tone={tone}>{children}</span>

function Timeline({ id }) {
  const detail = useRequest()
  const { run } = detail
  useEffect(() => { run(`/executions/${encodeURIComponent(id)}?limit=100`) }, [id, run])
  if (detail.error) return <RequestProblem error={detail.error} onRetry={() => run(`/executions/${encodeURIComponent(id)}?limit=100`)} />
  if (!detail.data) return <LoadingState label="Loading execution…" />
  const d = detail.data
  const rows = [['Status', humanizeEvent(d.status)], ['Route', text(d.route)], ['Current node', text(d.current_node)], ['Execution path', text(d.execution_path)],
    ['Selected model', text(d.selected_model)], ['Governance', d.governance_status ? humanizeEvent(d.governance_status) : 'No approval bound'],
    ['Retries', `${d.retry_count} retries · ${d.resume_count} resumes`], ['Created', when(d.created_at)], ['Updated', when(d.updated_at)]]
  const steps = d.timeline?.items || []
  return <>
    <dl className="kv">{rows.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
    {d.waiting_approval && <p className="review-notice">Waiting for a human decision. It cannot resume until a reviewer decides.</p>}
    {d.resume_available && <p className="muted small">The server reports this execution may be resumable; resuming rechecks every authorization and governance condition.</p>}
    <h3>Timeline <small className="muted">{d.timeline_semantics}</small></h3>
    {steps.length ? <ol className="timeline">{steps.map((step, i) => <li key={i}>
      <b>{step.kind === 'tool' ? `Tool ${text(step.tool)}` : step.node ? `Node ${step.node}` : humanizeEvent(step.kind)}</b> <Chip tone={TONE[step.status] || (step.status === 'SUCCEEDED' ? 'ok' : 'muted')}>{humanizeEvent(step.status)}</Chip>
      <span className="muted small"> {when(step.started_at)}{step.finished_at ? ` → ${when(step.finished_at)}` : ''} · {step.attempts} attempt{step.attempts === 1 ? '' : 's'}</span></li>)}</ol>
      : <p className="muted small">No operations recorded for this execution.</p>}
    {d.timeline?.has_more && <p className="muted small">Showing the first {steps.length} operations.</p>}
    <p className="muted small">Reasoning traces, prompts and tool result bodies are never stored in this view.</p>
  </>
}

export function ExecutionsView() {
  const [status, setStatus] = useState('')
  const [selected, setSelected] = useState(null)
  const list = usePaged(`/executions?limit=50${status ? `&status=${status}` : ''}`, nextPage.envelope)
  return <div className="board-layout">
    <section className="panel" aria-labelledby="executions-title">
      <div className="section-heading"><h2 id="executions-title">Executions</h2>
        <button type="button" className="icon-button ghost" onClick={list.refresh} aria-label="Refresh executions" disabled={list.loading}><Icon name="refresh" size={18} /></button></div>
      <label className="session-select">Status<select value={status} onChange={event => { setStatus(event.target.value); setSelected(null) }}>
        <option value="">All statuses</option>{STATUSES.map(s => <option key={s} value={s}>{humanizeEvent(s)}</option>)}</select></label>
      <ListState list={list} empty={status ? `No ${humanizeEvent(status).toLowerCase()} executions` : 'No executions yet'} emptyMessage="Durable executions you own appear here. Administrators see all executions.">
        <div className="table-scroll" tabIndex={0} role="region" aria-label="Executions"><table>
          <thead><tr><th>Created</th><th>Status</th><th>Route</th><th>Governance</th><th><span className="visually-hidden">Details</span></th></tr></thead>
          <tbody>{list.items.map(item => <tr key={item.execution_id} aria-current={selected === item.execution_id || undefined}>
            <td>{when(item.created_at)}</td><td><Chip tone={TONE[item.status]}>{humanizeEvent(item.status)}</Chip></td>
            <td>{text(item.route)}</td><td>{item.governance_status ? humanizeEvent(item.governance_status) : '—'}</td>
            <td><button type="button" className="ghost" onClick={() => setSelected(item.execution_id)} aria-label={`Open execution ${item.execution_id.slice(0, 8)}`}>Open</button></td></tr>)}</tbody>
        </table></div>
      </ListState>
    </section>
    <aside className="wo-inspector" aria-label="Execution details" aria-live="polite">
      {selected ? <><header><code className="identifier">{selected.slice(0, 8)}</code>
        <button type="button" className="icon-button ghost" onClick={() => setSelected(null)} aria-label="Close details"><Icon name="close" size={18} /></button></header>
        <Timeline id={selected} /></> : <EmptyState title="Select an execution" message="Its status, governance binding and operation timeline appear here." />}
    </aside>
  </div>
}
