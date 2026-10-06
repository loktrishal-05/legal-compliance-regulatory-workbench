import { Link } from 'react-router'
import { Icon } from '../../components/ui.jsx'
import { TERMS_V1 } from './termsV1.js'
import { TERMS_DOCUMENT } from './termsModel.js'

export const GUIDE = '/resources/application-user-guide.pdf'
const VIDEO = '/resources/guidance-video.mp4'

// The full terms, rendered from the approved document so they can be read without opening a DOCX.
export function TermsDocument({ id = 'terms-text' }) {
  return <div className="terms-text" id={id} tabIndex={0} role="region" aria-label={`${TERMS_V1.title}, version ${TERMS_V1.version}`}>
    {TERMS_V1.sections.map(section => <section key={section.heading}>
      <h3>{section.heading}</h3>
      {section.blocks.map((block, index) => block.list
        ? <ul key={index}>{block.items.map((item, i) => <li key={i}>{item.lead && <strong>{item.lead} </strong>}{item.text}</li>)}</ul>
        : <p key={index}>{block.lead && <strong>{block.lead} </strong>}{block.text}</p>)}
    </section>)}
  </div>
}

export const TermsDownload = () => <a className="button ghost" href={TERMS_DOCUMENT} download>
  <Icon name="book" size={18} />Download original terms (DOCX, v{TERMS_V1.version})</a>

const STARTS = [
  ['video', 'Watch the guidance video', '90-second overview of the Workbench', 'play'],
  ['guide', 'Open the user guide', 'How to ask, review and approve', 'book'],
  ['terms', 'Terms & Acceptable Use', `Version ${TERMS_V1.version}`, 'shield'],
  ['system', 'Application guidance', 'What this Workbench does and does not do', 'agent'],
]

export function ResourcesView() {
  // Jump links move focus to the section heading so keyboard and screen-reader users land where they asked.
  const go = id => event => { event.preventDefault(); const el = document.getElementById(id); el?.scrollIntoView({ block: 'start' }); el?.focus({ preventScroll: true }) }
  return <>
    <nav className="help-starts" aria-label="Getting started">{STARTS.map(([id, title, hint, icon]) =>
      <a key={id} href={`#help-${id}`} onClick={go(`help-${id}`)}><Icon name={icon} size={22} /><span><strong>{title}</strong><small>{hint}</small></span></a>)}</nav>

    <section className="panel" aria-labelledby="help-video">
      <h2 id="help-video" tabIndex={-1}>Guidance video</h2>
      <p className="muted">A short walkthrough of asking a governed question, reading cited evidence and human approval. It plays only when you start it.</p>
      <figure className="help-video">
        <video controls preload="metadata" playsInline poster="/resources/guidance-video-poster.webp" aria-describedby="help-video-caption">
          <source src={VIDEO} type="video/mp4" />
          <a href={VIDEO}>Download the guidance video (MP4)</a>
        </video>
        <figcaption id="help-video-caption" className="muted small">About 90 seconds · 1280×720 · served from this Workbench, no external player. Use the player controls or Space to play and pause; the fullscreen control is in the player.</figcaption>
      </figure>
    </section>

    <section className="panel" aria-labelledby="help-guide">
      <h2 id="help-guide" tabIndex={-1}>Application user guide</h2>
      <p>Step-by-step use of the Workbench: signing in, asking questions, reading evidence, approvals, voice review and troubleshooting.</p>
      <div className="toolbar">
        <a className="button primary" href={GUIDE} target="_blank" rel="noopener">Open user guide (PDF, opens in a new tab)</a>
        <a className="button ghost" href={GUIDE} download>Download user guide (PDF)</a>
      </div>
      <p className="review-notice"><strong>Correction to the guide:</strong> the Limitations section (page 7) describes some advanced features as rolling out progressively. Current wording: feature availability depends on role, deployment mode, configured data and enabled local services.</p>
    </section>

    <section className="panel" aria-labelledby="help-terms">
      <div className="section-heading"><h2 id="help-terms" tabIndex={-1}>{TERMS_V1.title}</h2><span className="badge">Version {TERMS_V1.version}</span></div>
      <p className="muted">The same terms you accept on first sign-in. The downloadable document is the authoritative original.</p>
      <TermsDocument />
      <div className="toolbar"><TermsDownload /></div>
    </section>

    <section className="panel" aria-labelledby="help-system">
      <h2 id="help-system" tabIndex={-1}>Application guidance</h2>
      <ul className="help-rules">
        <li><strong>Advisory only.</strong> Answers, recommendations and summaries must be independently verified. The AI never starts, stops, isolates, bypasses or controls plant equipment.</li>
        <li><strong>Humans approve.</strong> Anything that could influence operations is held as a draft for a reviewer. Approval releases advisory output only, and requesters cannot approve their own drafts.</li>
        <li><strong>Evidence has limits.</strong> Citations can be incomplete or outdated. P&amp;ID and OCR evidence is as drawn only and never proves valve state, isolation, permits or readiness.</li>
        <li><strong>Sovereign by design.</strong> Inference, retrieval and storage run on local services; no hosted AI is used for confidential work. Network isolation is enforced by your site controls.</li>
        <li><strong>Everything is recorded.</strong> Queries, decisions and approvals join a tamper-evident audit chain.</li>
        <li><strong>What you can see.</strong> Feature availability depends on role, deployment mode, configured data and enabled local services. Where something is not available, the Workbench says so rather than showing placeholder data.</li>
      </ul>
      <p className="muted small">Live service status: <Link to="/app/sovereignty">Sovereignty</Link> · configured routes: <Link to="/app/agents">Agents</Link> · resource policy: <Link to="/app/resources">Government resources</Link>.</p>
    </section>
  </>
}
