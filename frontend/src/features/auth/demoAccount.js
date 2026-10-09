// Demo sign-in helper. OFF unless VITE_DEMO_MODE === 'true' at build time. It only FILLS the form (never submits).
// VITE_* values are embedded in the public bundle: use only for synthetic demo accounts, never real credentials.
export const DEMO_ROLES = [
  ['admin', 'Workspace admin'], ['counsel', 'Legal counsel (reviewer)'], ['owner', 'Business owner'],
  ['auditor', 'Auditor (read-only)'], ['compliance', 'Compliance reviewer'], ['analyst', 'Analyst'],
]

export function demoAccounts(env = {}) {
  if (env.VITE_DEMO_MODE !== 'true') return []
  return DEMO_ROLES.map(([role, label]) => ({
    role, label,
    username: env[`VITE_DEMO_${role.toUpperCase()}_USERNAME`] || `demo-${role}`,
    password: env[`VITE_DEMO_${role.toUpperCase()}_PASSWORD`] || '',
  })).filter(account => account.password)
}
