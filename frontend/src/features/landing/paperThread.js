// Procedural hero: scattered pages -> a red thread stitches them -> they bind into one sealed stack.
// Pure layout maths (testable) + a canvas painter driven only by scroll progress p in [0, 1] and a slow idle time.
// When the light film arrives, a frame-sequence painter replaces drawScene() behind the same (ctx, w, h, p) call.
import { clamp, easeInOut, smoothstep } from './landingModel.js'

export const PALETTE = { ground: '#F3EFE6', paper: '#FBF8F2', ink: '#1C2330', rule: 'rgba(28,35,48,0.10)', accent: '#8E2C36', ribbon: '#2E6A4E' }

function rng(seed) {
  let s = seed >>> 0
  return () => { s = (s + 0x6d2b79f5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296 }
}

// Deterministic page set in normalized space (x, y in 0..1 of the viewport; depth 0.55..1).
export function createPages(count = 26, seed = 7) {
  const r = rng(seed)
  return Array.from({ length: count }, (_, i) => ({
    i,
    x: 0.30 + r() * 0.66, y: 0.10 + r() * 0.80,
    depth: 0.55 + r() * 0.45,
    rot: (r() - 0.5) * 1.4,
    drift: 0.4 + r() * 0.8, phase: r() * Math.PI * 2,
  }))
}

// Where page i sits at progress p: scattered (p<.32) -> threaded column (.32-.66) -> bound stack (>.66).
export function pageState(page, p, count, t = 0) {
  const align = smoothstep(0.32, 0.66, p)
  const bind = smoothstep(0.66, 0.92, p)
  const order = page.i / Math.max(1, count - 1)
  const wobble = (1 - align) * 0.012 * Math.sin(t * page.drift + page.phase)
  const column = { x: 0.62 + (order - 0.5) * 0.30, y: 0.50 + Math.sin(order * Math.PI * 2) * 0.10 }
  const stack = { x: 0.68 + (page.i % 3 - 1) * 0.002, y: 0.58 - page.i * 0.0035 }
  const x = page.x + (column.x - page.x) * align + (stack.x - column.x) * bind
  const y = page.y + wobble + (column.y - page.y) * align + (stack.y - column.y) * bind
  const rot = page.rot * (1 - align) + (order - 0.5) * 0.18 * align * (1 - bind) + (page.i % 2 ? 0.012 : -0.012) * bind
  const depth = page.depth + (0.86 - page.depth) * align + (1 - 0.86) * bind
  return { x, y, rot, depth, align, bind }
}

// Fraction of the thread drawn (0..1) and the seal reveal (0..1).
export const threadProgress = p => easeInOut(smoothstep(0.42, 0.74, p)) // starts once pages near their column
export const sealProgress = p => smoothstep(0.84, 0.97, p)

function drawPage(ctx, s, size, shadow = true) {
  const scale = s.depth * (1 + 0.9 * s.bind) // the bound record grows into the hero's focal point
  const w = size * 0.74 * scale, h = size * scale
  ctx.save()
  ctx.translate(s.x, s.y)
  ctx.rotate(s.rot)
  ctx.shadowColor = shadow ? 'rgba(28,35,48,0.22)' : 'transparent'
  ctx.shadowBlur = 24 * scale
  ctx.shadowOffsetY = 10 * scale
  ctx.fillStyle = PALETTE.paper
  ctx.fillRect(-w / 2, -h / 2, w, h)
  ctx.shadowColor = 'transparent'
  ctx.strokeStyle = 'rgba(28,35,48,0.08)'
  ctx.lineWidth = 1
  ctx.strokeRect(-w / 2, -h / 2, w, h)
  ctx.fillStyle = PALETTE.rule
  for (let k = 0; k < 7; k++) ctx.fillRect(-w * 0.36, -h * 0.34 + k * h * 0.1, w * (k === 6 ? 0.4 : 0.72), Math.max(1, h * 0.012))
  ctx.restore()
}

export function drawScene(ctx, width, height, p, pages, t = 0) {
  ctx.fillStyle = PALETTE.ground
  ctx.fillRect(0, 0, width, height)
  // Daylight from the upper left: a soft warm wash, never a glow blob.
  const light = ctx.createLinearGradient(0, 0, width, height)
  light.addColorStop(0, 'rgba(255,253,247,0.9)')
  light.addColorStop(0.55, 'rgba(255,253,247,0)')
  ctx.fillStyle = light
  ctx.fillRect(0, 0, width, height)
  const size = Math.min(width, height) * 0.22
  const states = pages.map(page => {
    const s = pageState(page, p, pages.length, t)
    return { ...s, x: s.x * width, y: s.y * height }
  })
  // Once bound, only the bottom sheet casts a shadow so the stack reads as one object, not a smudge.
  const bound = states[0].bind > 0.5
  ;[...states].sort((a, b) => a.depth - b.depth || b.y - a.y).forEach((s, k) => drawPage(ctx, s, size, !bound || k === 0))
  // The thread passes through one precise point on each page, in order.
  const tp = threadProgress(p)
  if (tp > 0) {
    const last = Math.max(1, Math.floor(tp * (states.length - 1)))
    ctx.save()
    ctx.strokeStyle = PALETTE.accent
    ctx.lineWidth = Math.max(1.5, size * 0.012)
    ctx.lineCap = 'round'
    ctx.beginPath()
    const route = states.slice(0, last + 1) // column order is left-to-right by construction
      .map(s => ({ x: s.x - size * 0.18 * s.depth * (1 + 0.9 * s.bind), y: s.y - size * 0.3 * s.depth * (1 + 0.9 * s.bind), bind: s.bind }))
    // Smooth curve through midpoints so the thread reads as one drawn line, never a zigzag.
    ctx.moveTo(route[0].x, route[0].y)
    for (let i = 1; i < route.length - 1; i++) {
      ctx.quadraticCurveTo(route[i].x, route[i].y, (route[i].x + route[i + 1].x) / 2, (route[i].y + route[i + 1].y) / 2)
    }
    const end = route[route.length - 1]
    ctx.lineTo(end.x, end.y)
    ctx.stroke()
    ctx.restore()
  }
  const seal = sealProgress(p)
  if (seal > 0) {
    const top = states.reduce((a, b) => (b.y < a.y ? b : a))
    const k = 1 + 0.9 * top.bind
    ctx.save()
    ctx.globalAlpha = seal
    ctx.fillStyle = PALETTE.ribbon
    ctx.fillRect(top.x + size * 0.2 * k, top.y - size * 0.5 * k, size * 0.035 * k, size * 0.98 * k)
    ctx.fillStyle = PALETTE.accent
    ctx.beginPath()
    ctx.arc(top.x - size * 0.16 * k, top.y - size * 0.3 * k, size * 0.06 * k * (0.6 + 0.4 * seal), 0, Math.PI * 2)
    ctx.fill()
    ctx.restore()
  }
}

// Story beats sit at 22% / 47% / 72% of the hero scroll.
export const BEAT_AT = [0.22, 0.47, 0.72]
export const beatOpacity = (p, at) => clamp(1 - Math.abs(p - at) / 0.13)
