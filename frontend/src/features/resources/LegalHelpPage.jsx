import { useEffect } from 'react'
import { useSearchParams } from 'react-router'
import { PageHeader } from '../../components/ui.jsx'
import { ResourcesView } from './ResourcesView.jsx'
import guide from '../../../../docs/product-resources/LEGAL_PLATFORM_USER_GUIDE.md?raw'
import draft from '../../../../docs/product-resources/LEGAL_PLATFORM_TERMS_AND_CONDITIONS_v2.0_DRAFT.md?raw'
import { guideBlocks, sectionSlug } from './guideModel.js'

function Inline({ text }) {
  return text.split(/(\*\*[^*]+\*\*)/).map((part, i) => part.startsWith('**') ? <strong key={i}>{part.slice(2, -2)}</strong> : part)
}

function GuideDocument({ text, prefix = '' }) {
  return <div className="legal-guide">{guideBlocks(text).map((block, i) => {
    if (block.kind === 'heading') {
      const Heading = block.level < 3 ? 'h3' : 'h4'
      return <Heading id={prefix + sectionSlug(block.text)} tabIndex={-1} key={i}><Inline text={block.text} /></Heading>
    }
    if (block.kind === 'table') return <div className="table-scroll" key={i}><table>
      <thead><tr>{block.rows[0].map((cell, n) => <th scope="col" key={n}><Inline text={cell} /></th>)}</tr></thead>
      <tbody>{block.rows.slice(1).map((row, n) => <tr key={n}>{row.map((cell, k) => <td key={k}><Inline text={cell} /></td>)}</tr>)}</tbody></table></div>
    if (block.kind === 'list') { const List = block.ordered ? 'ol' : 'ul'; return <List key={i}>{block.lines.map((line, n) => <li key={n}><Inline text={line} /></li>)}</List> }
    return <p key={i}><Inline text={block.text} /></p>
  })}</div>
}

export default function LegalHelpPage() {
  const [params] = useSearchParams()
  const section = params.get('guide_section')
  useEffect(() => {
    if (!section) return
    const node = document.getElementById(section) || document.getElementById(`draft-${section}`)
    const disclosure = node?.closest('details')
    if (disclosure) disclosure.open = true
    node?.scrollIntoView({ block: 'start' }); node?.focus({ preventScroll: true })
  }, [section])
  return <>
    <PageHeader title="Help & Resources" description="Current development guide, supplied overview video and draft terms. The enforced terms version remains v1.0." />
    <section className="panel"><h2>Legal platform overview</h2>
      <p>This supplied video explains the product direction. Features and limitations in the development guide below take precedence over the overview.</p>
      <video className="legal-guide-video" controls playsInline preload="none" poster="/resources/legal-guidance-video-poster.webp" aria-label="Legal assurance platform overview">
        <source src="/resources/legal-guidance-video.mp4" type="video/mp4" />
        <a href="/resources/legal-guidance-video.mp4">Download overview video</a>
      </video>
      <p className="muted">Visual product overview. A text guide with the workflows follows; narrated audio is not a source of legal authority.</p>
    </section>
    <section className="panel"><h2>Current legal user guide</h2><GuideDocument text={guide} /></section>
    <details className="panel"><summary>Terms v2 draft — pending counsel approval; not in force</summary><GuideDocument text={draft} prefix="draft-" /></details>
    <details className="panel"><summary>Archived industrial resources and enforced v1.0 terms</summary><ResourcesView /></details>
  </>
}
