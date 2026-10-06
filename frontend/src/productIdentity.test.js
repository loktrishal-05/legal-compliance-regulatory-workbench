import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter, RouterProvider, createMemoryRouter } from 'react-router'
import { createServer } from 'vite'

const product = 'Legal & Regulatory Assurance Platform'
const vite = () => createServer({ configFile: false, server: { middlewareMode: true, hmr: false }, optimizeDeps: { noDiscovery: true, entries: [] }, esbuild: { jsx: 'automatic' } })

test('browser and installation metadata identify the legal development product', () => {
  const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8')
  const manifest = JSON.parse(readFileSync(new URL('../public/manifest.webmanifest', import.meta.url), 'utf8'))
  const pkg = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'))
  const lock = JSON.parse(readFileSync(new URL('../package-lock.json', import.meta.url), 'utf8'))
  assert.match(html, /<title>Legal &amp; Regulatory Assurance Platform<\/title>/)
  assert.equal(manifest.name, product)
  assert.equal(pkg.name, 'legal-compliance-regulatory-workbench-frontend')
  assert.equal(lock.name, pkg.name)
  assert.equal(lock.packages[''].name, pkg.name)
  assert.ok(manifest.icons.every(icon => icon.src.includes('legal-')))
})

test('active identity and landing distinguish planned legal work from legacy infrastructure', async () => {
  const server = await vite()
  try {
    const { Logo } = await server.ssrLoadModule('/src/components/ui.jsx')
    const logo = renderToStaticMarkup(createElement(Logo))
    assert.match(logo, /alt="Legal &amp; Regulatory Assurance Platform"/)
    assert.ok(!logo.includes('sovereign-'))
    const { default: LandingPage } = await server.ssrLoadModule('/src/features/landing/LandingPage.jsx')
    const html = renderToStaticMarkup(createElement(MemoryRouter, null, createElement(LandingPage)))
    assert.match(html, /Legal &amp; Regulatory/)
    assert.match(html, /Development migration/)
    assert.match(html, /not yet available/i)
    for (const obsolete of ['Industrial intelligence', 'your plant.', 'Sovereign AI Workbench', '890', 'workbench-dashboard.webp', 'sovereign-mark.png']) assert.ok(!html.includes(obsolete), obsolete)
    assert.ok(!html.includes('<video'))
  } finally { await server.close() }
})

test('active sign-in uses neutral media and honest migration copy', async () => {
  const server = await vite()
  try {
    const { default: AuthLayout } = await server.ssrLoadModule('/src/features/auth/AuthLayout.jsx')
    const router = createMemoryRouter([{ path: '/login', handle: { authMedia: 'login', title: 'Sign in' }, element: createElement(AuthLayout) }], { initialEntries: ['/login'] })
    const html = renderToStaticMarkup(createElement(RouterProvider, { router }))
    assert.ok(!html.includes('/assets/auth/auth-bg-') && !html.includes('<video'))
    assert.match(html, /Development migration/)
    assert.ok(!html.includes('nothing leaves your infrastructure'))
    router.dispose()
  } finally { await server.close() }
})

test('help keeps original terms clearly labelled as legacy instead of rewriting consent', async () => {
  const server = await vite()
  try {
    const { ResourcesView } = await server.ssrLoadModule('/src/features/resources/ResourcesView.jsx')
    const html = renderToStaticMarkup(createElement(MemoryRouter, null, createElement(ResourcesView)))
    assert.match(html, /Legacy migration terms/)
    assert.match(html, /legal-platform terms.*pending approval/i)
    assert.match(html, /sovereign-workbench-terms-v1.0.docx/)
  } finally { await server.close() }
})
