// Legal assurance report: permitted aggregates from GET /dashboard as an interactive report canvas.
// Click selects (cross-highlight), double-click or "Drill through" opens the filtered records. Missing counts are never drawn as zero.
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import { Icon } from '../../../components/ui.jsx'
import { useResource } from '../../../hooks/useApi.js'
import { legalPaths, query } from '../shared/legalApi.js'
import { LegalResource } from '../shared/LegalShared.jsx'
import { COMPLIANCE_STATES, countEntries, displayTime, donutSlices, niceMax, share, weekEntries } from '../shared/viewModel.js'
import { useWorkspace } from '../shared/workspace.js'
import './dashboard.css'

// One-Meaning Rule: green only for satisfied, red only for failure/overdue, amber where a human must look.
const STATE_COLOR = { satisfied: 'var(--ok)', partially_satisfied: 'var(--ai-cyan)', unsatisfied: 'var(--danger)',
  insufficient_evidence: 'var(--human)', not_applicable: 'var(--stale)', needs_review: 'var(--knowledge)' }
const SERIES = ['var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)', 'var(--chart-4)']
const EXPIRY = [['expired', 'Already expired', 'var(--danger)'], ['30', 'Within 30 days', 'var(--human)'],
  ['60', 'Within 60 days', 'var(--chart-4)'], ['90', 'Within 90 days', 'var(--chart-1)']]
const total = entries => entries?.reduce((sum, e) => sum + e.count, 0) ?? null
const shortDate = day => new Date(`${day}T00:00:00Z`).toLocaleDateString(undefined, { month: 'short', day: 'numeric', timeZone: 'UTC' })
const reducedMotion = () => typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches

export function LegalDashboardPage() {
  const { workspace } = useWorkspace()
  const resource = useResource(`${legalPaths(workspace.workspace_id).workspace}/dashboard`)
  return <div className="report">
    <header className="report-bar">
      <div><h1 data-page-title tabIndex={-1}>Legal assurance report</h1>
        <p>{workspace.name} · only records you can open right now are counted · not a compliance certificate</p></div>
      <div className="report-meta">{resource.data && <span>Refreshed {displayTime(resource.data.generated_at)}</span>}
        <button type="button" className="report-button" onClick={resource.refresh} disabled={resource.loading}><Icon name="refresh" size={16} />Refresh</button></div>
    </header>
    <LegalResource resource={resource} what="this dashboard">{data => <Report data={data} />}</LegalResource>
  </div>
}

function Report({ data }) {
  const navigate = useNavigate()
  const [selected, setSelected] = useState(null)
  const [focus, setFocus] = useState(null)
  const states = countEntries(data.assessments_by_state, s => query('/app/legal/compliance', { resource: 'assessments', state: s }))
  const assessments = states && COMPLIANCE_STATES.map(s => states.find(e => e.key === s)).filter(Boolean).map(e => ({ ...e, color: STATE_COLOR[e.key] }))
  const evidence = countEntries(data.evidence_expiring, () => '/app/legal/compliance?resource=evidence-versions')
  const expiry = evidence && EXPIRY.map(([key, label, color]) => ({ ...evidence.find(e => e.key === key), key, label, color })).filter(e => Number.isInteger(e.count))
  const bars = (counts, href) => countEntries(counts, href)?.map((e, i) => ({ ...e, color: SERIES[i % SERIES.length] }))
  const tasks = countEntries(data.tasks_by_status, () => '')
  const visuals = [
    { id: 'assessments', title: 'Assessments by stored state', kind: 'donut', span: 5, entries: assessments,
      note: Number.isInteger(data.assessments_stale) ? `${data.assessments_stale} current projection${data.assessments_stale === 1 ? ' is' : 's are'} stale` : null },
    { id: 'obligations', title: 'Obligations due, next 8 weeks', kind: 'columns', span: 7, note: 'Human-confirmed due dates only',
      entries: weekEntries(data.obligations_due)?.map(e => ({ ...e, long: e.label, label: e.alert ? 'Overdue' : shortDate(e.key), color: e.alert ? 'var(--danger)' : 'var(--chart-1)' })) },
    { id: 'evidence', title: 'Evidence expiry', kind: 'stacked', span: 4, entries: expiry, note: 'Accepted evidence versions by expiry window' },
    { id: 'reviews', title: 'Pending reviews by type', kind: 'bars', span: 4, entries: bars(data.reviews_pending_by_target, () => '/app/legal/reviews') },
    { id: 'tasks', title: 'Tasks by status', kind: 'bars', span: 4, entries: bars(data.tasks_by_status, s => query('/app/legal/obligations', { status: s })) },
    { id: 'documents', title: 'Documents by status', kind: 'bars', span: 3, entries: bars(data.documents_by_status, () => '/app/legal/documents') },
    { id: 'jobs', title: 'Extraction jobs', kind: 'bars', span: 3, entries: bars(data.jobs_by_state, () => '/app/legal/documents') },
    { id: 'findings', title: 'Compliance findings', kind: 'bars', span: 3, entries: bars(data.findings_by_status, () => '/app/legal/compliance?resource=findings') },
    { id: 'regulatory', title: 'Regulatory source freshness', kind: 'bars', span: 3, entries: bars(data.regulatory_sources_by_freshness, () => '/app/legal/regulatory?resource=watchlists') },
  ]
  const openTasks = tasks && (data.tasks_by_status.open ?? 0) + (data.tasks_by_status.in_progress ?? 0)
  const kpis = [
    { label: 'Pending reviews', value: total(countEntries(data.reviews_pending_by_target, () => '')), context: 'awaiting an independent decision', href: '/app/legal/reviews' },
    { label: 'Open tasks', value: openTasks, context: 'open or in progress', href: '/app/legal/obligations' },
    { label: 'Overdue obligations', value: data.obligations_due?.overdue, context: 'past a confirmed due date', href: '/app/legal/obligations?overdue=true', tone: 'danger' },
    { label: 'Stale assessments', value: data.assessments_stale, context: `of ${total(assessments) ?? '—'} assessments need re-evaluation`, href: '/app/legal/compliance', tone: 'human' },
    { label: 'Expired evidence', value: data.evidence_expiring?.expired, context: 'evidence versions past expiry', href: '/app/legal/compliance?resource=evidence-versions', tone: 'danger' },
  ]
  const select = (visual, entry, sum) => setSelected(current => current?.visual.id === visual.id && current.entry.key === entry.key ? null : { visual, entry, sum })
  const shown = focus ? visuals.filter(v => v.id === focus) : visuals
  return <>
    <ul className="report-kpis" aria-label="Key figures">{kpis.map(kpi => <Kpi key={kpi.label} {...kpi} />)}</ul>
    <div className="report-selection" aria-live="polite">{selected
      ? <><span className="report-swatch" style={{ background: selected.entry.color }} aria-hidden="true" />
        <p><span>{selected.visual.title}</span> <strong>{selected.entry.long || selected.entry.label}</strong> · {selected.entry.count}
          {selected.sum ? ` (${share(selected.entry.count, selected.sum)}% of ${selected.sum})` : ''}</p>
        <button type="button" className="report-button primary" onClick={() => navigate(selected.entry.href)}>Drill through<Icon name="arrow" size={16} /></button>
        <button type="button" className="report-button" onClick={() => setSelected(null)}>Clear</button></>
      : <p className="report-hint">Select a slice, column or bar to inspect it, then drill through to the filtered records.</p>}</div>
    <div className={`report-grid${focus ? ' is-focus' : ''}`}>
      {shown.map((v, i) => <Visual key={v.id} v={v} index={i} selectedKey={selected?.visual.id === v.id ? selected.entry.key : null} onSelect={select}
        focused={focus === v.id} onFocusMode={() => setFocus(focus ? null : v.id)} />)}
    </div>
  </>
}

function useCountUp(value) {
  const [shown, setShown] = useState(() => (reducedMotion() ? value : 0))
  useEffect(() => {
    if (!Number.isInteger(value)) return undefined
    const start = performance.now()
    let frame = requestAnimationFrame(function tick(now) {
      const p = reducedMotion() ? 1 : Math.min(1, (now - start) / 900)
      setShown(Math.round(value * (1 - 2 ** (-10 * p))))
      if (p < 1) frame = requestAnimationFrame(tick)
      else setShown(value)
    })
    return () => cancelAnimationFrame(frame)
  }, [value])
  return shown
}

function Kpi({ label, value, context, href, tone }) {
  const navigate = useNavigate()
  const known = Number.isInteger(value)
  const shown = useCountUp(known ? value : 0)
  return <li><a className="report-kpi" data-tone={known && value > 0 ? tone : undefined} href={href}
    onClick={event => { event.preventDefault(); navigate(href) }} aria-label={`${label}: ${known ? value : 'not reported'}. ${context}`}>
    <span className="report-kpi-label">{label}</span>
    <span className="report-kpi-value" aria-hidden="true">{known ? shown : '—'}</span>
    <span className="report-kpi-context">{known ? context : 'Not reported by the server'}</span>
  </a></li>
}

function Visual({ v, index, selectedKey, onSelect, focused, onFocusMode }) {
  const navigate = useNavigate()
  const [table, setTable] = useState(false)
  const [tip, setTip] = useState(null)
  const box = useRef(null)
  const sum = total(v.entries)
  const show = (entry, event) => {
    const frame = box.current.getBoundingClientRect()
    const target = event.type === 'focus' ? event.currentTarget.getBoundingClientRect() : null
    setTip({ entry, x: (target ? target.left + target.width / 2 : event.clientX) - frame.left, y: (target ? target.top : event.clientY) - frame.top })
  }
  const mark = entry => ({ tabIndex: 0, role: 'button', 'aria-pressed': selectedKey === entry.key,
    'aria-label': `${entry.long || entry.label}: ${entry.count}${sum ? `, ${share(entry.count, sum)}% of ${sum}` : ''}. Enter selects; double-click drills through`,
    'data-dim': selectedKey && selectedKey !== entry.key ? '' : undefined,
    onMouseMove: event => show(entry, event), onMouseLeave: () => setTip(null), onFocus: event => show(entry, event), onBlur: () => setTip(null),
    onClick: () => onSelect(v, entry, sum), onDoubleClick: () => navigate(entry.href),
    onKeyDown: event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(v, entry, sum) } } })
  const Chart = { donut: Donut, columns: Columns, bars: Bars, stacked: Stacked }[v.kind]
  return <section className="report-visual" style={{ '--span': focused ? 12 : v.span, '--i': index }} ref={box} aria-labelledby={`visual-${v.id}`}>
    <header>
      <div><h2 id={`visual-${v.id}`}>{v.title}</h2>{v.note && <p>{v.note}</p>}</div>
      {!!sum && <div className="report-visual-actions">
        <button type="button" aria-pressed={table} aria-label={table ? 'Show chart' : 'Show data table'} title={table ? 'Show chart' : 'Show data table'} onClick={() => setTable(!table)}><Icon name={table ? 'grid' : 'table'} size={16} /></button>
        <button type="button" aria-pressed={focused} aria-label={focused ? 'Back to report' : 'Focus mode'} title={focused ? 'Back to report' : 'Focus mode'} onClick={onFocusMode}><Icon name={focused ? 'collapse' : 'expand'} size={16} /></button>
      </div>}
    </header>
    {!v.entries ? <p className="report-empty">Not reported by the server.</p>
      : !sum ? <p className="report-empty">No permitted records yet.</p>
        : table ? <DataTable v={v} sum={sum} navigate={navigate} />
          : <Chart entries={v.entries} sum={sum} mark={mark} selectedKey={selectedKey} onSelect={entry => onSelect(v, entry, sum)} focused={focused} />}
    {tip && !table && <div className="report-tip" style={{ left: tip.x, top: tip.y }} role="presentation">
      <span className="report-swatch" style={{ background: tip.entry.color }} /><strong>{tip.entry.long || tip.entry.label}</strong>
      <b>{tip.entry.count}</b>{sum > 0 && <small>{share(tip.entry.count, sum)}% of {sum}</small>}
    </div>}
  </section>
}

function DataTable({ v, sum, navigate }) {
  return <div className="table-scroll"><table><caption className="visually-hidden">{v.title}</caption>
    <thead><tr><th scope="col">Category</th><th scope="col" className="num">Count</th><th scope="col" className="num">Share</th></tr></thead>
    <tbody>{v.entries.map(e => <tr key={e.key}><th scope="row"><a href={e.href} onClick={event => { event.preventDefault(); navigate(e.href) }}>{e.long || e.label}</a></th>
      <td className="num">{e.count}</td><td className="num">{share(e.count, sum)}%</td></tr>)}</tbody></table></div>
}

function Donut({ entries, sum, mark, selectedKey, onSelect, focused }) {
  const active = entries.find(e => e.key === selectedKey)
  return <div className={`report-donut${focused ? ' is-large' : ''}`}>
    <svg viewBox="0 0 120 120" role="group" aria-label="Assessment states">
      <circle className="report-donut-track" cx="60" cy="60" r="46" />
      {donutSlices(entries).map(s => s.length > 0 && <circle key={s.key} {...mark(s)} className="report-mark" cx="60" cy="60" r="46" pathLength="100"
        stroke={s.color} strokeDasharray={`${Math.max(s.length - 0.8, 0.4)} ${100 - Math.max(s.length - 0.8, 0.4)}`} strokeDashoffset={25 - s.offset} />)}
      <text x="60" y="60" className="report-donut-value">{active ? active.count : sum}</text>
      <text x="60" y="74" className="report-donut-label">{active ? (active.label.length > 14 ? 'selected' : active.label) : 'assessments'}</text>
    </svg>
    <ul className="report-legend">{entries.map(e => <li key={e.key} data-dim={selectedKey && selectedKey !== e.key ? '' : undefined}>
      <button type="button" tabIndex={-1} onClick={() => onSelect(e)}><span className="report-swatch" style={{ background: e.color }} aria-hidden="true" />
        <span>{e.label}</span><b>{e.count}</b><small>{share(e.count, sum)}%</small></button></li>)}</ul>
  </div>
}

function Columns({ entries, mark }) {
  const max = niceMax(Math.max(...entries.map(e => e.count)))
  const W = 560, H = 230, left = 30, bottom = 28, top = 22
  const slot = (W - left) / entries.length
  const y = value => top + (H - top - bottom) * (1 - value / max)
  const ticks = [0, max / 2, max].filter((t, i, all) => Number.isInteger(t) && all.indexOf(t) === i)
  return <svg className="report-columns" viewBox={`0 0 ${W} ${H}`} role="group" aria-label="Obligations due per week">
    {ticks.map(t => <g key={t} className="report-gridline"><line x1={left} x2={W} y1={y(t)} y2={y(t)} /><text x={left - 8} y={y(t) + 4}>{t}</text></g>)}
    {entries.map((e, i) => { const x = left + i * slot, w = slot * 0.56, h = y(0) - y(e.count)
      return <g key={e.key} {...mark(e)} className="report-mark" style={{ '--i': i }}>
        <rect className="report-hit" x={x} y={top} width={slot} height={H - top - bottom} />
        <rect className="report-column" x={x + (slot - w) / 2} y={y(e.count)} width={w} height={Math.max(h, e.count ? 2 : 0)} rx="4" fill={e.color} />
        <text className="report-datalabel" x={x + slot / 2} y={y(e.count) - 7}>{e.count}</text>
        <text className="report-axis" x={x + slot / 2} y={H - 8} data-alert={e.alert ? '' : undefined}>{e.label}</text>
      </g> })}
  </svg>
}

function Bars({ entries, mark }) {
  const max = Math.max(...entries.map(e => e.count)) || 1
  return <ul className="report-bars">{entries.map((e, i) => <li key={e.key} {...mark(e)} className="report-mark" style={{ '--i': i }}>
    <span className="report-bar-label">{e.label}</span>
    <span className="report-bar-track"><span className="report-bar-fill" style={{ width: `${e.count / max * 100}%`, background: e.color }} /></span>
    <b>{e.count}</b>
  </li>)}</ul>
}

function Stacked({ entries, sum, mark, selectedKey, onSelect }) {
  return <div className="report-stacked">
    <div className="report-stack">{entries.filter(e => e.count > 0).map(e => <span key={e.key} {...mark(e)} className="report-mark"
      style={{ flexGrow: e.count, background: e.color }} />)}</div>
    <ul className="report-legend">{entries.map(e => <li key={e.key} data-dim={selectedKey && selectedKey !== e.key ? '' : undefined}>
      <button type="button" tabIndex={-1} disabled={!e.count} onClick={() => onSelect(e)}><span className="report-swatch" style={{ background: e.color }} aria-hidden="true" />
        <span>{e.label}</span><b>{e.count}</b><small>{share(e.count, sum)}%</small></button></li>)}</ul>
  </div>
}
