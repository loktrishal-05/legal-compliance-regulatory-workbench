import { Link } from 'react-router'
import { useRequest } from '../../../hooks/useApi.js'
import { newIdempotencyKey } from './legalApi.js'
import { CitationLink, LegalProblem } from './LegalShared.jsx'

export function Citations({ items = [] }) {
  return items.length ? <ul className="citations">{items.map((citation, i) => <li key={`${citation.span_id}-${i}`}><CitationLink citation={citation} /></li>)}</ul> : <p className="muted small">No source citation on this record.</p>
}

export function SubmitReview({ paths, target, row, onSubmitted }) {
  const request = useRequest()
  return <div className="legal-review-submit">
    <button type="button" disabled={request.loading || !!request.data || !row.revision_sha256} onClick={async () => {
      if (await request.run(paths.reviews(), { method: 'POST', body: { target_type: target, target_id: row.id,
        target_revision_sha256: row.revision_sha256, idempotency_key: newIdempotencyKey() } })) onSubmitted?.()
    }}>{request.loading ? 'Submitting…' : request.data ? 'Submitted' : 'Submit exact revision for review'}</button>
    {request.error && <LegalProblem error={request.error} what="this proposal" />}
    {request.data && <p role="status">Review created. <Link to="/app/legal/reviews">Open independent review queue</Link>.</p>}
  </div>
}

export function SourceFacts({ row }) {
  const items = row.statements || []
  return <>{items.map((statement, i) => <section className="legal-statement" key={i}><h3>Source fact {i + 1}</h3><p>{statement.text}</p><Citations items={statement.citations} /></section>)}
    {!!row.uncertainties?.length && <><h3>Uncertainties</h3><ul>{row.uncertainties.map(value => <li key={value}>{value.replaceAll('_', ' ')}</li>)}</ul></>}
    {!!row.missing_information?.length && <><h3>Missing information</h3><ul>{row.missing_information.map(value => <li key={value}>{value}</li>)}</ul></>}
  </>
}
