export const COMPLIANCE_STATES = ['satisfied', 'partially_satisfied', 'unsatisfied', 'insufficient_evidence', 'not_applicable', 'needs_review']
export const readableLabel = value => String(value ?? 'Not recorded').replaceAll('_', ' ')
export const displayTime = value => value ? new Date(value).toLocaleString() : 'Not confirmed'

export function dueInView(item, params) {
  const due = Date.parse(item.due_at)
  if (params.get('overdue') === 'true' && !(Number.isFinite(due) && due < Date.now())) return false
  for (const [key, lower] of [['from', true], ['until', false]]) {
    const bound = Date.parse(params.get(key))
    if (Number.isFinite(bound) && !(Number.isFinite(due) && (lower ? due >= bound : due < bound))) return false
  }
  return true
}

export function donutSlices(entries) {
  const total = entries.reduce((sum, item) => sum + item.count, 0)
  let offset = 0
  return entries.map(item => {
    const length = total ? item.count / total * 100 : 0
    const slice = { ...item, offset, length }
    offset += length
    return slice
  })
}

export function countEntries(counts, href) {
  if (!counts || typeof counts !== 'object') return null
  return Object.entries(counts).map(([key, count]) => ({ key, label: readableLabel(key), count, href: href(key) }))
    .filter(item => Number.isInteger(item.count) && item.count >= 0)
}

const addDays = (date, days) => new Date(Date.parse(`${date}T00:00:00Z`) + days * 86400000).toISOString().slice(0, 10)

// Dashboard obligations_due -> bar entries; each week drills into a half-open [week, week+7d) obligations view.
export function weekEntries(due) {
  if (!Array.isArray(due?.weeks)) return null
  const weeks = due.weeks.filter(w => Number.isInteger(w.count)).map(w => ({ key: w.week_start, label: `Week of ${w.week_start}`,
    count: w.count, href: `/app/legal/obligations?from=${w.week_start}&until=${addDays(w.week_start, 7)}` }))
  return Number.isInteger(due.overdue)
    ? [{ key: 'overdue', label: 'Overdue', count: due.overdue, href: '/app/legal/obligations?overdue=true', alert: true }, ...weeks] : weeks
}

// Axis ceiling for count charts: 1-2-5 steps, so gridlines land on whole, readable numbers.
export function niceMax(value) {
  if (!(value > 0)) return 1
  if (value <= 5) return Math.ceil(value)
  const magnitude = 10 ** Math.floor(Math.log10(value))
  return [1, 2, 5, 10].map(step => step * magnitude).find(step => step >= value)
}

export const share = (count, total) => (total > 0 ? Math.round(count / total * 100) : 0)
