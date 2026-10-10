// Permitted aggregates from GET /dashboard drawn as hand-written SVG. Missing counts are never drawn as zero.
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { EmptyState, PageHeader } from '../../../components/ui.jsx'
import { useResource } from '../../../hooks/useApi.js'
import { legalPaths, query } from '../shared/legalApi.js'
import { LegalResource } from '../shared/LegalShared.jsx'
import { COMPLIANCE_STATES, countEntries, displayTime, donutSlices, weekEntries } from '../shared/viewModel.js'
import { useWorkspace } from '../shared/workspace.js'

const COLORS = ['var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)', 'var(--chart-4)', 'var(--human)', 'var(--danger)']
const EXPIRY = { expired: 'Already expired', 30: 'Within 30 days', 60: 'Within 60 days', 90: 'Within 90 days' }

export function LegalDashboardPage() {
  const { workspace } = useWorkspace()
  const resource = useResource(`${legalPaths(workspace.workspace_id).workspace}/dashboard`)
  return <>
    <PageHeader title="Legal dashboard" description="Counts over records you can read right now. Nothing you cannot open is counted, and nothing here is a compliance certificate." actions={<button type="button" onClick={resource.refresh}>Refresh</button>} />
    <LegalResource resource={resource} what="this dashboard">{data => {
      const assessments = countEntries(data.assessments_by_state, s => query('/app/legal/compliance', { resource: 'assessments', state: s }))
      const ordered = assessments && COMPLIANCE_STATES.map(s => assessments.find(e => e.key === s)).filter(Boolean)
      const charts = [
        ['Assessments by stored state', ordered, 'donut', Number.isInteger(data.assessments_stale) ? `${data.assessments_stale} current projection(s) are stale and need re-evaluation.` : null],
        ['Obligations due, next 8 weeks', weekEntries(data.obligations_due), 'bars', 'Only human-confirmed due dates are counted.'],
        ['Pending reviews by type', countEntries(data.reviews_pending_by_target, () => '/app/legal/reviews'), 'bars'],
        ['Evidence expiry', countEntries(data.evidence_expiring, () => '/app/legal/compliance?resource=evidence-versions')
          ?.map(e => ({ ...e, label: EXPIRY[e.key] || e.label, alert: e.key === 'expired' })).sort((a, b) => Object.keys(EXPIRY).indexOf(a.key) - Object.keys(EXPIRY).indexOf(b.key)), 'bars'],
        ['Documents by status', countEntries(data.documents_by_status, () => '/app/legal/documents'), 'bars'],
        ['Extraction jobs by state', countEntries(data.jobs_by_state, () => '/app/legal/documents'), 'bars'],
        ['Tasks by status', countEntries(data.tasks_by_status, s => query('/app/legal/obligations', { status: s })), 'bars'],
        ['Compliance findings', countEntries(data.findings_by_status, () => '/app/legal/compliance?resource=findings'), 'bars'],
        ['Regulatory sources by freshness', countEntries(data.regulatory_sources_by_freshness, () => '/app/legal/regulatory?resource=watchlists'), 'bars'],
      ]
      return <><p className="muted small">Generated {displayTime(data.generated_at)}</p>
        <div className="legal-dashboard-grid">{charts.map(([title, entries, kind, note]) => <Chart key={title} title={title} entries={entries} kind={kind} note={note} />)}</div></>
    }}</LegalResource>
  </>
}

function Chart({ title, entries, kind, note }) {
  const [table, setTable] = useState(false)
  const [active, setActive] = useState(null)
  const navigate = useNavigate()
  if (!entries) return <section className="panel"><h2>{title}</h2><p className="muted">Not reported by the server.</p></section>
  const total = entries.reduce((sum, e) => sum + e.count, 0)
  const max = Math.max(...entries.map(x => x.count)) || 1
  const mark = entry => ({ tabIndex: 0, role: 'link', 'aria-label': `${entry.label}: ${entry.count}. Open filtered list`,
    onMouseEnter: () => setActive(entry), onFocus: () => setActive(entry), onMouseLeave: () => setActive(null), onBlur: () => setActive(null),
    onClick: () => navigate(entry.href), onKeyDown: e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(entry.href) } },
    style: { cursor: 'pointer' } })
  return <section className="panel"><h2>{title}</h2>
    {!total ? <EmptyState title="Nothing to show" message="No permitted records in this category yet." /> : table
      ? <div className="table-scroll"><table><caption className="visually-hidden">{title}</caption><thead><tr><th scope="col">Category</th><th scope="col">Count</th></tr></thead>
        <tbody>{entries.map(e => <tr key={e.key}><th scope="row"><a href={e.href} onClick={ev => { ev.preventDefault(); navigate(e.href) }}>{e.label}</a></th><td>{e.count}</td></tr>)}</tbody></table></div>
      : kind === 'donut' ? <svg viewBox="0 0 42 42" width="220" height="220" role="group" aria-label={title}>
        {donutSlices(entries).map((s, i) => s.length > 0 && <circle key={s.key} {...mark(s)} cx="21" cy="21" r="15.9" fill="none" stroke={COLORS[i % COLORS.length]}
          strokeWidth={active?.key === s.key ? 7 : 5} pathLength="100" strokeDasharray={`${s.length} ${100 - s.length}`} strokeDashoffset={25 - s.offset}><title>{`${s.label}: ${s.count}`}</title></circle>)}
        <text x="21" y="23" textAnchor="middle" fontSize="6" fill="currentColor">{total}</text></svg>
      : <svg viewBox={`0 0 300 ${entries.length * 22}`} width="100%" role="group" aria-label={title}>
        {entries.map((e, i) => { const w = e.count ? Math.max(e.count / max * 160, 2) : 0
          return <g key={e.key} {...mark(e)}><title>{`${e.label}: ${e.count}`}</title>
            <text x="0" y={i * 22 + 15} fontSize="10" fill="currentColor">{e.label.slice(0, 22)}</text>
            <rect x="110" y={i * 22 + 4} width={w} height="14" fill={e.alert ? 'var(--danger)' : COLORS[i % COLORS.length]}
              stroke={active?.key === e.key ? 'var(--focus)' : 'none'} strokeWidth="2" />
            <text x={114 + w} y={i * 22 + 15} fontSize="10" fill="currentColor">{e.count}</text></g> })}</svg>}
    {kind === 'donut' && !table && !!total && <ul className="legal-legend">{entries.map((e, i) => <li key={e.key}><span aria-hidden="true" style={{ background: COLORS[i % COLORS.length] }} /> {e.label}: {e.count}</li>)}</ul>}
    <p aria-live="polite" className="small">{active ? `${active.label}: ${active.count} — press Enter to open` : note || ' '}</p>
    {!!total && <button type="button" aria-pressed={table} onClick={() => setTable(!table)}>{table ? 'Show chart' : 'Show data table'}</button>}
  </section>
}
