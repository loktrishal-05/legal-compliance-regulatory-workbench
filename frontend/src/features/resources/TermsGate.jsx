import { useEffect, useRef, useState } from 'react'
import { Outlet, useNavigate } from 'react-router'
import { useSession } from '../../app/session.jsx'
import { useResource } from '../../hooks/useApi.js'
import { TERMS_REQUIRED_EVENT, apiRequest } from '../../services/api.js'
import { ErrorState, LoadingState, Logo } from '../../components/ui.jsx'
import { TermsDocument, TermsDownload } from './ResourcesView.jsx'
import { TERMS_V1 } from './termsV1.js'
import { TERMS_ACCEPT, TERMS_CURRENT, acceptBody, gateDecision, isVersionChanged, termsStatus } from './termsModel.js'
import '../../styles/workbench.css'
import { LEGACY_TERMS_NOTICE } from '../../product.js'

// Sits between authentication and the Workbench. The URL never changes, so after acceptance the user
// lands exactly where they were going. There is no skip: the only ways out are Accept or Sign out.
// The backend enforces the same rule on every protected API; a 403 from any of them re-opens this gate.
export function TermsGate() {
  const terms = useResource(TERMS_CURRENT)
  const { refresh } = terms
  useEffect(() => {
    window.addEventListener(TERMS_REQUIRED_EVENT, refresh)
    return () => window.removeEventListener(TERMS_REQUIRED_EVENT, refresh)
  }, [refresh])
  const decision = gateDecision(terms)
  if (decision === 'allow' || decision === 'unsupported') return <Outlet />
  const status = termsStatus(terms.data)
  return <div className="terms-gate" data-theme="light">
    <main id="main" className="terms-page">
      <Logo variant="horizontal" className="terms-logo" />
      {decision === 'loading' ? <LoadingState label="Checking the current terms…" />
        : decision === 'accept' ? <AcceptTerms key={status.version} status={status} onDone={refresh} />
        : <Blocked decision={decision} version={status?.version} onRetry={refresh} />}
    </main>
  </div>
}

function SignOut() {
  const { signOut } = useSession()
  const navigate = useNavigate()
  return <button type="button" className="ghost" onClick={async () => { if (await signOut()) navigate('/login', { replace: true }) }}>Sign out</button>
}

function Blocked({ decision, version, onRetry }) {
  return <section className="panel terms-panel">
    {decision === 'version-mismatch'
      ? <ErrorState title="Updated terms are not available in this Workbench" message={`The server requires terms version ${version}, but this Workbench contains version ${TERMS_V1.version}. You cannot accept terms you have not been shown. Ask your administrator to update the Workbench.`} />
      : <ErrorState title="The current terms could not be checked" message="The Workbench stays locked until the server confirms your acceptance of the current terms." onRetry={onRetry} />}
    <div className="toolbar"><SignOut /></div>
  </section>
}

function AcceptTerms({ status, onDone }) {
  const heading = useRef(null)
  const [checked, setChecked] = useState([])
  const [sending, setSubmit] = useState({ loading: false, error: null, notice: '' })
  useEffect(() => { heading.current?.focus() }, [])
  const { version, acknowledgements } = status
  const ready = acknowledgements.every(a => checked.includes(a.id))
  const toggle = (id, on) => setChecked(list => on ? [...new Set([...list, id])] : list.filter(item => item !== id))
  async function submit(event) {
    event.preventDefault()
    if (!ready || sending.loading) return
    setSubmit({ loading: true, error: null, notice: '' })
    try {
      await apiRequest(TERMS_ACCEPT, { method: 'POST', body: acceptBody(version, acknowledgements) })
      onDone() // the server now reports acceptance; the gate opens onto the page the user asked for
    } catch (error) {
      if (!isVersionChanged(error)) { setSubmit({ loading: false, error, notice: '' }); return }
      // The terms changed while this page was open: every statement must be confirmed again.
      setChecked([])
      setSubmit({ loading: false, error: null, notice: 'The terms changed while this page was open. Review them and confirm each statement again.' })
      onDone()
    }
  }
  return <form className="panel terms-panel" onSubmit={submit} aria-labelledby="terms-title">
    <header className="section-heading">
      <h1 id="terms-title" ref={heading} tabIndex={-1}>{TERMS_V1.title}</h1>
      <span className="badge">Version {version}</span>
    </header>
    <p>Before you use the Workbench, read and accept the current terms. Your acceptance is recorded by the server in the tamper-evident audit chain.</p>
    <p className="review-notice">{LEGACY_TERMS_NOTICE}</p>
    <TermsDocument id="terms-gate-text" />
    <div className="toolbar"><TermsDownload /></div>
    <fieldset className="terms-acks">
      <legend>Confirm each statement</legend>
      {acknowledgements.map(({ id, text }) => <label key={id} className="check">
        <input type="checkbox" checked={checked.includes(id)} onChange={event => toggle(id, event.target.checked)} />{text}</label>)}
    </fieldset>
    {sending.error && <p className="api-error" role="alert">{sending.error.message}</p>}
    {sending.notice && <p className="review-notice" role="status">{sending.notice}</p>}
    <div className="toolbar terms-actions">
      <button type="submit" className="primary" disabled={!ready || sending.loading} aria-describedby="terms-ready">{sending.loading ? 'Recording acceptance…' : 'Accept and continue'}</button>
      <SignOut />
      <span id="terms-ready" className="muted small" aria-live="polite">{ready ? 'All statements confirmed.' : `${acknowledgements.filter(a => checked.includes(a.id)).length} of ${acknowledgements.length} statements confirmed.`}</span>
    </div>
  </form>
}
