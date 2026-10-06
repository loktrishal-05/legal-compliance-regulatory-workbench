import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { SplitText } from 'gsap/SplitText'
import { useGSAP } from '@gsap/react'
import { useSession } from '../../app/session.jsx'
import { Logo } from '../../components/ui.jsx'
import { SOURCES, STORY, canvasSize, createParticles, particlePosition, smoothstep } from './landingModel.js'
import { BRAND_MARK, DEVELOPMENT_NOTICE, PRODUCT_NAME } from '../../product.js'
import { createHeroScene } from './heroScene.js'
import { createAtmosphere } from './atmosphere.js'
import './landing.css'

// Scroll-scrubbed canvas: five evidence clusters converge into the sovereign core. No video, no WebGL.
function ConvergenceCanvas({ controllerRef }) {
  const canvas = useRef(null)
  useEffect(() => {
    const element = canvas.current
    const context = element?.getContext?.('2d')
    if (!context) return undefined
    const particles = createParticles()
    const mark = new Image()
    mark.src = BRAND_MARK
    let progress = 1
    let frame = 0
    let size = { width: 1, height: 1, dpr: 1, cssWidth: 1, cssHeight: 1 }
    const draw = () => {
      frame = 0
      const { cssWidth: w, cssHeight: h, dpr } = size
      const scale = Math.min(w, h)
      const cx = w / 2
      const cy = h / 2
      context.setTransform(dpr, 0, 0, dpr, 0, 0)
      context.clearRect(0, 0, w, h)
      const glow = context.createRadialGradient(cx, cy, 0, cx, cy, scale * 0.42)
      glow.addColorStop(0, `rgba(53, 215, 232, ${0.06 + 0.22 * progress})`)
      glow.addColorStop(1, 'rgba(2, 14, 33, 0)')
      context.fillStyle = glow
      context.fillRect(0, 0, w, h)
      context.globalCompositeOperation = 'lighter'
      for (const particle of particles) {
        const position = particlePosition(particle, progress)
        context.globalAlpha = 0.3 + 0.6 * position.t
        context.fillStyle = particle.color
        context.beginPath()
        context.arc(cx + position.x * scale, cy + position.y * scale, particle.size * (1 + position.t * 0.5), 0, Math.PI * 2)
        context.fill()
      }
      context.globalAlpha = smoothstep(0.5, 0.85, progress)
      context.strokeStyle = 'rgba(53, 215, 232, 0.9)'
      context.lineWidth = 1.5
      context.beginPath()
      context.arc(cx, cy, scale * 0.16, 0, Math.PI * 2)
      context.stroke()
      if (mark.complete && mark.naturalWidth) {
        // Additive blending hides the mark's baked navy background on the dark canvas.
        context.globalAlpha = smoothstep(0.62, 0.95, progress)
        const markSize = scale * 0.25
        context.drawImage(mark, cx - markSize / 2, cy - markSize / 2, markSize, markSize)
      }
      context.globalCompositeOperation = 'source-over'
      context.globalAlpha = 1 - smoothstep(0.15, 0.5, progress)
      context.fillStyle = '#dbe7f6'
      context.font = `600 ${Math.max(12, Math.round(scale * 0.024))}px system-ui, sans-serif`
      context.textAlign = 'center'
      SOURCES.forEach((source, index) => {
        const angle = (index / SOURCES.length) * Math.PI * 2 - Math.PI / 2
        context.fillText(source.label, cx + Math.cos(angle) * scale * 0.46, cy + Math.sin(angle) * scale * 0.46)
      })
      context.globalAlpha = 1
    }
    const schedule = () => { if (!frame) frame = requestAnimationFrame(draw) }
    const resize = () => {
      const rect = element.getBoundingClientRect()
      const next = canvasSize(rect.width, rect.height, window.devicePixelRatio)
      element.width = next.width
      element.height = next.height
      size = { ...next, cssWidth: rect.width, cssHeight: rect.height }
      schedule()
    }
    const observer = new ResizeObserver(resize)
    observer.observe(element)
    mark.onload = schedule
    controllerRef.current = { setProgress: value => { if (value !== progress) { progress = value; schedule() } } }
    resize()
    return () => { observer.disconnect(); cancelAnimationFrame(frame); controllerRef.current = null }
  }, [controllerRef])
  return <canvas ref={canvas} className="unify-canvas" role="img" aria-label="Planned links among contracts, regulations, policies, evidence and human decisions" />
}

// The first viewport's signature: the approved mark assembled from GPU particles over a P&ID-style floor.
// Reduced motion, Save-Data or no WebGL keep the still mark; the page is fully readable either way.
const stillOnly = () => typeof window === 'undefined' || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches || !!navigator.connection?.saveData
function HeroScene({ apiRef }) {
  const canvas = useRef(null)
  const [still, setStill] = useState(stillOnly)
  useEffect(() => {
    const element = canvas.current
    if (still || !element) return undefined
    let scene = null, disposed = false, visible = true
    const cleanups = []
    const image = new Image()
    image.decoding = 'async'
    image.src = BRAND_MARK
    image.onload = () => {
      if (disposed) return
      try { scene = createHeroScene(element, image, { particles: window.innerWidth < 760 ? 6500 : 15000 }) } catch { scene = null }
      if (!scene) { setStill(true); return }
      // Size from the hero section (never from the canvas itself) and clamp, so the drawing buffer can never run away.
      const host = element.parentElement
      const fit = () => { const rect = host.getBoundingClientRect(); scene.resize(Math.min(rect.width, 3840), Math.min(rect.height, 2400), Math.min(window.devicePixelRatio || 1, window.innerWidth < 760 ? 1.4 : 1.75)) }
      const observer = new ResizeObserver(fit)
      observer.observe(host)
      fit()
      const sync = () => (visible && !document.hidden ? scene.play() : scene.pause())
      const io = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; sync() })
      io.observe(element)
      document.addEventListener('visibilitychange', sync)
      const onPointer = event => { const rect = element.getBoundingClientRect(); scene.setPointer(((event.clientX - rect.left) / rect.width) * 2 - 1, -(((event.clientY - rect.top) / rect.height) * 2 - 1)) }
      window.addEventListener('pointermove', onPointer, { passive: true })
      const assemble = { value: 0 }
      const tween = gsap.to(assemble, { value: 1, duration: 3.2, delay: 0.25, ease: 'power3.inOut', onUpdate: () => scene.setAssemble(assemble.value) })
      apiRef.current = scene
      sync()
      cleanups.push(() => { observer.disconnect(); io.disconnect(); tween.kill(); document.removeEventListener('visibilitychange', sync); window.removeEventListener('pointermove', onPointer) })
    }
    return () => { disposed = true; cleanups.forEach(fn => fn()); scene?.destroy(); apiRef.current = null }
  }, [still, apiRef])
  if (still) return <img className="hero-mark" src={BRAND_MARK} alt="" width="512" height="512" fetchPriority="high" />
  return <canvas ref={canvas} className="hero-canvas" aria-hidden="true" />
}

// One fixed backdrop for the whole page: smoke and beams that follow the cursor, from the hero to the footer.
// Reduced motion draws a single still frame; Save-Data or no WebGL keep the CSS gradient.
function Atmosphere() {
  const canvas = useRef(null)
  useEffect(() => {
    const element = canvas.current
    if (!element || navigator.connection?.saveData) return undefined
    const scene = createAtmosphere(element, { still: !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches })
    if (!scene) { element.hidden = true; return undefined }
    const sync = () => (document.hidden ? scene.pause() : scene.play())
    window.addEventListener('resize', scene.resize)
    document.addEventListener('visibilitychange', sync)
    sync()
    return () => { window.removeEventListener('resize', scene.resize); document.removeEventListener('visibilitychange', sync); scene.destroy() }
  }, [])
  return <canvas ref={canvas} className="atmosphere" aria-hidden="true" />
}

// Glass panels lean toward the cursor, drift a few pixels after it and catch light on the edge nearest to it.
function useMagneticGlass(root) {
  useEffect(() => {
    if (stillOnly() || !window.matchMedia?.('(hover: hover) and (pointer: fine)').matches) return undefined
    const cards = [...root.current.querySelectorAll('[data-glass]')]
    const move = event => {
      const card = event.currentTarget, rect = card.getBoundingClientRect()
      const x = (event.clientX - rect.left) / rect.width, y = (event.clientY - rect.top) / rect.height
      const tilt = Math.min(8, 2400 / Math.max(rect.width, rect.height)) // big panels tilt less
      card.style.setProperty('--mx', `${(x * 100).toFixed(1)}%`)
      card.style.setProperty('--my', `${(y * 100).toFixed(1)}%`)
      card.style.rotate = `${(0.5 - y).toFixed(3)} ${(x - 0.5).toFixed(3)} 0 ${(Math.hypot(x - 0.5, y - 0.5) * tilt * 2).toFixed(2)}deg`
      card.style.translate = `${((x - 0.5) * 12).toFixed(1)}px ${((y - 0.5) * 12).toFixed(1)}px`
    }
    const leave = event => { event.currentTarget.style.rotate = ''; event.currentTarget.style.translate = '' }
    cards.forEach(card => { card.addEventListener('pointermove', move); card.addEventListener('pointerleave', leave) })
    return () => cards.forEach(card => { card.removeEventListener('pointermove', move); card.removeEventListener('pointerleave', leave); leave({ currentTarget: card }) })
  }, [root])
}

const Tag = ({ id }) => {
  const [code, number] = STORY.find(item => item.id === id).tag.split('-')
  return <span className="tag-bubble" aria-hidden="true"><span>{code}</span><span>{number}</span></span>
}

function SourceCard({ source, children }) {
  return <article className="source-card" data-glass style={{ '--accent': source.color }}><header><span className="dot" />{source.label}</header>{children}<footer>{source.detail}</footer></article>
}

const STATIONS = [
  ['Ingest', 'Planned: secure contract and regulation intake with immutable originals and extraction quality. Existing PDF infrastructure is being adapted.'],
  ['Ground', 'Planned: every material legal statement links to authorized source spans and the exact document version.'],
  ['Evaluate', 'Planned: requirements, controls and evidence yield an explainable state. Missing evidence must never become a green status.'],
  ['Review', 'Existing independent advisory review is retained. Scoped legal findings and applicability decisions are still being built.'],
  ['Monitor', 'Planned: accepted obligations, deadlines and evidence freshness trigger deterministic work that survives restarts.'],
]

const ECOSYSTEM = [
  ['Regulatory sources', 'Manual import first · planned', 'Authoritative source approval and version provenance precede any claim of regulatory applicability. No live authority connector is configured.'],
  ['Enterprise identity', 'Operational-pilot gate', 'Development uses the existing sessions. Enterprise SSO, MFA and privileged re-authentication remain required before pilot readiness.'],
  ['Document systems', 'Future integration', 'Scoped document synchronization needs governed connectors, retries and source-change reconciliation.'],
  ['Ticketing and notifications', 'Planned', 'Accepted findings may create tasks and in-app notifications. External delivery is not configured.'],
  ['Jurisdiction packs', 'Not validated', 'Legal/compliance owners must approve sources, interpretations, playbooks, retention and reporting policies.'],
]

export default function LandingPage() {
  const root = useRef(null)
  const convergence = useRef(null)
  const heroScene = useRef(null)
  const session = useSession()
  const enter = session.status === 'authenticated' ? '/app/dashboard' : '/login'

  useMagneticGlass(root)
  useEffect(() => { document.title = `${PRODUCT_NAME} · Development migration` }, [])

  useGSAP(() => {
    gsap.registerPlugin(ScrollTrigger, SplitText)
    const mm = gsap.matchMedia()
    mm.add({ motion: '(prefers-reduced-motion: no-preference)', desktop: '(min-width: 1024px)' }, ({ conditions }) => {
      const { motion, desktop } = conditions
      if (!motion) { convergence.current?.setProgress(1); return undefined }
      root.current.classList.add('motion')
      root.current.style.setProperty('--flow', '0')
      // The rail carries pulses of light that stream down as the visitor scrolls and flare with scroll speed.
      const spine = root.current.querySelector('.spine')
      if (spine) ScrollTrigger.create({ trigger: root.current, start: 'top top', end: 'bottom bottom', onUpdate: self => {
        spine.style.setProperty('--off', (-window.scrollY / window.innerHeight * 0.35).toFixed(4))
        gsap.to(spine, { '--energy': Math.min(1, Math.abs(self.getVelocity()) / 2500), duration: 0.2, overwrite: true })
        gsap.to(spine, { '--energy': 0, duration: 1.4, delay: 0.25, ease: 'power2.out' })
      } })
      // Section headlines resolve word by word out of a blur, like an instrument coming into focus.
      gsap.utils.toArray('.story h2').forEach(heading => {
        const split = SplitText.create(heading, { type: 'words', wordsClass: 'word' })
        gsap.from(split.words, { opacity: 0, filter: 'blur(14px)', yPercent: 35, duration: 1.1, stagger: 0.07, ease: 'expo.out', clearProps: 'filter',
          scrollTrigger: { trigger: heading, start: 'top 88%', once: true } })
      })
      gsap.from('.hero-title .line', { yPercent: 105, duration: 1.3, stagger: 0.12, delay: 0.35, ease: 'expo.out' })
      gsap.from('.hero-copy > :not(h1)', { y: 24, opacity: 0, filter: 'blur(8px)', duration: 1.1, stagger: 0.1, delay: 0.75, ease: 'expo.out', clearProps: 'filter' })
      gsap.from('.hero-ghost', { opacity: 0, letterSpacing: '0.2em', duration: 2.4, ease: 'expo.out' })
      if (root.current.querySelector('.hero-mark')) gsap.to('.hero-mark', { yPercent: 22, ease: 'none', scrollTrigger: { trigger: '#hero', start: 'top top', end: 'bottom top', scrub: true } })
      ScrollTrigger.create({ trigger: '#hero', start: 'top top', end: 'bottom top', scrub: true, onUpdate: self => heroScene.current?.setScroll(self.progress) })
      gsap.to('.hero-copy', { yPercent: -14, opacity: 0.15, ease: 'none', scrollTrigger: { trigger: '#hero', start: '30% top', end: 'bottom top', scrub: true } })
      gsap.to('.hero-ghost', { xPercent: -8, ease: 'none', scrollTrigger: { trigger: '#hero', start: 'top top', end: 'bottom top', scrub: true } })
      gsap.utils.toArray('[data-reveal]').forEach(element => gsap.from(element, { y: 36, opacity: 0, filter: 'blur(10px)', duration: 1, ease: 'expo.out', clearProps: 'filter',
        scrollTrigger: { trigger: element, start: 'top 85%', once: true } }))
      gsap.utils.toArray('[data-count]').filter(element => Number(element.dataset.count) >= 10).forEach(element => {
        // The true value shows until the count begins; a verified fact never reads as 0 while waiting.
        ScrollTrigger.create({ trigger: element, start: 'top 95%', once: true, onEnter: () => {
          const counter = { value: 0 }
          gsap.to(counter, { value: Number(element.dataset.count), duration: 1.6, ease: 'power1.out',
            onUpdate: () => { element.textContent = Math.round(counter.value).toLocaleString() } })
        } })
      })
      const offsets = [[-70, -45, -7], [60, -25, 6], [-35, 40, -4], [80, 45, 7], [-55, 15, -3]]
      // Full-width cards on narrow screens scatter vertically only, so they are never clipped at the edge.
      gsap.to('.source-card', { x: i => (desktop ? offsets[i][0] * 2 : 0), y: i => offsets[i][1] * (desktop ? 2 : 1), rotate: i => offsets[i][2] * (desktop ? 1 : 0.5), ease: 'none',
        scrollTrigger: { trigger: '#scattered', start: desktop ? 'top top' : 'top 60%', end: desktop ? '+=120%' : 'bottom top', scrub: true, pin: desktop ? '#scattered' : false } })
      const unify = gsap.timeline({ scrollTrigger: { trigger: '#unify', start: 'top top', end: desktop ? '+=220%' : '+=140%', pin: true, scrub: 0.6,
        onUpdate: self => convergence.current?.setProgress(self.progress) } })
      unify.to({}, { duration: 1 }, 0)
        .fromTo('.unify-note-a', { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.1 }, 0.2)
        .to('.unify-note-a', { opacity: 0, duration: 0.08 }, 0.46)
        .fromTo('.unify-note-b', { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.1 }, 0.62)
      convergence.current?.setProgress(0)
      const stations = gsap.utils.toArray('.station')
      ScrollTrigger.create({ trigger: '#workflow', start: 'top top', end: desktop ? '+=250%' : 'bottom center', pin: desktop,
        onUpdate: self => {
          const active = Math.min(stations.length - 1, Math.floor(self.progress * stations.length))
          stations.forEach((station, index) => station.classList.toggle('is-active', index <= active))
          root.current?.style.setProperty('--flow', self.progress.toFixed(3))
        } })
      gsap.fromTo('.reveal-frame', { rotateX: 28, scale: 0.86, y: 60 }, { rotateX: 0, scale: 1, y: 0, ease: 'none',
        scrollTrigger: { trigger: '#reveal', start: 'top bottom', end: 'center center', scrub: true } })
      gsap.utils.toArray('.draw').forEach(path => gsap.fromTo(path, { strokeDashoffset: 1 }, { strokeDashoffset: 0, ease: 'none',
        scrollTrigger: { trigger: path.closest('section'), start: 'top 70%', end: 'center 45%', scrub: true } }))
      const element = root.current
      return () => element?.classList.remove('motion')
    })
  }, { scope: root })

  return <div className="landing" data-theme="dark" ref={root}>
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="landing-header">
      <Link to="/" aria-label={`${PRODUCT_NAME} home`}><Logo variant="horizontal" decorative className="landing-logo" /></Link>
      <nav aria-label="Story"><a href="#workflow">Build scope</a><a href="#governance">Governance</a><a href="#sovereignty">Private runtime</a><a href="#ecosystem">Integrations</a></nav>
      <Link className="button primary" to={enter}>{session.status === 'authenticated' ? 'Open Workbench' : 'Sign in'}</Link>
    </header>
    <Atmosphere />
    <svg className="spine" viewBox="0 0 24 1000" preserveAspectRatio="none" aria-hidden="true">
      <path className="spine-track" d="M12 0 V1000" />
      <path className="spine-glow" d="M12 0 V1000" pathLength="1" />
      <path className="spine-light" d="M12 0 V1000" pathLength="1" />
    </svg>
    <main id="main">
      <section id="hero" className="hero">
        <Tag id="hero" />
        <p className="hero-ghost" aria-hidden="true">LRA</p>
        <HeroScene apiRef={heroScene} />
        <div className="hero-scrim" aria-hidden="true" />
        <div className="hero-copy">
          <h1 className="hero-title"><span className="line-mask"><span className="line">Legal &amp; Regulatory</span></span> <span className="line-mask"><span className="line"><em>Assurance Platform</em></span></span></h1>
          <p className="lede">Building the link between legal text, evidence and accountable action. Contract intelligence, compliance monitoring and cited summaries are the target.</p>
          <p className="disclaimer">{DEVELOPMENT_NOTICE}</p>
          <div className="hero-actions"><Link className="button primary" to={enter}>{session.status === 'authenticated' ? 'Open the Workbench' : 'Enter the Workbench'}</Link><a className="button ghost" href="#scattered">See how it works</a></div>
          <p className="hero-facts" aria-label="Development boundaries"><span>Evidence-first design</span><span>Human-governed decisions</span><span>Local/private AI policy</span></p>
        </div>
        <a className="scroll-cue" href="#scattered" aria-label="Scroll to the story"><span /></a>
      </section>

      <section id="scattered" className="story scattered">
        <Tag id="scattered" />
        <div className="story-copy" data-reveal><h2>Legal evidence spans many documents</h2>
          <p>The target platform connects contracts, regulations, policies, evidence and accountable decisions. These are planned relationships, not current compliance results.</p>
          <p className="stat">Illustrative source categories only. No customer or live regulatory data is shown.</p></div>
        <div className="source-field">
          <SourceCard source={SOURCES[0]}><p className="doc-lines"><span /><span /><span /><span /></p><p className="note">Source version → clause → proposed obligation</p></SourceCard>
          <SourceCard source={SOURCES[1]}><p className="note">Approved source → effective version → requirement</p></SourceCard>
          <SourceCard source={SOURCES[2]}><p className="note">Policy → control → evidence</p></SourceCard>
          <SourceCard source={SOURCES[3]}><p className="note">Original artifact → provenance → freshness</p></SourceCard>
          <SourceCard source={SOURCES[4]}><p className="note">Exact revision → independent review → audit</p></SourceCard>
        </div>
      </section>

      <section id="unify" className="story unify">
        <Tag id="unify" />
        <ConvergenceCanvas controllerRef={convergence} />
        <div className="unify-copy"><h2>A living compliance model — planned</h2></div>
        <div className="unify-notes"><p className="unify-note unify-note-a">Sources, controls, obligations and evidence remain distinct.</p>
        <p className="unify-note unify-note-b">Accepted relationships will carry version, scope and human decision history.</p></div>
      </section>

      <section id="workflow" className="story workflow">
        <Tag id="workflow" />
        <div className="story-copy"><h2>The target legal workflow</h2><p>Not yet available end to end. The mature platform foundation is reused behind these planned legal modules.</p></div>
        <div className="flow-track" aria-hidden="true"><span className="flow-progress" /></div>
        <ol className="stations">{STATIONS.map(([name, text], index) => <li key={name} className="station" data-glass><span className="station-index">0{index + 1}</span><h3>{name}</h3><p>{text}</p></li>)}</ol>
      </section>

      <section id="reveal" className="story reveal">
        <Tag id="reveal" />
        <div className="story-copy" data-reveal><h2>A governed foundation, honestly labelled</h2><p>Existing sessions, evidence retrieval, advisory review, durable executions and audit are being adapted. Industrial regression views remain clearly marked until replaced.</p></div>
        <figure className="reveal-stage">
          <div className="reveal-frame">
            <div className="reveal-chrome" aria-hidden="true"><i /><i /><i /><span>{PRODUCT_NAME}</span></div>
            <div className="reveal-status"><h3>Development migration</h3><p>Legal dashboards will use authorized backend data. No compliance score, customer records or legal findings are fabricated here.</p></div>
          </div>
          <figcaption>Build status, not a dashboard preview. The historical industrial screenshot is retained outside the active landing page.</figcaption>
        </figure>
      </section>

      <section id="pid" className="story pid">
        <Tag id="pid" />
        <div className="story-copy" data-reveal><h2>Contract intelligence — planned</h2>
          <p>Parties, clauses, obligations and playbook deviations will remain source-linked proposals until authorized review.</p>
          <p className="disclaimer">No contract analysis or legal accuracy is claimed in this phase.</p></div>
        <div className="pid-figure" data-reveal data-glass><h3>Implementation gates</h3><p>Secure intake → exact source spans → validated extraction → independent review.</p><p>Original text remains available beside every material interpretation.</p></div>
      </section>

      <section id="maintenance" className="story maintenance">
        <Tag id="maintenance" />
        <div className="story-copy" data-reveal><h2>Obligations and evidence freshness — planned</h2><p>Approved duties, owners and deadlines will persist. Changed sources or stale evidence must invalidate current conclusions and request re-evaluation.</p></div>
        <div className="chart-figure" data-reveal data-glass><h3>Deterministic monitoring</h3><p>Timers, recurrence, reminders and escalation belong to durable software, not the language model.</p><p>Restart and duplicate-event tests must pass before this is described as continuous monitoring.</p></div>
        <div className="evidence-cards">
          <article className="evidence observation" data-reveal data-glass><small>Source fact</small><p>Exact text and version provide the evidence basis.</p></article>
          <article className="evidence hypothesis" data-reveal data-glass><small>Proposed interpretation</small><p>Uncertainty and missing information stay visible.</p></article>
          <article className="evidence verify" data-reveal data-glass><small>Human decision</small><p>An independent authorized reviewer governs acceptance.</p></article>
        </div>
      </section>

      <section id="governance" className="story governance">
        <Tag id="governance" />
        <div className="story-copy" data-reveal><h2>Humans approve. The chain remembers.</h2>
          <p>Reviewers see the exact proposal, its evidence and its risk before deciding. The requester can never approve their own request, and every decision joins a hash-linked audit chain.</p>
          <p className="disclaimer">Tamper-evident, not tamper-proof: modification of the recorded chain is detectable. Approval releases advisory output only.</p></div>
        <div className="chain-figure"><ol className="chain" aria-label="Illustrative audit chain">
          {['GOVERNED_REVISION_CREATED', 'EVIDENCE_MANIFEST_CREATED', 'APPROVAL_DECISION_APPROVE', 'ADVISORY_RELEASE_SUCCESS'].map((event, index) => <li key={event} className="block" data-reveal data-glass>
            <small>#{1040 + index}</small><strong>{event}</strong><code>prev → hash</code></li>)}
        </ol>
        <p className="chain-caption">Illustration. The event names are real audit event types; the sequence numbers and hashes are placeholders.</p></div>
      </section>

      <section id="voice" className="story voice">
        <Tag id="voice" />
        <div className="story-copy" data-reveal><h2>Source text before interpretation</h2>
          <p>Legal OCR corrections, summaries and obligations will retain the original source. Existing transcript-review infrastructure is reused only after legal-domain evaluation.</p></div>
        <div className="voice-demo" data-reveal data-glass>
          <p className="raw">Planned review contract: preserve source → identify uncertainty → record a human correction.</p>
          <p className="reason">Do not silently repair ambiguous dates, parties or obligations.</p>
          <p className="fixed">Legal speech recognition and multilingual legal accuracy are not yet evaluated.</p>
        </div>
      </section>

      <section id="sovereignty" className="story sovereignty">
        <Tag id="sovereignty" />
        <div className="story-copy" data-reveal><h2>Private runtime policy</h2>
          <p>The existing gateway restricts inference to local/private services. Dedicated service ownership, confidentiality and workspace isolation still require implementation and verification.</p>
          <p className="disclaimer">Offline-capable, not automatically air-gapped: network isolation is enforced by your site controls.</p></div>
        <div className="topology" data-reveal data-glass role="img" aria-label="Local services inside the site boundary">
          <span className="node core">Workbench API</span>
          {['Private model endpoint', 'PostgreSQL', 'Qdrant', 'Immutable source storage · planned', 'Authorized retrieval · planned'].map(node => <span key={node} className="node">{node}</span>)}
          <span className="boundary-label">Target topology · not a deployment claim</span>
        </div>
      </section>

      <section id="ecosystem" className="story ecosystem">
        <Tag id="ecosystem" />
        <div className="story-copy" data-reveal><h2>Integration boundaries, clearly stated</h2><p>Source authority, permissions and operational failure handling come before connector claims. Confidential documents are not inputs to public regulatory acquisition.</p></div>
        <ul className="eco-grid">{ECOSYSTEM.map(([name, status, note]) => <li key={name} data-reveal data-glass><strong>{name}</strong><span className="badge">{status}</span><p>{note}</p></li>)}</ul>
      </section>

      <section id="enter" className="story enter">
        <Tag id="enter" />
        <img className="enter-mark brand-img" src={BRAND_MARK} alt="" width="220" height="220" />
        <h2 data-reveal>Open the development workbench</h2>
        <p data-reveal>Review the existing platform foundation. Legal workflows remain under controlled construction.</p>
        <Link className="button primary large" to={enter}>Open the workbench</Link>
      </section>
    </main>
    <footer className="landing-footer"><Logo variant="horizontal" decorative className="landing-logo" /><p>Development migration. Historical industrial benchmarks do not establish legal accuracy. No legal advice, compliance certification or live authority integration is claimed.</p></footer>
  </div>
}
