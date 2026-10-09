import assert from 'node:assert/strict'
import test from 'node:test'
import { demoAccounts } from './demoAccount.js'

test('demo sign-in is off by default and for any value other than exactly "true"', () => {
  assert.deepEqual(demoAccounts({}), [])
  assert.deepEqual(demoAccounts({ VITE_DEMO_MODE: 'TRUE', VITE_DEMO_ADMIN_PASSWORD: 'x' }), [])
  assert.deepEqual(demoAccounts({ VITE_DEMO_MODE: '1', VITE_DEMO_ADMIN_PASSWORD: 'x' }), [])
})

test('demo mode lists only roles whose synthetic password is configured', () => {
  const accounts = demoAccounts({ VITE_DEMO_MODE: 'true', VITE_DEMO_COUNSEL_PASSWORD: 'synthetic-counsel',
    VITE_DEMO_OWNER_USERNAME: 'owner@demo.test', VITE_DEMO_OWNER_PASSWORD: 'synthetic-owner' })
  assert.deepEqual(accounts.map(a => [a.role, a.username]), [['counsel', 'demo-counsel'], ['owner', 'owner@demo.test']])
  assert.deepEqual(demoAccounts({ VITE_DEMO_MODE: 'true' }), [])
})
