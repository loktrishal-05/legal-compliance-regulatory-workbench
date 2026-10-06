// Landing content model and scroll/canvas maths. Pure and testable.

// Historical industrial acceptance facts only. Never market these as current legal-platform results.
export const PRODUCT_FACTS = {
  hostedAiCalls: 0,
  localModels: 2,
  primaryModel: 'qwen3.5:9b',
  fastModel: 'qwen3.5:4b',
  languages: 3,
  workflowSteps: 5,
  evidenceSources: 5,
  backendTests: 890,
  benchmarkCases: 75,
  frozenBenchmarkFiles: 168,
  asOf: 'September 2026',
}

export const STORY = [
  { id: 'hero', tag: 'LRA-00', title: 'Legal & Regulatory Assurance Platform' },
  { id: 'scattered', tag: 'SRC-01', title: 'Legal evidence across documents' },
  { id: 'unify', tag: 'CORE-02', title: 'A connected compliance model' },
  { id: 'workflow', tag: 'FLOW-03', title: 'The target legal workflow' },
  { id: 'reveal', tag: 'UI-04', title: 'A reusable governed foundation' },
  { id: 'pid', tag: 'DOC-05', title: 'Contract intelligence — planned' },
  { id: 'maintenance', tag: 'DUE-06', title: 'Obligations and evidence freshness — planned' },
  { id: 'governance', tag: 'HITL-07', title: 'Humans approve. The chain remembers.' },
  { id: 'voice', tag: 'REV-08', title: 'Source text before interpretation' },
  { id: 'sovereignty', tag: 'RUN-09', title: 'Private runtime policy' },
  { id: 'ecosystem', tag: 'GOV-10', title: 'Integration boundaries' },
  { id: 'enter', tag: 'GO-11', title: 'Open the development workbench' },
]

export const SOURCES = [
  { id: 'contracts', label: 'Contracts', detail: 'Planned: parties, clauses and obligations', color: '#35d7e8' },
  { id: 'regulations', label: 'Regulations', detail: 'Planned: approved sources and effective versions', color: '#3d8bff' },
  { id: 'policies', label: 'Policies', detail: 'Planned: requirements and control mappings', color: '#2fe0a4' },
  { id: 'evidence', label: 'Evidence', detail: 'Planned: provenance and freshness', color: '#f2a93b' },
  { id: 'reviews', label: 'Human decisions', detail: 'Existing review foundation; legal authority pending', color: '#8b6cff' },
]

export const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value))
export const easeInOut = t => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2)
export const smoothstep = (edge0, edge1, x) => { const t = clamp((x - edge0) / (edge1 - edge0)); return t * t * (3 - 2 * t) }

// Scroll progress (0..1) to a bounded frame index for image-sequence style rendering.
export function progressToFrame(progress, frameCount) {
  if (!Number.isFinite(progress) || frameCount < 1) return 0
  return Math.min(frameCount - 1, Math.max(0, Math.round(clamp(progress) * (frameCount - 1))))
}

// DPR-aware backing store, capped at 2x to bound GPU memory.
export function canvasSize(cssWidth, cssHeight, devicePixelRatio = 1) {
  const dpr = Math.min(2, Math.max(1, devicePixelRatio || 1))
  return { width: Math.max(1, Math.round(cssWidth * dpr)), height: Math.max(1, Math.round(cssHeight * dpr)), dpr }
}

// "object-fit: cover" for canvas drawing.
export function coverRect(sourceWidth, sourceHeight, targetWidth, targetHeight) {
  const scale = Math.max(targetWidth / sourceWidth, targetHeight / sourceHeight)
  const width = sourceWidth * scale
  const height = sourceHeight * scale
  return { x: (targetWidth - width) / 2, y: (targetHeight - height) / 2, width, height }
}

// Deterministic PRNG so every visitor sees the same convergence.
export function seeded(seed) {
  let state = seed >>> 0
  return () => { state = (state + 0x6d2b79f5) >>> 0; let t = state; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296 }
}

export function createParticles(perSource = 60, seed = 20260929) {
  const random = seeded(seed)
  return SOURCES.flatMap((source, sourceIndex) => Array.from({ length: perSource }, (_, index) => {
    const angle = (sourceIndex / SOURCES.length) * Math.PI * 2 - Math.PI / 2
    return { source: sourceIndex, color: source.color, homeAngle: angle,
      jitterX: (random() - 0.5) * 0.18, jitterY: (random() - 0.5) * 0.18,
      ringAngle: ((sourceIndex * perSource + index) / (SOURCES.length * perSource)) * Math.PI * 2,
      delay: random() * 0.25, size: 0.6 + random() * 1.6 }
  }))
}

// Unit-space particle position: scattered clusters (0) converge onto the core ring (1).
export function particlePosition(particle, progress) {
  const t = easeInOut(clamp((progress - particle.delay) / 0.7))
  const homeX = Math.cos(particle.homeAngle) * 0.36 + particle.jitterX
  const homeY = Math.sin(particle.homeAngle) * 0.36 + particle.jitterY
  const ringX = Math.cos(particle.ringAngle) * 0.16
  const ringY = Math.sin(particle.ringAngle) * 0.16
  return { x: homeX + (ringX - homeX) * t, y: homeY + (ringY - homeY) * t, t }
}
