// Independent exact-revision review queue. The UI hides self-review as a courtesy; the server is the authority.
import { useMemo, useState } from 'react'
import { PageHeader } from '../../../components/ui.jsx'
import { useRequest, useResource } from '../../../hooks/useApi.js'
import { useSession } from '../../../app/session.jsx'
import { REVIEW_DECISIONS, REVIEW_STATUS, canDecide, legalPaths, shortHash } from '../shared/legalApi.js'
import { LegalProblem, LegalResource, ReviewBadge } from '../shared/LegalShared.jsx'
import { useWorkspace } from '../shared/workspace.js'

const DECISION_LABEL = { approve: 'Approve', reject: 'Reject', request_changes: 'Request changes', escalate: 'Escalate' }

export function ReviewsPage() {
  const { workspace } = useWorkspace()
  const { user } = useSession()
  const paths = useMemo(() => legalPaths(workspace.workspace_id), [workspace.workspace_id])
  const [filters, setFilters] = useState({ status: 'pending', target_type: '' })
  const reviews = useResource(paths.reviews({ ...filters, limit: 100 }))
  return <>
    <PageHeader title="Review queue" description="Each decision binds the exact revision hash. You cannot decide your own requests; escalation never approves." />
    <form className="toolbar" aria-label="Filter reviews" onSubmit={e => e.preventDefault()}>
      <label>Status<select value={filters.status} onChange={e => setFilters({ ...filters, status: e.target.value })}>
        <option value="">Any</option>{Object.entries(REVIEW_STATUS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label>Target type<input value={filters.target_type} maxLength={60} placeholder="e.g. contract_obligation"
        onChange={e => setFilters({ ...filters, target_type: e.target.value.trim() })} /></label>
    </form>
    <LegalResource resource={reviews} empty="No reviews in this view" emptyMessage="Only reviews whose sources you can currently access are listed." what="reviews">{items =>
      <ul className="queue-rows">{items.map(review => <ReviewRow key={review.review_id} paths={paths} initial={review}
        userId={user?.id} onDecided={reviews.refresh} />)}</ul>}
    </LegalResource>
  </>
}

function ReviewRow({ paths, initial, userId, onDecided }) {
  const decide = useRequest()
  const review = decide.data || initial
  const [form, setForm] = useState({ decision: 'approve', rationale: '' })
  const allowed = canDecide(review, userId)
  const submit = async event => {
    event.preventDefault()
    if (await decide.run(paths.decide(review.review_id), { method: 'POST', body: form })) onDecided()
  }
  return <li className="panel">
    <div className="review-head"><strong>{review.target_type.replaceAll('_', ' ')}</strong> <ReviewBadge status={review.status} /></div>
    <dl className="kv"><dt>Target</dt><dd><code>{review.target_id}</code></dd>
      <dt>Exact revision</dt><dd><code title={review.target_revision_sha256}>{shortHash(review.target_revision_sha256)}</code></dd>
      <dt>Requested</dt><dd>{review.created_at ? new Date(review.created_at).toLocaleString() : '—'}{review.requester_id === userId && ' · by you'}</dd></dl>
    {review.decisions.length > 0 && <ol className="timeline">{review.decisions.map(d => <li key={d.decision_id}>
      {DECISION_LABEL[d.decision] || d.decision} — {d.rationale} <span className="muted small">({d.created_at ? new Date(d.created_at).toLocaleString() : ''})</span></li>)}</ol>}
    {allowed ? <form onSubmit={submit}><fieldset disabled={decide.loading} className="toolbar">
      <label>Decision<select value={form.decision} onChange={e => setForm({ ...form, decision: e.target.value })}>
        {REVIEW_DECISIONS.map(d => <option key={d} value={d}>{DECISION_LABEL[d]}</option>)}</select></label>
      <label>Rationale<input required maxLength={2000} value={form.rationale} onChange={e => setForm({ ...form, rationale: e.target.value })} /></label>
      <button type="submit">Record decision</button>
    </fieldset></form>
      : <p className="muted small">{review.requester_id === userId ? 'You requested this review, so another reviewer must decide it.'
        : 'Decided; history is immutable.'}</p>}
    <div aria-live="polite">{decide.error && <LegalProblem error={decide.error} what="this review" />}</div>
  </li>
}
