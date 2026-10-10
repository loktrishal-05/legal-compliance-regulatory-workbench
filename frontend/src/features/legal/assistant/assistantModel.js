export const VOICE_INPUT_NOTICE = "Voice input may be processed by your browser vendor's speech service; do not dictate confidential content"

export function categoryLabel(value) {
  return ({ source_fact: 'Source fact', fact: 'Source fact', observation: 'Observation',
    interpretation: 'Interpretation — needs review', recommendation: 'Recommendation — needs review' })[value] || 'Unclassified statement'
}

export function answerState(answer) {
  return ({ answered: { label: 'Guide sections', tone: 'neutral' }, qualified: { label: 'Qualified source matches', tone: 'review' },
    needs_review: { label: 'Needs human review', tone: 'review' }, refused: { label: 'No supported answer', tone: 'review' },
    degraded: { label: 'Service degraded', tone: 'review' } })[answer?.status] || { label: 'Unrecognized response', tone: 'review' }
}

export function nextFocusIndex(index, count, reverse = false) {
  if (!count) return null
  if (index < 0) return reverse ? count - 1 : 0
  return (index + (reverse ? -1 : 1) + count) % count
}

export function voiceCapabilities(scope = globalThis.window) {
  const recognition = scope?.SpeechRecognition || scope?.webkitSpeechRecognition
  const synth = scope?.speechSynthesis
  return { input: typeof recognition === 'function', output: Boolean(synth?.speak),
    localOutput: Boolean(synth?.getVoices?.().some(voice => voice.localService === true)) }
}

export function createRecognition(Constructor, optedIn) {
  return optedIn === true && typeof Constructor === 'function' ? new Constructor() : null
}

export function speakLocally(text, synth = globalThis.window?.speechSynthesis, Utterance = globalThis.window?.SpeechSynthesisUtterance) {
  const voice = synth?.getVoices?.().find(v => v.localService === true)
  if (!voice || !Utterance || !text?.trim()) return false
  synth.cancel()
  const speech = new Utterance(text.slice(0, 6000))
  speech.voice = voice
  speech.lang = voice.lang
  speech.rate = 1
  synth.speak(speech)
  return true
}

export function transcriptFromEvent(event) {
  const final = []
  for (let i = event?.resultIndex || 0; i < (event?.results?.length || 0); i++) {
    if (event.results[i].isFinal) final.push(event.results[i][0]?.transcript || '')
  }
  return final.join(' ').trim().slice(0, 2000)
}
