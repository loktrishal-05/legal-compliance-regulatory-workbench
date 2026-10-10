import test from 'node:test'
import assert from 'node:assert/strict'
import { categoryLabel, answerState, nextFocusIndex, voiceCapabilities, createRecognition, speakLocally, transcriptFromEvent } from './assistantModel.js'

test('statement and response states never turn an answer into an approved legal conclusion', () => {
  assert.equal(categoryLabel('source_fact'), 'Source fact')
  assert.equal(categoryLabel('observation'), 'Observation')
  assert.equal(categoryLabel('interpretation'), 'Interpretation — needs review')
  assert.equal(categoryLabel('recommendation'), 'Recommendation — needs review')
  assert.equal(categoryLabel('accepted'), 'Unclassified statement')
  assert.equal(answerState({ status: 'degraded' }).label, 'Service degraded')
  assert.equal(answerState({ status: 'refused' }).label, 'No supported answer')
  assert.equal(answerState({ status: 'qualified' }).label, 'Qualified source matches')
  assert.equal(answerState({ status: 'approved' }).label, 'Unrecognized response')
})

test('focus cycling traps either direction and handles an empty dialog', () => {
  assert.equal(nextFocusIndex(2, 3, false), 0)
  assert.equal(nextFocusIndex(0, 3, true), 2)
  assert.equal(nextFocusIndex(-1, 3, false), 0)
  assert.equal(nextFocusIndex(0, 0, false), null)
})

test('recognition is never constructed without an explicit opt-in and is hidden when unsupported', () => {
  let constructed = 0
  class FakeRecognition { constructor() { constructed++ } }
  assert.equal(createRecognition(FakeRecognition, false), null)
  assert.equal(createRecognition(FakeRecognition, 'true'), null)
  assert.equal(constructed, 0)
  assert.ok(createRecognition(FakeRecognition, true) instanceof FakeRecognition)
  assert.equal(constructed, 1)
  assert.equal(voiceCapabilities({}).input, false)
  assert.equal(voiceCapabilities({ SpeechRecognition: FakeRecognition }).input, true)
})

test('read aloud uses only a browser-reported local voice and never falls back to a cloud/default voice', () => {
  const calls = []
  const synth = { getVoices: () => [{ name: 'Remote', localService: false }], speak: v => calls.push(v), cancel: () => {} }
  class Utterance { constructor(text) { this.text = text } }
  assert.equal(speakLocally('Synthetic source quote', synth, Utterance), false)
  assert.equal(calls.length, 0)
  synth.getVoices = () => [{ name: 'Local system voice', localService: true, lang: 'en-US' }]
  assert.equal(speakLocally('Synthetic source quote', synth, Utterance), true)
  assert.equal(calls[0].voice.localService, true)
  assert.equal(calls[0].text, 'Synthetic source quote')
})

test('only final recognition is returned for review, bounded, without any network or automatic send', () => {
  assert.equal(transcriptFromEvent({ resultIndex: 0, results: [{ isFinal: false, 0: { transcript: 'interim' } }] }), '')
  assert.equal(transcriptFromEvent({ resultIndex: 0, results: [{ isFinal: true, 0: { transcript: 'How do I upload?' } }] }), 'How do I upload?')
  assert.ok(transcriptFromEvent({ results: [{ isFinal: true, 0: { transcript: 'a'.repeat(4000) } }] }).length <= 2000)
})
