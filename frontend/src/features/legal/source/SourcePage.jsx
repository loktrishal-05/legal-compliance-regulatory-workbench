// Source viewer: exact stored spans with locators, transcription corrections (never legal meaning), blank-region
// transcription, and the labelled corrected projection shown next to — never instead of — the original.
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'
import { EmptyState, PageHeader } from '../../../components/ui.jsx'
import { useRequest, useResource } from '../../../hooks/useApi.js'
import { legalPaths, locatorLabel, newIdempotencyKey, sha256Hex, shortHash } from '../shared/legalApi.js'
import { LegalProblem, LegalResource } from '../shared/LegalShared.jsx'
import { useWorkspace } from '../shared/workspace.js'

export function SourcePage() {
  const { workspace } = useWorkspace()
  const [params, setParams] = useSearchParams()
  const documentId = params.get('document')
  const versionId = params.get('version')
  const selectedSpan = params.get('span')
  const paths = useMemo(() => legalPaths(workspace.workspace_id), [workspace.workspace_id])
  const [view, setView] = useState('original')
  const spans = useResource(documentId && versionId ? paths.spans(documentId, versionId, { limit: 500 }) : null)
  const projection = useResource(documentId && versionId && view === 'corrected' ? paths.projection(documentId, versionId) : null)
  if (!documentId || !versionId) return <><PageHeader title="Source viewer" />
    <EmptyState title="Choose a document version" message="Open a version from Documents, or follow a citation link." /></>
  const select = spanId => setParams(prev => { const next = new URLSearchParams(prev); next.set('span', spanId); return next })
  return <>
    <PageHeader title="Source viewer" description="Exact stored text and locators. Corrections fix transcription only; they never change legal meaning or the original." />
    <div className="segmented" role="group" aria-label="Text view">
      <button type="button" aria-pressed={view === 'original'} onClick={() => setView('original')}>Original extraction</button>
      <button type="button" aria-pressed={view === 'corrected'} onClick={() => setView('corrected')}>Corrected projection</button>
    </div>
    {view === 'original' ? <section className="panel" aria-labelledby="spans-title">
      <h2 id="spans-title">Original extraction spans</h2>
      <LegalResource resource={spans} empty="No extracted spans" emptyMessage="Run extraction from Documents, or the version needs manual transcription." what="this source">{data => <>
        <dl className="kv"><dt>Extraction status</dt><dd><span className="badge">{data.status}</span></dd>
          <dt>Source SHA-256</dt><dd><code title={data.source_sha256}>{shortHash(data.source_sha256)}</code></dd>
          <dt>Warnings</dt><dd>{data.warnings?.length ? data.warnings.join(', ') : 'None'}</dd></dl>
        <ol className="span-list">{data.items.map(span => <li key={span.span_id} aria-current={span.span_id === selectedSpan ? 'true' : undefined}>
          <button type="button" className="ghost" onClick={() => select(span.span_id)} aria-pressed={span.span_id === selectedSpan}>{locatorLabel(span.locator)}</button>
          <blockquote>{span.quote}</blockquote></li>)}</ol>
        {selectedSpan && data.items.some(s => s.span_id === selectedSpan) && <CorrectionPanel key={selectedSpan} paths={paths} documentId={documentId}
          versionId={versionId} span={data.items.find(s => s.span_id === selectedSpan)} />}
        <RegionPanel paths={paths} documentId={documentId} versionId={versionId} extractionId={data.extraction_id} />
      </>}</LegalResource>
    </section> : <section className="panel" aria-labelledby="proj-title">
      <h2 id="proj-title">Corrected projection <span className="badge badge-planned">Not the original</span></h2>
      <LegalResource resource={projection} what="this source">{data => <>
        <p className="muted small">Original text SHA-256 <code>{shortHash(data.original_text_sha256)}</code>. Highlighted segments are approved transcription corrections.</p>
        <p className="projection-text">{data.segments.map((segment, i) => segment.kind === 'approved_correction'
          ? <mark key={i} title={`Original: ${segment.original_text}`}>{segment.text}</mark> : <span key={i}>{segment.text}</span>)}</p>
        {data.manual_regions.length > 0 && <><h3>Approved manual transcriptions</h3>
          <ul>{data.manual_regions.map(region => <li key={region.transcription_id}>Page {region.page} [{region.bbox.join(', ')}]: {region.text}</li>)}</ul></>}
      </>}</LegalResource>
    </section>}
    <DecisionPanel paths={paths} documentId={documentId} versionId={versionId} />
  </>
}

function CorrectionPanel({ paths, documentId, versionId, span }) {
  const [form, setForm] = useState({ corrected_text: span.quote, rationale: '' })
  const request = useRequest()
  const submit = async event => {
    event.preventDefault()
    request.run(paths.proposeCorrection(documentId, versionId, span.span_id), { method: 'POST', body: {
      idempotency_key: newIdempotencyKey(), expected_quote_sha256: await sha256Hex(span.quote), ...form } })
  }
  return <form className="panel" onSubmit={submit} aria-labelledby="correct-title">
    <h3 id="correct-title">Propose a transcription correction · {locatorLabel(span.locator)}</h3>
    <fieldset disabled={request.loading}>
      <label>Corrected text<textarea required maxLength={64000} rows={3} value={form.corrected_text} onChange={e => setForm({ ...form, corrected_text: e.target.value })} /></label>
      <label>Rationale<input required maxLength={2000} value={form.rationale} onChange={e => setForm({ ...form, rationale: e.target.value })} /></label>
      <div className="toolbar"><button type="submit">Propose correction</button></div>
    </fieldset>
    <div aria-live="polite">{request.error && <LegalProblem error={request.error} what="this span" />}
      {request.data && <p>Proposed. Correction ID <code>{request.data.correction_id}</code> — an independent reviewer must decide it. Status: <span className="badge">{request.data.outcome}</span></p>}</div>
  </form>
}

function RegionPanel({ paths, documentId, versionId, extractionId }) {
  const [form, setForm] = useState({ page: 1, bbox: '0,0,100,100', text: '', rationale: '' })
  const request = useRequest()
  const review = useRequest()
  const submit = event => {
    event.preventDefault()
    request.run(paths.regionTranscription(documentId, versionId), { method: 'POST', body: {
      extraction_id: extractionId, page: Number(form.page), bbox: form.bbox.split(',').map(Number), text: form.text,
      rationale: form.rationale, idempotency_key: newIdempotencyKey() } })
  }
  const sendForReview = () => review.run(paths.reviews(), { method: 'POST', body: { target_type: 'region_transcription',
    target_id: request.data.transcription_id, target_revision_sha256: request.data.transcription_sha256,
    idempotency_key: `region:${request.data.transcription_sha256}` } })
  return <details className="disclosure"><summary>Transcribe a blank or unreadable page region</summary>
    <form onSubmit={submit}><fieldset disabled={request.loading} className="toolbar">
      <label>Page<input type="number" min={1} max={10000} required value={form.page} onChange={e => setForm({ ...form, page: e.target.value })} /></label>
      <label>Region x0,y0,x1,y1<input required pattern="\s*\d+(\.\d+)?\s*(,\s*\d+(\.\d+)?\s*){3}" value={form.bbox} onChange={e => setForm({ ...form, bbox: e.target.value })} /></label>
      <label>Text<input required maxLength={64000} value={form.text} onChange={e => setForm({ ...form, text: e.target.value })} /></label>
      <label>Rationale<input required maxLength={2000} value={form.rationale} onChange={e => setForm({ ...form, rationale: e.target.value })} /></label>
      <button type="submit">Save transcription</button>
    </fieldset></form>
    <div aria-live="polite">{(request.error || review.error) && <LegalProblem error={request.error || review.error} />}
      {request.data && !review.data && <p>Saved (not yet reviewed). <button type="button" onClick={sendForReview} disabled={review.loading}>Submit for independent review</button></p>}
      {review.data && <p>Review requested: <span className="badge">{review.data.status}</span></p>}</div>
  </details>
}

function DecisionPanel({ paths, documentId, versionId }) {
  const [correctionId, setCorrectionId] = useState('')
  const [decision, setDecision] = useState({ outcome: 'approved', rationale: '' })
  const loaded = useRequest()
  const decided = useRequest()
  const current = decided.data || loaded.data
  return <section className="panel" aria-labelledby="decide-title">
    <h2 id="decide-title">Decide a correction (independent reviewer)</h2>
    <form className="toolbar" onSubmit={e => { e.preventDefault(); decided.reset(); loaded.run(paths.correction(documentId, versionId, correctionId.trim())) }}>
      <label>Correction ID<input required value={correctionId} onChange={e => setCorrectionId(e.target.value)} /></label>
      <button type="submit">Load</button>
    </form>
    {(loaded.error || decided.error) && <LegalProblem error={loaded.error || decided.error} what="this correction" />}
    {current && <>
      <div className="split"><div><h3>Original quote</h3><blockquote>{current.original_quote}</blockquote></div>
        <div><h3>Proposed transcription</h3><blockquote>{current.corrected_text}</blockquote></div></div>
      <p>Status <span className="badge">{current.outcome}</span> · {locatorLabel(current.locator)} · rationale: {current.rationale}</p>
      {current.outcome === 'proposed' && <form onSubmit={e => { e.preventDefault(); decided.run(paths.decideCorrection(documentId, versionId, current.correction_id), { method: 'POST', body: decision }) }}>
        <fieldset disabled={decided.loading} className="toolbar">
          <label>Outcome<select value={decision.outcome} onChange={e => setDecision({ ...decision, outcome: e.target.value })}>
            <option value="approved">Approve transcription</option><option value="rejected">Reject</option></select></label>
          <label>Rationale<input required maxLength={2000} value={decision.rationale} onChange={e => setDecision({ ...decision, rationale: e.target.value })} /></label>
          <button type="submit">Record decision</button>
        </fieldset>
        <p className="muted small">The server refuses decisions on your own proposals and checks your current review grant.</p>
      </form>}
    </>}
  </section>
}
