import { Link } from 'react-router'
import { Icon } from '../../components/ui.jsx'
import { TERMS_V1 } from './termsV1.js'
import { TERMS_DOCUMENT } from './termsModel.js'
import { DEVELOPMENT_NOTICE, LEGACY_TERMS_NOTICE } from '../../product.js'

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
    <p className="review-notice">{DEVELOPMENT_NOTICE}</p>
    <nav className="help-starts" aria-label="Getting started">{STARTS.map(([id, title, hint, icon]) =>
      <a key={id} href={`#help-${id}`} onClick={go(`help-${id}`)}><Icon name={icon} size={22} /><span><strong>{title}</strong><small>{hint}</small></span></a>)}</nav>

    <section className="panel" aria-labelledby="help-video">
      <h2 id="help-video" tabIndex={-1}>Legacy industrial guidance video</h2>
      <p className="muted">Preserved historical walkthrough, not current legal-platform guidance. It plays only when you start it.</p>
      <figure className="help-video">
        <video controls preload="metadata" playsInline poster="/resources/guidance-video-poster.webp" aria-describedby="help-video-caption">
          <source src={VIDEO} type="video/mp4" />
          <a href={VIDEO}>Download the guidance video (MP4)</a>
        </video>
        <figcaption id="help-video-caption" className="muted small">About 90 seconds · 1280×720 · served from this Workbench, no external player. Use the player controls or Space to play and pause; the fullscreen control is in the player.</figcaption>
      </figure>
    </section>

    <section className="panel" aria-labelledby="help-guide">
      <h2 id="help-guide" tabIndex={-1}>Legacy application user guide</h2>
      <p>Historical industrial-platform instructions, preserved unchanged. Legal-platform user guidance will follow the implemented workflows.</p>
      <div className="toolbar">
        <a className="button primary" href={GUIDE} target="_blank" rel="noopener">Open user guide (PDF, opens in a new tab)</a>
        <a className="button ghost" href={GUIDE} download>Download user guide (PDF)</a>
      </div>
      <p className="review-notice"><strong>Correction to the guide:</strong> the Limitations section (page 7) describes some advanced features as rolling out progressively. Current wording: feature availability depends on role, deployment mode, configured data and enabled local services.</p>
    </section>

    <section className="panel" aria-labelledby="help-terms">
      <div className="section-heading"><h2 id="help-terms" tabIndex={-1}>{TERMS_V1.title}</h2><span className="badge">Version {TERMS_V1.version}</span></div>
      <p className="review-notice">{LEGACY_TERMS_NOTICE}</p>
      <TermsDocument />
      <div className="toolbar"><TermsDownload /></div>
    </section>

    <section className="panel" aria-labelledby="help-system">
      <h2 id="help-system" tabIndex={-1}>Application guidance</h2>
      <ul className="help-rules">
        <li><strong>Advisory only.</strong> Independently verify every output. This development build does not provide legal advice, sign contracts or certify compliance.</li>
        <li><strong>Humans approve.</strong> Anything that could influence operations is held as a draft for a reviewer. Approval releases advisory output only, and requesters cannot approve their own drafts.</li>
        <li><strong>Evidence has limits.</strong> Legal source/version/authority checks and extraction review are still being built. Existing industrial citations do not establish legal compliance.</li>
        <li><strong>Private runtime policy.</strong> The gateway restricts inference to local/private endpoints. Service ownership, network isolation and deployment configuration still require verification.</li>
        <li><strong>Audit scope.</strong> Existing material review decisions join a tamper-evident chain. Legal event coverage arrives with legal workflows.</li>
        <li><strong>What you can see.</strong> Feature availability depends on role, deployment mode, configured data and enabled local services. Where something is not available, the Workbench says so rather than showing placeholder data.</li>
      </ul>
      <p className="muted small">Process observations: <Link to="/app/sovereignty">Private runtime</Link> · configured routes: <Link to="/app/agents">Agents</Link> · resource policy: <Link to="/app/resources">Government resources</Link>.</p>
    </section>
  </>
}
