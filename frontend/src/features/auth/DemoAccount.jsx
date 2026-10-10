// "Use demo account": fills the sign-in fields for a synthetic demo role. Rendered only in demo builds.
import { useState } from 'react'
import { demoAccounts } from './demoAccount.js'

export function DemoAccount({ onFill, env = import.meta.env }) {
  const accounts = demoAccounts(env)
  const [role, setRole] = useState(accounts[0]?.role || '')
  if (!accounts.length) return null
  const fill = () => {
    const account = accounts.find(item => item.role === role)
    if (account) onFill(account.username, account.password)
  }
  return <section className="demo-account" aria-labelledby="demo-account-title">
    <h2 id="demo-account-title" className="small">Demo data only — synthetic</h2>
    <div className="toolbar">
      <label>Demo role<select value={role} onChange={event => setRole(event.target.value)}>
        {accounts.map(account => <option key={account.role} value={account.role}>{account.label}</option>)}
      </select></label>
      <button type="button" onClick={fill}>Use demo account</button>
    </div>
    <p className="muted small">Fills the fields only; review and press Sign in yourself.</p>
  </section>
}
