import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { PageHeader } from '../../../components/ui.jsx'
import { useRequest, useResource } from '../../../hooks/useApi.js'
import { legalPaths } from '../shared/legalApi.js'
import { LegalProblem, LegalResource } from '../shared/LegalShared.jsx'
import { Citations } from '../shared/WorkflowViews.jsx'
import { displayTime, dueInView, readableLabel } from '../shared/viewModel.js'
import { useWorkspace } from '../shared/workspace.js'

const TASK_STATES = ['open', 'in_progress', 'submitted', 'done', 'cancelled']

export function ObligationsPage() {
  const { workspace } = useWorkspace()
  const paths = legalPaths(workspace.workspace_id)
  const [params, setParams] = useSearchParams()
  const filtered = ['from', 'until', 'overdue'].some(key => params.get(key))
  return <>
    <PageHeader title="Obligations and tasks" description="Obligations exist only after an independent review accepts a cited proposal. Due dates stay unconfirmed until a person confirms the timezone and date; the original deadline wording is kept verbatim." />
    {filtered && <p className="review-notice" role="status">Showing obligations due {params.get('overdue') ? 'before now (overdue)' : `from ${params.get('from') || '…'} until ${params.get('until') || '…'}`}. <button type="button" onClick={() => setParams({})}>Clear filter</button></p>}
    <Obligations paths={paths} params={params} />
    <Tasks paths={paths} initialStatus={params.get('status') || ''} />
    <Notifications paths={paths} />
  </>
}

function Obligations({ paths, params }) {
  const list = useResource(paths.obligations({ limit: 500 }))
  const [confirming, setConfirming] = useState(null)
  return <section className="panel"><h2>Obligations</h2>
    <LegalResource resource={list} empty="No permitted obligations" emptyMessage="Accepted contract obligations appear here after independent review." what="obligations">{data => {
      const items = data.items.filter(row => dueInView(row, params))
      return items.length ? <div className="table-scroll"><table><thead><tr><th scope="col">Obligation</th><th scope="col">Status</th><th scope="col">Due</th><th scope="col">Source</th><th scope="col">Action</th></tr></thead><tbody>{items.map(row => <tr key={row.obligation_id}>
        <td><strong>{row.actor}</strong> {row.action}<small className="legal-record-id">“{row.original_deadline_phrase || 'no deadline wording'}”</small></td>
        <td><span className="badge">{readableLabel(row.status)}</span></td>
        <td>{row.due_at ? `${displayTime(row.due_at)} (${row.timezone})` : 'Not confirmed'}</td>
        <td><Citations items={row.citations} /></td>
        <td><button type="button" aria-pressed={confirming?.obligation_id === row.obligation_id} onClick={() => setConfirming(row)}>{row.confirmed_at ? 'Re-confirm deadline' : 'Confirm deadline'}</button></td>
      </tr>)}</tbody></table></div> : <p>No loaded obligations match this filter.</p>
    }}</LegalResource>
    {confirming && <ConfirmDeadline paths={paths} row={confirming} onDone={() => { setConfirming(null); list.refresh() }} />}
  </section>
}

function ConfirmDeadline({ paths, row, onDone }) {
  const request = useRequest()
  return <form className="panel" onSubmit={async e => {
    e.preventDefault()
    const body = Object.fromEntries(new FormData(e.currentTarget))
    body.notice_days = Number(body.notice_days)
    if (!body.recurrence_rule) delete body.recurrence_rule
    if (await request.run(`${paths.workspace}/obligations/${encodeURIComponent(row.obligation_id)}/deadline`, { method: 'POST', body })) onDone()
  }}><fieldset className="toolbar" disabled={request.loading}><legend>Confirm “{row.original_deadline_phrase || row.action}”</legend>
    <label>Timezone<input name="timezone" required defaultValue={row.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone} /></label>
    <label>Due (local date or date-time)<input name="due_local" required placeholder="2026-12-31" /></label>
    <label>Owner member ID<input name="owner_id" required defaultValue={row.owner_id || ''} /></label>
    <label>Notice days<input name="notice_days" type="number" min="0" max="365" defaultValue={row.notice_days ?? 0} /></label>
    <label>Recurrence rule (optional)<input name="recurrence_rule" defaultValue={row.recurrence_rule || ''} /></label>
    <button type="submit">Confirm</button></fieldset>
    {request.error && <LegalProblem error={request.error} what="this obligation" />}
  </form>
}

function Tasks({ paths, initialStatus }) {
  const [status, setStatus] = useState(initialStatus)
  const [mine, setMine] = useState(false)
  const list = useResource(paths.tasks({ status, mine: mine ? 'true' : undefined, limit: 200 }))
  const update = useRequest()
  const move = async (task, next) => { if (await update.run(`${paths.workspace}/tasks/${encodeURIComponent(task.task_id)}`, { method: 'PATCH', body: { status: next } })) list.refresh() }
  return <section className="panel"><h2>Tasks</h2>
    <div className="toolbar"><label>Status<select value={status} onChange={e => setStatus(e.target.value)}><option value="">All</option>{TASK_STATES.map(s => <option key={s} value={s}>{readableLabel(s)}</option>)}</select></label>
      <label><input type="checkbox" checked={mine} onChange={e => setMine(e.target.checked)} /> Only mine</label></div>
    {update.error && <LegalProblem error={update.error} what="this task" />}
    <LegalResource resource={list} empty="No permitted tasks" emptyMessage="Nothing to do in this view." what="tasks">{data =>
      <div className="table-scroll"><table><thead><tr><th scope="col">Task</th><th scope="col">Status</th><th scope="col">Due</th><th scope="col">Move to</th></tr></thead><tbody>{data.items.map(task => <tr key={task.task_id}>
        <td>{task.title}<small className="legal-record-id">{readableLabel(task.kind)}{task.evidence_request ? ` · evidence requested: ${task.evidence_request}` : ''}</small></td>
        <td><span className="badge">{readableLabel(task.status)}</span>{task.overdue && <span className="badge review-rejected">Overdue</span>}</td>
        <td>{displayTime(task.due_at)}</td>
        <td><label className="visually-hidden" htmlFor={`move-${task.task_id}`}>Move {task.title}</label><select id={`move-${task.task_id}`} value="" disabled={update.loading} onChange={e => e.target.value && move(task, e.target.value)}>
          <option value="">Choose…</option>{TASK_STATES.filter(s => s !== task.status).map(s => <option key={s} value={s}>{readableLabel(s)}</option>)}</select></td>
      </tr>)}</tbody></table></div>}</LegalResource>
    <p className="muted small">The server decides who may move a task: owners progress their own work, managers close it, and remediation closes only through <Link to="/app/legal/reviews">independent review</Link>.</p>
  </section>
}

function Notifications({ paths }) {
  const list = useResource(paths.notifications({ unread: 'true' }))
  const mark = useRequest()
  return <section className="panel"><h2>Unread notifications</h2>
    {mark.error && <LegalProblem error={mark.error} what="this notification" />}
    <LegalResource resource={list} empty="No unread notifications" emptyMessage="You are up to date." what="notifications">{data =>
      <ul aria-live="polite">{data.items.map(n => <li key={n.notification_id}>{readableLabel(n.kind)} · {readableLabel(n.subject_type)} · {displayTime(n.created_at)}{' '}
        <button type="button" onClick={async () => { if (await mark.run(`${paths.workspace}/notifications/${encodeURIComponent(n.notification_id)}/read`, { method: 'POST' })) list.refresh() }}>Mark read</button></li>)}</ul>}</LegalResource>
  </section>
}
