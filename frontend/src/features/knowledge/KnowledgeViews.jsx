import { useState } from 'react'
import { usePaged } from '../../hooks/useApi.js'
import { nextPage } from '../../services/api.js'
import { Icon, ListState } from '../../components/ui.jsx'
import { Chip } from '../executions/ExecutionsView.jsx'
import { humanizeEvent } from '../insights/insightsModel.js'

const date = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' })
const when = iso => iso ? date.format(Date.parse(iso)) : null
const LIFECYCLE = { CANDIDATE: 'warn', VERIFIED: 'ok', STALE: 'bad', REVOKED: 'muted' }

export function VerifiedRegistry() {
  const [status, setStatus] = useState('')
  const list = usePaged(`/verified-knowledge?limit=50${status ? `&status=${status}` : ''}`, nextPage.header)
  return <section className="panel" aria-labelledby="registry-title">
    <div className="section-heading"><h2 id="registry-title">Verified knowledge registry</h2>
      <button type="button" className="icon-button ghost" onClick={list.refresh} aria-label="Refresh registry" disabled={list.loading}><Icon name="refresh" size={18} /></button></div>
    <p className="muted small">Human-approved answers bound to exact source revisions. When a source changes, its answer becomes stale and must be re-verified before reuse.</p>
    <div className="segmented" role="group" aria-label="Lifecycle state">{['', ...Object.keys(LIFECYCLE)].map(value =>
      <button key={value || 'all'} type="button" aria-pressed={status === value} onClick={() => setStatus(value)}>{value ? humanizeEvent(value) : 'All'}</button>)}</div>
    <ListState list={list} empty={status ? `No ${humanizeEvent(status).toLowerCase()} entries` : 'No verified knowledge yet'} emptyMessage="Entries appear after a reviewer approves a candidate answer.">
      {list.items.length ? <ul className="registry-list">{list.items.map(item => <li key={item.knowledge_id} className="evidence-card">
        <header><span className="evidence-file">{item.title}</span><Chip tone={LIFECYCLE[item.lifecycle_state] || 'muted'}>{humanizeEvent(item.lifecycle_state)}</Chip></header>
        <p className="evidence-path">{item.question}</p>
        <blockquote>{item.statement}</blockquote>
        <footer><span className="muted small">Revision {item.revision} · {item.evidence?.length ?? 0} cited source{item.evidence?.length === 1 ? '' : 's'}</span>
          <span className="muted small">{item.trust?.verified_at ? `Verified ${when(item.trust.verified_at)}` : 'Not verified'}</span>
          {item.asset_scope?.length ? <span className="muted small identifier">{item.asset_scope.join(', ')}</span> : null}</footer>
      </li>)}</ul> : <p className="muted">No matches in the records scanned so far. Load more to keep scanning.</p>}
    </ListState>
  </section>
}

const GAP_COLUMNS = [['OPEN', 'Open', 'open'], ['UNDER_REVIEW', 'Under review', 'in_progress'], ['RESOLVED', 'Resolved', 'closed'], ['DISMISSED', 'Dismissed', 'dismissed']]

export function GapBoard() {
  const list = usePaged('/knowledge-gaps?limit=100', nextPage.offset)
  return <section className="panel" aria-labelledby="gaps-title">
    <div className="section-heading"><h2 id="gaps-title">Gap lifecycle</h2>
      <button type="button" className="icon-button ghost" onClick={list.refresh} aria-label="Refresh gaps" disabled={list.loading}><Icon name="refresh" size={18} /></button></div>
    <p className="muted small">A recent working set: persisted review records plus gaps detected in the latest runs. It is not an all-time inventory.</p>
    <ListState list={list} empty="No knowledge gaps recorded" emptyMessage="Gaps appear when a governed run finds evidence missing.">
      <div className="kanban">{GAP_COLUMNS.map(([status, label, tone]) => { const items = list.items.filter(gap => gap.status === status)
        return <section key={status} className="kanban-col" data-status={tone} aria-label={`${label}, ${items.length} gaps`}>
          <header><span className="col-dot" aria-hidden="true" /><h3>{label}</h3><span className="count">{items.length}</span></header>
          <div className="kanban-list">{items.length ? items.map(gap => <article key={gap.gap_id} className="wo-card">
            <span className="wo-top"><span className="wo-type">{humanizeEvent(gap.gap_type)}</span></span>
            <span className="wo-desc">{gap.subject}</span>
            {gap.required_evidence && <span className="muted small">Needs: {Array.isArray(gap.required_evidence) ? gap.required_evidence.join(', ') : String(gap.required_evidence)}</span>}
            <span className="wo-meta"><span>{when(gap.created_at) ? `Recorded ${when(gap.created_at)}` : 'Detected, not yet reviewed'}</span>
              {gap.resolution_note && <span>{gap.resolution_note}</span>}</span>
          </article>) : <p className="muted small kanban-empty">None</p>}</div>
        </section> })}</div>
    </ListState>
  </section>
}
