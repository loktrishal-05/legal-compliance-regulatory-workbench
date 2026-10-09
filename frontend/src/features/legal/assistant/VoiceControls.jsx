import { useEffect, useRef, useState } from 'react'
import { createRecognition, speakLocally, transcriptFromEvent, voiceCapabilities, VOICE_INPUT_NOTICE } from './assistantModel.js'

export default function VoiceControls({ answerText = '', onTranscript }) {
  const [capabilities, setCapabilities] = useState(() => voiceCapabilities())
  const [optedIn, setOptedIn] = useState(false)
  const [listening, setListening] = useState(false)
  const [notice, setNotice] = useState('')
  const recognition = useRef(null)
  const consent = useRef(false)
  const transcriptHandler = useRef(onTranscript)
  useEffect(() => { transcriptHandler.current = onTranscript }, [onTranscript])
  useEffect(() => {
    const synth = window.speechSynthesis
    const refresh = () => setCapabilities(voiceCapabilities())
    synth?.addEventListener?.('voiceschanged', refresh)
    return () => { consent.current = false; synth?.removeEventListener?.('voiceschanged', refresh); recognition.current?.abort(); synth?.cancel() }
  }, [])

  function toggle(value) {
    consent.current = value
    setOptedIn(value)
    if (!value) { recognition.current?.abort(); setListening(false) }
  }

  function dictate() {
    if (listening) { recognition.current?.stop(); return }
    const instance = createRecognition(window.SpeechRecognition || window.webkitSpeechRecognition, consent.current)
    if (!instance) return
    recognition.current = instance
    instance.continuous = false
    instance.interimResults = false
    instance.onstart = () => { setListening(true); setNotice('Listening. Review the transcript before sending.') }
    instance.onend = () => setListening(false)
    instance.onerror = () => { setListening(false); setNotice('Dictation unavailable or microphone permission denied. You can type instead.') }
    instance.onresult = event => {
      if (!consent.current) return
      const text = transcriptFromEvent(event)
      if (text) { transcriptHandler.current?.(text); setNotice('Transcript inserted. Review it, then choose Send.') }
    }
    try { instance.start() } catch { setNotice('Dictation could not start. Type your question instead.') }
  }

  return <div className="assistant-voice">
    {capabilities.output && <div className="assistant-voice-actions">
      <button type="button" className="button" disabled={!answerText || !capabilities.localOutput}
        onClick={() => { if (!speakLocally(answerText)) setNotice('No browser-reported local voice is available.') }}>Read aloud locally</button>
      <button type="button" className="button" onClick={() => window.speechSynthesis.cancel()}>Stop reading</button>
      {!capabilities.localOutput && <span className="muted small">No local system voice available.</span>}
    </div>}
    {capabilities.input && <><label className="assistant-voice-consent">
      <input type="checkbox" checked={optedIn} onChange={event => toggle(event.target.checked)} />
      <span>{VOICE_INPUT_NOTICE}</span>
    </label><button type="button" className="button" disabled={!optedIn} aria-pressed={listening} onClick={dictate}>
      {listening ? 'Stop dictation' : 'Start dictation'}</button></>}
    {notice && <p className="small muted" role="status">{notice}</p>}
  </div>
}
