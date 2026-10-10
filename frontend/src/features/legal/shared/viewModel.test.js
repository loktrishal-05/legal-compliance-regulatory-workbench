import test from 'node:test'
import assert from 'node:assert/strict'
import { countEntries, donutSlices, dueInView, niceMax, share, weekEntries } from './viewModel.js'

test('missing and invalid chart counts never become invented zero measurements', () => {
  assert.equal(countEntries(null, () => '/'), null)
  assert.deepEqual(countEntries({ known: 0, unrecorded: null, invalid: -1 }, () => '/').map(x => x.key), ['known'])
  assert.deepEqual(donutSlices([{ count: 0 }]).map(x => x.length), [0])
  const slices = donutSlices([{ count: 1 }, { count: 3 }])
  assert.equal(slices[1].offset + slices[1].length, 100)
})

test('deadline drilldown uses a half-open interval and excludes unconfirmed dates', () => {
  const params = new URLSearchParams('from=2026-10-10T00:00:00Z&until=2026-10-17T00:00:00Z')
  assert.equal(dueInView({ due_at: '2026-10-10T00:00:00Z' }, params), true)
  assert.equal(dueInView({ due_at: '2026-10-17T00:00:00Z' }, params), false)
  assert.equal(dueInView({ due_at: null }, params), false)
})

test('obligation weeks drill into the exact half-open week and keep overdue first', () => {
  const [overdue, week] = weekEntries({ weeks: [{ week_start: '2026-10-28', count: 2 }], overdue: 1 })
  assert.equal(overdue.href, '/app/legal/obligations?overdue=true')
  assert.equal(week.href, '/app/legal/obligations?from=2026-10-28&until=2026-11-04')
  assert.equal(weekEntries(null), null)
})

test('chart axis ceiling uses 1-2-5 steps and percentages never divide by zero', () => {
  assert.deepEqual([0, 1, 4, 6, 12, 37, 180].map(niceMax), [1, 1, 4, 10, 20, 50, 200])
  assert.equal(share(1, 3), 33)
  assert.equal(share(2, 0), 0)
})
