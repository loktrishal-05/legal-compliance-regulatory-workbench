// Cinematic light landing: "loose pages become one bound, cited record" (docs/DESIGN_DIRECTION.md).
// Server/first render is static and fully readable; motion is layered on client-side only without reduced motion.
import { useEffect, useRef } from 'react'
import { Link } from 'react-router'
import { useSession } from '../../app/session.jsx'
import { DEVELOPMENT_NOTICE, PRODUCT_NAME } from '../../product.js'
import { copy } from './landingCopy.js'
import { canvasSize } from './landingModel.js'
import { BEAT_AT, createPages, drawScene } from './paperThread.js'
import './landing.css'

const t = copy('en')

function ReviewMock() {
  // Illustrative only: mirrors the real review queue layout with synthetic values.
  const rows = [
    ['contract obligation', 'Buyer shall pay within 30 days of invoice.', 'Line 6', 'Pending'],
    ['compliance finding', 'Retention evidence expired on the mapped control.', 'Page 2', 'Escalated'],
    ['region transcription', 'Handwritten margin note, page 4.', 'Page 4', 'Approved'],
  ]
  return <div className="mock" role="img" aria-label={t.revealNote}>
    <div className="mock-bar"><span>Review queue</span><span className="mock-chip">exact revision · 3f9a1c…</span></div>
    <ul className="mock-rows">{rows.map(([type, quote, where, status]) => <li key={type} className="mock-row">
      <div><strong>{type}</strong><blockquote>“{quote}”</blockquote><span className="mock-loc">{where} · cited span</span></div>
      <span className={`mock-status s-${status.toLowerCase()}`}>{status}</span>
    </li>)}</ul>
    <div className="mock-actions"><span>Approve</span><span>Request changes</span><span>Escalate</span></div>
  </div>
}

export default function LandingPage() {
  const { status } = useSession()
  const root = useRef(null)
  const canvas = useRef(null)
  const enterHref = status === 'authenticated' ? '/app/legal' : '/login?next=/app/legal'

  useEffect(() => {
    const node = root.current, cv = canvas.current
    if (!node || !cv) return undefined
    const pages = createPages()
    const ctx = cv.getContext('2d')
    let progress = 0, idle = 0, alive = true
    const paint = () => {
      if (!ctx) return
      const { width, height, dpr } = canvasSize(cv.clientWidth, cv.clientHeight, window.devicePixelRatio)
      if (cv.width !== width || cv.height !== height) { cv.width = width; cv.height = height }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      drawScene(ctx, cv.clientWidth, cv.clientHeight, progress, pages, idle)
    }
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      progress = 0.92 // static key frame: the bound record
      paint()
      window.addEventListener('resize', paint)
      return () => window.removeEventListener('resize', paint)
    }
    let cleanup = () => {}
    ;(async () => {
      const [{ default: gsap }, { ScrollTrigger }, { default: Lenis }] = await Promise.all([
        import('gsap'), import('gsap/ScrollTrigger'), import('lenis')])
      if (!alive) return
      gsap.registerPlugin(ScrollTrigger)
      node.classList.add('is-cinematic')
      const lenis = new Lenis({ lerp: 0.09, smoothWheel: true })
      lenis.on('scroll', ScrollTrigger.update)
      const raf = time => lenis.raf(time * 1000)
      gsap.ticker.add(raf)
      gsap.ticker.lagSmoothing(0)
      let heroVisible = true
      const tick = () => { if (heroVisible) { idle += 0.016; paint() } }
      gsap.ticker.add(tick)
      const anchors = event => {
        const link = event.target.closest('a[href^="#"]')
        if (!link) return
        event.preventDefault()
        lenis.scrollTo(link.getAttribute('href'), { offset: -24 })
      }
      node.addEventListener('click', anchors)
      const track = node.querySelector('.hero-track')
      const scrub = { trigger: track, start: 'top top', end: 'bottom bottom', scrub: 0.6 }
      const context = gsap.context(() => {
        gsap.from('.intro > *', { opacity: 0, y: 60, filter: 'blur(18px)', duration: 1.2, ease: 'expo.out', stagger: 0.08 })
        ScrollTrigger.create({ ...scrub, onUpdate: self => { progress = self.progress },
          onLeave: () => { heroVisible = false }, onEnterBack: () => { heroVisible = true } })
        gsap.timeline({ scrollTrigger: scrub })
          .fromTo(cv, { scale: 1.15 }, { scale: 1, ease: 'none', duration: 1 }, 0)
          .to('.intro', { y: -80, scale: 0.92, opacity: 0, filter: 'blur(10px)', ease: 'power2.in', duration: 0.12 }, 0.04)
          .to('.veil', { opacity: 1, ease: 'none', duration: 0.2 }, 0.8)
        gsap.utils.toArray('.beat').forEach((beat, i) => {
          const at = BEAT_AT[i]
          gsap.timeline({ scrollTrigger: scrub })
            .set(beat, { opacity: 0 }, 0)
            .fromTo(beat, { opacity: 0, y: 50, filter: 'blur(14px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', ease: 'power2.out', duration: 0.09 }, at - 0.1)
            .to(beat, { opacity: 0, y: -50, filter: 'blur(14px)', ease: 'power2.in', duration: 0.09 }, at + 0.06)
            .set({}, {}, 1)
        })
        gsap.fromTo('.statement .w', { opacity: 0.12 }, { opacity: 1, stagger: 0.05, ease: 'none',
          scrollTrigger: { trigger: '.statement', start: 'top 75%', end: 'bottom 45%', scrub: 0.6 } })
        gsap.fromTo('.mock', { rotateX: 58, scale: 0.72, y: 60 }, { rotateX: 0, scale: 1, y: 0, ease: 'power2.inOut',
          scrollTrigger: { trigger: '.reveal-stage', start: 'top 85%', end: 'center 55%', scrub: 0.6 } })
        gsap.from('.mock-row', { opacity: 0, y: 24, stagger: 0.12, duration: 0.8, ease: 'expo.out',
          scrollTrigger: { trigger: '.mock', start: 'center 70%' } })
        gsap.fromTo('.flow-thread', { strokeDashoffset: 1 }, { strokeDashoffset: 0, ease: 'none',
          scrollTrigger: { trigger: '.flow', start: 'top 70%', end: 'bottom 60%', scrub: 0.6 } })
        gsap.from('.flow-step', { opacity: 0, y: 40, stagger: 0.12, duration: 0.9, ease: 'expo.out',
          scrollTrigger: { trigger: '.flow', start: 'top 65%' } })
        gsap.from('.pillar', { opacity: 0, y: 50, rotateY: -18, stagger: 0.1, duration: 1, ease: 'expo.out',
          scrollTrigger: { trigger: '.pillars', start: 'top 70%' } })
        gsap.utils.toArray('.count').forEach(el => {
          const state = { v: 0 }
          gsap.to(state, { v: Number(el.dataset.value), duration: 1.4, ease: 'power2.out',
            onUpdate: () => { el.textContent = String(Math.round(state.v)) },
            scrollTrigger: { trigger: el, start: 'top 85%', once: true } })
        })
      }, node)
      window.addEventListener('resize', paint)
      cleanup = () => {
        context.revert()
        gsap.ticker.remove(raf)
        gsap.ticker.remove(tick)
        lenis.destroy()
        node.removeEventListener('click', anchors)
        window.removeEventListener('resize', paint)
        node.classList.remove('is-cinematic')
      }
    })()
    paint()
    return () => { alive = false; cleanup() }
  }, [])

  return <div className="landing" data-theme="light" ref={root}>
    <a className="skip" href="#hero">Skip to content</a>
    <header className="pill-nav">
      <Link to="/" className="wordmark" aria-label={PRODUCT_NAME}><span className="seal" aria-hidden="true" />LRA</Link>
      <nav aria-label="Sections"><ul>{t.nav.map(([id, label]) => <li key={id}><a href={`#${id}`}>{label}</a></li>)}</ul></nav>
      <div className="nav-actions"><Link to="/login" className="btn ghost">{t.signIn}</Link><Link to={enterHref} className="btn">{t.openWorkbench}</Link></div>
    </header>
    <main>
      <section id="story" className="hero-track" aria-labelledby="hero-title">
        <div className="stage">
          <canvas ref={canvas} className="paper-canvas" aria-hidden="true" />
          <div className="veil" aria-hidden="true" />
          <div id="hero" className="intro">
            <p className="kicker">{t.kicker}</p>
            <h1 id="hero-title" className="display">{t.headline[0]}<br /><em>{t.headline[1]}</em></h1>
            <p className="lede">{t.lede}</p>
            <div className="ctas"><Link to={enterHref} className="btn">{t.ctaPrimary}</Link><a href="#workflow" className="btn ghost">{t.ctaSecondary}</a></div>
            <p className="hint" aria-hidden="true">{t.scrollHint}</p>
          </div>
          <ol className="beats">{t.beats.map(beat => <li key={beat.id} id={beat.id} className="beat">
            <span className="beat-n">{beat.n} / 03</span><h2>{beat.title}</h2><p>{beat.body}</p></li>)}</ol>
        </div>
      </section>

      <section id="governance" className="statement" aria-label="Principle">
        <p className="display-sm">{t.statement.split(' ').map((word, i) => <span key={i} className="w">{word} </span>)}</p>
      </section>

      <section id="reveal" className="reveal" aria-labelledby="reveal-title">
        <p className="kicker">{t.revealKicker}</p>
        <h2 id="reveal-title" className="display-md">{t.revealTitle}</h2>
        <div className="reveal-stage"><ReviewMock /></div>
        <p className="note">{t.revealNote}</p>
      </section>

      <section id="workflow" className="flow" aria-labelledby="flow-title">
        <h2 id="flow-title" className="display-md">{t.flowTitle}</h2>
        <svg className="flow-line" viewBox="0 0 1000 120" preserveAspectRatio="none" aria-hidden="true">
          <path className="flow-thread" pathLength="1" d="M10 60 C 160 -10, 260 130, 400 60 S 640 -10, 780 60 S 940 120, 990 60" />
        </svg>
        <ol className="flow-steps">{t.flow.map(([title, body], i) => <li key={title} className="flow-step">
          <span className="step-n">{String(i + 1).padStart(2, '0')}</span><h3>{title}</h3><p>{body}</p></li>)}</ol>
      </section>

      <section id="pillars" className="pillars" aria-labelledby="pillars-title">
        <h2 id="pillars-title" className="display-md">{t.pillarsTitle}</h2>
        <div className="pillar-grid">{t.pillars.map(p => <article key={p.id} id={p.id} className="pillar">
          <h3>{p.title}</h3><p>{p.body}</p></article>)}</div>
      </section>

      <section className="proof" aria-labelledby="proof-title">
        <h2 id="proof-title" className="display-md">{t.proofTitle}</h2>
        <dl className="proof-grid">{t.proof.map(item => <div key={item.label}>
          <dt>{item.label}</dt><dd><span className="count" data-value={item.value}>{item.value}</span><sup>*</sup></dd></div>)}</dl>
        <p className="note">* {t.proofNote}</p>
      </section>

      <section id="sovereignty" className="split" aria-labelledby="sov-title">
        <div><h2 id="sov-title" className="display-md">{t.sovereigntyTitle}</h2><p>{t.sovereigntyBody}</p></div>
        <div id="ecosystem"><h2 className="display-sm">{t.ecosystemTitle}</h2>
          <dl className="bounds">{t.ecosystem.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl></div>
      </section>

      <section id="enter" className="closing" aria-labelledby="enter-title">
        <h2 id="enter-title" className="display">{t.closingTitle}</h2>
        <p className="lede">{t.closingBody}</p>
        <div className="ctas"><Link to={enterHref} className="btn">{t.ctaPrimary}</Link><Link to="/login" className="btn ghost">{t.signIn}</Link></div>
      </section>
    </main>
    <footer className="foot"><p>{DEVELOPMENT_NOTICE}</p><p className="muted">{t.footer}</p></footer>
  </div>
}
