import { useEffect, useState } from 'react'
import { usePaged, useRequest } from '../../hooks/useApi.js'
import { API_BASE_URL, nextPage } from '../../services/api.js'
import { EmptyState, ListState, LoadingState, RequestProblem } from '../../components/ui.jsx'
import { Chip } from '../executions/ExecutionsView.jsx'

const REGISTRY = { VERIFIED: ['Documented tag', 'ok'], CANDIDATE: ['Candidate', 'warn'], UNVERIFIED: ['Unverified', 'muted'], CONFLICTING: ['Conflicting', 'bad'], UNKNOWN: ['Unknown', 'muted'] }
const percent = value => typeof value === 'number' ? `${Math.round(value * 100)}%` : null
const regionState = region => region.conflicts?.length ? 'conflict' : region.human_review_required ? 'review' : 'documented'

function RegionDetail({ region }) {
  if (!region) return <p className="muted small">Select a region on the drawing or in the list to read its OCR text, candidates and registry matches.</p>
  return <div className="pid-region-detail">
    <p><strong className="identifier">{region.combined_text || 'No OCR text'}</strong></p>
    <p className="muted small">{region.confidence == null ? 'Vision-only region: no OCR score exists.' : `OCR confidence ${percent(region.confidence)}`} · page {region.page}</p>
    <div className="review-chips">{region.human_review_required && <Chip tone="warn">Human review required</Chip>}{region.conflicts?.length ? <Chip tone="bad">{region.conflicts.length} conflict{region.conflicts.length > 1 ? 's' : ''}</Chip> : null}</div>
    {region.fusion?.length ? <ul className="data-list">{region.fusion.map((f, i) => { const [label, tone] = REGISTRY[f.registry_status] || [f.registry_status, 'muted']
      return <li key={i}><span className="identifier">{f.equipment_candidate || f.normalized_text || 'No candidate'}</span> <Chip tone={tone}>{label}</Chip>
        <span className="muted small"> {f.evidence_origin?.join(' + ')}{f.visual_confidence != null ? ` · visual ${percent(f.visual_confidence)}` : ''}</span></li> })}</ul>
      : <p className="muted small">No registry fusion recorded; treat as unverified.</p>}
    {region.visual_candidates?.length ? <p className="muted small">{region.visual_candidates.length} visual candidate{region.visual_candidates.length > 1 ? 's' : ''}{region.visual_model ? ` from ${region.visual_model}` : ''}.</p> : null}
    <p className="muted small">Source {region.source_filename}{region.locator ? ` · ${region.locator}` : ''}</p>
  </div>
}

function Drawing({ id }) {
  const detail = useRequest()
  const { run } = detail
  const [page, setPage] = useState(1)
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState(null)
  useEffect(() => { run(`/documents/pid/${encodeURIComponent(id)}?page=${page}&limit=100&offset=${offset}`) }, [id, page, offset, run])
  if (detail.error) return <RequestProblem error={detail.error} title="Drawing unavailable" onRetry={() => run(`/documents/pid/${encodeURIComponent(id)}?page=${page}&limit=100&offset=${offset}`)} />
  if (!detail.data) return <LoadingState label="Loading drawing…" />
  const d = detail.data
  const sheet = d.pages.find(p => p.page === d.selected_page) || d.pages[0]
  const regions = d.regions.items
  const active = regions.find(r => r.evidence_id === selected)
  return <>
    <p className="review-notice">{d.limitation}</p>
    <div className="board-toolbar">
      {d.pages.length > 1 && <label className="session-select">Page<select value={page} onChange={event => { setPage(+event.target.value); setOffset(0); setSelected(null) }}>
        {d.pages.map(p => <option key={p.page} value={p.page}>Page {p.page}</option>)}</select></label>}
      <p className="muted small">{regions.length} region{regions.length === 1 ? '' : 's'} on this page{d.regions.has_more || offset ? ` (from ${offset + 1})` : ''} · revision {d.revision || 'not recorded'}</p>
    </div>
    <div className="pid-layout">
      {sheet ? <figure className="pid-sheet">
        <div className="pid-canvas">
          <img src={`${API_BASE_URL}${sheet.image_url}`} width={sheet.width} height={sheet.height} alt={`${d.title || d.filename}, page ${sheet.page} as drawn`} />
          <svg viewBox={`0 0 ${sheet.width} ${sheet.height}`} preserveAspectRatio="none" aria-hidden="true">
            {regions.map(r => { const [x1, y1, x2, y2] = r.bbox
              return <rect key={r.evidence_id} className="pid-box" data-state={regionState(r)} aria-current={selected === r.evidence_id || undefined}
                x={x1} y={y1} width={Math.max(1, x2 - x1)} height={Math.max(1, y2 - y1)} onClick={() => setSelected(r.evidence_id)} /> })}
          </svg>
        </div>
        <figcaption className="muted small">Rendered drawing with OCR/vision regions. Blue: documented tag · amber: review required · red: conflict.</figcaption>
      </figure> : <EmptyState title="No rendered page" />}
      <aside className="wo-inspector" aria-label="Region details">
        <h3>Regions</h3>
        {regions.length ? <ul className="pid-regions">{regions.map(r => <li key={r.evidence_id}>
          <button type="button" className="queue-row" aria-pressed={selected === r.evidence_id} onClick={() => setSelected(r.evidence_id)}>
            <span className="queue-row-title identifier">{r.combined_text || 'Vision-only region'}</span>
            <span className="queue-row-meta"><span>{r.confidence == null ? 'no OCR score' : `OCR ${percent(r.confidence)}`}</span><span>{regionState(r) === 'documented' ? 'documented' : regionState(r) === 'conflict' ? 'conflict' : 'review'}</span></span>
          </button></li>)}</ul> : <p className="muted small">No regions were extracted from this page.</p>}
        {(offset > 0 || d.regions.has_more) && <div className="toolbar">
          {offset > 0 && <button type="button" onClick={() => { setOffset(Math.max(0, offset - 100)); setSelected(null) }}>Previous regions</button>}
          {d.regions.has_more && <button type="button" onClick={() => { setOffset(d.regions.next_offset); setSelected(null) }}>Next regions</button>}</div>}
        <RegionDetail region={active} />
      </aside>
    </div>
  </>
}

export function PidViewer() {
  const list = usePaged('/documents/pid?limit=50', nextPage.envelope)
  const [chosen, setChosen] = useState(null)
  const id = chosen || list.items.find(v => v.artifacts_available)?.document_version_id || null
  return <>
    <section className="panel" aria-labelledby="pid-list-title">
      <h2 id="pid-list-title">Drawings</h2>
      <ListState list={list} empty="No P&IDs have been processed yet" emptyMessage="Administrators process drawings locally; processed versions appear here.">
        <div className="table-scroll" tabIndex={0} role="region" aria-label="P&ID drawings"><table>
          <thead><tr><th>Drawing</th><th>Revision</th><th>Status</th><th>Pages</th><th><span className="visually-hidden">Open</span></th></tr></thead>
          <tbody>{list.items.map(v => <tr key={v.document_version_id} aria-current={id === v.document_version_id || undefined}>
            <td>{v.title || v.filename}</td><td>{v.revision || '—'}</td><td>{v.processing_status}</td><td>{v.page_count ?? 'Unavailable'}</td>
            <td>{v.artifacts_available ? <button type="button" className="ghost" onClick={() => setChosen(v.document_version_id)}>Open</button> : <span className="muted small">Artifacts unavailable</span>}</td></tr>)}</tbody>
        </table></div>
      </ListState>
    </section>
    {id && <section className="panel" aria-label="Drawing viewer"><Drawing key={id} id={id} /></section>}
  </>
}
