import assert from 'node:assert/strict'
import test from 'node:test'
import { BEAT_AT, beatOpacity, createPages, pageState, sealProgress, threadProgress } from './paperThread.js'

test('pages are deterministic and stay inside the viewport', () => {
  const a = createPages(26, 7), b = createPages(26, 7)
  assert.deepEqual(a, b)
  for (const page of a) {
    assert.ok(page.x > 0 && page.x < 1 && page.y > 0 && page.y < 1)
    assert.ok(page.depth >= 0.55 && page.depth <= 1)
  }
})

test('story maths: scatter -> stitch -> bind, clamped at both ends', () => {
  const pages = createPages()
  const scattered = pageState(pages[3], 0, pages.length)
  const bound = pageState(pages[3], 1, pages.length)
  assert.equal(scattered.align, 0)
  assert.equal(bound.bind, 1)
  for (const page of pages) assert.ok(Math.abs(pageState(page, 1, pages.length).x - 0.68) <= 0.0021) // one fanned stack
  assert.equal(threadProgress(0), 0)
  assert.equal(threadProgress(1), 1)
  assert.equal(sealProgress(0.5), 0)
  assert.equal(sealProgress(1), 1)
  assert.deepEqual(pageState(pages[0], -5, pages.length), pageState(pages[0], 0, pages.length))
})

test('each story beat peaks at its own scroll position only', () => {
  BEAT_AT.forEach((at, i) => {
    assert.equal(beatOpacity(at, at), 1)
    BEAT_AT.filter((_, j) => j !== i).forEach(other => assert.equal(beatOpacity(other, at), 0))
  })
})
