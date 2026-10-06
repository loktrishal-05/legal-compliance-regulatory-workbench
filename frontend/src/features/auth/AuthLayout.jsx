import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, Outlet, useMatches } from 'react-router'
import { playbackMode, readMediaEnvironment } from './authModel.js'
import { Icon, Logo } from '../../components/ui.jsx'
import { useBackendHealth } from '../../hooks/useBackendHealth.js'
import '../../styles/auth.css'
import { DEVELOPMENT_AUTH_MEDIA, PRODUCT_NAME } from '../../product.js'

// Moving between sign-in, sign-up and recovery crossfades the scene instead of cutting it.
function useCrossfade(media) {
  const [layers, setLayers] = useState([media])
  const top = layers[layers.length - 1]
  if (top.video !== media.video) setLayers([top, media])
  useEffect(() => {
    if (layers.length < 2) return undefined
    const timer = setTimeout(() => setLayers(current => current.slice(-1)), 1200)
    return () => clearTimeout(timer)
  }, [layers])
  return layers[layers.length - 1].video === media.video ? layers : [media]
}

// Presentational backdrop: the poster always renders first; the video is decorative and silent.
export function AuthBackdrop({ media, mode, onFailed, videoRef }) {
  const [ready, setReady] = useState(false)
  const layers = useCrossfade(media)
  const attach = useCallback(element => {
    if (videoRef) videoRef.current = element
    if (!element) return
    element.muted = true // React does not reflect `muted`; autoplay policies require it.
    element.defaultMuted = true
    element.play?.()?.catch?.(() => onFailed?.(true))
  }, [videoRef, onFailed])
  return <div className="auth-media" aria-hidden="true">
    {layers.map((layer, index) => { const current = index === layers.length - 1
      return <div key={layer.video} className={`auth-layer${current ? '' : ' is-leaving'}`}>
        <img className="auth-poster" src={layer.poster} alt="" decoding="async" fetchPriority="high" />
        {mode === 'video' && current && <video ref={attach} className={`auth-video${ready ? ' is-ready' : ''}`}
          src={layer.video} poster={layer.poster} autoPlay muted loop playsInline preload="metadata" tabIndex={-1}
          disablePictureInPicture disableRemotePlayback onLoadedData={() => setReady(true)} onError={() => onFailed?.(true)} />}
      </div> })}
    <div className="auth-grade" /><div className="auth-grain" />
  </div>
}

// Only verified product facts; the live line reflects the real backend health probe.
const STORIES = {
  login: 'Evidence first. Decisions stay with people.',
  signup: 'Access starts with an authorized account.',
  recovery: 'Recover access through configured account services.',
}
const PROOF = [
  ['shield', 'Private AI policy', 'local/private inference only; provisioning is required'],
  ['agent', 'Development migration', 'legal workflows are not yet available'],
  ['check', 'Human review', 'existing advisory review infrastructure is retained'],
]

export default function AuthLayout() {
  const matches = useMatches()
  const handle = [...matches].reverse().find(match => match.handle?.authMedia)?.handle || {}
  const [env, setEnv] = useState(null) // Unknown until mounted: poster first, always.
  const [failed, setFailed] = useState(false)
  const [userPaused, setUserPaused] = useState(false)
  const video = useRef(null)
  const { status } = useBackendHealth()
  const media = DEVELOPMENT_AUTH_MEDIA
  const mode = failed || !media.video ? 'poster' : playbackMode(env)

  useEffect(() => { document.title = `${handle.title || 'Sign in'} · ${PRODUCT_NAME}` }, [handle.title])
  useEffect(() => {
    const update = () => setEnv(readMediaEnvironment())
    update()
    const query = window.matchMedia?.('(prefers-reduced-motion: reduce)')
    query?.addEventListener?.('change', update)
    return () => query?.removeEventListener?.('change', update)
  }, [])
  // Pause in hidden tabs; resume only if the viewer did not pause it.
  useEffect(() => {
    const onVisibility = () => {
      const element = video.current
      if (!element) return
      if (document.hidden) element.pause()
      else if (!userPaused) element.play?.()?.catch?.(() => setFailed(true))
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => document.removeEventListener('visibilitychange', onVisibility)
  }, [userPaused])
  function togglePause() {
    const element = video.current
    if (!element) return
    if (userPaused) { element.play?.()?.catch?.(() => setFailed(true)); setUserPaused(false) } else { element.pause(); setUserPaused(true) }
  }
  const online = status === 'Connected'

  return <div className="auth-shell" data-theme="dark" data-placement={media.placement} data-still={userPaused || mode !== 'video' || undefined}>
    <AuthBackdrop media={media} mode={mode} videoRef={video} onFailed={setFailed} />
    <header className="auth-top">
      <Link to="/" className="auth-brand" aria-label={`${PRODUCT_NAME} home`}><Logo variant="horizontal" decorative /></Link>
      <div className="auth-top-actions">
        <span className="auth-live" data-state={online ? 'ok' : status === 'Checking' ? 'pending' : 'bad'} role="status">
          <span className="auth-live-dot" aria-hidden="true" /><span className="auth-live-long">{online ? 'Backend process online' : status === 'Checking' ? 'Checking backend…' : 'Backend unavailable'}</span><span className="auth-live-short" aria-hidden="true">{online ? 'Online' : status === 'Checking' ? 'Checking' : 'Offline'}</span></span>
        {mode === 'video' && <button type="button" className="icon-button auth-pause" onClick={togglePause} aria-pressed={userPaused}
          aria-label={userPaused ? 'Play background video' : 'Pause background video'}><Icon name={userPaused ? 'play' : 'pause'} size={18} /></button>}
      </div>
    </header>
    <main id="main" className="auth-stage">
      <section className="auth-story" aria-label={`About ${PRODUCT_NAME}`}>
        <p className="auth-story-title" key={handle.authMedia}>{STORIES[handle.authMedia] || STORIES.login}</p>
        <p className="auth-story-lede">{PRODUCT_NAME}. Contract intelligence, compliance monitoring and cited summaries are the target; this build currently provides the reusable platform foundation.</p>
        <ul className="auth-proof">{PROOF.map(([icon, figure, text]) => <li key={figure}><Icon name={icon} size={18} /><span><strong>{figure}</strong> {text}</span></li>)}</ul>
      </section>
      <div className="auth-card"><Outlet /></div>
    </main>
    <footer className="auth-foot">Development foundation · server-controlled accounts · no legal advice or compliance certification</footer>
  </div>
}
